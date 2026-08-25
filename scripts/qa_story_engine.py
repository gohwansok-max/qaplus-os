# -*- coding: utf-8 -*-
"""QA+ 쇼츠용 다변화·근거 검증 스토리 엔진.

외부 LLM은 대본 표현을 다양화하는 보조 수단이며, 법적 기준·수치·인증 결과를
추정하거나 보장하는 용도로 사용하지 않는다. 최신 주장에는 공식 출처 문맥이
필요하며, 출처가 부족하면 안전한 실무 점검형 대본으로 자동 전환한다.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = BASE_DIR / "outputs" / "metadata"

# 식품 법령·고시·HACCP 관련 최신 근거는 공식 도메인만 대본 입력으로 허용한다.
OFFICIAL_HOSTS = {
    "mfds.go.kr",
    "www.mfds.go.kr",
    "foodsafetykorea.go.kr",
    "www.foodsafetykorea.go.kr",
    "law.go.kr",
    "www.law.go.kr",
    "haccp.or.kr",
    "www.haccp.or.kr",
}

ANGLES = (
    {
        "id": "field-troubleshooting",
        "badge": "🚨 현장 트러블슈팅",
        "opening": "{topic}에서 이상 신호가 반복될 때, 장비 교체보다 먼저 확인해야 할 현장 단서가 있습니다.",
        "subtitle": "설비·기록·현장을 함께 보는 점검 순서",
    },
    {
        "id": "audit-defense",
        "badge": "🔍 심사 대응 점검",
        "opening": "심사에서 {topic} 기록을 펼쳤을 때, 바로 이어질 질문은 '이 기준의 근거가 무엇인가'입니다.",
        "subtitle": "기록과 현장 일치성을 보여주는 방법",
    },
    {
        "id": "junior-mistake",
        "badge": "💡 신입 QA 실수 방지",
        "opening": "{topic}에서 가장 위험한 실수는 다른 사업장 양식을 그대로 복사하는 것입니다.",
        "subtitle": "자사 데이터로 기준을 설명하는 방법",
    },
    {
        "id": "response-window",
        "badge": "⏱️ 이탈 대응 골든타임",
        "opening": "{topic} 이탈을 발견한 직후에는 원인 추정보다 제품 식별과 격리부터 해야 합니다.",
        "subtitle": "혼선을 줄이는 이탈 대응 순서",
    },
)

COLORS = (
    (239, 68, 68),
    (245, 158, 11),
    (6, 182, 212),
    (139, 92, 246),
    (16, 185, 129),
)

# 이 표현은 출처 유무와 무관하게 과장·보장으로 간주해 자동 생성물에 허용하지 않는다.
BANNED_PHRASES = (
    "100%",
    "무조건 통과",
    "완벽 통과",
    "심사 합격 보장",
    "지적 0건",
    "절대 탈락",
    "반드시 인정",
)


def _clean_text(value: Any, limit: int = 72) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit].rstrip()


def _clean_title(value: Any) -> str:
    lines = [line.strip() for line in str(value or "").splitlines() if line.strip()]
    if not lines:
        return "현장 점검 핵심"
    lines = [_clean_text(line, 19) for line in lines[:2]]
    return "\n".join(lines)


def _has_banned_phrase(value: Any) -> bool:
    text = str(value or "")
    return any(phrase in text for phrase in BANNED_PHRASES)


def _topic(value: str) -> str:
    return _clean_text(value, 60) or "식품 품질관리 핵심 점검"


def _story_id() -> str:
    """한 번의 생성 작업을 식별하는 난수 기반 ID를 만든다."""
    return dt.datetime.now().strftime("%Y%m%d%H%M%S%f") + "-" + uuid.uuid4().hex[:8]


def _angle(topic_name: str, story_id: str) -> dict[str, str]:
    """동일 주제라도 실행마다 다른 서사 앵글을 선택한다."""
    digest = hashlib.sha256(f"{topic_name}|{story_id}".encode("utf-8")).hexdigest()
    return ANGLES[int(digest[:8], 16) % len(ANGLES)]


def _scene_fingerprint(scenes: list[dict[str, Any]]) -> str:
    """장면의 제목·나레이션·핵심 포인트로 중복 여부를 판단한다."""
    raw = "|".join(
        _clean_text(scene.get("title"), 100)
        + "|" + _clean_text(scene.get("narration"), 400)
        + "|" + "|".join(_clean_text(point, 100) for point in scene.get("key_points", []))
        for scene in scenes
    )
    normalized = re.sub(r"[^0-9A-Za-z가-힣]+", "", raw).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _recent_story_fingerprints(limit: int = 30) -> set[str]:
    """최근 생성 메타데이터의 대본 지문을 불러온다. 오류 파일은 무시한다."""
    if not METADATA_DIR.exists():
        return set()
    fingerprints: set[str] = set()
    for path in sorted(METADATA_DIR.glob("*_sources.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]:
        try:
            fingerprint = json.loads(path.read_text(encoding="utf-8")).get("script_fingerprint", "")
            if fingerprint:
                fingerprints.add(str(fingerprint))
        except (OSError, ValueError):
            continue
    return fingerprints


def fetch_official_sources(topic_name: str) -> list[dict[str, str]]:
    """공식 사이트 검색 결과만 반환한다. 검색 실패는 영상 생성 실패로 처리하지 않는다."""
    try:
        from ddgs import DDGS
    except ImportError:
        print("  [근거 확인] ddgs 미설치: 공식 출처 검색을 건너뜁니다.")
        return []

    query = f"{topic_name} 식품 안전관리인증기준 식품의약품안전처"
    sources: list[dict[str, str]] = []
    seen: set[str] = set()
    try:
        results = DDGS().text(query, max_results=10)
        for item in results:
            url = str(item.get("href") or item.get("url") or "").strip()
            host = urlparse(url).netloc.lower()
            if host not in OFFICIAL_HOSTS or url in seen:
                continue
            title = _clean_text(item.get("title"), 120)
            snippet = _clean_text(item.get("body"), 350)
            if not title or not snippet:
                continue
            sources.append({"title": title, "url": url, "snippet": snippet})
            seen.add(url)
            if len(sources) == 3:
                break
    except Exception as exc:
        print(f"  [근거 확인] 공식 검색을 건너뜁니다: {type(exc).__name__}")

    if sources:
        print(f"  [근거 확인] 공식 출처 {len(sources)}건을 대본 검증 문맥에 반영합니다.")
    else:
        print("  [근거 확인] 주제와 직접 연결된 공식 출처를 찾지 못해 수치·법령 단정 없이 생성합니다.")
    return sources


def _source_context(sources: list[dict[str, str]]) -> str:
    if not sources:
        return "공식 출처 문맥이 없습니다. 법령 조항·수치·인증 결과를 단정하지 마세요."
    blocks = []
    for index, source in enumerate(sources, start=1):
        blocks.append(
            f"[공식 출처 {index}]\n제목: {source['title']}\nURL: {source['url']}\n발췌: {source['snippet']}"
        )
    return "\n\n".join(blocks)


def _strip_json_fence(raw: str) -> str:
    text = str(raw or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    first, last = text.find("{"), text.rfind("}")
    return text[first : last + 1] if first >= 0 and last > first else text


def _validate_scenes(candidate: Any) -> list[dict[str, Any]] | None:
    if not isinstance(candidate, list) or len(candidate) != 5:
        return None
    validated: list[dict[str, Any]] = []
    for index, scene in enumerate(candidate, start=1):
        if not isinstance(scene, dict):
            return None
        key_points = scene.get("key_points")
        if not isinstance(key_points, list) or len(key_points) < 2:
            return None
        normalized = {
            "id": index,
            "badge": _clean_text(scene.get("badge"), 22),
            "badge_color": COLORS[index - 1],
            "title": _clean_title(scene.get("title")),
            "subtitle": _clean_text(scene.get("subtitle"), 32),
            "key_points": [_clean_text(key_points[0], 42), _clean_text(key_points[1], 42)],
            "senior_tip": _clean_text(scene.get("senior_tip"), 52),
            "narration": _clean_text(scene.get("narration"), 260),
        }
        if not all(normalized[field] for field in ("badge", "title", "subtitle", "senior_tip", "narration")):
            return None
        if any(_has_banned_phrase(value) for value in normalized.values() if isinstance(value, str)):
            return None
        if any(_has_banned_phrase(point) for point in normalized["key_points"]):
            return None
        validated.append(normalized)
    return validated


def generate_with_cheapai(
    topic_name: str,
    angle: dict[str, str],
    sources: list[dict[str, str]],
    story_id: str,
    previous_fingerprints: set[str],
) -> tuple[list[dict[str, Any]] | None, str | None, str | None]:
    """OpenAI 호환 CheapAI API 호출. 실패하면 안전한 로컬 대본으로 전환한다."""
    api_key = os.environ.get("CHEAPAI_API_KEY", "").strip()
    if not api_key:
        return None, None, None

    base_url = os.environ.get("CHEAPAI_BASE_URL", "https://api.cheapai.im/v1").rstrip("/")
    primary_model = os.environ.get("CHEAPAI_STORY_MODEL", "claude-sonnet-5").strip()
    fallback_model = os.environ.get("CHEAPAI_STORY_FALLBACK_MODEL", "gpt-5.6-sol").strip()
    try:
        timeout_seconds = min(max(int(os.environ.get("CHEAPAI_STORY_TIMEOUT_SECONDS", "35")), 10), 60)
    except ValueError:
        timeout_seconds = 35

    source_context = _source_context(sources)
    system_prompt = """당신은 큐에이플러스(QA+)의 식품 품질관리 콘텐츠 편집자입니다.
아래에 제공된 공식 출처 문맥만을 근거로 하여, 현장 실무자용 9:16 쇼츠 5개 씬을 작성합니다.

안전 규칙:
- 공식 출처 문맥에 없는 법령 조항, 숫자, 장비 사양, 시험 기준, 심사 관행은 절대 지어내지 마세요.
- 출처가 부족한 내용은 '사업장 유효성 평가', '사내 SOP', '최신 고시 원문 확인' 같은 조건부 실무 조언으로 표현하세요.
- '100%', '무조건 통과', '완벽 통과', '합격 보장', '지적 0건' 같은 보장·과장 표현을 사용하지 마세요.
- 실제 회사명, 개인명, 특정 사업장을 식별할 수 있는 정보는 넣지 마세요.
- 인사말 없이 첫 장면부터 현장 문제를 제시하고, 전문 용어에는 자연스러운 쉬운 설명을 덧붙이세요.
- 장면 5의 마무리는 최신 고시·사업장 기준 확인을 권하는 면책형 안내여야 합니다.

반드시 아래 JSON 객체만 반환하세요. 마크다운 코드블록을 쓰지 마세요.
{
  "scenes": [
    {"badge":"짧은 배지", "title":"첫줄\\n둘째줄", "subtitle":"짧은 소제목", "key_points":["핵심 1","핵심 2"], "senior_tip":"현장 팁", "narration":"나레이션"},
    {"badge":"짧은 배지", "title":"첫줄\\n둘째줄", "subtitle":"짧은 소제목", "key_points":["핵심 1","핵심 2"], "senior_tip":"현장 팁", "narration":"나레이션"},
    {"badge":"짧은 배지", "title":"첫줄\\n둘째줄", "subtitle":"짧은 소제목", "key_points":["핵심 1","핵심 2"], "senior_tip":"현장 팁", "narration":"나레이션"},
    {"badge":"짧은 배지", "title":"첫줄\\n둘째줄", "subtitle":"짧은 소제목", "key_points":["핵심 1","핵심 2"], "senior_tip":"현장 팁", "narration":"나레이션"},
    {"badge":"짧은 배지", "title":"첫줄\\n둘째줄", "subtitle":"짧은 소제목", "key_points":["핵심 1","핵심 2"], "senior_tip":"현장 팁", "narration":"나레이션"}
  ]
}"""
    base_user_prompt = (
        f"주제: {topic_name}\n"
        f"이번 스토리텔링 앵글: {angle['id']}\n"
        f"첫 장면의 방향: {angle['opening'].format(topic=topic_name)}\n"
        f"고유 생성 코드: {story_id}\n\n"
        "이 실행은 기존 영상과 전혀 다른 대본이어야 합니다. 제목·첫 문장·예시·체크포인트의 순서를 바꾸고, 같은 표현을 재사용하지 마세요. 고유 생성 코드는 영상에 쓰거나 읽지 마세요.\n\n"
        f"공식 출처 문맥:\n{source_context}"
    )

    for model in [value for value in (primary_model, fallback_model) if value]:
        for attempt in range(1, 3):
            try:
                user_prompt = base_user_prompt + f"\n\n생성 시도: {attempt}. 이전 시도와도 겹치지 않게 새로 작성하세요."
                response = requests.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "temperature": 1.0,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                    timeout=timeout_seconds,
                )
                if not response.ok:
                    print(f"  [LLM] {model} 응답 실패: HTTP {response.status_code}")
                    break
                raw = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                parsed = json.loads(_strip_json_fence(raw))
                scenes = _validate_scenes(parsed.get("scenes"))
                fingerprint = _scene_fingerprint(scenes) if scenes else ""
                if scenes and fingerprint not in previous_fingerprints:
                    print(f"  [LLM] {model} 기반 출처 검증형 신규 대본 생성 완료 (시도 {attempt})")
                    return scenes, model, fingerprint
                if scenes:
                    print(f"  [LLM] 최근 대본과 동일해 재생성합니다 (시도 {attempt}).")
                else:
                    print(f"  [LLM] {model} 응답이 품질·안전 검증을 통과하지 못했습니다.")
            except (requests.RequestException, ValueError, IndexError, TypeError) as exc:
                print(f"  [LLM] {model} 호출을 건너뜁니다: {type(exc).__name__}")
                break
    return None, None, None


def _fallback_scene(
    index: int, badge: str, title: str, subtitle: str, key_points: list[str], tip: str, narration: str
) -> dict[str, Any]:
    return {
        "id": index,
        "badge": badge,
        "badge_color": COLORS[index - 1],
        "title": title,
        "subtitle": subtitle,
        "key_points": key_points,
        "senior_tip": tip,
        "narration": narration,
    }


def local_verified_fallback(topic_name: str, angle: dict[str, str], story_id: str) -> list[dict[str, Any]]:
    """외부 모델이 지연돼도 서사 구조 자체가 달라지는 안전한 대체 대본."""
    topic_name = _topic(topic_name)
    route_options = {
        "field-troubleshooting": (
            ("변경점 역추적", "원료·설비·작업 순서가 바뀐 순간", "변경 전후를 한 장의 흐름으로 비교"),
            ("현장 관찰", "기록값과 실제 작업 동선의 차이", "작업자가 보는 신호를 먼저 들어보기"),
            ("반복 신호", "같은 이상이 나타나는 공통 조건", "발생 시점과 제품 흐름을 나란히 놓기"),
        ),
        "audit-defense": (
            ("심사관 첫 질문", "기준의 근거가 무엇인지", "기준서·검증자료·기록을 한 묶음으로 준비"),
            ("현장 동행 점검", "문서와 실제 작업이 같은지", "작업자 설명과 기록 시각을 연결"),
            ("기록 추적 시연", "한 제품을 끝까지 찾을 수 있는지", "원료부터 출하 전 확인까지 흐름을 보여주기"),
        ),
        "junior-mistake": (
            ("복사한 양식", "내 공장에 맞지 않는 기준", "제품·설비·공정 조건부터 다시 적기"),
            ("숫자만 외운 실수", "근거 없이 적용한 관리값", "유효성 평가 자료에서 이유를 찾기"),
            ("현장을 못 물어본 실수", "작업자가 실제로 하는 방법", "문서 작성 전 작업 흐름부터 듣기"),
        ),
        "response-window": (
            ("발견 직후", "원인 추정보다 제품 식별", "시간·라인·작업자를 먼저 묶기"),
            ("영향 범위", "어디까지 확인해야 하는지", "전후 공정과 보관 제품을 분리해 보기"),
            ("재가동 전", "조치가 실제로 작동하는지", "책임자 확인과 기록 완결을 함께 하기"),
        ),
    }
    route_list = route_options.get(angle["id"], route_options["field-troubleshooting"])
    route = route_list[int(hashlib.sha256(story_id.encode("utf-8")).hexdigest()[:8], 16) % len(route_list)]
    label, focus, action = route
    badge = f"{angle['badge']} · {label}"

    if angle["id"] == "audit-defense":
        return [
            _fallback_scene(1, badge, "심사 때 바로 나오는\n첫 질문", focus, ["관리 기준의 근거 위치", "최신 문서 연결 상태"], "근거 문서는 파일명보다 찾는 순서가 중요합니다.", f"{topic_name} 심사에서 첫 질문은 기준의 근거입니다. {focus}를 바로 설명할 수 있어야 합니다."),
            _fallback_scene(2, badge, "문서 3종을\n한 줄로 연결", "기준서·검증자료·기록", ["기준서의 관리 항목", "검증자료의 판단 근거"], "한 항목을 세 문서에서 이어 보세요.", f"다음은 문서 연결입니다. {action}. 그러면 심사 질문이 와도 자료를 새로 찾느라 흐름이 끊기지 않습니다."),
            _fallback_scene(3, badge, "현장 설명과\n기록 시각 대조", "문서와 실제 작업 일치", ["작업자가 하는 확인", "기록에 남은 확인"], "작업자에게 문서 문장이 아닌 실제 순서를 물어보세요.", "심사는 서류만 보는 자리가 아닙니다. 현장 설명과 기록이 같은 방향을 가리키는지를 확인하는 과정입니다."),
            _fallback_scene(4, badge, "질문을 받으면\n원인부터 말하지 말기", "확인 범위와 조치 순서", ["영향 제품의 식별", "조치 기록의 연결"], "확정 전에는 추정과 사실을 구분해 적으세요.", "이탈 질문에는 단정 대신 확인 범위를 먼저 제시하세요. 사실에 근거한 순서가 가장 설득력 있는 답변입니다."),
            _fallback_scene(5, badge, "다음 심사 전\n10분 점검", "현장에서 바로 해볼 체크", ["최신 고시 원문 대조", "사업장 검증자료 확인"], "오늘 한 항목만 골라 문서와 현장을 함께 보세요.", f"마지막으로 {topic_name} 관련 최신 공식 자료와 사내 기준을 다시 대조하세요. 조건이 달라지면 근거도 다시 확인해야 합니다."),
        ]

    if angle["id"] == "junior-mistake":
        return [
            _fallback_scene(1, badge, "신입 QA가\n가장 먼저 하는 실수", focus, ["타사 양식 그대로 사용", "내 공장 조건 미확인"], "양식은 답안지가 아니라 확인할 질문 목록입니다.", f"{topic_name}에서 실수는 문서부터 복사하는 것입니다. {focus}를 먼저 이해하지 않으면 좋은 양식도 현장에서 힘을 못 씁니다."),
            _fallback_scene(2, badge, "먼저 적을 것은\n관리 수치가 아닙니다", "기준이 필요한 이유", ["위해요소와 관리 목적", "현재 공정 조건"], "숫자 앞에 '왜 관리하는가'를 한 줄로 적어보세요.", "관리 수치부터 정하려고 하지 마세요. 제품과 공정에서 무엇을 막으려는지 정리하면 필요한 확인 방법이 보입니다."),
            _fallback_scene(3, badge, "작업자에게 꼭\n물어볼 질문 2개", "문서 밖의 실제 흐름", ["실제로 확인하는 시점", "막힐 때의 대응 방법"], "문서 검토 전에 5분 현장 인터뷰를 해보세요.", f"{action}. 문서와 작업이 다르면 문서를 고치는 것이 먼저인지, 작업을 바로잡는 것이 먼저인지 판단할 수 있습니다."),
            _fallback_scene(4, badge, "기록을 쓸 때\n빠지기 쉬운 것", "판단 근거 남기기", ["누가 확인했는지", "무엇을 근거로 판단했는지"], "나중에 본 사람이 같은 결론을 낼 수 있어야 합니다.", "기록은 체크 표시만 남기는 종이가 아닙니다. 판단 근거가 이어져야 다음 근무자도 같은 기준으로 움직일 수 있습니다."),
            _fallback_scene(5, badge, "오늘의 숙제\n양식 한 장 고치기", "내 공장 기준으로 바꾸기", ["최신 공식 자료 확인", "사업장 검증자료 반영"], "완벽하게 바꾸려 하지 말고 한 칸부터 시작하세요.", f"오늘은 {topic_name} 양식에서 한 항목만 골라 자사 조건에 맞게 바꿔보세요. 적용 전에는 최신 고시 원문도 함께 확인해야 합니다."),
        ]

    if angle["id"] == "response-window":
        return [
            _fallback_scene(1, badge, "이상 신호가 뜨면\n첫 1분에 할 일", focus, ["시간·라인·제품 식별", "현재 작업 상태 확인"], "원인을 말하기 전에 사실부터 묶어 두세요.", f"{topic_name} 이탈은 발견 직후가 가장 중요합니다. {focus}를 먼저 잡아야 뒤의 판단이 흔들리지 않습니다."),
            _fallback_scene(2, badge, "멈추고 찾고\n표시하는 순서", "영향 범위 혼선 줄이기", ["해당 제품 임시 분리", "전후 작업 흐름 확인"], "제품 표시가 명확해야 나중에 추적이 가능합니다.", f"둘째는 범위 관리입니다. {action}. 이 단계에서 빠르게 구분해 두면 불필요한 혼선도 줄어듭니다."),
            _fallback_scene(3, badge, "원인 분석은\n그 다음입니다", "추정과 사실 구분", ["확인된 사실 기록", "추가 확인 항목 지정"], "모르는 내용은 빈칸으로 남기지 말고 확인 계획을 적으세요.", "원인을 빨리 단정하면 조치가 흔들릴 수 있습니다. 확인한 사실과 더 확인할 내용을 나누어 기록하는 것이 안전합니다."),
            _fallback_scene(4, badge, "재가동 전\n질문 하나", "조치 유효성 확인", ["조치가 현장에 적용됐는지", "책임자 확인이 남았는지"], "재가동 기준은 사내 절차와 연결해 두세요.", "조치했다는 말보다 조치가 실제로 작동하는지 확인하는 기록이 중요합니다. 재가동 전에는 이 연결을 한 번 더 보세요."),
            _fallback_scene(5, badge, "이탈 기록을\n다음 예방으로", "재발 방지 자료 만들기", ["최신 기준과 절차 대조", "교육·점검 항목 반영"], "한 번의 이탈을 다음 점검표에 반영하세요.", f"마지막으로 {topic_name} 관련 절차와 최신 공식 자료를 확인하세요. 이번 기록이 다음 이탈을 줄이는 현장 데이터가 됩니다."),
        ]

    return [
        _fallback_scene(1, badge, "같은 이상 신호\n반복될 때", focus, ["문제 발생 시점", "직전 변경 사항"], "가설보다 먼저 시간 순서를 적어보세요.", f"{topic_name}에서 이상 신호가 반복되면 장비 교체부터 하지 마세요. {focus}를 따라가면 현장 단서가 보이기 시작합니다."),
        _fallback_scene(2, badge, "기록만 보지 말고\n현장을 같이 보기", "숫자가 나온 조건 확인", ["기록값의 시간", "실제 작업의 시간"], "기록 시각과 작업 시각을 나란히 비교하세요.", f"둘째는 현장 확인입니다. {action}. 숫자는 결과이고, 그 숫자가 나온 조건이 원인을 좁혀 줍니다."),
        _fallback_scene(3, badge, "변경점 3가지를\n한 줄에 적기", "원료·설비·작업 방법", ["새로 바뀐 요소", "바뀌지 않은 요소"], "변경이 없었다는 말도 확인 기록으로 남기세요.", "원료, 설비, 작업 방법을 한 번에 모두 의심하지 마세요. 바뀐 것과 그대로인 것을 나누면 점검 범위가 줄어듭니다."),
        _fallback_scene(4, badge, "현장 조치는\n작게 검증하기", "조치 전후 비교", ["조치 내용 기록", "확인 방법 설정"], "조치와 확인 방법을 한 쌍으로 작성하세요.", "조치가 맞는지 보려면 확인 방법도 함께 정해야 합니다. 작은 범위에서 검증하고 결과를 기록한 뒤 다음 판단으로 넘어가세요."),
        _fallback_scene(5, badge, "반복 신호를\n예방 데이터로", "다음 점검에 반영", ["최신 공식 자료 확인", "사내 기준·교육 반영"], "반복된 문제는 점검 항목으로 승격하세요.", f"오늘의 결론입니다. {topic_name}은 한 번의 처방으로 끝나지 않습니다. 최신 공식 자료와 사업장 검증 결과를 함께 확인해 다음 점검에 반영하세요."),
    ]


def _metadata_path(topic_name: str, story_id: str) -> Path:
    clean = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", topic_name).strip("_")[:32] or "topic"
    return METADATA_DIR / f"{dt.date.today().isoformat()}_{clean}_{story_id}_sources.json"


def build_verified_story(topic_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """큐·수동 주제 모두에 사용할 단일 진입점. 동일 주제도 매번 다른 대본을 만든다."""
    topic_name = _topic(topic_name)
    story_id = _story_id()
    angle = _angle(topic_name, story_id)
    previous_fingerprints = _recent_story_fingerprints()
    sources = fetch_official_sources(topic_name)
    scenes, model, fingerprint = generate_with_cheapai(
        topic_name, angle, sources, story_id, previous_fingerprints
    )
    mode = "llm_verified" if scenes else "local_verified_fallback"
    if scenes is None:
        # 네트워크·모델 지연 시에도 최근 대본과 정확히 같은 문안은 보내지 않는다.
        for fallback_attempt in range(1, 17):
            fallback_id = f"{story_id}-{fallback_attempt}"
            fallback_angle = _angle(topic_name, fallback_id)
            scenes = local_verified_fallback(topic_name, fallback_angle, fallback_id)
            fingerprint = _scene_fingerprint(scenes)
            if fingerprint not in previous_fingerprints:
                angle = fallback_angle
                break
        else:
            # 이론적으로 모든 변주가 소진된 경우에도 마지막 장면에 신규 검토 문장을 추가한다.
            scenes[-1]["narration"] += " 이번 생성에서는 내부 점검 순서를 새로 기록해 두세요."
            fingerprint = _scene_fingerprint(scenes)

    metadata: dict[str, Any] = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "story_id": story_id,
        "topic": topic_name,
        "story_angle": angle["id"],
        "generation_mode": mode,
        "model": model,
        "script_fingerprint": fingerprint,
        "recent_fingerprint_count": len(previous_fingerprints),
        "official_sources": sources,
        "source_count": len(sources),
        "review_note": "게시 전 최신 고시 원문·사업장 유효성 평가·표현 적정성을 최종 확인하세요.",
    }
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    _metadata_path(topic_name, story_id).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return scenes, metadata
