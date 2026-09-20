#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 4인 블로그 에이전트 자동 생성 파이프라인
사용법:
  python scripts/generate_blog.py --topic "만두 HACCP 가열공정 CCP-1B 한계기준 설정"
  python scripts/generate_blog.py                # 큐(knowledge/qa_topics_queue.json)에서 자동 선택
"""

import os
import sys
import json
import argparse
import datetime
import re
import urllib.request
import urllib.error
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def now_kst():
    """ GitHub Actions 러너는 UTC로 돌기 때문에 날짜 계산은 항상 KST 기준으로 통일한다.
    (UTC 기준으로 계산하면 KST 아침 실행 시 outputs 폴더가 전날 날짜로 잡혀
    already_ran_today()가 어제 발행 기록을 오늘 것으로 착각하는 버그가 있었음) """
    return datetime.datetime.now(KST)

# Windows 콘솔 인코딩 방어
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 프로젝트 루트 경로
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(ROOT_DIR, "agents", "cco", "blog_agents")
TOPICS_QUEUE_PATH = os.path.join(ROOT_DIR, "knowledge", "qa_topics_queue.json")
BLOG_PUBLISHED_LOG_PATH = os.path.join(ROOT_DIR, "knowledge", "blog_published_topics.json")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from telegram_sender import send_blog_review_to_telegram, send_document_to_telegram, send_message_to_telegram
except Exception:
    def send_message_to_telegram(message):
        print("[!] telegram_sender 모듈을 불러오지 못해 텔레그램 발송을 건너뜁니다.")
        return False
    def send_document_to_telegram(file_path, caption=None):
        return False
    def send_blog_review_to_telegram(title, post_id, blog_id, html_path):
        return False

from blog_publish_rules import extract_internal_topic_code, strip_internal_topic_code, validate_blog_post


def today_output_dir():
    now = now_kst()
    d = os.path.join(ROOT_DIR, "outputs", now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))
    os.makedirs(d, exist_ok=True)
    return d


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def load_published_topics():
    """ 이미 블로그로 만든 주제 목록 (video 파이프라인의 qa_topics_queue.json status/rendered_file 필드는 건드리지 않음) """
    return load_json(BLOG_PUBLISHED_LOG_PATH, {"published_topics": []})


def mark_topic_published(topic, title, final_path):
    log = load_published_topics()
    log["published_topics"].append({
        "topic": topic,
        "title": title,
        "file": final_path,
        "date": now_kst().strftime("%Y-%m-%d"),
    })
    with open(BLOG_PUBLISHED_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def pick_topic_from_queue():
    """ qa_topics_queue.json에서 아직 블로그로 안 만든 주제를 하나 고른다.
    video 파이프라인의 status/rendered_file 필드는 읽기만 하고 절대 수정하지 않는다. """
    queue = load_json(TOPICS_QUEUE_PATH, {"topics": []})
    published = {p["topic"] for p in load_published_topics().get("published_topics", [])}
    for item in queue.get("topics", []):
        topic = item.get("topic", "")
        if topic and topic not in published:
            return topic
    return None


OUTPUTS_DIR = os.path.join(ROOT_DIR, "outputs", "blog")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

def load_env():
    """로컬 .env와 프로세스 환경변수를 병합한다.

    GitHub Actions Secrets는 프로세스 환경변수로 주입되므로 반드시 포함해야 한다.
    동일한 키가 있으면 배포 환경의 값이 로컬 .env보다 우선한다.
    """
    env_path = os.path.join(ROOT_DIR, ".env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    env.update(os.environ)
    return env

ENV = load_env()

def get_llm_configs():
    """DeepSeek 단일 공급자 사용. 유료 폴백은 의도적으로 차단한다."""
    if ENV.get("DEEPSEEK_API_KEY") and not ENV.get("DEEPSEEK_API_KEY", "").startswith("your_"):
        return [{
            "name": "DeepSeek",
            "api_key": ENV["DEEPSEEK_API_KEY"],
            "base_url": ENV.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            "model": ENV.get("DEEPSEEK_BLOG_MODEL", "deepseek-flash")
        }]
    return []
def get_llm_config():
    configs = get_llm_configs()
    return configs[0] if configs else None


def call_llm(system_prompt, user_content, config):
    """ OpenAI-호환 REST API 호출 """
    url = f"{config['base_url'].rstrip('/')}/chat/completions"
    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    }
    # gpt-5.6 계열은 temperature 커스텀 값을 지원하지 않아(기본값 1만 허용) 모델명에 따라 분기
    if not payload["model"].startswith("gpt-5.6"):
        payload["temperature"] = 0.7

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=240) as response:
        res_body = response.read().decode("utf-8")
        data = json.loads(res_body)
        return data["choices"][0]["message"]["content"]


def call_llm_with_fallback(system_prompt, user_content, configs):
    """ configs를 순서대로 시도, 실패하면 다음 설정(공식 OpenAI 등)으로 자동 대체 """
    last_error = None
    for config in configs:
        try:
            return call_llm(system_prompt, user_content, config), config
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="replace")
            print(f"[!] {config['name']} 호출 실패 ({e.code}): {err_msg[:200]} — 다음 설정으로 대체 시도")
            last_error = e
        except Exception as e:
            print(f"[!] {config['name']} 호출 실패: {e} — 다음 설정으로 대체 시도")
            last_error = e
    raise RuntimeError(f"모든 LLM 설정이 실패했습니다: {last_error}")

def read_prompt(filename):
    """ 에이전트 프롬프트 파일 읽기 """
    path = os.path.join(AGENTS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>| ]', '_', name)[:50]

def run_blog_pipeline(topic):
    raw_topic = topic
    source_code = extract_internal_topic_code(raw_topic)
    topic = strip_internal_topic_code(raw_topic)
    if source_code:
        print(f"[*] 내부 파일 구분코드 제거: {source_code} → 순수 주제만 사용")
    print("\n========================================================")
    print(f"[*] [QA+ 4-Agent Blog Pipeline] 시작")
    print(f"[*] 주제: {topic}")
    print("========================================================\n")
    
    configs = get_llm_configs()
    if not configs:
        raise RuntimeError(
            "유효한 LLM API 키가 없습니다. "
            "DEEPSEEK_API_KEY 환경변수를 확인하세요."
        )

    print(f"[*] LLM 우선순위: {' → '.join(c['name'] + '(' + c['model'] + ')' for c in configs)}")

    # 1단계: 리서치 에이전트
    print("\n[1/3] [리서치] 1단계: 리서치 & 목차 기획 에이전트 가동 중...")
    prompt_1 = read_prompt("01_research_agent.md")
    research_output, research_config = call_llm_with_fallback(prompt_1, f"다음 주제에 대해 심층 리서치 및 목차를 설계해주세요:\n\n주제: {topic}", configs)
    print(f"[+] 1단계 리서치 완료! ({research_config['name']})")

    # 2단계: 작가 에이전트
    print("\n[2/3] [집필] 2단계: 20년 멘토 작가 에이전트 본문 집필 중...")
    prompt_2 = read_prompt("02_writer_agent.md")
    writer_input = f"다음은 리서치 결과입니다:\n\n{research_output}\n\n위 내용을 바탕으로 20년 식품품질 전문가 멘토 페르소나를 적용하여 실무자 블로그 본문 전체를 작성해주세요."
    writer_output, writer_config = call_llm_with_fallback(prompt_2, writer_input, configs)
    print(f"[+] 2단계 원고 집필 완료! ({writer_config['name']})")

    # 3단계: 이미지 기획은 고정 템플릿으로 처리하여 LLM 호출을 제거한다.
    print("\n[3/3] [디자인] 무료 이미지 템플릿 적용 중...")
    image_output = f"""
본문 이미지 1
AI 이미지 프롬프트: `{topic} 식품 품질관리 교육용 대표 이미지, 깔끔한 인포그래픽`
본문 이미지 2
AI 이미지 프롬프트: `{topic} 공정 흐름도와 체크리스트, 실무 교육용 인포그래픽`
본문 이미지 3
AI 이미지 프롬프트: `{topic} HACCP 및 품질관리 핵심 포인트, 깔끔한 교육용 인포그래픽`
"""
    image_prompt_config = {"name": "local-template"}
    print("[+] 3단계 시각자료 기획 완료! (local-template, LLM 호출 없음)")

    # 4단계: 편집장 & QA 검수 에이전트
    print("\n[3/3] [검수/패키징] 4단계: 수석 에디터 & QA 검수 및 패키징 중...")
    prompt_4 = read_prompt("04_editor_agent.md")
    editor_input = f"[본문 원고]\n{writer_output}\n\n[시각자료 기획서]\n{image_output}\n\n위 두 내용을 종합하여 법령/사실관계를 검수하고, SEO 메타데이터와 네이버 블로그/티스토리/워드프레스용 최종 완성본을 패키징해주세요."
    final_package, editor_config = call_llm_with_fallback(prompt_4, editor_input, configs)
    print(f"[+] 4단계 최종 검수 및 패키징 완료! ({editor_config['name']})")
    llm_config = editor_config

    def _extract_html_block(package):
        match = re.search(r"```html\s*(.*?)```", package, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _has_required_image_slots(html):
        if not html:
            return False

        for idx in (1, 2, 3):
            # 각 placeholder가 실제 <img> 태그의 src 속성 안에 있어야
            # 이미지 URL로 치환된 뒤 최종 검증에서 이미지로 인식된다.
            pattern = rf'<img\b[^>]*\bsrc\s*=\s*["\'][^"\']*IMAGE_PLACEHOLDER_{idx}[^"\']*["\'][^>]*>'
            if not re.search(pattern, html, re.IGNORECASE):
                return False

        return True

    body_html = _extract_html_block(final_package)

    # HTML 코드블록 누락 또는 이미지 슬롯 누락 시 편집 단계를 1회 자동 재시도한다.
    if not body_html or not _has_required_image_slots(body_html):
        retry_reasons = []
        if not body_html:
            retry_reasons.append("HTML 코드블록 누락")
        if body_html and not _has_required_image_slots(body_html):
            retry_reasons.append("IMAGE_PLACEHOLDER_1~3 이미지 슬롯 누락")

        print(f"[!] {' / '.join(retry_reasons)} — 에디터 패키징을 1회 재시도합니다.")

        retry_input = f"""
아래 원고와 시각자료 기획서를 Blogger 발행용 최종 패키지로 다시 작성하세요.

반드시 아래 조건을 모두 지키세요.

1. 최종 결과에 반드시 ```html 코드블록을 포함하세요.
2. ```html 코드블록 안에는 Blogger HTML 모드에 그대로 붙여넣을 수 있는 완성된 HTML 본문만 넣으세요.
3. 아래 3개의 이미지 슬롯을 본문의 서로 다른 자연스러운 위치에 반드시 포함하세요.
   - <img src="IMAGE_PLACEHOLDER_1" alt="주제와 관련된 대표 이미지 설명">
   - <img src="IMAGE_PLACEHOLDER_2" alt="주제와 관련된 본문 이미지 설명">
   - <img src="IMAGE_PLACEHOLDER_3" alt="주제와 관련된 본문 이미지 설명">
4. IMAGE_PLACEHOLDER_1, IMAGE_PLACEHOLDER_2, IMAGE_PLACEHOLDER_3는 반드시 각각 <img> 태그의 src 속성 안에 있어야 합니다.
5. 세 placeholder를 삭제하거나 한 위치에 몰아넣거나 텍스트로만 출력하지 마세요.
6. 마크다운 원문만 반환하지 마세요.
7. 기존 최종 패키징 규격의 최종 포스팅 제목, 메타 디스크립션, 카테고리 정보도 유지하세요.
8. 내부 관리코드(EQ003, FS001 같은 코드)는 제목과 공개 본문에 노출하지 마세요.
9. 설명을 덧붙이지 말고 최종 패키지만 반환하세요.

[본문 원고]
{writer_output}

[시각자료 기획서]
{image_output}
"""

        final_package, editor_config = call_llm_with_fallback(prompt_4, retry_input, configs)
        llm_config = editor_config
        body_html = _extract_html_block(final_package)

        if body_html:
            print(f"[+] 에디터 패키징 재시도 완료! ({editor_config['name']})")

    # 재시도 후에도 발행 가능한 HTML 구조가 아니면 이미지 생성/API 비용을 더 쓰기 전에 즉시 실패한다.
    if not body_html:
        raise RuntimeError(
            "에디터가 2회 연속 Blogger용 ```html 코드블록을 생성하지 못했습니다."
        )

    if not _has_required_image_slots(body_html):
        raise RuntimeError(
            "에디터가 재시도 후에도 IMAGE_PLACEHOLDER_1~3을 "
            "각각 <img> 태그의 src 속성에 배치하지 못했습니다."
        )

    # --- 표준 산출물 경로: outputs/{연도}/{월}/{일}/ (blog-osmu 스킬과 동일한 규칙) ---
    dated_dir = today_output_dir()
    safe_topic = sanitize_filename(topic).replace(" ", "_")

    # 최종 재시도 결과를 기준으로 메타데이터를 다시 추출한다.
    title_match = re.search(r"\*\*최종 포스팅 제목\*\*\s*[:：]\s*(.+)", final_package)
    desc_match = re.search(r"\*\*메타 디스크립션[^*]*\*\*\s*[:：]\s*(.+)", final_package)
    title = title_match.group(1).strip() if title_match else topic

    final_html_path = os.path.join(dated_dir, f"[블로그최종]_{safe_topic}.html")

    # 부록/전체 원고 (검토용, md)
    # 재시도가 있었다면 재시도된 최종 패키지를 기록한다.
    raw_path = os.path.join(dated_dir, f"[블로그원본]_{safe_topic}.md")
    full_content = f"""# [QA+ 블로그 생성 결과물] {topic}
생성일시: {now_kst().strftime("%Y-%m-%d %H:%M:%S")} (KST)
적용모델: {llm_config['model']}

================================================================================
{final_package}
================================================================================

[부록: 1단계 리서치 원본]
{research_output}

[부록: 3단계 시각자료 기획 원본]
{image_output}
"""
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    # --- 본문 이미지 실제 생성 + GitHub raw URL로 치환 (IMAGE_PLACEHOLDER_N 그대로 두면 깨진 이미지로 보임) ---
    # 에디터 에이전트가 `[IMAGE_PLACEHOLDER_1]`처럼 대괄호를 붙이거나 안 붙이거나 둘 다 나올 수 있어
    # 대괄호 유무에 상관없이 정규식으로 치환한다 (단순 문자열 replace는 대괄호가 붙으면 못 잡음).
    try:
        from blog_image_generator import generate_and_host_images
        image_urls = generate_and_host_images(image_output, ROOT_DIR, dated_dir, safe_topic)
    except Exception as e:
        print(f"[!] 이미지 생성 단계 오류 (본문은 이미지 없이 진행): {e}")
        image_urls = {}

    def _replace_placeholder(m):
        key = f"IMAGE_PLACEHOLDER_{m.group(1)}"
        return image_urls.get(key, m.group(0))

    body_html = re.sub(r'\[?IMAGE_PLACEHOLDER_(\d+)\]?', _replace_placeholder, body_html)
    # 생성 실패해서 못 채운 placeholder는 img 태그째로 제거 (깨진 이미지 아이콘 방지)
    body_html = re.sub(r'<img[^>]*IMAGE_PLACEHOLDER_\d+[^>]*/?>', '', body_html)

    labels_match = re.search(r"\*\*카테고리\*\*\s*[:：]\s*(.+)", final_package)
    labels = [l.strip() for l in labels_match.group(1).split("/")] if labels_match else None

    # 최종 안전장치: 규칙 위반 글은 파일만 남기지 않고 즉시 실패 처리하여
    # Blogger 임시저장·공개 발행 단계로 절대 넘어가지 않는다.
    validation = validate_blog_post(title, body_html, labels=labels, source_code=source_code, minimum_images=3)
    print(f"[OK] 발행 전 규칙 검사 통과: 고유 이미지 {validation['image_count']}장, 내부코드 0건")

    html_doc = f"""<!-- QA+ 블로그 최종본 — Blogger 편집기 HTML 모드에 붙여넣기 -->
<!-- 제목: {title} -->
<!-- 검색 설명: {desc_match.group(1).strip() if desc_match else ''} -->

{body_html}
"""
    with open(final_html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    # --- Blogger에는 항상 임시저장한다. 공개 발행은 텔레그램 버튼을 누른 뒤에만 실행한다. ---
    publish_status = "ready_to_publish"
    publish_url = None
    publish_post_id = None
    try:
        from blogger_publisher import is_configured, publish_post
        if is_configured():
            result = publish_post(title, body_html, labels=labels, is_draft=True)
            if result.get("ok"):
                publish_status = f"blogger_{result['status']}"
                publish_url = result.get("url")
                publish_post_id = result.get("post_id")
                print(f"[OK] Blogger {result['status']} 완료: {publish_url} (post_id={publish_post_id})")
            else:
                print(f"[!] Blogger 발행 실패 (수동 발행으로 폴백): {result.get('error')}")
        else:
            print("[*] Blogger 자동 발행 미설정 — HTML 파일만 생성하고 수동 발행 안내로 진행합니다.")
    except Exception as e:
        print(f"[!] Blogger 발행 모듈 오류 (수동 발행으로 폴백): {e}")

    # blog_log.json (해당 날짜 폴더) 갱신 — blog-osmu 스킬과 동일한 스키마
    blog_log_path = os.path.join(dated_dir, "blog_log.json")
    blog_log = load_json(blog_log_path, [])
    blog_log.append({
        "date": now_kst().strftime("%Y-%m-%d"),
        "topic": topic,
        "title": title,
        "file": os.path.relpath(final_html_path, ROOT_DIR).replace("\\", "/"),
        "status": publish_status,
        "blogger_url": publish_url,
        "blogger_post_id": publish_post_id,
        "validation": validation,
        "llm_providers": {
            "research": research_config["name"],
            "writer": writer_config["name"],
            "image_prompt": image_prompt_config["name"],
            "editor": editor_config["name"],
        },
    })
    with open(blog_log_path, "w", encoding="utf-8") as f:
        json.dump(blog_log, f, ensure_ascii=False, indent=2)

    # 전역 발행 이력 (다음 실행 시 중복 주제 자동 회피용)
    # 중복 방지는 큐의 원본 키로 기록하되, 공개되는 제목·본문·파일명에는 코드를 쓰지 않는다.
    mark_topic_published(raw_topic, title, os.path.relpath(final_html_path, ROOT_DIR).replace("\\", "/"))

    # 텔레그램 알림: 임시저장 성공 시 미리보기·공개 발행 버튼 제공.
    if publish_post_id:
        send_blog_review_to_telegram(
            title,
            publish_post_id,
            os.environ.get("BLOGGER_BLOG_ID"),
            final_html_path,
        )
    else:
        tg_message = (
            f"⚠️ <b>[QA+] 글은 완성됐지만 Blogger 연결이 필요합니다</b>\n\n"
            f"📌 <b>제목:</b> {title}\n"
            f"📂 <b>파일:</b> {os.path.basename(final_html_path)}\n\n"
            f"Blogger 시크릿 4개를 설정하면 다음 글부터 미리보기·발행 버튼이 활성화됩니다."
        )
        send_message_to_telegram(tg_message)
        send_document_to_telegram(final_html_path, "QA+ 블로그 최종 HTML — 파일을 눌러 내려받을 수 있습니다.")

    print("\n========================================================")
    print(f"[OK] 블로그 원고 생성이 성공적으로 완료되었습니다!")
    print(f"[*] 최종 HTML: {final_html_path}")
    print(f"[*] 원본(md): {raw_path}")
    print("========================================================\n")
    return final_html_path

def already_ran_today():
    """ 오늘 날짜 폴더에 이미 '공개 발행'된 글이 있는지 확인.
    GitHub Actions 자체 cron + cron-job.org 백업 트리거를 이중으로 걸어둔 경우,
    하나가 이미 성공했으면 나머지 하나는 조용히 스킵해서 하루에 중복 발행되지 않게 한다.
    임시저장(blogger_draft)은 아직 미완성 상태이므로 중복으로 치지 않고 다시 시도하게 둔다 —
    안 그러면 사람이 발행 버튼을 안 눌러도 다음 실행이 조용히 스킵되어 그날 글이 하나도
    안 올라가는 사각지대가 생긴다. """
    dated_dir = today_output_dir()
    blog_log = load_json(os.path.join(dated_dir, "blog_log.json"), [])
    return any(entry.get("status") == "blogger_발행됨" for entry in blog_log)


def run_check_only(topic_arg):
    """ AI 호출 없이 발행 파이프라인이 돌아갈 준비가 됐는지만 점검한다 (LLM/Blogger/텔레그램 설정, 큐 주제 존재 여부). """
    ok = True

    configs = get_llm_configs()
    if configs:
        print(f"[OK] LLM 설정: {' → '.join(c['name'] + '(' + c['model'] + ')' for c in configs)}")
    else:
        print("[FAIL] LLM 설정 없음 — DEEPSEEK_API_KEY 환경변수를 확인하세요.")
        ok = False

    topic = topic_arg or pick_topic_from_queue()
    if topic:
        print(f"[OK] 사용할 주제: {topic}")
    else:
        print("[FAIL] 큐에 아직 블로그로 만들지 않은 주제가 없고 --topic도 지정되지 않았습니다.")
        ok = False

    from blogger_publisher import is_configured as blogger_is_configured
    if blogger_is_configured():
        print("[OK] Blogger 자동 발행 설정됨")
    else:
        print("[!] Blogger 자동 발행 미설정 — HTML 파일만 생성되고 자동 임시저장/발행은 건너뜁니다.")

    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        print("[OK] 텔레그램 알림 설정됨")
    else:
        print("[!] 텔레그램 알림 미설정 — TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID 확인 필요")

    if already_ran_today():
        print("[!] 오늘 이미 공개 발행된 글이 있습니다 (--force 없이 실행하면 스킵됨)")

    print("\n[*] --check-only: AI 호출 0회, 텔레그램/Blogger 호출 0회로 점검만 수행했습니다.")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QA+ 4-Agent Blog Automation Generator")
    parser.add_argument("--topic", type=str, help="블로그 주제 또는 키워드 (미입력 시 큐에서 자동 선택)")
    parser.add_argument("--force", action="store_true", help="오늘 이미 발행됐어도 강제로 한 번 더 생성")
    parser.add_argument("--check-only", action="store_true", help="AI/텔레그램/Blogger 호출 없이 설정과 큐 상태만 점검하고 종료")
    args = parser.parse_args()

    if args.check_only:
        sys.exit(0 if run_check_only(args.topic) else 1)

    if not args.topic and not args.force and already_ran_today():
        print("[*] 오늘 이미 발행이 완료된 글이 있어 스킵합니다 (이중 트리거 대비 안전장치). 강제 실행하려면 --force를 붙이세요.")
        send_message_to_telegram(
            "⏭️ <b>[QA+] 블로그 자동화 — 오늘 이미 발행 완료라 스킵</b>\n\n"
            "이중 트리거(백업 크론) 안전장치로 이번 실행은 건너뛰었습니다. 조치 불필요."
        )
        sys.exit(0)

    topic_input = args.topic
    if not topic_input:
        topic_input = pick_topic_from_queue()
        if topic_input:
            print(f"[*] 큐에서 자동 선택된 주제: {topic_input}")
        else:
            print("[!] 큐에 아직 블로그로 만들지 않은 주제가 없습니다. --topic으로 직접 지정해주세요.")
            send_message_to_telegram(
                "⚠️ <b>[QA+] 블로그 자동화 — 실패 (주제 없음)</b>\n\n"
                "knowledge/qa_topics_queue.json에 아직 블로그로 안 만든 주제가 없습니다. "
                "큐에 새 주제를 추가해주세요."
            )
            sys.exit(1)

    try:
        run_blog_pipeline(topic_input)
    except Exception as e:
        print(f"[!] 블로그 파이프라인 실행 중 오류 발생: {e}")
        send_message_to_telegram(
            f"🚨 <b>[QA+] 블로그 자동화 — 파이프라인 실패</b>\n\n"
            f"📌 <b>주제:</b> {topic_input}\n"
            f"❌ <b>오류:</b> {str(e)[:300]}\n\n"
            f"GitHub Actions 로그를 확인해주세요."
        )
        raise
