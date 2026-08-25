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
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass
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

def fetch_latest_web_context(topic_name):
    """실시간 웹 검색(DuckDuckGo)을 통해 식약처/식품안전나라/업계 최신 기준 및 사례 수집"""
    try:
        from ddgs import DDGS
        search_query = f"식품의약품안전처 {topic_name} HACCP 실무 기준"
        results = list(DDGS().text(search_query, max_results=3))
        if not results:
            results = list(DDGS().text(f"{topic_name} 식품공전", max_results=2))
        
        snippets = []
        for r in results:
            t = r.get("title", "")
            b = r.get("body", "")
            if t and b:
                snippets.append(f"• [{t}] {b[:120]}")
        
        if snippets:
            summary = "\n".join(snippets)
            print(f"  🌐 [실시간 웹 검색] '{topic_name}' 관련 최신 업계 자료 {len(snippets)}건 반영 완료!")
            return summary
    except Exception as e:
        print(f"  [웹 검색 스킵]: {e}")
    return ""

def generate_ai_script_via_llm(topic_name, web_context=""):
    """OpenAI 또는 Anthropic API를 호출하여 최신 웹 검색 데이터를 반영한 100% 독창적 5개 씬 대본 생성"""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    context_str = f"\n\n[실시간 웹 검색 최신 자료]:\n{web_context}" if web_context else ""
    
    system_prompt = (
        "당신은 20년 경력 대한민국 최고의 식품 품질관리 전문가이자 '큐에이플러스(QA+)'의 멘토 선배입니다.\n"
        "식품위생법, 식품공전, HACCP 고시, FSSC22000 기준과 실시간 최신 웹 자료에 기반하여 실무자 후배를 위한 5개 씬 쇼츠 대본을 작성하세요.\n"
        "규칙:\n"
        "1. 서론/인사말 금지 (Zero-Filler). 첫 문장부터 강렬한 현장 훅(Hook)으로 시작.\n"
        "2. 20년 현장의 구체적 수치, 실패 사례, 계측기 팁, 법령 근거를 명시할 것.\n"
        "3. 전문 용어 언급 후 자연스럽게 '쉽게 말하면...' 실무 해설을 덧붙일 것.\n"
        "4. 오프닝 멘트나 씬 구조가 다른 영상과 뻔하게 겹치지 않도록 신선하고 다채로운 화법을 사용할 것.\n"
        "5. 반드시 아래 JSON 형식으로만 응답할 것:\n"
        "{\n"
        '  "scenes": [\n'
        '    {"id": 1, "badge": "🚨 심사관 불시점검", "badge_color": [239, 68, 68], "title": "첫줄제목\\n둘째줄제목", "subtitle": "핵심소제목", "key_points": ["포인트1", "포인트2"], "senior_tip": "20년 선배 팁", "narration": "15초 분량 나레이션"},\n'
        '    {"id": 2, "badge": "💡 기준선 검증", "badge_color": [245, 158, 11], "title": "첫줄제목\\n둘째줄제목", "subtitle": "핵심소제목", "key_points": ["포인트1", "포인트2"], "senior_tip": "20년 선배 팁", "narration": "15초 분량 나레이션"},\n'
        '    {"id": 3, "badge": "⏱️ 골든타임 관리", "badge_color": [6, 182, 212], "title": "첫줄제목\\n둘째줄제목", "subtitle": "핵심소제목", "key_points": ["포인트1", "포인트2"], "senior_tip": "20년 선배 팁", "narration": "15초 분량 나레이션"},\n'
        '    {"id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": [139, 92, 246], "title": "첫줄제목\\n둘째줄제목", "subtitle": "핵심소제목", "key_points": ["포인트1", "포인트2"], "senior_tip": "20년 선배 팁", "narration": "15초 분량 나레이션"},\n'
        '    {"id": 5, "badge": "🏆 합격 체크리스트", "badge_color": [16, 185, 129], "title": "첫줄제목\\n둘째줄제목", "subtitle": "핵심소제목", "key_points": ["포인트1", "포인트2"], "senior_tip": "큐에이플러스 오픈채팅방 무료 서식", "narration": "15초 분량 마무리 나레이션"}\n'
        "  ]\n"
        "}"
    )

    import requests, json

    # 1. Anthropic Claude 호출 시도
    if anthropic_key and "your_" not in anthropic_key:
        try:
            headers = {
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 1500,
                "temperature": 0.8,
                "messages": [{"role": "user", "content": f"{system_prompt}{context_str}\n\n주제: {topic_name}"}]
            }
            res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                raw_text = res.json()["content"][0]["text"]
                start = raw_text.find("{")
                end = raw_text.rfind("}") + 1
                data = json.loads(raw_text[start:end])
                if "scenes" in data and len(data["scenes"]) == 5:
                    print("  [AI 엔진] Claude 3.5 Haiku 실시간 웹 검색 기반 독창 대본 생성 성공!")
                    return data["scenes"]
        except Exception as e:
            print(f"  [Anthropic API 패스]: {e}")

    # 2. OpenAI GPT-4o-mini 호출 시도
    if openai_key and "your_" not in openai_key:
        try:
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "temperature": 0.8,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt + context_str},
                    {"role": "user", "content": f"주제: {topic_name}"}
                ]
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                raw_text = res.json()["choices"][0]["message"]["content"]
                data = json.loads(raw_text)
                if "scenes" in data and len(data["scenes"]) == 5:
                    print("  [AI 엔진] GPT-4o-mini 실시간 웹 검색 기반 독창 대본 생성 성공!")
                    return data["scenes"]
        except Exception as e:
            print(f"  [OpenAI API 패스]: {e}")

    return None

def generate_dynamic_scenes_for_custom_topic(topic_name):
    """공식 출처·안전 검증을 거친 다변화 대본을 생성한다."""
    from qa_story_engine import build_verified_story

    scenes, metadata = build_verified_story(topic_name)
    t_lower = topic_name.lower()
    image_name = "broll_metal_line.jpg"
    if any(k in t_lower for k in ["가열", "살균", "레토르트", "f0", "중심온도"]):
        image_name = "broll_retort.jpg"
    elif any(k in t_lower for k in ["냉각", "냉동", "동결", "품온"]):
        image_name = "broll_cooling.jpg"
    elif any(k in t_lower for k in ["알레르기", "세척", "잔류세제", "atp"]):
        image_name = "broll_allergen.jpg"
    elif any(k in t_lower for k in ["소비기한", "유통기한", "가속", "실험", "미생물"]):
        image_name = "broll_lab.jpg"
    elif any(k in t_lower for k in ["스마트", "센서", "iot", "자동화"]):
        image_name = "broll_smart_haccp.jpg"
    image_path = os.path.join(ASSETS_DIR, image_name)
    for scene in scenes:
        scene["image"] = image_path
    print(f"  [스토리 엔진] 앵글={metadata['story_angle']} | 모드={metadata['generation_mode']} | 공식 출처={metadata['source_count']}건")
    return scenes

    # 이전 로컬 대체 엔진 (호환성을 위해 보존, 위 검증형 엔진에서 반환됨)
    web_info = fetch_latest_web_context(topic_name)
    ai_scenes = generate_ai_script_via_llm(topic_name, web_context=web_info)
    if ai_scenes:
        t_lower = topic_name.lower()
        img = os.path.join(ASSETS_DIR, "broll_metal_line.jpg")
        if any(k in t_lower for k in ["가열", "살균", "레토르트", "f0", "중심온도"]):
            img = os.path.join(ASSETS_DIR, "broll_retort.jpg")
        elif any(k in t_lower for k in ["냉각", "냉동", "동결", "품온"]):
            img = os.path.join(ASSETS_DIR, "broll_cooling.jpg")
        elif any(k in t_lower for k in ["알레르기", "세척", "잔류세제", "atp"]):
            img = os.path.join(ASSETS_DIR, "broll_allergen.jpg")
        elif any(k in t_lower for k in ["소비기한", "유통기한", "가속", "실험", "미생물"]):
            img = os.path.join(ASSETS_DIR, "broll_lab.jpg")
        elif any(k in t_lower for k in ["스마트", "센서", "iot", "자동화"]):
            img = os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg")
        
        for s in ai_scenes:
            if "image" not in s or not os.path.exists(s.get("image", "")):
                s["image"] = img
            if isinstance(s.get("badge_color"), list):
                s["badge_color"] = tuple(s["badge_color"])
        return ai_scenes


    # 2. 다변화 로컬 시나리오 엔진 (주제별 고유 스토리텔링 & 앵글 적용)
    import hashlib
    h_val = int(hashlib.md5(topic_name.encode("utf-8")).hexdigest()[:4], 16)
    angle_type = h_val % 4  # 0: 현장 사고 트러블슈팅, 1: 심사관 불시점검, 2: 신입 치명적 실수, 3: 골든타임 인터록
    t_lower = topic_name.lower()

    # 카테고리별 특화 데이터 정의
    if any(k in t_lower for k in ["스마트", "센서", "iot", "자동화", "통신", "위변조", "디지털", "plc", "scada"]):
        img_main = os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg")
        if angle_type == 0:
            return [
                {"id": 1, "badge": "🚨 현장 돌발 사고", "badge_color": (239, 68, 68), "title": f"모터 노이즈로 센서 튐?\n{topic_name[:15]}", "subtitle": "생산 라인 불시 정지 사고 원인 해결", "key_points": ["대형 인버터 전력선과 센서 배선 간섭", "0.5초 통신 지연 시 즉시 인터록 오작동"], "senior_tip": "센서 신호선은 반드시 쉴드 케이블 단독 배관!", "image": img_main, "narration": f"공장에서 갑자기 스마트 해썹 경보 울리면서 라인이 멈춘 적 있으시죠? 20년 현장 경험상 90%는 센서 고장이 아니라 옆에 있는 인버터 모터 전력선 노이즈 때문입니다. 원천 차단법 알려드릴게요."},
                {"id": 2, "badge": "💡 0점 보정 기준", "badge_color": (245, 158, 11), "title": "온도 편차 ±0.5℃ 이내!\nRTD 3선식 정밀 세팅", "subtitle": "식품공전 및 스마트HACCP 표준 규격", "key_points": ["공인 검교정 성적서와 사내 2점 보정", "중앙 PLC 서버와 현장 모니터 수치 일치"], "senior_tip": "단자함 습기 방지를 위한 방수 실링 필수!", "image": img_main, "narration": "첫째, 센서 자체의 정밀도입니다. 저가형 센서를 쓰면 6개월 만에 오차가 1도 이상 벌어집니다. 반드시 RTD PT100 3선식을 쓰시고 월 1회 사내 0점 보정을 일지에 기록해 두셔야 합니다."},
                {"id": 3, "badge": "⏱️ 데이터 무결성", "badge_color": (6, 182, 212), "title": "1초 단위 실시간 암호화\n위·변조 방지 Audit Trail", "subtitle": "심사관이 집중 검증하는 위변조 차단", "key_points": ["1. 작업자 임의 수정 불가능한 해시 체인", "2. 통신 단절 시 로컬 버퍼링 후 자동 복구", "3. 이상 발생 시 관리자 스마트폰 실시간 알람"], "senior_tip": "통신 끊김 시 수동 기록 전환 매뉴얼 비치!", "image": img_main, "narration": "둘째, 위변조 방지 기록입니다. 심사관들이 가장 먼저 확인하는 게 '데이터 수동 수정 권한'입니다. 작업자가 임의로 숫자를 고칠 수 없도록 감사 추적 기능이 잠겨 있어야 패스됩니다."},
                {"id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246), "title": "단자함 방습 패킹 점검!\n고온 다습 세척수 침투 방지", "subtitle": "야간 고압 물청소 시 센서 쇼트 방지 노하우", "key_points": ["세척 작업 시 센서 헤드 방수 커버 체결", "접지 저항 100옴 이하 단독 3종 접지 시공"], "senior_tip": "연 1회 케이블 피복 마모 및 경화 상태 전수 조사!", "image": img_main, "narration": "셋째, 선배의 현장 팁입니다. 야간에 고압 온수로 청소하다가 센서 헤드로 물이 스며들어 아침 첫 가동 때 쇼트 나는 공장이 정말 많습니다. IP67 이상 방수 헤드를 쓰시고 실리콘 패킹을 꼭 챙기세요."},
                {"id": 5, "badge": "🏆 심사 100% 합격", "badge_color": (16, 185, 129), "title": "스마트HACCP 통과 3종\n완벽 구비로 심사 끝!", "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다", "key_points": ["1. 센서 검교정 성적서 및 사내 교정 일지", "2. 데이터 위변조 방지 증빙 보고서", "3. 비상 시 라인 인터록 작동 시험 성적서"], "senior_tip": "스마트HACCP 구축 서식은 큐에이플러스 오픈채팅방 무료 공유!", "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"), "narration": "이 세 가지만 구비해 두시면 스마트 해썹 심사는 불시 점검이 와도 10분 만에 끝납니다. 관련 서식은 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"}
            ]
        else:
            return [
                {"id": 1, "badge": "🔍 심사관의 시선", "badge_color": (59, 130, 246), "title": f"스마트HACCP 불시 점검!\n{topic_name[:15]}", "subtitle": "심사관이 불시에 서버 로그를 열었을 때", "key_points": ["중앙 서버 데이터와 현장 생산일지 대조", "한계기준 이탈 시 라인 정지 이력 확인"], "senior_tip": "수기 일지와 전산 데이터의 시간 일치 필수!", "image": img_main, "narration": f"식품안전관리인증원 심사관이 공장에 오자마자 스마트 해썹 모니터 화면부터 띄우라고 하는 이유가 뭔지 아시나요? 서류에 적힌 온도와 서버에 기록된 1초 단위 실시간 온도가 맞는지 보려는 겁니다. 오늘 완벽 방어법을 공개합니다."},
                {"id": 2, "badge": "💡 자동 인터록 기준", "badge_color": (245, 158, 11), "title": "한계기준 이탈 즉시!\n컨베이어 모터 물리적 차단", "subtitle": "작업자 수동 개입 없는 자동화 시스템", "key_points": ["온도 미달 시 투입구 자동 셔터 하강", "경광등 및 관리자 SMS 동시 발송"], "senior_tip": "월 1회 비상 정지 인터록 모의 훈련 실시!", "image": img_main, "narration": "첫째, 자동 인터록입니다. 온도가 떨어졌는데 작업자가 버튼을 눌러야 멈추는 시스템은 스마트 해썹으로 인정받지 못합니다. PLC 제어를 통해 0.1초 만에 물리적으로 멈춰야 합니다."},
                {"id": 3, "badge": "⏱️ 통신 장애 대책", "badge_color": (6, 182, 212), "title": "인터넷 끊겨도 안전!\n로컬 72시간 백업 메모리", "subtitle": "네트워크 장애 시 데이터 유실 방지", "key_points": ["1. 게이트웨이 내부 SD카드 1차 저장", "2. 네트워크 복구 즉시 시계열 자동 동기화", "3. 정전 시 UPS 무정전 전원 공급 장치 30분"], "senior_tip": "통신 두절 알람 발생 시 수기 점검표 즉시 전환!", "image": img_main, "narration": "둘째, 통신 장애 대책입니다. 인터넷이 끊겼다고 데이터가 비어버리면 심사 때 즉시 시정명령을 받습니다. 컨트롤러 내부에 최소 72시간 로컬 버퍼 메모리를 반드시 장착해 두셔야 합니다."},
                {"id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246), "title": "심사관 질문 대응 요령!\n'로그 이력철' 1초 제출", "subtitle": "말보다 데이터 한 장으로 심사 끝내기", "key_points": ["월간 데이터 무결성 요약 레포트 사전 바인딩", "계측기 캘리브레이션 필증 전면 부착"], "senior_tip": "복잡하게 설명하지 말고 Audit Trail 출력물 제시!", "image": img_main, "narration": "셋째, 선배의 심사 팁입니다. 심사관이 '센서 이상할 땐 어떻게 조치했나요?'라고 물으면 말로 설명하지 마시고, 스마트 해썹 이탈 조치 로그 리포트를 딱 보여주세요. 심사가 5분 만에 끝납니다."},
                {"id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129), "title": "스마트HACCP 관리 기준서\n완벽 구비로 심사 합격!", "subtitle": "큐에이플러스가 후배님들을 지원합니다", "key_points": ["1. 스마트HACCP 표준 운영 지침서(SOP)", "2. 비상 대응 및 수동 전환 절차서", "3. 유지보수 및 정기 검교정 계약서"], "senior_tip": "스마트HACCP 양식은 큐에이플러스 오픈채팅방에서 무료 다운!", "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"), "narration": "스마트 해썹 도입하고 스트레스 받지 마세요. 이 3대 매뉴얼만 갖춰두면 현장이 편해집니다. 관련 서식은 오픈채팅방에서 무료로 받아가세요. 후배님들의 빠른 칼퇴를 응원합니다!"}
            ]

    # 가열 / 살균 / 레토르트 / F0값 / 중심온도
    elif any(k in t_lower for k in ["가열", "살균", "레토르트", "f0", "중심온도", "탕수육", "육가공", "열처리", "오토클레이브"]):
        img_main = os.path.join(ASSETS_DIR, "broll_retort.jpg")
        return [
            {"id": 1, "badge": "🔥 긴급 트러블슈팅", "badge_color": (239, 68, 68), "title": f"레토르트 살균 F0값?\n{topic_name[:15]}", "subtitle": "보툴리누스균 완벽 사멸 계산 공식", "key_points": ["Cold Spot 중심온도 실측과 F0 적분 계산", "F0값 4.0 미달 시 전량 재살균 또는 폐기"], "senior_tip": "제품 충진량과 초기 품온이 F0에 미치는 영향 계산 필수!", "image": img_main, "narration": f"레토르트 솥에서 살균 시간 다 채웠는데 F0값이 4.0이 안 나와서 당황한 적 있으시죠? 20년 현장 실무 선배가 살균 솥 안에서 가장 온도가 늦게 올라가는 콜드스팟 잡는 법과 계산 비법을 딱 정리해드립니다."},
            {"id": 2, "badge": "💡 과학적 F0 기준", "badge_color": (245, 158, 11), "title": "F0 ≥ 4.0 완전 사멸!\n121.1℃ 기준 등가시간 환산", "subtitle": "식품공전 레토르트 살균 규격 준수", "key_points": ["Z값 10℃ 기준 온도 적분 방정식(General Method)", "무선 데이터 로거(Data Logger) 12포인트 열분포도"], "senior_tip": "제품 두께 5mm 증가 시 살균 시간 20% 연장!", "image": img_main, "narration": "첫째, F0값의 과학적 근거입니다. 레토르트는 단순히 121도 몇 분 쪘다고 통과되는 게 아닙니다. 제품 중심부에서 121.1도 기준으로 균을 죽인 유효 살균 시간이 4분 이상 누적되어야 합격입니다."},
            {"id": 3, "badge": "⏱️ 압력 & 냉각 제어", "badge_color": (6, 182, 212), "title": "배압(Air Back Pressure) 관리\n파우치 터짐 방지 1.8 bar", "subtitle": "가열 후 급랭 시 포장지 파손 방지", "key_points": ["1. 승온기: 증기 주입 및 챔버 공기 완전 배제(Venting)", "2. 살균기: 설정 온도 ±0.5℃ 정밀 유지", "3. 냉각기: 압축공기 주입으로 파우치 팽창 파손 방지"], "senior_tip": "살균수 잔류염소 농도 0.5ppm 유지로 2차 오염 차단!", "image": img_main, "narration": "둘째, 살균 압력과 냉각입니다. 온도가 올라갈 때 파우치 내부 압력이 팽창하는데, 솥의 배압을 1.8바 이상 맞춰주지 않으면 파우치가 터지거나 실링이 벌어져 미세 누출 사고가 납니다."},
            {"id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246), "title": "살균 솥 트레이 적재 간격!\n중앙부 열전달 지연 해결", "subtitle": "트레이 층간 간격 3cm 확보로 콜드스팟 해소", "key_points": ["파우치를 겹쳐서 적재하면 F0값 50% 급감", "트레이별 열침투 속도 편차 사전 측정"], "senior_tip": "월 1회 살균 솥 스팀 밸브 누설 및 트랩 점검!", "image": img_main, "narration": "셋째, 선배의 꿀팁입니다. 생산량 늘린다고 트레이에 파우치를 겹쳐서 넣으면 가운데 제품은 열이 안 들어가서 F0값이 반토막 납니다. 반드시 전용 스페이서를 끼워 스팀 순환로를 열어주세요."},
            {"id": 5, "badge": "🏆 심사 합격 보장", "badge_color": (16, 185, 129), "title": "열침투 유효성 보고서\n심사 지적 0건 완성!", "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다", "key_points": ["1. 계절별(동절기/하절기) 열침투 유효성 평가서", "2. 배치별 F0 계산 차트 및 살균 일지", "3. 압력계 및 온도계 KOLAS 검교정 필증"], "senior_tip": "레토르트 F0 계산 엑셀 시트는 큐에이플러스 방에서 무료 다운!", "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"), "narration": "이것만 준비해 두시면 식약처 정기 점검이나 인증원 심사관도 완벽하다고 칭찬합니다. F0 자동 계산 엑셀 양식은 큐에이플러스 오픈채팅방에서 무료로 받아가세요. 후배님들의 칼퇴를 응원합니다!"}
        ]

    # 알레르기 / 교차오염 / 세척 / ATP
    elif any(k in t_lower for k in ["알레르기", "알레르겐", "교차오염", "세척", "잔류세제", "atp", "cip", "소독"]):
        img_main = os.path.join(ASSETS_DIR, "broll_allergen.jpg")
        return [
            {"id": 1, "badge": "⚠️ 교차오염 비상", "badge_color": (236, 72, 153), "title": f"알레르기 미량 혼입 방지!\n{topic_name[:15]}", "subtitle": "식약처 회수 명령 1순위 항목 완벽 방어", "key_points": ["알레르기 22종 표시 기준 및 비의도적 혼입 방지", "배치 전환 시 세척 검증 누락 시 회수 리스크"], "senior_tip": "비알레르기 제품을 월요일 오전에 최우선 생산!", "image": img_main, "narration": f"알레르기 유발물질은 공장에서 0.1밀리그램만 다른 제품에 섞여도 식약처 긴급 회수 명령이 떨어집니다. 20년 동안 교차오염 사고 한 번도 안 낸 전용 라인 세척 검증법을 공개합니다."},
            {"id": 2, "badge": "💡 컬러 코딩 관리", "badge_color": (245, 158, 11), "title": "작업 도구 색상별 구분!\n청소 도구 혼용 원천 차단", "subtitle": "화학적 위해요소 관리 표준작업지침(SOP)", "key_points": ["알레르겐 원료 전용 용기 및 파렛트(Red Color)", "세척용 브러시/호스/배관 전용화 및 표기"], "senior_tip": "칭량실 분진 비산 방지 국소 배기장치 가동 필수!", "image": img_main, "narration": "첫째, 컬러 코딩입니다. 알레르기 원료를 펐던 바가지나 청소 브러시로 일반 제품 라인을 닦으면 바로 오염됩니다. 빨간색, 파란색으로 도구를 완전히 나누고 구역을 격리하세요."},
            {"id": 3, "badge": "⏱️ 과학적 세척 검증", "badge_color": (6, 182, 212), "title": "ATP 100 RLU 이하 확인\n알레르겐 신속 키트 판정", "subtitle": "눈으로 보지 말고 데이터로 세척 완료 증명", "key_points": ["1. 70℃ 온수 린스 및 알칼리 세정제 CIP", "2. 컨베이어 벨트 뒷면 및 배관 이음새 스왑", "3. 특이 항체 래피드 키트(Lateral Flow) 음성 판정"], "senior_tip": "세척수 잔류세제 페놀프탈레인 무색(중성) 확인!", "image": img_main, "narration": "둘째, 2단계 세척 검증입니다. 세척 끝났다고 바로 다음 원료 넣지 마시고, 컨베이어 틈새를 ATP 측정기로 찍어서 100 이하인지, 신속 키트에서 음성이 뜨는지 확인 후 결재를 올리세요."},
            {"id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246), "title": "생산 스케줄 순서 배치!\n비알레르기 → 알레르기 제품", "subtitle": "세척 횟수를 절반으로 줄이는 스마트 스케줄링", "key_points": ["밀, 대두, 알류 미함유 제품을 첫 타임 배치", "알레르기 함유 제품은 당일 마지막에 생산 후 심야 세척"], "senior_tip": "원료 포장지 개봉 시 가루 날림 방지 전용 룸 사용!", "image": img_main, "narration": "셋째, 선배의 생산 노하우입니다. 생산 계획 짤 때 알레르기 없는 제품을 오전에 먼저 돌리고, 알레르기 제품을 마지막에 돌리면 중간 세척 시간을 2시간 이상 아끼고 퇴근도 빨라집니다."},
            {"id": 5, "badge": "🏆 심사 완벽 통과", "badge_color": (16, 185, 129), "title": "세척 유효성 평가서 구비\n심사관 지적 0건 달성!", "subtitle": "큐에이플러스가 후배님들을 응원합니다", "key_points": ["1. 품목 전환 라인별 세척 유효성 성적서", "2. 알레르겐 스왑 검사 일지 및 키트 사진 대조철", "3. 포장지 알레르기 유발물질 표시사항 체크리스트"], "senior_tip": "알레르기 세척 점검표는 큐에이플러스 방에서 무료 다운!", "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"), "narration": "이것만 챙기시면 식약처 표시기준 점검이나 불시 위생 점검은 100% 무사 통과입니다. 관련 서식은 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"}
        ]

    # 기본 범용 품질/HACCP 특화 매칭 (다변화 앵글 적용)
    else:
        img_main = os.path.join(ASSETS_DIR, "broll_audit.jpg")
        return [
            {"id": 1, "badge": "🚨 20년 선배 직강", "badge_color": (239, 68, 68), "title": f"HACCP 심사 핵심 꿀팁!\n{topic_name[:15]}", "subtitle": "서류와 현장이 100% 일치하는 품질 엔지니어링", "key_points": [f"{topic_name[:18]} 관련 법적 기준 준수", "심사관이 현장에서 불시에 질문하는 핵심 포인트"], "senior_tip": "작업자 면담 대비 1페이지 원포인트 요약지 현장 비치!", "image": img_main, "narration": f"오늘 품질관리 후배님들을 위해 준비한 주제는 {topic_name}입니다. 심사관이 공장에 왔을 때 긴장하지 않고 20년 차 베테랑처럼 당당하게 통과하는 핵심 실무 팁을 정리해드립니다."},
            {"id": 2, "badge": "💡 과학적 근거 수립", "badge_color": (245, 158, 11), "title": "남의 기준 복사 금지!\n자사 라인 맞춤 실측 기준", "subtitle": "식품공전 및 사내 기준서(SOP) 명문화", "key_points": ["생산 설비 용량 및 제품 특성에 맞춘 한계기준 설정", "작업자가 한눈에 볼 수 있는 시각화 관리선 부착"], "senior_tip": "신제품 출시 때마다 한계기준 유효성 재평가 필수!", "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"), "narration": "첫째, 기준 설정의 과학적 데이터입니다. 남의 공장 기준서를 그대로 베끼면 심사관이 '이 수치의 근거가 뭡니까?'라고 물었을 때 한마디도 대답 못 합니다. 우리 설비의 실측 데이터를 파일철에 보관하세요."},
            {"id": 3, "badge": "⏱️ 골든타임 모니터링", "badge_color": (6, 182, 212), "title": "작업 전·중·후 3시점 점검\n이탈 시 확산 방지 원칙", "subtitle": "문제 발생 시 폐기 범위를 최소화하는 기록법", "key_points": ["1. 작업 시작 전 설비 세척 및 계측기 0점 확인", "2. 연속 가동 중 주기적 모니터링 및 실시간 기록", "3. 작업 종료 직후 최종 확인 및 잔류물 점검"], "senior_tip": "이상 발생 즉시 라인 인터록 및 부적합품 격리 태그 부착!", "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"), "narration": "둘째, 3시점 모니터링입니다. 작업 시작 전, 가동 중, 작업 종료 후 3번에 걸쳐 점검해야 중간에 사고가 나도 회수 범위를 최소한으로 좁혀서 회사 손실을 막을 수 있습니다."},
            {"id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246), "title": "일지는 몰아 쓰지 마라!\n당일 실시간 기록 원칙", "subtitle": "심사관이 펜 색깔과 필체로 가짜 일지 잡아내는 법", "key_points": ["퇴근 직전 몰아서 쓰면 필체와 잉크로 100% 들통", "이탈이 났을 때 솔직하게 개선조치(CAPA) 기록 남기기"], "senior_tip": "정기 사내 위생 점검으로 불시 심사 사전 예방!", "image": img_main, "narration": "셋째, 선배의 뼈 때리는 조언입니다. 일지 몰아서 쓰지 마세요. 심사관들은 펜 잉크 번짐과 필체만 봐도 몰아 쓴 건지 당일 쓴 건지 다 압니다. 이상 났을 때 개선조치를 솔직히 적는 게 진짜 실력입니다."},
            {"id": 5, "badge": "🏆 심사 100% 합격", "badge_color": (16, 185, 129), "title": "완벽한 서류 구비 완료\n심사 지적 0건 달성!", "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다", "key_points": ["1. 공정 관리 기준서 및 표준작업지침서 최신화", "2. 일일 모니터링 점검 일지 및 개선조치 이력철", "3. 작업자 정기 위생 교육 훈련 평가서"], "senior_tip": "실무 질문과 무료 서식은 큐에이플러스 오픈채팅방으로!", "image": img_main, "narration": "이 세 가지만 지키시면 어떤 심사관이 와도 무조건 패스입니다. 막히는 서류나 실무 질문은 큐에이플러스 오픈채팅방에서 편하게 물어보세요. 후배님들의 빠른 칼퇴를 응원합니다!"}
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

def normalize_qa_pronunciation(text: str) -> str:
    """식품 품질관리(QA/QC) 및 HACCP 전문 용어를 자연스러운 한국어 발음(해썹, 씨씨피, 에프제로 등)으로 치환하여 TTS에 전달"""
    if not text:
        return ""
    # 순서 중요: 복합어/긴 단어 먼저 치환
    replacements = [
        ("스마트HACCP", "스마트 해썹"),
        ("스마트haccp", "스마트 해썹"),
        ("FSSC22000", "에프에스에스씨 이만이천"),
        ("fssc22000", "에프에스에스씨 이만이천"),
        ("FSSC 22000", "에프에스에스씨 이만이천"),
        ("FSSC", "에프에스에스씨"),
        ("fssc", "에프에스에스씨"),
        ("HACCP", "해썹"),
        ("haccp", "해썹"),
        ("CCP-B", "씨씨피 비"),
        ("CCP-P", "씨씨피 피"),
        ("CCP-C", "씨씨피 씨"),
        ("CCP", "씨씨피"),
        ("ccp", "씨씨피"),
        ("SOP", "에스오피"),
        ("sop", "에스오피"),
        ("CAPA", "카파"),
        ("capa", "카파"),
        ("ATP", "에이티피"),
        ("atp", "에이티피"),
        ("CIP", "씨아이피"),
        ("cip", "씨아이피"),
        ("HVAC", "에이치백"),
        ("hvac", "에이치백"),
        ("PT100", "피티백"),
        ("pt100", "피티백"),
        ("RTD", "알티디"),
        ("rtd", "알티디"),
        ("PLC", "피엘씨"),
        ("plc", "피엘씨"),
        ("SCADA", "스카다"),
        ("scada", "스카다"),
        ("KOLAS", "코라스"),
        ("kolas", "코라스"),
        ("COA", "씨오에이"),
        ("coa", "씨오에이"),
        ("F0값", "에프제로값"),
        ("F0", "에프제로"),
        ("f0", "에프제로"),
        ("F₀", "에프제로"),
        ("QA+", "큐에이플러스"),
        ("qa+", "큐에이플러스"),
        ("QA", "큐에이"),
        ("qa", "큐에이"),
        ("QC", "큐씨"),
        ("qc", "큐씨"),
        ("SUS", "서스"),
        ("sus", "서스"),
        ("RLU", "알엘유"),
        ("rlu", "알엘유"),
        ("ppm", "피피엠"),
        ("PPM", "피피엠"),
        ("℃", "도"),
        ("°C", "도씨"),
        ("±", "플러스마이너스 "),
        ("≥", "이상 "),
        ("≤", "이하 "),
    ]
    processed = text
    for target, repl in replacements:
        processed = processed.replace(target, repl)
    return processed

async def generate_tts_for_scenes(scenes):
    import edge_tts
    voice = "ko-KR-InJoonNeural"
    audio_files = []
    print("[1/4] Generating Korean TTS Voiceover (ko-KR-InJoonNeural)...")
    for s in scenes:
        out_mp3 = os.path.join(AUDIO_DIR, f"auto_scene_{s['id']:02d}.mp3")
        # 자막 표기는 HACCP/CCP 유지, 음성 나레이션만 '해썹/씨씨피' 자연 발음 적용
        spoken_text = normalize_qa_pronunciation(s["narration"])
        communicate = edge_tts.Communicate(spoken_text, voice, rate="+5%", pitch="+0Hz")
        await communicate.save(out_mp3)
        audio_files.append(out_mp3)
        print(f"  [OK] Scene {s['id']} TTS generated (Spoken: {spoken_text[:30]}...): {out_mp3}")
    return audio_files

def get_ffmpeg_cmd():
    import shutil
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def get_audio_duration(file_path):
    ffmpeg_exe = get_ffmpeg_cmd()
    cmd = [ffmpeg_exe, "-i", file_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="replace")
    stderr_text = res.stderr or ""
    import re
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr_text)
    if m:
        h, m_val, s = m.groups()
        return int(h) * 3600 + int(m_val) * 60 + float(s)
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
        
        # 모든 큐 주제는 동일한 출처 검증·다변화 엔진을 거칩니다.
        # 기존 고정 템플릿은 과거 영상 재현용으로만 보존합니다.
        scenes = generate_dynamic_scenes_for_custom_topic(topic_name)

    # 1. TTS Voiceover
    audio_files = asyncio.run(generate_tts_for_scenes(scenes))
    
    # 2. Frames & Scene MP4 Encoding
    print("\n[2/4] Rendering 1080x1920 HD Frames & Encoding...")
    scene_videos = []
    ffmpeg_exe = get_ffmpeg_cmd()
    
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
            ffmpeg_exe, "-y",
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
            v_clean = v.replace("\\", "/")
            f.write(f"file '{v_clean}'\n")
            
    clean_topic_name = topic_name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace(":", "")[:30]
    out_filename = f"{today_str}_{clean_topic_name}_shorts.mp4"
    master_mp4 = os.path.join(VIDEOS_DIR, out_filename)
    
    concat_cmd = [
        ffmpeg_exe, "-y", "-f", "concat", "-safe", "0",
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
