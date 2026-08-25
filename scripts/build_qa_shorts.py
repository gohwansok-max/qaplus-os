# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 9:16 Shorts 자동 생성 엔진
- 한국 파란색 일체형 방진복 B-Roll 이미지 활용
- 20년 선배 따뜻한 한국어 TTS (ko-KR-InJoonNeural) 음성 합성
- 1080x1920 초고화질 가독성 극대화 텍스트 렌더링
- FFmpeg 기반 최종 MP4 영상 자동 빌드
"""

import os
import sys
import json
import subprocess
import asyncio

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
VIDEOS_DIR = os.path.join(OUTPUTS_DIR, "videos")
AUDIO_DIR = os.path.join(OUTPUTS_DIR, "audio")
FRAMES_DIR = os.path.join(OUTPUTS_DIR, "frames")
ASSETS_DIR = os.path.join(BASE_DIR, "remotion", "public", "assets")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

SCENES = [
    {
        "id": 1,
        "badge": "🚨 심사관 지적 1위",
        "badge_color": (239, 68, 68),
        "title": "HACCP 심사 탈락 위기?\n금속검출기 검증 주기!",
        "subtitle": "20년 선배가 알려주는 3분 합격 공식",
        "key_points": [
            "검증 주기 누락 시 당일 생산 전량 보류/폐기",
            "심사관이 현장에서 가장 먼저 확인하는 필수 CCP"
        ],
        "senior_tip": "장비 고장 시 회수 범위를 줄이는 골든타임 관리!",
        "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
        "narration": "HACCP 정기 심사 때 금속검출기 일지 보면서 심사관이 가장 먼저 짚어내는 게 뭔지 아시나요? 바로 테스트피스 검증 주기입니다. 오늘 딱 3분 만에 무조건 패스하는 3대 핵심만 정리해드릴게요."
    },
    {
        "id": 2,
        "badge": "💡 한계기준 설정",
        "badge_color": (245, 158, 11),
        "title": "남의 기준 베끼면 부적합!\n제품 감도(Effect) 검증 필수",
        "subtitle": "Fe 1.5mm / Sus 2.0mm 설정의 과학적 근거",
        "key_points": [
            "수분·염분·품온에 따른 감도 영향 실측",
            "신제품/배합비 변경 시 유효성 평가서 구비"
        ],
        "senior_tip": "10회 연속 통과 테스트 데이터가 없으면 감점 대상!",
        "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
        "narration": "첫째, 한계기준 설정입니다. 남의 공장 기준 그대로 베껴 쓰시면 심사 때 유효성 평가에서 바로 지적받습니다. 수분과 염분에 따른 제품 감도 영향 테스트 근거를 반드시 남겨두셔야 합니다."
    },
    {
        "id": 3,
        "badge": "⏱️ 검증 골든타임",
        "badge_color": (6, 182, 212),
        "title": "무조건 지켜야 할\n'3시점 검증 원칙'",
        "subtitle": "사고 났을 때 덤터기 쓸 물량을 차단하는 법",
        "key_points": [
            "1. 작업 시작 전 : 10분 예열 후 정상 작동 확인",
            "2. 작업 중 (2~3시간) : 라인 가동 중 감도 유지",
            "3. 작업 종료 직후 : 당일 생산 로트 유효성 최종 보증"
        ],
        "senior_tip": "종료 후 검증을 빼먹으면 하루 종일 만든 물량 전량 재검사!",
        "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
        "narration": "둘째, 3시점 검증 원칙입니다. 작업 시작 전, 작업 중 2에서 3시간 간격, 그리고 작업 종료 직후에 검증합니다. 특히 종료 후 검증을 빼먹으면 당일 생산한 전 물량을 재검사해야 하니 꼭 챙기세요."
    },
    {
        "id": 4,
        "badge": "🔥 20년 선배 꿀팁",
        "badge_color": (139, 92, 246),
        "title": "가장자리로 넣으면 낭패!\n'헤드 정중앙' 통과 원칙",
        "subtitle": "현장 작업자가 가장 많이 실수하는 치명적 포인트",
        "key_points": [
            "검출기 정중앙이 자기장이 가장 약한 Cold Spot",
            "제품의 가장 두꺼운 중심부에 시편 올려서 통과"
        ],
        "senior_tip": "리젝트(Reject) 불합격품 보관함 시건장치 열쇠 확인!",
        "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
        "narration": "셋째, 20년 선배의 실무 팁입니다. 테스트피스를 통과시킬 때는 가장자리가 아니라 자기장이 가장 약한 헤드 정중앙으로 통과시키셔야 합니다. 그리고 불합격품 보관함 시건장치 열쇠도 꼭 확인하세요."
    },
    {
        "id": 5,
        "badge": "🏆 합격 체크리스트",
        "badge_color": (16, 185, 129),
        "title": "심사관이 감탄하는\n3대 필수 구비 서류",
        "subtitle": "이것만 준비하면 HACCP / FSSC22000 100% 통과!",
        "key_points": [
            "1. 금속검출기 한계기준 설정 및 유효성 평가서",
            "2. 일일 3시점 모니터링 일지 & 이탈 조치 기록",
            "3. 테스트피스 연 1회 검교정 성적서"
        ],
        "senior_tip": "궁금한 서식이나 질문은 큐에이플러스 오픈채팅방으로!",
        "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
        "narration": "이 세 가지만 지키면 금속검출 공정 심사는 무조건 통과입니다. 궁금한 서식이나 질문은 큐에이플러스 오픈채팅방으로 편하게 남겨주세요. 후배님들의 칼퇴를 응원합니다!"
    }
]

def get_font(size, bold=True):
    font_names = [
        "C:\\Windows\\Fonts\\malgunbd.ttf" if bold else "C:\\Windows\\Fonts\\malgun.ttf",
        "C:\\Windows\\Fonts\\NanumGothicBold.ttf" if bold else "C:\\Windows\\Fonts\\NanumGothic.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf"
    ]
    for fn in font_names:
        if os.path.exists(fn):
            try:
                return ImageFont.truetype(fn, size)
            except Exception:
                pass
    return ImageFont.load_default()

def render_scene_frame(scene_data, frame_num_in_scene=0, total_scene_frames=300):
    width, height = 1080, 1920
    
    # 1. Base B-Roll Image
    if os.path.exists(scene_data["image"]):
        raw_bg = Image.open(scene_data["image"]).convert("RGBA")
        raw_bg = raw_bg.resize((width, height), Image.Resampling.LANCZOS)
        bg_img = raw_bg
    else:
        bg_img = Image.new("RGBA", (width, height), (15, 23, 42, 255))

    # 2. Dark Vignette & Gradient Overlay (선명한 텍스트 대비 확보)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    
    for y in range(height):
        if y < 450:
            alpha = int(230 * (1 - y / 450) + 140 * (y / 450))
        elif y < 1100:
            alpha = int(140 * (1 - (y - 450) / 650) + 220 * ((y - 450) / 650))
        else:
            alpha = int(220 * (1 - (y - 1100) / 820) + 255 * ((y - 1100) / 820))
        draw_ov.line([(0, y), (width, y)], fill=(5, 9, 18, alpha))
        
    combined = Image.alpha_composite(bg_img, overlay)
    draw = ImageDraw.Draw(combined)

    # 3. Top Progress Bar
    progress = frame_num_in_scene / max(1, total_scene_frames)
    draw.rectangle([(0, 0), (width, 12)], fill=(30, 41, 59))
    draw.rectangle([(0, 0), (int(width * progress), 12)], fill=(56, 189, 248))

    # 4. Top Header: Badge & QA+ Tag
    font_badge = get_font(28, bold=True)
    font_tag = get_font(22, bold=True)
    font_title = get_font(52, bold=True)
    font_sub = get_font(26, bold=True)
    
    badge_text = scene_data["badge"]
    badge_w = draw.textlength(badge_text, font=font_badge) + 60
    badge_x = (width - badge_w) // 2 - 80
    badge_y = 110
    
    # Badge Pill with dark border
    draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + 60)], radius=30, fill=scene_data["badge_color"])
    draw.text((badge_x + 30, badge_y + 12), badge_text, font=font_badge, fill=(255, 255, 255))
    
    # Brand Pill
    brand_text = "큐에이플러스 (QA+)"
    brand_w = draw.textlength(brand_text, font=font_tag) + 40
    brand_x = badge_x + badge_w + 15
    draw.rounded_rectangle([(brand_x, badge_y + 6), (brand_x + brand_w, badge_y + 54)], radius=24, fill=(15, 23, 42, 240), outline=(255, 255, 255, 120), width=1)
    draw.text((brand_x + 20, badge_y + 16), brand_text, font=font_tag, fill=(226, 232, 240))

    # Title (Multi-line centered)
    title_lines = scene_data["title"].split("\n")
    cur_y = 200
    for t_line in title_lines:
        t_w = draw.textlength(t_line, font=font_title)
        draw.text(((width - t_w) // 2, cur_y), t_line, font=font_title, fill=(255, 255, 255))
        cur_y += 68
        
    # Subtitle
    sub_w = draw.textlength(scene_data["subtitle"], font=font_sub)
    draw.text(((width - sub_w) // 2, cur_y + 10), scene_data["subtitle"], font=font_sub, fill=(56, 189, 248))

    # 5. Center Glassmorphic Main Card
    card_x1, card_y1 = 60, 680
    card_x2, card_y2 = 1020, 1560
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=36, fill=(11, 19, 38, 245), outline=scene_data["badge_color"], width=3)
    
    # Card Header Indicator
    draw.ellipse([(card_x1 + 40, card_y1 + 40), (card_x1 + 60, card_y1 + 60)], fill=scene_data["badge_color"])
    font_card_head = get_font(26, bold=True)
    draw.text((card_x1 + 75, card_y1 + 35), "실무 핵심 체크포인트", font=font_card_head, fill=scene_data["badge_color"])
    
    # Key Points
    font_point = get_font(32, bold=True)
    pt_y = card_y1 + 105
    for pt in scene_data["key_points"]:
        draw.text((card_x1 + 40, pt_y), "[v]", font=font_point, fill=(34, 197, 94))
        draw.text((card_x1 + 95, pt_y), pt, font=font_point, fill=(248, 250, 252))
        pt_y += 90

    # 💡 [가독성 완벽 개선] 20년 선배 꿀팁 Callout Box: 어두운 배경 + 고대비 골드/화이트 텍스트
    tip_y1 = pt_y + 35
    tip_y2 = tip_y1 + 195
    
    # 짙은 딥네이비/블랙 배경 (fill) + 선명한 골드 테두리 (outline)
    draw.rounded_rectangle([(card_x1 + 30, tip_y1), (card_x2 - 30, tip_y2)], radius=22, fill=(15, 23, 42, 255), outline=(245, 158, 11), width=3)
    # 왼쪽 골드 강조 바
    draw.rounded_rectangle([(card_x1 + 30, tip_y1), (card_x1 + 44, tip_y2)], radius=6, fill=(245, 158, 11))
    
    font_tip_title = get_font(24, bold=True)
    font_tip_text = get_font(30, bold=True)
    
    # 선명한 골드 타이틀
    draw.text((card_x1 + 65, tip_y1 + 25), "💡 20년 QA 선배의 조언", font=font_tip_title, fill=(251, 191, 36))
    
    # 순백색(100% 화이트) 본문 텍스트로 가독성 극대화
    draw.text((card_x1 + 65, tip_y1 + 75), scene_data["senior_tip"], font=font_tip_text, fill=(255, 255, 255))

    # 6. Bottom Sticky Community Banner
    bot_y1, bot_y2 = 1660, 1820
    draw.rounded_rectangle([(60, bot_y1), (1020, bot_y2)], radius=28, fill=(15, 23, 42, 250), outline=(56, 189, 248, 200), width=2)
    
    font_bot_title = get_font(27, bold=True)
    font_bot_sub = get_font(21, bold=False)
    
    bot_t1 = "200명 참여 중! 큐에이플러스 오픈채팅방"
    bot_t2 = "매일 무료 인포그래픽 & 실무 Q&A 상시 답변 (100% 무료 나눔)"
    
    b1_w = draw.textlength(bot_t1, font=font_bot_title)
    b2_w = draw.textlength(bot_t2, font=font_bot_sub)
    
    draw.text(((width - b1_w) // 2, bot_y1 + 32), bot_t1, font=font_bot_title, fill=(56, 189, 248))
    draw.text(((width - b2_w) // 2, bot_y1 + 82), bot_t2, font=font_bot_sub, fill=(203, 213, 225))

    return combined.convert("RGB")

async def generate_all_tts():
    import edge_tts
    voice = "ko-KR-InJoonNeural"
    audio_files = []
    print("[1/4] Generating Korean TTS Voiceover (ko-KR-InJoonNeural)...")
    for s in SCENES:
        out_mp3 = os.path.join(AUDIO_DIR, f"scene_{s['id']:02d}.mp3")
        # Check if already generated to save time
        if not os.path.exists(out_mp3) or os.path.getsize(out_mp3) == 0:
            communicate = edge_tts.Communicate(s["narration"], voice, rate="+5%", pitch="+0Hz")
            await communicate.save(out_mp3)
        audio_files.append(out_mp3)
        print(f"  [OK] Scene {s['id']} TTS ready: {out_mp3}")
    return audio_files

def get_audio_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 10.0

def build_full_video():
    # 1. TTS Generation
    audio_files = asyncio.run(generate_all_tts())
    
    # 2. Frame Rendering & Scene Video Encoding
    print("\n[2/4] Rendering 1080x1920 HD High-Contrast Frames & Encoding Scene Videos...")
    scene_videos = []
    
    for idx, s in enumerate(SCENES):
        audio_file = audio_files[idx]
        duration = get_audio_duration(audio_file) + 0.6  # Add 0.6s buffer
        fps = 30
        total_frames = int(duration * fps)
        
        # Render high-contrast poster frame
        frame_img = render_scene_frame(s, 15, total_frames)
        frame_path = os.path.join(FRAMES_DIR, f"scene_{s['id']:02d}_poster.png")
        frame_img.save(frame_path, quality=95)
        
        # Encode scene video using ffmpeg with loop & audio
        scene_mp4 = os.path.join(VIDEOS_DIR, f"scene_{s['id']:02d}.mp4")
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", frame_path,
            "-i", audio_file,
            "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-shortest",
            "-t", str(duration),
            scene_mp4
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        scene_videos.append(scene_mp4)
        print(f"  [OK] Scene {s['id']} MP4 encoded ({duration:.1f}s): {scene_mp4}")
        
    # 3. Concat all scene videos into Master Shorts MP4
    print("\n[3/4] Concatenating all scenes into Master YouTube Shorts MP4...")
    concat_list_path = os.path.join(VIDEOS_DIR, "concat_list.txt")
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for v in scene_videos:
            f.write(f"file '{v.replace('\\', '/')}'\n")
            
    master_mp4 = os.path.join(VIDEOS_DIR, "qa_metal_detector_shorts.mp4")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        master_mp4
    ]
    subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"  [SUCCESS] Master MP4 Video Generated: {master_mp4}")
    
    # 4. Generate Interactive Web Player
    print("\n[4/4] Updating Interactive HTML Web Player...")
    generate_html_player(master_mp4)
    print("  [SUCCESS] Done! All production assets ready.")

def generate_html_player(video_path):
    html_path = os.path.join(OUTPUTS_DIR, "qa_shorts_player.html")
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>큐에이플러스(QA+) - 금속검출기 검증 실무 쇼츠 영상</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url("https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800;900&display=swap");
    body {{ font-family: 'Pretendard', sans-serif; background-color: #070b14; color: #f8fafc; }}
  </style>
</head>
<body class="min-h-screen flex flex-col items-center p-4 md:p-8">

  <header class="w-full max-w-4xl flex items-center justify-between bg-slate-900/90 border border-slate-800 p-5 rounded-2xl mb-8 backdrop-blur shadow-2xl">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white text-2xl shadow-lg shadow-sky-500/30">
        <i class="fa-solid fa-shield-halved"></i>
      </div>
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-extrabold bg-sky-500/20 text-sky-400 border border-sky-500/30">큐에이플러스 (QA+)</span>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">20년 선배 멘토링</span>
        </div>
        <h1 class="text-xl font-black text-white mt-0.5">HACCP 금속검출기 검증 실무 완벽 가이드 (9:16 Shorts)</h1>
      </div>
    </div>

    <a href="videos/qa_metal_detector_shorts.mp4" download class="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold rounded-xl shadow-lg shadow-sky-500/30 transition active:scale-95">
      <i class="fa-solid fa-download"></i>
      <span>MP4 다운로드</span>
    </a>
  </header>

  <main class="w-full max-w-4xl grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
    <div class="md:col-span-6 flex justify-center">
      <div class="w-[360px] h-[640px] rounded-[32px] overflow-hidden border-4 border-slate-700 bg-black shadow-2xl relative group">
        <video id="qaVideo" src="videos/qa_metal_detector_shorts.mp4" controls autoplay loop class="w-full h-full object-cover"></video>
      </div>
    </div>

    <div class="md:col-span-6 flex flex-col gap-4">
      <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 class="text-lg font-black text-sky-400 mb-3 flex items-center gap-2">
          <i class="fa-solid fa-layer-group"></i>
          <span>영상 구성 5개 씬 (총 59초)</span>
        </h2>
        <div class="flex flex-col gap-3 text-sm">
          <div class="p-3 rounded-xl bg-slate-800/60 border border-red-500/30 flex items-start gap-3">
            <span class="px-2 py-0.5 rounded bg-red-500 text-white font-bold text-xs">Scene 1</span>
            <div>
              <p class="font-bold text-white">🚨 심사관 지적 1위 : 금속검출기 검증 주기</p>
              <p class="text-xs text-slate-400">한국 식품공장 파란 방진복 B-Roll & 후킹</p>
            </div>
          </div>
          <div class="p-3 rounded-xl bg-slate-800/60 border border-amber-500/30 flex items-start gap-3">
            <span class="px-2 py-0.5 rounded bg-amber-500 text-white font-bold text-xs">Scene 2</span>
            <div>
              <p class="font-bold text-white">💡 한계기준 설정 : Fe 1.5 / Sus 2.0 과학적 근거</p>
              <p class="text-xs text-slate-400">시편 봉 캘리브레이션 실측 장면</p>
            </div>
          </div>
          <div class="p-3 rounded-xl bg-slate-800/60 border border-cyan-500/30 flex items-start gap-3">
            <span class="px-2 py-0.5 rounded bg-cyan-500 text-white font-bold text-xs">Scene 3</span>
            <div>
              <p class="font-bold text-white">⏱️ 3시점 검증 원칙 : 시작/중간/종료</p>
              <p class="text-xs text-slate-400">스마트 HACCP 중앙 관제 모니터링</p>
            </div>
          </div>
          <div class="p-3 rounded-xl bg-slate-800/60 border border-purple-500/30 flex items-start gap-3">
            <span class="px-2 py-0.5 rounded bg-purple-500 text-white font-bold text-xs">Scene 4</span>
            <div>
              <p class="font-bold text-white">🔥 20년 선배 꿀팁 : 헤드 정중앙 통과 원칙</p>
              <p class="text-xs text-slate-400">Cold Spot 방어 및 리젝트 시건장치 확인</p>
            </div>
          </div>
          <div class="p-3 rounded-xl bg-slate-800/60 border border-emerald-500/30 flex items-start gap-3">
            <span class="px-2 py-0.5 rounded bg-emerald-500 text-white font-bold text-xs">Scene 5</span>
            <div>
              <p class="font-bold text-white">🏆 합격 체크리스트 : 필수 구비 서류 3종</p>
              <p class="text-xs text-slate-400">HACCP 심사관 태블릿 점검 & 오픈채팅방 안내</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    build_full_video()
