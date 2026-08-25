# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "video_frames")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SCENES = [
    {"scene": 1, "time": "00:00 - 00:30", "category": "STEP 1 • 기초 개념", "title": "한계기준(Critical Limit)의 본질 & 운용한계(OL)", "color": (6, 182, 212)},
    {"scene": 2, "time": "00:30 - 01:00", "category": "STEP 2 • 설정 방법론", "title": "한계기준 설정 4단계 표준 프로세스", "color": (59, 130, 246)},
    {"scene": 3, "time": "01:00 - 01:30", "category": "STEP 3 • 검증 철학", "title": "유효성 검증(Validation) vs 일상 검증(Verification)", "color": (139, 92, 246)},
    {"scene": 4, "time": "01:30 - 02:00", "category": "STEP 4 • 실증 기법", "title": "유효성 검증 3대 핵심 방법론", "color": (16, 185, 129)},
    {"scene": 5, "time": "02:00 - 02:30", "category": "STEP 5 • 실무 사례", "title": "현장 실무 사례 분석: 가열살균 & 금속검출", "color": (245, 158, 11)},
    {"scene": 6, "time": "02:30 - 03:00", "category": "STEP 6 • 유지관리 & 요약", "title": "재검증(Re-validation) 조건 & 심사 3대 체크리스트", "color": (236, 72, 153)}
]

def render_slides():
    print("Starting 1080p Frame Rendering via PIL...")
    generated = []
    for item in SCENES:
        img = Image.new("RGB", (1920, 1080), (15, 23, 42))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(60, 40), (1860, 130)], fill=(30, 41, 59), outline=(51, 65, 85), width=2)
        draw.rounded_rectangle([(90, 60), (320, 110)], radius=10, fill=item["color"])
        draw.rounded_rectangle([(140, 200), (1780, 880)], radius=24, fill=(24, 33, 47), outline=item["color"], width=3)
        draw.rounded_rectangle([(140, 920), (1780, 1030)], radius=16, fill=(11, 15, 25), outline=(51, 65, 85), width=1)
        filename = f"scene_{item['scene']:02d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath)
        generated.append(filepath)
        print(f"  [OK] Rendered {filename}")
    if generated:
        frames = [Image.open(f) for f in generated]
        gif_path = os.path.join(OUTPUT_DIR, "ccp_3min_preview.gif")
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=2500, loop=0)
        print(f"  [OK] Generated GIF: {gif_path}")

if __name__ == "__main__":
    render_slides()