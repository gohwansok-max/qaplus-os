# -*- coding: utf-8 -*-
"""QA+ HyperFrames 쇼츠 렌더러.

기존 qa_motion_shorts.py의 씬 JSON을 입력으로 받아 HTML/GSAP 기반
1080x1920 영상을 렌더링한다. Remotion 경로는 수정하지 않는다.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
HF_DIR = BASE_DIR / "qa-shorts" / "hyperframes"
ASSET_DIR = HF_DIR / "assets"
OUT_DIR = BASE_DIR / "outputs" / "videos"
FPS = 30

DEMO_SCENES = [
    {"type": "hook", "duration": 5.6, "headline": "CCP 기록\n숫자만 쓰면 끝?", "sub": "기록은 판정과 조치까지 연결돼야 합니다.", "narration": "CCP 기록, 숫자만 쓰면 끝일까요? 아닙니다."},
    {"type": "flow", "duration": 6.2, "headline": "기록의 기본 구조", "steps": ["측정값", "판정", "이탈 시 조치"], "narration": "기록에는 측정값, 판정, 그리고 이탈 시 조치가 함께 있어야 합니다."},
    {"type": "compare", "duration": 6.4, "headline": "한계기준 이탈 시", "bad": ["숫자만 기록", "제품 그대로 진행"], "good": ["제품 우선 보류", "원인 확인·조치 기록"], "narration": "한계기준을 벗어났다면 제품을 우선 보류하고, 원인을 확인한 뒤 조치 결과를 기록하세요."},
    {"type": "checklist", "duration": 6.1, "headline": "심사에서 보는 연결", "items": ["측정값과 판정", "이탈 행과 조치", "조치 후 검증"], "narration": "마지막으로 검증까지 남겨야 기록이 단순한 숫자가 아니라 증거가 됩니다."},
    {"type": "outro", "duration": 5.8, "headline": "기준 → 측정 → 판정\n→ 조치 → 검증", "sub": "최신 고시와 사업장 HACCP 관리계획서를 최종 확인하세요.", "narration": "실제 기준은 우리 공정의 HACCP 관리계획서와 최신 고시를 확인하세요."},
]


def _esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _items(values: list[str], cls: str = "") -> str:
    return "".join(f'<li class="{cls}"><span class="dot"></span>{_esc(v)}</li>' for v in values)


def _scene_markup(scene: dict, index: int, start: float, audio: str | None) -> str:
    typ = scene.get("type", "checklist")
    headline = _esc(scene.get("headline") or scene.get("title") or scene.get("takeaway"))
    sub = _esc(scene.get("sub") or scene.get("caption") or "")
    body = ""
    if typ == "flow":
        steps = scene.get("steps", [])
        body = '<div class="flow">' + "".join(f'<div class="flow-step"><b>0{i+1}</b><span>{_esc(v)}</span></div>' for i, v in enumerate(steps)) + "</div>"
    elif typ == "compare":
        body = f'<div class="compare"><div class="bad"><small>흔한 실수</small><ul>{_items(scene.get("bad", []))}</ul></div><div class="good"><small>이렇게 기록</small><ul>{_items(scene.get("good", []))}</ul></div></div>'
    elif typ == "checklist":
        body = f'<ul class="checklist">{_items(scene.get("items", []))}</ul>'
    else:
        body = f'<div class="accent-line"></div><p class="sub">{sub}</p>'
    audio_tag = f'<audio id="audio-scene-{index+1}" src="{_esc(audio)}" data-start="0" data-duration="{scene["duration"]:.3f}" preload="auto"></audio>' if audio else ""
    return f'''<section id="scene-{index+1}-{typ}" class="scene scene-{typ}" data-composition-id="scene-{index}" data-start="{start:.3f}" data-duration="{scene["duration"]:.3f}" data-width="1080" data-height="1920">\n      <div class="scene-inner"><span class="scene-no">0{index + 1} / 05</span><h1>{headline.replace(chr(10), "<br>")}</h1>{body}</div>{audio_tag}\n    </section>'''


def write_html(scenes: list[dict], title: str, audio_paths: list[str] | None = None) -> Path:
    HF_DIR.mkdir(parents=True, exist_ok=True)
    starts, cursor = [], 0.0
    for s in scenes:
        starts.append(cursor)
        cursor += float(s["duration"])
    sections = "\n".join(_scene_markup(s, i, starts[i], audio_paths[i] if audio_paths else None) for i, s in enumerate(scenes))
    total = cursor
    title = _esc(title)
    content = '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=1080,height=1920"><title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#07111f;color:#f8fafc;font-family:Arial,sans-serif}}#master-root{{position:relative;width:1080px;height:1920px;background:radial-gradient(circle at 75% 12%,#164e63 0,#0b1c31 35%,#050b16 100%);overflow:hidden}}#master-root:before{{content:"";position:absolute;inset:0;background:linear-gradient(135deg,transparent 0 42%,rgba(34,211,238,.1) 42.1% 42.4%,transparent 42.5% 100%);opacity:.8}}.scene{{position:absolute;inset:0;padding:180px 78px 160px;opacity:0;visibility:hidden}}.scene-inner{{position:relative;z-index:2;height:100%;display:flex;flex-direction:column;justify-content:center;}}.scene-no{{color:#67e8f9;font-size:28px;font-weight:800;letter-spacing:.12em;margin-bottom:36px}}h1{{font-size:86px;line-height:1.08;letter-spacing:-.06em;margin:0 0 54px;font-weight:900}}.sub,.scene p.sub{{font-size:34px;line-height:1.45;color:#cbd5e1;margin:0;max-width:850px}}.accent-line{{width:180px;height:8px;border-radius:8px;background:#22d3ee;margin:-20px 0 42px;box-shadow:0 0 30px #22d3ee}}.flow,.checklist,.compare{{display:flex;flex-direction:column;gap:22px}}.flow-step,.checklist li,.bad,.good{{border:1px solid rgba(148,163,184,.28);background:rgba(15,23,42,.72);border-radius:22px;padding:28px 32px;font-size:38px;box-shadow:0 16px 50px rgba(0,0,0,.18)}}.flow-step{{display:flex;align-items:center;gap:24px}}.flow-step b{{color:#22d3ee;font-size:30px}}ul{{list-style:none;padding:0;margin:0}.checklist li{{display:flex;align-items:center;gap:20px}}.dot{{display:inline-block;width:20px;height:20px;border-radius:50%;background:#22d3ee;box-shadow:0 0 20px #22d3ee;flex:0 0 auto}}.compare{{gap:26px}}.bad,.good{{padding:30px 34px}}.bad{{border-color:rgba(251,113,133,.55)}}.good{{border-color:rgba(45,212,191,.65)}}small{{display:block;font-size:26px;font-weight:800;margin-bottom:20px;color:#fda4af}}.good small{{color:#5eead4}}.bad li,.good li{{font-size:34px;line-height:1.4;margin:12px 0}.good .dot{{background:#5eead4;box-shadow:0 0 20px #5eead4}}#brand{{position:absolute;z-index:5;top:64px;left:78px;font-size:25px;letter-spacing:.1em;color:#a5f3fc;font-weight:800}}#progress{{position:absolute;z-index:5;left:78px;right:78px;bottom:78px;height:8px;background:rgba(148,163,184,.25);border-radius:8px}}#progress i{{display:block;height:100%;width:20%;background:#22d3ee;border-radius:8px;box-shadow:0 0 18px #22d3ee}}[data-composition-id="master"]>.scene{{display:block}}.scene.active{{visibility:visible;opacity:1}}\n</style></head><body><div id="master-root" data-composition-id="master" data-width="1080" data-height="1920" data-start="0" data-duration="{total:.3f}"><div id="brand">QA+ / FOOD QUALITY PRACTICE</div>{sections}<div id="progress"><i></i></div><script>window.__timelines=window.__timelines||{{}};window.__timelines.master=gsap.timeline({{paused:true}});</script></div>
<script>const scenes=[...document.querySelectorAll('.scene')];const bar=document.querySelector('#progress i');scenes.forEach((el,i)=>{{const inner=el.querySelector('.scene-inner');gsap.set(el,{{autoAlpha:0}});gsap.set(inner,{{y:36,scale:.98}});const tl=gsap.timeline({{paused:true}});tl.to(el,{{autoAlpha:1,duration:.35}}).to(inner,{{y:0,scale:1,duration:.65,ease:'power3.out'}},0).to(el,{{autoAlpha:0,duration:.3}},Math.max(.4,parseFloat(el.dataset.duration)-.3));window.__timelines[el.dataset.compositionId]=tl}});</script></body></html>'''
    content = content.replace("{{", "{").replace("}}", "}").replace("{title}", title).replace("{sections}", sections).replace("{total:.3f}", f"{total:.3f}")
    out = HF_DIR / "index.html"
    out.write_text(content, encoding="utf-8")
    (HF_DIR / "meta.json").write_text(json.dumps({"title": title, "width": 1080, "height": 1920, "fps": FPS, "duration": total, "renderer": "hyperframes"}, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def render_demo() -> Path:
    # 기존 HyperFrames 검증 음성을 재사용하여 렌더러 자체와 영상 출력부터 검증한다.
    source_audio = Path("/home/ubuntu/haccp-hyperframes-short/voiceover.wav")
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    audio = ASSET_DIR / "voiceover.wav"
    shutil.copyfile(source_audio, audio)
    write_html(DEMO_SCENES, "CCP 기록, 숫자만 쓰면 끝일까요?", ["assets/voiceover.wav"] + [None] * (len(DEMO_SCENES) - 1))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUT_DIR / "hyperframes_haccp_ccp_demo.mp4"
    subprocess.run(["npx", "--yes", "hyperframes", "check"], cwd=HF_DIR, check=True)
    subprocess.run(["npx", "--yes", "hyperframes", "render", "--resolution", "portrait", "--quality", "high", "--workers", "1", "-o", str(output)], cwd=HF_DIR, check=True)
    return output


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if not args.demo:
        ap.error("현재 검증 단계는 --demo로 실행합니다.")
    result = render_demo()
    print(json.dumps({"path": str(result), "size": result.stat().st_size}, ensure_ascii=False))
