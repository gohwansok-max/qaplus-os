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
    from telegram_sender import send_message_to_telegram
except Exception:
    def send_message_to_telegram(message):
        print("[!] telegram_sender 모듈을 불러오지 못해 텔레그램 발송을 건너뜁니다.")
        return False


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
    """ .env 파일 파싱 """
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
    return env

ENV = load_env()

def get_llm_configs():
    """ 사용할 LLM 설정을 우선순위대로 리스트로 반환.
    video 파이프라인(daily_qa_video.yml)과 동일하게 '칩섭 우선, 실패 시 공식 OpenAI 대체' 원칙을 따른다
    (비용 절감). 블로그 전용 모델명(CHEAPAI_BLOG_MODEL 등)이 있으면 그걸 쓰고, 없으면
    video 파이프라인과 공유하는 CHEAPAI_STORY_MODEL 값을 건드리지 않고 별도 기본값(gpt-5.6-terra)을 쓴다. """
    configs = []
    if ENV.get("CHEAPAI_API_KEY") and not ENV.get("CHEAPAI_API_KEY", "").startswith("your_"):
        configs.append({
            "name": "CheapAI",
            "api_key": ENV["CHEAPAI_API_KEY"],
            "base_url": ENV.get("CHEAPAI_BASE_URL", "https://api.cheapai.im/v1"),
            "model": ENV.get("CHEAPAI_BLOG_MODEL", "gpt-5.6-terra")
        })
    if ENV.get("OFFICIAL_OPENAI_API_KEY") and not ENV.get("OFFICIAL_OPENAI_API_KEY", "").startswith("your_"):
        configs.append({
            "name": "공식 OpenAI",
            "api_key": ENV["OFFICIAL_OPENAI_API_KEY"],
            "base_url": ENV.get("OFFICIAL_OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": ENV.get("OFFICIAL_OPENAI_BLOG_MODEL", "gpt-5.6-terra")
        })
    if ENV.get("OPENAI_API_KEY") and not ENV.get("OPENAI_API_KEY", "").startswith("your_"):
        configs.append({
            "name": "OpenAI(일반)",
            "api_key": ENV["OPENAI_API_KEY"],
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini"
        })
    return configs


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
    print("\n========================================================")
    print(f"[*] [QA+ 4-Agent Blog Pipeline] 시작")
    print(f"[*] 주제: {topic}")
    print("========================================================\n")
    
    configs = get_llm_configs()
    if not configs:
        print("[!] .env에 유효한 API 키가 설정되지 않았습니다. (CHEAPAI_API_KEY 또는 OFFICIAL_OPENAI_API_KEY 확인)")
        return

    print(f"[*] LLM 우선순위: {' → '.join(c['name'] + '(' + c['model'] + ')' for c in configs)}")

    # 1단계: 리서치 에이전트
    print("\n[1/4] [리서치] 1단계: 리서치 & 목차 기획 에이전트 가동 중...")
    prompt_1 = read_prompt("01_research_agent.md")
    research_output, used_config = call_llm_with_fallback(prompt_1, f"다음 주제에 대해 심층 리서치 및 목차를 설계해주세요:\n\n주제: {topic}", configs)
    print(f"[+] 1단계 리서치 완료! ({used_config['name']})")

    # 2단계: 작가 에이전트
    print("\n[2/4] [집필] 2단계: 20년 멘토 작가 에이전트 본문 집필 중...")
    prompt_2 = read_prompt("02_writer_agent.md")
    writer_input = f"다음은 리서치 결과입니다:\n\n{research_output}\n\n위 내용을 바탕으로 20년 식품품질 전문가 멘토 페르소나를 적용하여 실무자 블로그 본문 전체를 작성해주세요."
    writer_output, used_config = call_llm_with_fallback(prompt_2, writer_input, configs)
    print(f"[+] 2단계 원고 집필 완료! ({used_config['name']})")

    # 3단계: 이미지/인포그래픽 디자이너 에이전트
    print("\n[3/4] [디자인] 3단계: 썸네일 및 인포그래픽 디자인 에이전트 가동 중...")
    prompt_3 = read_prompt("03_image_agent.md")
    image_input = f"다음 블로그 원고의 이미지 마커 위치에 어울리는 대표 썸네일 프롬프트, 본문 이미지 프롬프트, Mermaid 다이어그램을 생성해주세요:\n\n{writer_output}"
    image_output, used_config = call_llm_with_fallback(prompt_3, image_input, configs)
    print(f"[+] 3단계 시각자료 기획 완료! ({used_config['name']})")

    # 4단계: 편집장 & QA 검수 에이전트
    print("\n[4/4] [검수/패키징] 4단계: 수석 에디터 & QA 검수 및 패키징 중...")
    prompt_4 = read_prompt("04_editor_agent.md")
    editor_input = f"[본문 원고]\n{writer_output}\n\n[시각자료 기획서]\n{image_output}\n\n위 두 내용을 종합하여 법령/사실관계를 검수하고, SEO 메타데이터와 네이버 블로그/티스토리/워드프레스용 최종 완성본을 패키징해주세요."
    final_package, used_config = call_llm_with_fallback(prompt_4, editor_input, configs)
    print(f"[+] 4단계 최종 검수 및 패키징 완료! ({used_config['name']})")
    llm_config = used_config
    
    # --- 표준 산출물 경로: outputs/{연도}/{월}/{일}/ (blog-osmu 스킬과 동일한 규칙) ---
    dated_dir = today_output_dir()
    safe_topic = sanitize_filename(topic).replace(" ", "_")

    # 부록/전체 원고 (검토용, md)
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

    # 04_editor_agent.md 규격의 ```html ... ``` 블록을 추출해 Blogger 붙여넣기용 최종 HTML로 저장
    html_match = re.search(r"```html\s*(.*?)```", final_package, re.DOTALL)
    title_match = re.search(r"\*\*최종 포스팅 제목\*\*\s*[:：]\s*(.+)", final_package)
    desc_match = re.search(r"\*\*메타 디스크립션[^*]*\*\*\s*[:：]\s*(.+)", final_package)
    title = title_match.group(1).strip() if title_match else topic

    final_html_path = os.path.join(dated_dir, f"[블로그최종]_{safe_topic}.html")
    if html_match:
        body_html = html_match.group(1).strip()
    else:
        # 에디터 에이전트가 HTML 블록을 안 만들었으면 마크다운 전체를 <pre>로 감싸 최소한 발행 가능하게 둔다.
        body_html = f"<pre>{final_package}</pre>"
        print("[!] HTML 코드블록을 찾지 못해 마크다운 원문을 <pre>로 감싸 저장했습니다 — 수동 정리가 필요할 수 있습니다.")

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

    html_doc = f"""<!-- QA+ 블로그 최종본 — Blogger 편집기 HTML 모드에 붙여넣기 -->
<!-- 제목: {title} -->
<!-- 검색 설명: {desc_match.group(1).strip() if desc_match else ''} -->

{body_html}
"""
    with open(final_html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    # --- Blogger 자동 발행 (BLOGGER_* 환경변수가 모두 설정된 경우에만 동작, 없으면 기존처럼 수동 안내만) ---
    publish_status = "ready_to_publish"
    publish_url = None
    publish_post_id = None
    try:
        from blogger_publisher import is_configured, publish_post
        if is_configured():
            labels_match = re.search(r"\*\*카테고리\*\*\s*[:：]\s*(.+)", final_package)
            labels = [l.strip() for l in labels_match.group(1).split("/")] if labels_match else None
            is_draft = os.environ.get("BLOGGER_AUTO_PUBLISH", "false").lower() != "true"
            result = publish_post(title, body_html, labels=labels, is_draft=is_draft)
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
    })
    with open(blog_log_path, "w", encoding="utf-8") as f:
        json.dump(blog_log, f, ensure_ascii=False, indent=2)

    # 전역 발행 이력 (다음 실행 시 중복 주제 자동 회피용)
    mark_topic_published(topic, title, os.path.relpath(final_html_path, ROOT_DIR).replace("\\", "/"))

    # 텔레그램 알림
    if publish_url:
        status_label = "공개 발행됨" if publish_status == "blogger_발행됨" else "임시저장"
        tg_message = (
            f"✅ <b>[QA+] 블로그 글이 Blogger에 자동 등록됐습니다</b>\n\n"
            f"📌 <b>제목:</b> {title}\n"
            f"🔗 <b>{status_label}:</b> {publish_url}\n\n"
            + ("내용 확인 후 Blogger에서 발행 버튼만 눌러주세요." if status_label == "임시저장" else "이미 공개 발행되었습니다.")
        )
    else:
        tg_message = (
            f"📝 <b>[QA+] 오늘의 블로그 글이 준비됐습니다</b>\n\n"
            f"📌 <b>제목:</b> {title}\n"
            f"📂 <b>파일:</b> {os.path.basename(final_html_path)}\n\n"
            f"Blogger 편집기(HTML 모드)에 붙여넣고 이미지 업로드 후 직접 발행해주세요."
        )
    send_message_to_telegram(tg_message)

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QA+ 4-Agent Blog Automation Generator")
    parser.add_argument("--topic", type=str, help="블로그 주제 또는 키워드 (미입력 시 큐에서 자동 선택)")
    parser.add_argument("--force", action="store_true", help="오늘 이미 발행됐어도 강제로 한 번 더 생성")
    args = parser.parse_args()

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
