"""QA+ 실시간 공식 웹 근거 쇼츠 대본 엔진.

콘텐츠 사실은 매 실행마다 공식 웹 검색 결과로만 입력한다. 최근 생성 이력은
대본을 재활용하지 않고 중복을 거부하기 위한 검사에만 사용한다.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse
from html import unescape

import requests

from qa_story_engine import (
    ANGLES,
    BANNED_PHRASES,
    COLORS,
    _clean_text,
    _clean_title,
    _has_banned_phrase,
    _scene_fingerprint,
)

BASE_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = BASE_DIR / "outputs" / "metadata"
OFFICIAL_HOSTS = {
    "mfds.go.kr", "www.mfds.go.kr",
    "foodsafetykorea.go.kr", "www.foodsafetykorea.go.kr",
    "law.go.kr", "www.law.go.kr",
    "haccp.or.kr", "www.haccp.or.kr",
}
STOPWORDS = {
    "식품", "품질", "관리", "안전", "해썹", "haccp", "관련", "대한", "위한", "있는",
    "확인", "최신", "공식", "자료", "기준", "현장", "사업장", "실무", "대해",
}


def _topic(value: str) -> str:
    return _clean_text(value, 80) or "식품 품질관리 핵심 점검"


def _story_id() -> str:
    return dt.datetime.now().strftime("%Y%m%d%H%M%S%f") + "-" + uuid.uuid4().hex[:8]


def _angle(topic_name: str, story_id: str) -> dict[str, str]:
    digest = hashlib.sha256(f"{topic_name}|{story_id}".encode("utf-8")).hexdigest()
    return ANGLES[int(digest[:8], 16) % len(ANGLES)]


def _html_excerpt(url: str, fallback: str) -> str:
    """검색 결과만 쓰지 않고 공식 원문을 다시 요청해 짧은 최신 문맥을 확보한다."""
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "QAPlusContentResearch/1.0"},
            timeout=8,
        )
        if not response.ok:
            return fallback
        html = response.text
        html = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 100:
            return fallback
        return _clean_text(f"{fallback} | 원문 발췌: {text}", 520)
    except requests.RequestException:
        return fallback


def _bing_official_results(query: str) -> list[dict[str, str]]:
    """DDGS 장애 시에도 공식 도메인 결과만 골라내는 일반 웹 검색 대체 경로."""
    try:
        response = requests.get(
            f"https://www.bing.com/search?q={quote_plus(query)}",
            headers={"User-Agent": "Mozilla/5.0 QAPlusResearch/1.0"},
            timeout=10,
        )
        if not response.ok:
            return []
        results: list[dict[str, str]] = []
        for block in re.findall(r'<li[^>]+class="b_algo"[\\s\\S]*?</li>', response.text, flags=re.I):
            match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>([\\s\\S]*?)</a>', block, flags=re.I)
            if not match:
                continue
            url = unescape(match.group(1)).strip()
            host = urlparse(url).netloc.lower()
            if host not in OFFICIAL_HOSTS:
                continue
            title = _clean_text(re.sub(r"<[^>]+>", " ", unescape(match.group(2))), 140)
            body = _clean_text(re.sub(r"<[^>]+>", " ", unescape(block)), 360)
            if title and body:
                results.append({"href": url, "title": title, "body": body})
        return results
    except requests.RequestException:
        return []


def fetch_live_official_sources(topic_name: str) -> list[dict[str, str]]:
    """매 호출마다 최신 공식 웹을 검색한다. 캐시·주제 DB는 사용하지 않는다."""
    try:
        from ddgs import DDGS
    except ImportError as exc:
        raise RuntimeError("실시간 공식 웹 검색 모듈(ddgs)이 설치되어 있지 않습니다.") from exc

    queries = (
        f"{topic_name} 식품의약품안전처",
        f"{topic_name} 식품안전나라",
        f"{topic_name} HACCP 고시 법령",
    )
    sources: list[dict[str, str]] = []
    seen: set[str] = set()
    for query in queries:
        try:
            results = DDGS().text(query, max_results=12)
        except Exception as exc:
            print(f"  [실시간 웹 검색] DDGS 장애({type(exc).__name__}), 공식 도메인 웹 검색으로 전환합니다.")
            results = _bing_official_results(query)
        if not results:
            continue
        for item in results:
            url = str(item.get("href") or item.get("url") or "").strip()
            host = urlparse(url).netloc.lower()
            if not url or host not in OFFICIAL_HOSTS or url in seen:
                continue
            title = _clean_text(item.get("title"), 140)
            snippet = _clean_text(item.get("body"), 360)
            if not title or not snippet:
                continue
            seen.add(url)
            # 검색 결과의 최신 공식 발췌를 즉시 사용한다. 원문 전체를 넣어 모델 응답이
            # 지연되는 문제를 피하면서도 URL·검색어·검색시각을 메타데이터에 남긴다.
            sources.append({
                "title": title,
                "url": url,
                "snippet": snippet,
                "search_query": query,
                "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            })
            if len(sources) >= 3:
                break
        if len(sources) >= 3:
            break

    minimum = max(1, int(os.environ.get("QA_WEB_MIN_SOURCE_COUNT", "2")))
    if len(sources) < minimum:
        raise RuntimeError(
            f"실시간 공식 웹 근거가 {len(sources)}건으로 부족합니다(필요 {minimum}건). "
            "근거 없는 대체 대본은 생성하지 않습니다."
        )
    print(f"  [실시간 웹 검색] 공식 출처 {len(sources)}건을 새로 수집했습니다.")
    return sources


def _source_context(sources: list[dict[str, str]]) -> str:
    return "\n\n".join(
        f"[공식 최신 출처 {index}]\n제목: {_clean_text(item['title'], 90)}\n"
        f"URL: {item['url']}\n발췌: {_clean_text(item['snippet'], 220)}"
        for index, item in enumerate(sources[:3], start=1)
    )


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
    return text[first:last + 1] if first >= 0 and last > first else text


def _validate_scenes(candidate: Any) -> list[dict[str, Any]] | None:
    if not isinstance(candidate, list) or len(candidate) != 5:
        return None
    scenes: list[dict[str, Any]] = []
    for index, scene in enumerate(candidate, start=1):
        if not isinstance(scene, dict) or not isinstance(scene.get("key_points"), list):
            return None
        points = scene["key_points"]
        if len(points) < 2:
            return None
        normalized = {
            "id": index,
            "badge": _clean_text(scene.get("badge"), 22),
            "badge_color": COLORS[index - 1],
            "title": _clean_title(scene.get("title")),
            "subtitle": _clean_text(scene.get("subtitle"), 32),
            "key_points": [_clean_text(points[0], 42), _clean_text(points[1], 42)],
            "senior_tip": _clean_text(scene.get("senior_tip"), 52),
            "narration": _clean_text(scene.get("narration"), 260),
        }
        if not all(normalized[key] for key in ("badge", "title", "subtitle", "senior_tip", "narration")):
            return None
        strings = [value for value in normalized.values() if isinstance(value, str)] + normalized["key_points"]
        if any(any(banned in value for banned in BANNED_PHRASES) for value in strings):
            return None
        scenes.append(normalized)
    return scenes


def _dedupe_terms(scenes: list[dict[str, Any]]) -> list[str]:
    raw = " ".join(
        " ".join([scene["title"], scene["subtitle"], scene["narration"], *scene["key_points"]])
        for scene in scenes
    ).lower()
    terms = {term for term in re.findall(r"[0-9a-z가-힣]{2,}", raw) if term not in STOPWORDS}
    return sorted(terms)


def _recent_story_profiles(limit: int = 80) -> tuple[set[str], list[set[str]], set[str]]:
    fingerprints: set[str] = set()
    profiles: list[set[str]] = []
    openings: set[str] = set()
    if not METADATA_DIR.exists():
        return fingerprints, profiles, openings
    for path in sorted(METADATA_DIR.glob("*_sources.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if record.get("script_fingerprint"):
            fingerprints.add(str(record["script_fingerprint"]))
        terms = {str(value) for value in record.get("dedupe_terms", []) if value}
        if terms:
            profiles.append(terms)
        if record.get("opening_normalized"):
            openings.add(str(record["opening_normalized"]))
    return fingerprints, profiles, openings


def _normalized_opening(scenes: list[dict[str, Any]]) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", scenes[0]["narration"].lower())


def _is_new_script(
    scenes: list[dict[str, Any]],
    fingerprint: str,
    previous_fingerprints: set[str],
    previous_profiles: list[set[str]],
    previous_openings: set[str],
) -> tuple[bool, str]:
    if fingerprint in previous_fingerprints:
        return False, "동일 대본 지문"
    opening = _normalized_opening(scenes)
    if opening in previous_openings:
        return False, "동일 오프닝"
    terms = set(_dedupe_terms(scenes))
    threshold = float(os.environ.get("QA_SCRIPT_SIMILARITY_THRESHOLD", "0.72"))
    for profile in previous_profiles:
        union = terms | profile
        similarity = len(terms & profile) / len(union) if union else 0.0
        if similarity >= threshold:
            return False, f"유사도 {similarity:.0%}"
    return True, "신규"


def _provider_candidates() -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    cheap_key = os.environ.get("CHEAPAI_API_KEY", "").strip()
    cheap_base = os.environ.get("CHEAPAI_BASE_URL", "https://api.cheapai.im/v1").rstrip("/")
    if cheap_key:
        models = (
            os.environ.get("CHEAPAI_STORY_MODEL", "gpt-5.6-sol").strip(),
            os.environ.get("CHEAPAI_STORY_FALLBACK_MODEL", "claude-sonnet-5").strip(),
        )
        for model in dict.fromkeys(model for model in models if model):
            candidates.append({"provider": "cheapai", "base_url": cheap_base, "api_key": cheap_key, "model": model})

    official_key = os.environ.get("OFFICIAL_OPENAI_API_KEY", "").strip()
    if official_key:
        candidates.append({
            "provider": "official_openai",
            "base_url": os.environ.get("OFFICIAL_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            "api_key": official_key,
            "model": os.environ.get("OFFICIAL_OPENAI_STORY_MODEL", "gpt-5-mini").strip(),
        })
    return candidates


def _prompt(topic_name: str, angle: dict[str, str], sources: list[dict[str, str]], story_id: str, attempt: int) -> tuple[str, str]:
    system = """당신은 큐에이플러스(QA+)의 식품 품질관리 콘텐츠 편집자입니다.
제공된 공식 최신 웹 출처만 근거로 9:16 쇼츠용 5개 장면을 작성합니다.

필수 규칙:
- 출처에 없는 법령 조항, 수치, 장비사양, 심사 관행을 만들지 마세요.
- 출처가 부족한 부분은 사내 SOP·사업장 유효성 평가·최신 고시 원문 확인이 필요하다고 표현하세요.
- 100%, 무조건 통과, 완벽 통과, 합격 보장, 지적 0건 같은 보장·과장 표현을 쓰지 마세요.
- 첫 장면은 인사말 없이 이번 앵글의 문제를 제시하세요.
- 기존 영상과 제목, 첫 문장, 사례, 체크 순서가 겹치지 않게 작성하세요.
- 다섯 번째 장면은 최신 공식 원문과 사업장 적용성 확인으로 마무리하세요.
- JSON 객체만 반환하세요. 코드블록을 쓰지 마세요.

JSON 형식:
{"scenes":[{"badge":"짧은 배지","title":"첫줄\\n둘째줄","subtitle":"짧은 소제목","key_points":["핵심1","핵심2"],"senior_tip":"현장 팁","narration":"나레이션"},{"badge":"짧은 배지","title":"첫줄\\n둘째줄","subtitle":"짧은 소제목","key_points":["핵심1","핵심2"],"senior_tip":"현장 팁","narration":"나레이션"},{"badge":"짧은 배지","title":"첫줄\\n둘째줄","subtitle":"짧은 소제목","key_points":["핵심1","핵심2"],"senior_tip":"현장 팁","narration":"나레이션"},{"badge":"짧은 배지","title":"첫줄\\n둘째줄","subtitle":"짧은 소제목","key_points":["핵심1","핵심2"],"senior_tip":"현장 팁","narration":"나레이션"},{"badge":"짧은 배지","title":"첫줄\\n둘째줄","subtitle":"짧은 소제목","key_points":["핵심1","핵심2"],"senior_tip":"현장 팁","narration":"나레이션"}]}"""
    user = (
        f"주제: {topic_name}\n"
        f"이번 앵글: {angle['id']}\n"
        f"오프닝 방향: {angle['opening'].format(topic=topic_name)}\n"
        f"고유 생성 코드: {story_id}\n"
        f"생성 시도: {attempt}\n\n"
        f"실시간 공식 웹 근거:\n{_source_context(sources)}"
    )
    return system, user


def generate_live_web_script(topic_name: str, angle: dict[str, str], sources: list[dict[str, str]], story_id: str) -> tuple[list[dict[str, Any]], str, str, str]:
    fingerprints, profiles, openings = _recent_story_profiles()
    candidates = _provider_candidates()
    if not candidates:
        raise RuntimeError("사용 가능한 LLM API 키가 없습니다. CHIPSUB_API 또는 공식 OpenAI API 키를 설정하세요.")
    try:
        timeout = min(max(int(os.environ.get("QA_LLM_TIMEOUT_SECONDS", "15")), 10), 60)
    except ValueError:
        timeout = 25

    try:
        max_attempts = min(max(int(os.environ.get("QA_LLM_MAX_ATTEMPTS_PER_MODEL", "2")), 1), 3)
    except ValueError:
        max_attempts = 2

    errors: list[str] = []
    for candidate in candidates:
        for attempt in range(1, max_attempts + 1):
            try:
                system, user = _prompt(topic_name, angle, sources, story_id, attempt)
                response = requests.post(
                    f"{candidate['base_url']}/chat/completions",
                    headers={"Authorization": f"Bearer {candidate['api_key']}", "Content-Type": "application/json"},
                    json={
                        "model": candidate["model"],
                        "temperature": 1.0,
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    },
                    timeout=timeout,
                )
                if not response.ok:
                    errors.append(f"{candidate['provider']}/{candidate['model']}: HTTP {response.status_code}")
                    break
                raw = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                parsed = json.loads(_strip_json_fence(raw))
                scenes = _validate_scenes(parsed.get("scenes"))
                if not scenes:
                    errors.append(f"{candidate['provider']}/{candidate['model']}: 형식·안전 검증 실패")
                    continue
                fingerprint = _scene_fingerprint(scenes)
                is_new, reason = _is_new_script(scenes, fingerprint, fingerprints, profiles, openings)
                if is_new:
                    print(f"  [라이브 웹 대본] {candidate['provider']}/{candidate['model']} 신규 대본 생성 성공 (시도 {attempt})")
                    return scenes, candidate["provider"], candidate["model"], fingerprint
                errors.append(f"{candidate['provider']}/{candidate['model']}: {reason}")
            except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
                errors.append(f"{candidate['provider']}/{candidate['model']}: {type(exc).__name__}")
            time.sleep(min(1.5 * attempt, 3.0))
    raise RuntimeError("실시간 최신·신규 대본 생성에 실패했습니다. " + " | ".join(errors[-6:]))


def build_live_web_story(topic_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    topic_name = _topic(topic_name)
    story_id = _story_id()
    angle = _angle(topic_name, story_id)
    sources = fetch_live_official_sources(topic_name)
    scenes, provider, model, fingerprint = generate_live_web_script(topic_name, angle, sources, story_id)
    metadata: dict[str, Any] = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "story_id": story_id,
        "topic": topic_name,
        "story_angle": angle["id"],
        "generation_mode": "live_web_llm_verified",
        "provider": provider,
        "model": model,
        "script_fingerprint": fingerprint,
        "opening_normalized": _normalized_opening(scenes),
        "dedupe_terms": _dedupe_terms(scenes),
        "official_sources": sources,
        "source_count": len(sources),
        "review_note": "매 실행 시 공식 웹을 검색했습니다. 게시 전 최신 원문과 사업장 적용성을 최종 확인하세요.",
    }
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    safe_topic = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", topic_name).strip("_")[:32] or "topic"
    (METADATA_DIR / f"{dt.date.today().isoformat()}_{safe_topic}_{story_id}_sources.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return scenes, metadata
