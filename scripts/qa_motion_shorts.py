# -*- coding: utf-8 -*-
"""QA+ 모션그래픽 쇼츠 파이프라인 (Remotion).

주제 1개 → (LLM) 모션 씬 JSON → Edge-TTS 음성·자막 타이밍 → Remotion 렌더 → MP4(40~60초, 1080x1920)

LLM 호출 우선순위 (QA_LLM_PROVIDERS, 쉼표 구분, 기본 "claude_cli,codex_cli,cheapai")
  1. claude_cli : Claude 구독(Claude Code CLI). env CLAUDE_CODE_OAUTH_TOKEN  (`claude setup-token`으로 발급)
  2. codex_cli  : ChatGPT 구독(Codex CLI).   env CODEX_AUTH_JSON (로컬 ~/.codex/auth.json 내용)
  3. cheapai    : 기존 CHIPSUB_API(OpenAI 호환)
  4. local      : 안전한 로컬 대체 대본 (항상 마지막)
법령·수치는 공식 출처 문맥에 있는 것만 쓰도록 프롬프트·검증으로 강제한다.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_story_engine as eng  # noqa: E402

BASE_DIR = Path(__file__).resolve().parents[1]
PROJ = BASE_DIR / "qa-shorts"
RUN_DIR = PROJ / "public" / "run"
VIDEOS_DIR = BASE_DIR / "outputs" / "videos"
AUDIO_DIR = BASE_DIR / "outputs" / "audio"
FPS = 30
VOICE = os.environ.get("QA_TTS_VOICE", "ko-KR-InJoonNeural")
MIN_SEC, MAX_SEC = 40.0, 60.0
SCENE_TYPES = {"hook", "stat", "flow", "compare", "checklist", "outro"}
CTA = "매일 무료 자료 · 큐에이플러스 오픈채팅"

SYSTEM_PROMPT = """당신은 식품 품질관리 20년 차 실무자의 목소리로 쓰는 쇼츠 작가입니다. 대상은 식품회사 신입·주니어 QA/QC와 HACCP·FSSC 22000 준비 담당자입니다.
9:16 모션그래픽 쇼츠 1편(낭독 40~55초)의 씬 JSON을 작성합니다.

[내용 규칙]
- 아래 '공식 출처 문맥'에 없는 법령 조항·수치·한계기준·인증 요구사항은 지어내지 마세요. 확실치 않으면 수치를 쓰지 말고 '사업장 유효성 평가', '최신 고시 원문 확인'처럼 조건부로 표현하세요.
- 'stat' 씬은 출처 문맥에 근거한 숫자일 때만 쓰세요. 근거가 없으면 stat을 쓰지 마세요.
- '100%', '무조건 통과', '합격 보장', '지적 0건' 등 보장·과장·공포 마케팅 표현 금지. 특정 회사·개인 식별 정보 금지.
- 인사말·서론 금지. 첫 문장은 3초 안에 시선을 잡는 질문/반전/현장 장면. 모든 문장이 실무 인사이트여야 합니다.
- 전문 용어 뒤에는 '쉽게 말하면'으로 일상어 풀이를 한 번 넣으세요. 말투는 존댓말의 든든한 선배.
- 매번 다른 구성: 아래 '이번 앵글'과 '피해야 할 최근 주제'를 반영하세요.

[구조 규칙]
- scenes 6~7개. 첫 씬 type=hook, 마지막 씬 type=outro, 가운데 4~5개는 stat/flow/compare/checklist 중 3종류 이상 사용.
- 씬마다 narration(낭독문) 필수. 1~2문장, 28~85자. 전체 narration 합계 260~380자.
- hook 첫 narration은 30자 이내.
- 화면 텍스트는 짧게: headline 줄당 12자 이내(\\n으로 2줄), 항목 문구 22자 이내.

[씬 스키마]
hook:      {"type":"hook","kicker":"배지 10자 이내","headline":"첫줄\\n둘째줄","sub":"보조 문구 28자 이내","narration":"..."}
stat:      {"type":"stat","label":"무엇의 수치인지 16자 이내","value":"출처 근거 숫자+단위(예: 2.0mm)","caption":"의미 26자 이내","note":"출처명(선택)","narration":"..."}
flow:      {"type":"flow","title":"20자 이내","steps":["단계 3~4개"],"narration":"..."}
compare:   {"type":"compare","title":"20자 이내","bad":{"label":"흔한 실수","items":["2~3개"]},"good":{"label":"이렇게","items":["2~3개"]},"narration":"..."}
checklist: {"type":"checklist","title":"20자 이내","items":["3~4개"],"narration":"..."}
outro:     {"type":"outro","takeaway":"오늘의 한 줄 결론 30자 이내","narration":"마지막에 최신 고시·사업장 기준 확인 권고 포함"}

반드시 JSON 객체 하나만 반환: {"badge":"상단 배지 8자 이내","scenes":[...]}  (마크다운·설명 금지)"""


# ───────────────────────── LLM 공급자 ─────────────────────────
def _user_prompt(topic: str, angle: dict, sources: list, avoid: list[str]) -> str:
    return (
        f"주제: {topic}\n이번 앵글: {angle['id']} — {angle['opening'].format(topic=topic)}\n"
        f"피해야 할 최근 주제: {', '.join(avoid) if avoid else '없음'}\n"
        f"오늘 날짜: {dt.date.today().isoformat()}\n\n공식 출처 문맥:\n{eng._source_context(sources)}"
    )


def _llm_claude_cli(system: str, user: str) -> str | None:
    if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or not shutil.which("claude"):
        return None
    model = os.environ.get("QA_CLAUDE_MODEL", "sonnet")
    res = subprocess.run(
        ["claude", "-p", "--output-format", "text", "--model", model, "--max-turns", "2",
         "--append-system-prompt", system],
        input=user, capture_output=True, text=True, timeout=300,
    )
    if res.returncode != 0:
        print(f"  [LLM] claude_cli 실패: {res.stderr.strip()[:200]}")
        return None
    return res.stdout


def _llm_codex_cli(system: str, user: str) -> str | None:
    auth = os.environ.get("CODEX_AUTH_JSON", "").strip()
    if not auth or not shutil.which("codex"):
        return None
    home = Path.home() / ".codex"
    home.mkdir(parents=True, exist_ok=True)
    (home / "auth.json").write_text(auth, encoding="utf-8")
    out = RUN_DIR / "codex_last.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        ["codex", "exec", "--skip-git-repo-check", "-s", "read-only", "--output-last-message", str(out), "-"],
        input=system + "\n\n" + user, capture_output=True, text=True, timeout=300,
    )
    if res.returncode != 0 or not out.exists():
        print(f"  [LLM] codex_cli 실패: {res.stderr.strip()[:200]}")
        return None
    return out.read_text(encoding="utf-8")


def _llm_cheapai(system: str, user: str) -> str | None:
    key = os.environ.get("CHEAPAI_API_KEY", "").strip()
    if not key:
        return None
    base = os.environ.get("CHEAPAI_BASE_URL", "https://api.cheapai.im/v1").rstrip("/")
    for model in (os.environ.get("CHEAPAI_STORY_MODEL", "claude-sonnet-5"), os.environ.get("CHEAPAI_STORY_FALLBACK_MODEL", "gpt-5.6-sol")):
        try:
            r = requests.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "temperature": 1.0,
                      "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                timeout=60,
            )
            if r.ok:
                return r.json()["choices"][0]["message"]["content"]
            print(f"  [LLM] cheapai/{model} HTTP {r.status_code}")
        except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
            print(f"  [LLM] cheapai/{model} 실패: {type(exc).__name__}")
    return None


PROVIDERS = {"claude_cli": _llm_claude_cli, "codex_cli": _llm_codex_cli, "cheapai": _llm_cheapai}


# ───────────────────────── 대본 검증 ─────────────────────────
def _s(v: Any, n: int) -> str:
    return re.sub(r"[ \t]+", " ", str(v or "")).strip()[:n]


def _list(v: Any, lo: int, hi: int, n: int) -> list[str] | None:
    if not isinstance(v, list):
        return None
    items = [_s(x, n) for x in v if _s(x, n)]
    return items[:hi] if len(items) >= lo else None


def validate_script(raw: Any, sources: list) -> dict | None:
    """스키마·분량·금지표현·수치 근거를 검사하고 정규화한다. 실패 시 None."""
    if not isinstance(raw, dict) or not isinstance(raw.get("scenes"), list):
        return None
    scenes_in = raw["scenes"]
    if not 6 <= len(scenes_in) <= 7 or scenes_in[0].get("type") != "hook" or scenes_in[-1].get("type") != "outro":
        return None
    source_text = " ".join(s["snippet"] + s["title"] for s in sources)
    out: list[dict] = []
    for sc in scenes_in:
        t = sc.get("type")
        if t not in SCENE_TYPES:
            return None
        nar = _s(sc.get("narration"), 120)
        if not 15 <= len(nar) <= 100:
            return None
        o: dict[str, Any] = {"type": t, "narration": nar}
        if t == "hook":
            o.update(kicker=_s(sc.get("kicker"), 12), headline="\n".join(_s(x, 14) for x in str(sc.get("headline", "")).splitlines()[:2]), sub=_s(sc.get("sub"), 32))
            if not (o["kicker"] and o["headline"] and o["sub"]):
                return None
        elif t == "stat":
            o.update(label=_s(sc.get("label"), 18), value=_s(sc.get("value"), 12), caption=_s(sc.get("caption"), 30), note=_s(sc.get("note"), 40))
            nums = re.findall(r"\d+(?:\.\d+)?", o["value"])
            if not (o["label"] and o["value"] and o["caption"]) or not nums or not any(n in source_text for n in nums):
                return None  # 출처에 없는 숫자는 stat으로 쓰지 않는다 (Zero-Inference)
        elif t == "flow":
            steps = _list(sc.get("steps"), 3, 4, 22)
            o.update(title=_s(sc.get("title"), 22), steps=steps)
            if not (o["title"] and steps):
                return None
        elif t == "compare":
            bad, good = sc.get("bad") or {}, sc.get("good") or {}
            bi, gi = _list(bad.get("items"), 2, 3, 24), _list(good.get("items"), 2, 3, 24)
            o.update(title=_s(sc.get("title"), 22), bad={"label": _s(bad.get("label"), 10), "items": bi}, good={"label": _s(good.get("label"), 10), "items": gi})
            if not (o["title"] and bi and gi and o["bad"]["label"] and o["good"]["label"]):
                return None
        elif t == "checklist":
            items = _list(sc.get("items"), 3, 4, 24)
            o.update(title=_s(sc.get("title"), 22), items=items)
            if not (o["title"] and items):
                return None
        elif t == "outro":
            o.update(takeaway=_s(sc.get("takeaway"), 34), cta=CTA)
            if not o["takeaway"]:
                return None
        if any(eng._has_banned_phrase(v) for v in json.dumps(o, ensure_ascii=False).split('"')):
            return None
        out.append(o)
    total = sum(len(x["narration"]) for x in out)
    if not 240 <= total <= 400 or len({x["type"] for x in out[1:-1]}) < 3:
        return None
    return {"badge": _s(raw.get("badge"), 10) or "품질 실무", "scenes": out}


def _fingerprint(script: dict) -> str:
    norm = re.sub(r"[^0-9A-Za-z가-힣]+", "", "".join(s["narration"] for s in script["scenes"]))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _local_fallback(topic: str, angle: dict, story_id: str) -> dict:
    """LLM이 모두 실패했을 때: 기존 검증형 로컬 대본을 모션 씬으로 매핑 (수치 없음)."""
    old = eng.local_verified_fallback(topic, angle, story_id)
    sc = []
    for i, o in enumerate(old):
        nar = o["narration"]
        if i == 0:
            sc.append({"type": "hook", "kicker": "현장 실무", "headline": o["title"], "sub": o["subtitle"], "narration": nar})
        elif i == 2:
            sc.append({"type": "flow", "title": o["subtitle"][:22], "steps": o["key_points"] + [o["senior_tip"][:22]], "narration": nar})
        elif i == 4:
            sc.append({"type": "outro", "takeaway": o["senior_tip"][:34], "cta": CTA, "narration": nar})
        else:
            sc.append({"type": "checklist", "title": o["title"].replace("\n", " ")[:22], "items": o["key_points"] + [o["senior_tip"][:24]], "narration": nar})
    return {"badge": "품질 실무", "scenes": sc}


def generate_motion_script(topic: str) -> tuple[dict, dict]:
    topic = eng._topic(topic)
    story_id = eng._story_id()
    angle = eng._angle(topic, story_id)
    recent = eng._recent_story_fingerprints()
    sources = eng.fetch_official_sources(topic)
    avoid = _recent_topics()
    user = _user_prompt(topic, angle, sources, avoid)
    script, provider = None, "local_verified_fallback"
    for name in [p.strip() for p in os.environ.get("QA_LLM_PROVIDERS", "claude_cli,codex_cli,cheapai").split(",") if p.strip()]:
        fn = PROVIDERS.get(name)
        if not fn:
            continue
        for attempt in (1, 2):
            try:
                raw = fn(SYSTEM_PROMPT, user + f"\n\n생성 시도 {attempt}: 직전 시도와 다르게 새로 작성.")
            except (subprocess.SubprocessError, OSError) as exc:
                print(f"  [LLM] {name} 호출 실패: {type(exc).__name__}")
                break
            if raw is None:
                break
            try:
                cand = validate_script(json.loads(eng._strip_json_fence(raw)), sources)
            except ValueError:
                cand = None
            if cand and _fingerprint(cand) not in recent:
                script, provider = cand, name
                break
            print(f"  [LLM] {name} 응답이 검증을 통과하지 못했습니다 (시도 {attempt})")
        if script:
            break
    if not script:
        script = _local_fallback(topic, angle, story_id)
    meta = {"story_id": story_id, "topic": topic, "story_angle": angle["id"], "generation_mode": provider,
            "renderer": "remotion", "script_fingerprint": _fingerprint(script),
            "official_sources": sources, "source_count": len(sources),
            "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "review_note": "게시 전 최신 고시 원문·사업장 유효성 평가·표현 적정성을 최종 확인하세요."}
    eng.METADATA_DIR.mkdir(parents=True, exist_ok=True)
    eng._metadata_path(topic, story_id).write_text(json.dumps({**meta, "script": script}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [대본] 생성 완료 · provider={provider} · 씬 {len(script['scenes'])}개")
    return script, meta


def _recent_topics(limit: int = 10) -> list[str]:
    topics: list[str] = []
    if eng.METADATA_DIR.exists():
        for p in sorted(eng.METADATA_DIR.glob("*_sources.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            try:
                topics.append(json.loads(p.read_text(encoding="utf-8")).get("topic", ""))
            except (OSError, ValueError):
                pass
    return [t for t in topics if t]


# ───────────────────────── TTS · 자막 · 타이밍 ─────────────────────────
def _probe(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


async def _tts(scenes: list[dict], run: Path, rate: str) -> None:
    import edge_tts
    for i, s in enumerate(scenes, 1):
        out = run / f"scene_{i:02d}.mp3"
        await edge_tts.Communicate(s["narration"], VOICE, rate=rate).save(str(out))
        s["audio"] = f"run/{run.name}/{out.name}"
        s["_sec"] = _probe(out)


def _captions(text: str, frames: int, lead: int = 5) -> list[dict]:
    """문장→어절 묶음(≤15자) 단위 자막. 글자 수 비례로 음성 구간에 배분한다."""
    chunks: list[str] = []
    for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
        cur = ""
        for w in sent.split():
            if cur and len(cur) + 1 + len(w) > 15:
                chunks.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            chunks.append(cur)
    span = max(1, frames - lead - 6)
    total = sum(len(c) for c in chunks) or 1
    caps, t = [], lead
    for c in chunks:
        n = max(8, round(span * len(c) / total))
        caps.append({"text": c.rstrip(".!?"), "start": t, "end": min(frames, t + n)})
        t += n
    return caps


def build_props(script: dict, run: Path) -> dict:
    scenes = script["scenes"]
    for rate in ("+5%", "+15%", "+25%"):
        asyncio.run(_tts(scenes, run, rate))
        voice = sum(s["_sec"] for s in scenes)
        total = voice + 0.45 * len(scenes)
        print(f"  [TTS] rate={rate} 낭독 {voice:.1f}s → 총 {total:.1f}s")
        if total <= MAX_SEC - 1:
            break
    if total > MAX_SEC:
        raise RuntimeError(f"영상 길이 {total:.1f}s > {MAX_SEC}s — 대본이 너무 깁니다")
    pad = max(0.0, MIN_SEC + 0.5 - total)  # 40초 미만이면 마지막 씬 여운으로 보충
    if pad > 6:
        raise RuntimeError(f"영상 길이 {total:.1f}s < {MIN_SEC}s — 대본이 너무 짧습니다")
    cursor = 0
    for i, s in enumerate(scenes):
        frames = round((s["_sec"] + 0.45 + (pad if i == len(scenes) - 1 else 0)) * FPS)
        s["startFrame"], s["durationFrames"] = cursor, frames
        s["captions"] = _captions(s["narration"], round((s["_sec"] + 0.2) * FPS))
        cursor += frames
        s.pop("_sec", None)
    bgm = "run/bgm.wav" if _stage_file(AUDIO_DIR / "bgm_ambient_tech.wav", run.parent / "bgm.wav") else None
    sfx = "run/sfx.wav" if _stage_file(AUDIO_DIR / "sfx_whoosh.wav", run.parent / "sfx.wav") else None
    return {"topic": "", "badge": script["badge"], "scenes": scenes, "totalFrames": cursor, "bgm": bgm, "sfx": sfx}


def _stage_file(src: Path, dst: Path) -> bool:
    if src.exists():
        shutil.copyfile(src, dst)
        return True
    return False


# ───────────────────────── 렌더 ─────────────────────────
def render(props: dict, out: Path) -> None:
    props_file = RUN_DIR / "props.json"
    props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    if not (PROJ / "node_modules").exists():
        subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=PROJ, check=True)
    cmd = ["npx", "remotion", "render", "src/index.ts", "QaShort", str(out), f"--props={props_file}",
           "--concurrency=2", "--log=error"]
    browser = os.environ.get("REMOTION_BROWSER_EXECUTABLE", "")
    if browser:
        cmd.append(f"--browser-executable={browser}")
    subprocess.run(cmd, cwd=PROJ, check=True)


def build_motion_short(topic: str) -> dict:
    """주제 → MP4. 반환: {path, filename, scenes(메타용), meta}"""
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%H%M%S")
    run = RUN_DIR / stamp
    run.mkdir(parents=True, exist_ok=True)
    print("\n[1/3] 모션 대본 생성")
    script, meta = generate_motion_script(topic)
    print("[2/3] Edge-TTS 음성 · 자막 타이밍")
    props = build_props(script, run)
    props["topic"] = topic
    clean = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", topic).strip("_")[:30] or "topic"
    filename = f"{dt.date.today().isoformat()}_{clean}_shorts.mp4"
    out = VIDEOS_DIR / filename
    print(f"[3/3] Remotion 렌더 ({props['totalFrames'] / FPS:.1f}s, {len(props['scenes'])}씬)")
    render(props, out)
    shutil.rmtree(run, ignore_errors=True)
    meta_scenes = []
    for s in script["scenes"]:
        meta_scenes.append({"title": s.get("headline") or s.get("title") or s.get("takeaway", ""), "subtitle": s.get("sub") or s.get("caption") or ""})
    return {"path": str(out), "filename": filename, "scenes": meta_scenes, "meta": meta,
            "duration_sec": props["totalFrames"] / FPS, "props": props}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    r = build_motion_short(ap.parse_args().topic)
    print(json.dumps({k: r[k] for k in ("path", "duration_sec")}, ensure_ascii=False))
