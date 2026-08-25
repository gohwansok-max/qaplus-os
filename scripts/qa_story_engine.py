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


def local_verified_fallback(topic_name: str, angle: dict[str, str], story_id: str) -> list[dict[str, Any]]:
    """키·네트워크·모델 응답이 없을 때도 실행별로 변주되는 안전한 대체 대본."""
    topic_name = _topic(topic_name)
    variation_options = (
        "기록의 시간 순서를 따라가며 확인해 보겠습니다.",
        "작업자가 실제로 무엇을 했는지부터 짚어보겠습니다.",
        "설비 조건이 바뀐 순간을 찾는 데서 시작하겠습니다.",
        "제품 추적이 가능한 기록 흐름을 먼저 정리하겠습니다.",
        "변경관리 관점에서 한 단계씩 살펴보겠습니다.",
        "현장과 문서가 같은 말을 하는지 확인해 보겠습니다.",
        "작은 이탈이 커지기 전의 신호를 먼저 보겠습니다.",
        "오늘은 점검표가 아닌 실제 작업 흐름으로 접근하겠습니다.",
    )
    variation = variation_options[int(hashlib.sha256(story_id.encode("utf-8")).hexdigest()[:8], 16) % len(variation_options)]
    opening = angle["opening"].format(topic=topic_name) + " " + variation
    return [
        {
            "id": 1,
            "badge": angle["badge"],
            "badge_color": COLORS[0],
            "title": f"{topic_name[:18]}\n{variation[:15]}",
            "subtitle": angle["subtitle"],
            "key_points": ["기록값과 실제 작업 상태를 함께 확인", "변경된 원료·설비·작업 조건을 먼저 파악"],
            "senior_tip": "문제가 생긴 시점의 제품·공정·작업자를 먼저 연결해 두세요.",
            "narration": opening + " 쉽게 말하면, 숫자 하나만 보지 말고 그 숫자가 나온 현장 조건까지 함께 봐야 한다는 뜻입니다.",
        },
        {
            "id": 2,
            "badge": "💡 기준 근거 확인",
            "badge_color": COLORS[1],
            "title": "남의 기준 복사 대신\n자사 데이터 확인",
            "subtitle": "사업장 유효성 평가가 기준의 출발점",
            "key_points": ["제품·설비·작업 조건별 근거를 보관", "변경 발생 시 기준의 적합성을 재검토"],
            "senior_tip": "기준서에는 '왜 이 기준인가'를 설명할 근거 문서를 연결하세요.",
            "narration": "첫째, 관리 기준의 근거입니다. " + variation + " 같은 공정처럼 보여도 제품과 설비 조건이 다르면 관리 방법도 달라질 수 있습니다. 쉽게 말하면, 우리 공장의 실측 데이터가 가장 강한 답변입니다.",
        },
        {
            "id": 3,
            "badge": "⏱️ 모니터링 설계",
            "badge_color": COLORS[2],
            "title": "작업 전·중·후\n확인 시점부터 정하기",
            "subtitle": "이탈 발견 범위를 줄이는 기록 설계",
            "key_points": ["누가·언제·무엇을 확인하는지 명확화", "기록 시각과 실제 작업 시점을 일치"],
            "senior_tip": "점검 주기는 위험도와 공정 특성에 맞춰 사업장 기준으로 정하세요.",
            "narration": "둘째, 모니터링입니다. 중요한 것은 횟수를 외우는 게 아니라 이상이 생겼을 때 영향 범위를 추적할 수 있게 기록을 설계하는 것입니다. 쉽게 말하면, 나중에 제품을 정확히 찾을 수 있어야 합니다.",
        },
        {
            "id": 4,
            "badge": "🔥 이탈 조치 핵심",
            "badge_color": COLORS[3],
            "title": "이상 발견 직후\n추정보다 격리 먼저",
            "subtitle": "혼선을 줄이는 현장 대응 순서",
            "key_points": ["해당 제품과 공정을 식별해 임시 분리", "원인·조치·재발방지 내용을 같은 흐름으로 기록"],
            "senior_tip": "이탈 기록은 잘못을 숨기는 문서가 아니라 재발을 막는 현장 데이터입니다.",
            "narration": "셋째, 이탈 대응입니다. 원인을 단정하기 전에 영향 가능한 제품과 공정을 먼저 구분해 두세요. 쉽게 말하면, 멈추고 찾고 기록한 뒤에 원인을 분석하는 순서가 현장을 지켜줍니다.",
        },
        {
            "id": 5,
            "badge": "🏆 최종 확인",
            "badge_color": COLORS[4],
            "title": "최신 고시와 SOP\n두 가지를 함께 확인",
            "subtitle": "현장 적용 전 마지막 체크",
            "key_points": ["최신 공식 고시 원문과 사내 기준서 대조", "주제별 유효성 평가·교육·기록을 함께 검토"],
            "senior_tip": "수치나 시험 조건은 반드시 최신 고시와 사업장 검증 자료로 확정하세요.",
            "narration": "오늘 하나만 기억하세요. " + topic_name + "은 일반적인 공식 하나로 끝나지 않습니다. 최신 공식 자료와 우리 사업장 조건을 함께 확인한 뒤 적용하시면 됩니다. 막히는 부분은 편하게 질문 남겨주세요.",
        },
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
