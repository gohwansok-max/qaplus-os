# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 일일 쇼츠 자동 발행 오토파일럿 엔진
- knowledge/qa_topics_queue.json 에서 다음 대기 주제를 자동 로드 또는 사용자 지정 주제 수신
- 5개 씬 대본 및 20년 선배 한국어 음성(TTS) 자동 합성
- 1080x1920 세로형 초고화질 텍스트 오버레이 렌더링
- 당일 날짜 기반 MP4 영상 자동 빌드 및 큐 업데이트
- 텔레그램(Telegram) 연동 시 완성된 MP4를 톡방으로 자동 발송
"""

import os
import sys
import json
import argparse
import datetime
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
QUEUE_FILE = os.path.join(BASE_DIR, "knowledge", "qa_topics_queue.json")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

# 큐에 등록된 템플릿 DB
TOPIC_TEMPLATES = {
    1: {
        "title": "금속검출기(CCP) 테스트피스 모니터링 주기 및 한계기준",
        "scenes": [
            {
                "id": 1, "badge": "🚨 심사관 지적 1위", "badge_color": (239, 68, 68),
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
                "id": 2, "badge": "💡 한계기준 설정", "badge_color": (245, 158, 11),
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
                "id": 3, "badge": "⏱️ 검증 골든타임", "badge_color": (6, 182, 212),
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
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
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
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
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
    },
    2: {
        "title": "가열살균 공정(CCP-B) Cold Spot 중심온도 실측 및 시간 관리",
        "scenes": [
            {
                "id": 1, "badge": "🚨 심사관 지적 1위", "badge_color": (239, 68, 68),
                "title": "가열살균 심사 탈락?\nCold Spot 실측 누락!",
                "subtitle": "20년 선배가 알려주는 3분 합격 공식",
                "key_points": [
                    "표면 온도만 재면 미생물 생존 위험",
                    "가장 늦게 데워지는 최냉점(Cold Spot) 실측 필수"
                ],
                "senior_tip": "제품의 정중앙 또는 가장 두꺼운 부위 중심 온도를 잴 것!",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "HACCP 가열살균 공정에서 심사관이 가장 먼저 확인하는 게 뭔지 아시나요? 바로 최냉점, 콜드스팟 실측 데이터입니다. 표면 온도만 재면 심사에서 바로 탈락합니다."
            },
            {
                "id": 2, "badge": "💡 한계기준 설정", "badge_color": (245, 158, 11),
                "title": "중심온도 85℃ 1분\n가열 한계기준의 본질",
                "subtitle": "병원성 미생물 사멸의 과학적 근거",
                "key_points": [
                    "살모넬라, 병원성대장균 5-log 사멸 조건 충족",
                    "배합비/점도 변경 시 가열 침투 시험 재수행"
                ],
                "senior_tip": "온도계 센서 삽입 깊이를 지그(Jig)로 고정하여 편차 차단!",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "첫째, 한계기준 설정입니다. 중심온도 85도에서 1분 이상 가열하는 기준은 과학적인 사멸 시험 근거가 있어야 합니다. 점도가 바뀌면 열 침투 시간이 달라지니 꼭 재검증하세요."
            },
            {
                "id": 3, "badge": "⏱️ 검증 골든타임", "badge_color": (6, 182, 212),
                "title": "가열 솥 3위치 실측\n상부/중부/하부 편차 확인",
                "subtitle": "대용량 솥 열분포 불균일 방어",
                "key_points": [
                    "1. 가열 탱크 내 교반 속도 일정 유지",
                    "2. 솥 위치별(상/중/하) 온도 편차 2℃ 이내 검증",
                    "3. 로트별 가열 시작시간과 종료시간 기록"
                ],
                "senior_tip": "디지털 무선 데이터로거로 실시간 열분포 프로파일 확보!",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "둘째, 열분포 검증입니다. 가열 솥의 상부와 하부는 온도가 다릅니다. 상부, 중부, 하부 세 지점의 온도를 측정해서 편차가 없는지 반드시 확인해야 합니다."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "온도계 0점 보정(0℃/100℃)\n매월 사내 교정 필수",
                "subtitle": "심사 전날 급하게 하지 않는 계측기 관리",
                "key_points": [
                    "얼음물(0℃) 및 끓는물(100℃) 2점 보정 기록",
                    "온도계 센서 와이어 단선 및 꺾임 점검"
                ],
                "senior_tip": "연 1회 공인기관 검교정 성적서 원본 바인더 구비!",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 선배의 꿀팁입니다. 중심온도계는 매월 얼음물과 끓는물로 사내 영점 보정을 해야 합니다. 계측기 오차 1도 때문에 이탈 판정을 받을 수 있으니 꼭 체크하세요."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "가열 CCP 심사 3종 세트\n완벽 구비로 100% 합격!",
                "subtitle": "식품안전의 기본, 가열살균 완전정복",
                "key_points": [
                    "1. Cold Spot 열침투 유효성 평가 보고서",
                    "2. CCP 가열살균 일일 모니터링 일지",
                    "3. 중심온도계 검교정 필증 및 성적서"
                ],
                "senior_tip": "가열살균 양식과 서식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 준비하시면 가열살균 심사는 무조건 통과입니다. 관련 서식은 큐에이플러스 오픈채팅방에서 언제든 무료로 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    }
}

def generate_dynamic_scenes_for_custom_topic(topic_name):
    """임의의 사용자 지정 주제에 대해 자동으로 5개 고화질 씬을 동적 생성"""
    return [
        {
            "id": 1, "badge": "🚨 실무 긴급 진단", "badge_color": (239, 68, 68),
            "title": f"HACCP 핵심 점검!\n{topic_name[:18]}",
            "subtitle": "20년 선배가 알려주는 실무 가이드",
            "key_points": [
                f"{topic_name[:20]} 관련 법적 기준 준수",
                "심사관이 현장에서 불시 점검하는 핵심 포인트"
            ],
            "senior_tip": "현장 기록 일지와 실제 작업 프로세스의 일치성 확인!",
            "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
            "narration": f"오늘 다룰 핵심 주제는 바로 {topic_name}입니다. 식품 안전 심사 때 지적받지 않고 한 번에 통과하는 핵심 실무 팁을 정리해드립니다."
        },
        {
            "id": 2, "badge": "💡 핵심 기준 설정", "badge_color": (245, 158, 11),
            "title": f"과학적 근거 없는 기준은 감점!\n표준 관리선 확립",
            "subtitle": "식품공전 및 HACCP 고시 완벽 준수",
            "key_points": [
                "제품 특성 및 생산 공정에 맞는 한계기준 설정",
                "사내 표준작업지침서(SOP) 명문화 및 교육"
            ],
            "senior_tip": "작업자가 한눈에 볼 수 있도록 현장 부착물 비치!",
            "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
            "narration": "첫째, 기준 설정의 과학적 근거입니다. 남의 공장 양식을 그대로 베끼지 마시고, 자사 생산 라인에 맞는 실측 데이터 근거를 확보해 두셔야 합니다."
        },
        {
            "id": 3, "badge": "⏱️ 정기 모니터링", "badge_color": (6, 182, 212),
            "title": "빈틈없는 일상 점검\n골든타임 관리 원칙",
            "subtitle": "이탈 발생 시 확산 방지 모니터링",
            "key_points": [
                "1. 작업 시작 전 준비 상태 확인",
                "2. 연속 가동 중 주기적 정기 점검",
                "3. 교대 및 작업 마감 시 최종 확인"
            ],
            "senior_tip": "이상 발견 즉시 생산 라인 인터록 및 격리 조치!",
            "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
            "narration": "둘째, 주기적인 모니터링입니다. 작업 시작 전, 가동 중, 그리고 작업 종료 직후 3시점 점검 원칙을 지켜야 사고 시 폐기 범위를 최소화할 수 있습니다."
        },
        {
            "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
            "title": "현장 트러블슈팅\n실무자가 자주 놓치는 함정",
            "subtitle": "20년 현장 경험으로 검증된 노하우",
            "key_points": [
                "지정된 양식에 누락 없이 당일 실시간 기록",
                "개선조치(CAPA) 발생 시 원인 분석 보고서 작성"
            ],
            "senior_tip": "정기 사내 위생 점검으로 심사 전 사전 예방!",
            "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
            "narration": "셋째, 20년 선배의 실무 팁입니다. 일지는 몰아서 쓰지 마시고 작업 시점에 즉시 기록하셔야 합니다. 이상 발생 시 개선조치 기록을 남기는 것이 핵심입니다."
        },
        {
            "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
            "title": "완벽한 서류 구비\n심사 100% 합격 보장!",
            "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
            "key_points": [
                "1. 공정 관리 기준서 및 SOP 최신화",
                "2. 일일 점검 일지 및 개선조치 이력철",
                "3. 작업자 위생 교육 훈련 일지 구비"
            ],
            "senior_tip": "실무 질문과 무료 서식은 큐에이플러스 오픈채팅방으로!",
            "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
            "narration": "이것만 지키시면 심사는 무조건 통과입니다. 관련 서식과 실무 질문은 큐에이플러스 오픈채팅방에서 편하게 물어보세요. 후배님들의 칼퇴를 응원합니다!"
        }
    ]

def get_font(size, bold=True):
    font_names = [
        "C:\\Windows\\Fonts\\malgunbd.ttf" if bold else "C:\\Windows\\Fonts\\malgun.ttf",
        "C:\\Windows\\Fonts\\NanumGothicBold.ttf" if bold else "C:\\Windows\\Fonts\\NanumGothic.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
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
    
    if os.path.exists(scene_data["image"]):
        raw_bg = Image.open(scene_data["image"]).convert("RGBA")
        raw_bg = raw_bg.resize((width, height), Image.Resampling.LANCZOS)
        bg_img = raw_bg
    else:
        bg_img = Image.new("RGBA", (width, height), (15, 23, 42, 255))

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

    # Progress bar
    progress = frame_num_in_scene / max(1, total_scene_frames)
    draw.rectangle([(0, 0), (width, 12)], fill=(30, 41, 59))
    draw.rectangle([(0, 0), (int(width * progress), 12)], fill=(56, 189, 248))

    # Top Header
    font_badge = get_font(28, bold=True)
    font_tag = get_font(22, bold=True)
    font_title = get_font(52, bold=True)
    font_sub = get_font(26, bold=True)
    
    badge_text = scene_data["badge"]
    badge_w = draw.textlength(badge_text, font=font_badge) + 60
    badge_x = (width - badge_w) // 2 - 80
    badge_y = 110
    
    draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + 60)], radius=30, fill=scene_data["badge_color"])
    draw.text((badge_x + 30, badge_y + 12), badge_text, font=font_badge, fill=(255, 255, 255))
    
    brand_text = "큐에이플러스 (QA+)"
    brand_w = draw.textlength(brand_text, font=font_tag) + 40
    brand_x = badge_x + badge_w + 15
    draw.rounded_rectangle([(brand_x, badge_y + 6), (brand_x + brand_w, badge_y + 54)], radius=24, fill=(15, 23, 42, 240), outline=(255, 255, 255, 120), width=1)
    draw.text((brand_x + 20, badge_y + 16), brand_text, font=font_tag, fill=(226, 232, 240))

    # Title
    title_lines = scene_data["title"].split("\n")
    cur_y = 200
    for t_line in title_lines:
        t_w = draw.textlength(t_line, font=font_title)
        draw.text(((width - t_w) // 2, cur_y), t_line, font=font_title, fill=(255, 255, 255))
        cur_y += 68
        
    sub_w = draw.textlength(scene_data["subtitle"], font=font_sub)
    draw.text(((width - sub_w) // 2, cur_y + 10), scene_data["subtitle"], font=font_sub, fill=(56, 189, 248))

    # Center Glassmorphic Main Card
    card_x1, card_y1 = 60, 680
    card_x2, card_y2 = 1020, 1560
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=36, fill=(11, 19, 38, 245), outline=scene_data["badge_color"], width=3)
    
    draw.ellipse([(card_x1 + 40, card_y1 + 40), (card_x1 + 60, card_y1 + 60)], fill=scene_data["badge_color"])
    font_card_head = get_font(26, bold=True)
    draw.text((card_x1 + 75, card_y1 + 35), "실무 핵심 체크포인트", font=font_card_head, fill=scene_data["badge_color"])
    
    font_point = get_font(32, bold=True)
    pt_y = card_y1 + 105
    for pt in scene_data["key_points"]:
        draw.text((card_x1 + 40, pt_y), "[v]", font=font_point, fill=(34, 197, 94))
        draw.text((card_x1 + 95, pt_y), pt, font=font_point, fill=(248, 250, 252))
        pt_y += 90

    # High Contrast Senior Tip Box
    tip_y1 = pt_y + 35
    tip_y2 = tip_y1 + 195
    draw.rounded_rectangle([(card_x1 + 30, tip_y1), (card_x2 - 30, tip_y2)], radius=22, fill=(15, 23, 42, 255), outline=(245, 158, 11), width=3)
    draw.rounded_rectangle([(card_x1 + 30, tip_y1), (card_x1 + 44, tip_y2)], radius=6, fill=(245, 158, 11))
    
    font_tip_title = get_font(24, bold=True)
    font_tip_text = get_font(30, bold=True)
    
    draw.text((card_x1 + 65, tip_y1 + 25), "💡 20년 QA 선배의 조언", font=font_tip_title, fill=(251, 191, 36))
    draw.text((card_x1 + 65, tip_y1 + 75), scene_data["senior_tip"], font=font_tip_text, fill=(255, 255, 255))

    # Bottom Sticky Banner
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

async def generate_tts_for_scenes(scenes):
    import edge_tts
    voice = "ko-KR-InJoonNeural"
    audio_files = []
    print("[1/4] Generating Korean TTS Voiceover (ko-KR-InJoonNeural)...")
    for s in scenes:
        out_mp3 = os.path.join(AUDIO_DIR, f"auto_scene_{s['id']:02d}.mp3")
        communicate = edge_tts.Communicate(s["narration"], voice, rate="+5%", pitch="+0Hz")
        await communicate.save(out_mp3)
        audio_files.append(out_mp3)
        print(f"  [OK] Scene {s['id']} TTS generated: {out_mp3}")
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

def run_daily_autopilot(custom_topic=None):
    print("==================================================================")
    print("  🚀 [큐에이플러스 AI CEO OS] 쇼츠 영상 자동 렌더링 가동")
    print("==================================================================")
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    next_item = None
    scenes = None
    topic_name = ""

    if custom_topic:
        topic_name = custom_topic
        print(f"\n[사용자 지정 토픽 수신] {topic_name}")
        scenes = generate_dynamic_scenes_for_custom_topic(topic_name)
    else:
        # Load next pending topic from Queue
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            queue_data = json.load(f)
            
        for item in queue_data["topics"]:
            if item["status"] == "pending":
                next_item = item
                break
                
        if not next_item:
            print("[!] 모든 대기 토픽이 완료되었습니다. 큐를 리셋하여 1번부터 순환합니다.")
            next_item = queue_data["topics"][0]

        topic_id = next_item["id"]
        topic_name = next_item["topic"]
        print(f"\n[큐에서 선택된 오늘의 토픽] ID #{topic_id}: {topic_name}")
        
        template_data = TOPIC_TEMPLATES.get(topic_id)
        if template_data:
            scenes = template_data["scenes"]
        else:
            scenes = generate_dynamic_scenes_for_custom_topic(topic_name)

    # 1. TTS Voiceover
    audio_files = asyncio.run(generate_tts_for_scenes(scenes))
    
    # 2. Frames & Scene MP4 Encoding
    print("\n[2/4] Rendering 1080x1920 HD Frames & Encoding...")
    scene_videos = []
    
    for idx, s in enumerate(scenes):
        audio_file = audio_files[idx]
        duration = get_audio_duration(audio_file) + 0.6
        fps = 30
        total_frames = int(duration * fps)
        
        frame_img = render_scene_frame(s, 15, total_frames)
        frame_path = os.path.join(FRAMES_DIR, f"auto_scene_{s['id']:02d}_poster.png")
        frame_img.save(frame_path, quality=95)
        
        scene_mp4 = os.path.join(VIDEOS_DIR, f"auto_scene_{s['id']:02d}.mp4")
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
        print(f"  [OK] Scene {s['id']} MP4 ready: {scene_mp4}")
        
    # 3. Master Concat
    print("\n[3/4] Master Shorts MP4 Concatenation...")
    concat_list_path = os.path.join(VIDEOS_DIR, "auto_concat_list.txt")
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for v in scene_videos:
            f.write(f"file '{v.replace('\\', '/')}'\n")
            
    clean_topic_name = topic_name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace(":", "")[:30]
    out_filename = f"{today_str}_{clean_topic_name}_shorts.mp4"
    master_mp4 = os.path.join(VIDEOS_DIR, out_filename)
    
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        master_mp4
    ]
    subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"  🎉 [완성] 신규 쇼츠 MP4: {master_mp4}")
    
    # 4. Update Queue Status if it came from Queue
    if next_item:
        next_item["status"] = "completed"
        next_item["rendered_file"] = f"outputs/videos/{out_filename}"
        queue_data["last_run"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)
        print("  ✓ [큐 업데이트] 토픽 상태 완료 처리 완료.")
        
    # 5. Telegram Dispatch if configured
    try:
        from telegram_sender import send_video_to_telegram
        caption = f"🎬 <b>[큐에이플러스] 숏츠 영상 완성!</b>\n\n📌 <b>주제:</b> {topic_name}\n📁 <b>파일명:</b> {out_filename}\n\n💡 20년 선배 멘토링 쇼츠가 렌더링되었습니다. 다운로드하여 유튜브에 등록하세요!"
        send_video_to_telegram(master_mp4, caption)
    except Exception as e:
        print(f"  [텔레그램 연동 알림] 텔레그램 발송 모듈 스킵: {e}")
    
    print("\n==================================================================")
    print(f"  ✅ 숏츠 영상 제작이 성공적으로 완료되었습니다: {out_filename}")
    print("==================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="큐에이플러스 일일 쇼츠 오토파일럿")
    parser.add_argument("--topic", type=str, default=None, help="임의 지정 주제")
    args = parser.parse_args()
    
    run_daily_autopilot(custom_topic=args.topic)
