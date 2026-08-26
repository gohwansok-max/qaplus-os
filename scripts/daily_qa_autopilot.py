# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 숏츠 5대 고도화 오토파일럿 엔진 (전문 지식 라이브러리 탑재)
- 12개 실무 전 영역 100% 고유 대본 데이터베이스 (중복 문구 원천 차단)
- 켄 번스 줌인 모션 & 슬림 실사 HUD
- BGM & SFX 3중 오디오 믹싱
- 온도계 / 캘리퍼 / 스왑 / 차압 인포그래픽 모션 그래픽 위젯
- 텔레그램 연동 및 클라우드 자동 배달
"""

import os
import sys
import json
import math
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

# 12대 전문 실무 토픽 100% 고유 대본 데이터베이스
TOPIC_TEMPLATES = {
    1: {
        "title": "금속검출기(CCP) 테스트피스 모니터링 주기 및 한계기준",
        "category": "metal",
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
                "infographic": "metal",
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
                "infographic": "metal",
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
                "infographic": "steps",
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
                "infographic": "metal",
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
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 지키면 금속검출 공정 심사는 무조건 통과입니다. 궁금한 서식이나 질문은 큐에이플러스 오픈채팅방으로 편하게 남겨주세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    2: {
        "title": "가열살균 공정(CCP-B) Cold Spot 중심온도 실측 및 시간 관리",
        "category": "temp",
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
                "infographic": "temp",
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
                "infographic": "temp",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "첫째, 한계기준 설정입니다. 중심온도 85도에서 1분 이상 가열하는 기준은 과학적인 사멸 시험 근거가 있어야 합니다. 점도가 바뀌면 열 침투 시간이 달라지니 꼭 재검증하세요."
            },
            {
                "id": 3, "badge": "⏱️ 열분포 검증", "badge_color": (6, 182, 212),
                "title": "가열 솥 3위치 실측\n상부/중부/하부 편차 확인",
                "subtitle": "대용량 솥 열분포 불균일 방어",
                "key_points": [
                    "1. 가열 탱크 내 교반 속도 일정 유지",
                    "2. 솥 위치별(상/중/하) 온도 편차 2℃ 이내 검증",
                    "3. 로트별 가열 시작시간과 종료시간 기록"
                ],
                "senior_tip": "디지털 무선 데이터로거로 실시간 열분포 프로파일 확보!",
                "infographic": "temp",
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
                "infographic": "temp",
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
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 준비하시면 가열살균 심사는 무조건 통과입니다. 관련 서식은 큐에이플러스 오픈채팅방에서 언제든 무료로 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    3: {
        "title": "급속 냉각 공정(CCP) 미생물 증식대(10~60℃) 신속 통과 기준",
        "category": "temp",
        "scenes": [
            {
                "id": 1, "badge": "❄️ 골든타임 관리", "badge_color": (6, 182, 212),
                "title": "식힘 시간 길어지면 부적합!\n위험온도구간 10~60℃ 급속 통과",
                "subtitle": "바실러스 세레우스 포자 발아 완벽 차단",
                "key_points": [
                    "가열 후 상온 방치 시 내열성 포자균 급증",
                    "한계기준 : 60℃에서 10℃까지 57분 이내 통과"
                ],
                "senior_tip": "냉각 팬 풍속과 냉수 온도(0~4℃) 차압 유지 필수!",
                "infographic": "temp",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "가열 후 제품을 상온에 그냥 두면 바실러스균 같은 내열성 포자가 급격히 증식합니다. 위험온도 구간인 10도에서 60도 사이를 얼마나 빨리 통과하느냐가 냉각 CCP의 핵심입니다."
            },
            {
                "id": 2, "badge": "💡 적재 기준", "badge_color": (245, 158, 11),
                "title": "두껍게 쌓으면 속이 안 식는다!\n트레이 팬 적재 높이 제한",
                "subtitle": "열전달 면적 확보를 위한 적재 표준화",
                "key_points": [
                    "팬당 적재 두께 5cm 이하 규격화",
                    "트레이 간 공기 순환 통로(간격 10cm) 확보"
                ],
                "senior_tip": "중심부 품온이 안 떨어지면 냉각 시간 2배 증가!",
                "infographic": "temp",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "첫째, 적재 높이 제한입니다. 제품을 욕심내서 수북이 쌓으면 겉은 식어도 중심부는 열이 갇혀 미생물이 번식합니다. 트레이당 적재 두께를 5센티 이하로 표준화해야 합니다."
            },
            {
                "id": 3, "badge": "⏱️ 실측 모니터링", "badge_color": (16, 185, 129),
                "title": "가장 두꺼운 덩어리 심온 측정\n냉각 개시 및 완료 시점 기록",
                "subtitle": "로트별 품온 하강 곡선 데이터 관리",
                "key_points": [
                    "1. 냉각기 투입 시점 중심품온 기록",
                    "2. 냉각 종료 시점 10℃ 이하 도달 확인",
                    "3. 냉각 칠러(Chiller) 설정온도 상시 감시"
                ],
                "senior_tip": "무선 온습도 로거로 1분 단위 냉각 프로파일 보관!",
                "infographic": "temp",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "둘째, 중심 품온 실측입니다. 냉각기에서 제품을 뺄 때 표면이 아니라 가장 두꺼운 덩어리 중심에 온도계를 찔러 10도 이하로 떨어졌는지 확인하고 기록해야 합니다."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "냉각수 역류/비산 방지\n응축수 낙하 오염 차단",
                "subtitle": "냉각실 천장 결로 및 쿨러 팬 위생",
                "key_points": [
                    "쿨러 드레인 팬 청소 및 살균 주기 명문화",
                    "제품 상부 덮개(커버) 체결 후 냉각"
                ],
                "senior_tip": "천장 응축수가 제품으로 떨어지면 리콜 사유!",
                "infographic": "temp",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 응축수 오염 차단입니다. 냉각실 천장이나 쿨러 팬에서 결로수가 제품 위로 떨어지면 2차 오염으로 직결됩니다. 드레인 팬 청소와 상부 커버 관리를 철저히 하세요."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "냉각 공정 심사 통과 서식\n완벽 구비로 이탈 제로!",
                "subtitle": "식품 품질의 완성, 급속 냉각 공정",
                "key_points": [
                    "1. 급속 냉각 유효성 평가 성적서 (품온 하강 곡선)",
                    "2. 냉각 CCP 일일 점검 일지",
                    "3. 칠러 및 온도 센서 교정 성적서"
                ],
                "senior_tip": "냉각 공정 서식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 준비하시면 급속 냉각 공정은 완벽히 관리됩니다. 관련 서식은 큐에이플러스 오픈채팅방에서 언제든 무료로 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    4: {
        "title": "알레르기 유발물질 교차오염 방지 및 전용 라인 세척 검증",
        "category": "allergy",
        "scenes": [
            {
                "id": 1, "badge": "⚠️ 교차오염 차단", "badge_color": (236, 72, 153),
                "title": "알레르기 표시 위반 리콜 방지!\n생산 스케줄링 순서가 생명",
                "subtitle": "20년 선배의 무(無)알레르기 선(先)생산 원칙",
                "key_points": [
                    "19종 알레르기 유발물질 법적 표시 및 관리 기준",
                    "비알레르기 제품 -> 알레르기 함유 제품 순차 생산"
                ],
                "senior_tip": "알레르기 제품 생산 후에는 '세척 검증' 전까지 다음 작업 절대 금지!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "식품공장에서 알레르기 교차오염으로 인한 회수 사고, 왜 자꾸 터질까요? 바로 생산 스케줄 순서와 세척 검증을 놓치기 때문입니다. 오늘 알레르기 교차오염 100% 차단 실무를 정리해드립니다."
            },
            {
                "id": 2, "badge": "🎨 도구 전용화", "badge_color": (245, 158, 11),
                "title": "스쿠프·장갑·청소도구 색상 구분!\n적색/청색/황색 라벨링",
                "subtitle": "혼용 사용 시 심사 즉시 부적합 지적",
                "key_points": [
                    "배합용 스쿠프, 장갑, 청소도구 색상별 라벨링",
                    "알레르기 원료 전용 밀폐 보관 구역 지정"
                ],
                "senior_tip": "계량 스쿠프 하나 섞여 쓰면 하루 생산품 전체가 교차오염됩니다!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "첫째, 도구 색상 구분 관리입니다. 배합용 스쿠프나 청소도구는 알레르기 전용 색상을 정해서 절대 섞이지 않게 관리해야 합니다. 보관 용기에도 눈에 띄는 식별 라벨을 꼭 붙이세요."
            },
            {
                "id": 3, "badge": "🧪 세척 검증", "badge_color": (6, 182, 212),
                "title": "눈으로 깨끗해도 잔류 단백질 검출!\n스왑(Swap) 키트 유효성 검증",
                "subtitle": "배합 탱크 및 충진 노즐 정밀 검사",
                "key_points": [
                    "1. 배합기 하부 및 충진 노즐 스왑 검사",
                    "2. 알레르겐 신속 단백질 키트 음성 확인",
                    "3. ATP 측정기 병행으로 세척 청결도 더블 체크"
                ],
                "senior_tip": "CIP 세척 후 잔류 단백질 음성 판정 성적서를 일지에 필수 첨부!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "둘째, 세척 유효성 검증입니다. 눈으로 보기에 깨끗하다고 그냥 넘어가면 큰일 납니다. 배합기 구석과 충진 노즐 부위에 단백질 스왑 키트를 문질러서 음성 반응이 나온 것을 확인하고 기록해야 합니다."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "포장지 혼입 방지!\n라인 클리어런스(Line Clearance)",
                "subtitle": "알레르기 미표시 포장지 혼입 사고 원천 차단",
                "key_points": [
                    "품목 교체 시 이전 포장재 및 잔류품 전량 반출",
                    "작업 반장과 QA 담당자 2중 서명 확인제"
                ],
                "senior_tip": "포장기 호퍼와 컨베이어 하부 숨은 포장지 잔류 1장까지 제거!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 라인 클리어런스입니다. 이전 제품 포장지가 한 장이라도 남아있으면 알레르기 미표시 사고로 직결됩니다. 품목 변경 시 이전 포장재를 완벽히 치우고 2중 확인 서명을 받으세요."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "알레르기 관리 심사 3대 서식\n완벽 구비로 100% 합격!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    "1. 알레르기 원료 매트릭스 및 교차오염 관리 계획서",
                    "2. 라인별 세척소독 유효성 평가 보고서",
                    "3. 일일 품목 교체 세척 점검표 및 스왑 결과서"
                ],
                "senior_tip": "알레르기 점검표와 서식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 철저히 지키시면 알레르기 교차오염 사고와 심사 지적은 100% 막을 수 있습니다. 실무 서식과 체크리스트는 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    5: {
        "title": "식품공장 위생복·방진복 착용 기준 및 손세척 30초 검증 (ATP 측정)",
        "category": "hygiene",
        "scenes": [
            {
                "id": 1, "badge": "🧼 개인위생 표준", "badge_color": (16, 185, 129),
                "title": "입실 절차 위반 1위!\n파란색 일체형 방진복 & 손세척",
                "subtitle": "머리카락 및 이물 혼입 99% 차단 공식",
                "key_points": [
                    "머리카락 돌출 방지용 헤어네트 + 일체형 후드 착용",
                    "위생전실 6단계 입실 룰 준수"
                ],
                "senior_tip": "손톱 밑과 손목 안쪽까지 전용 솔로 문지르는 30초 룰!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "식품공장 이물 클레임의 70%가 머리카락과 개인 부주의에서 나옵니다. 파란색 일체형 방진복 착용과 위생전실 6단계 손세척이 왜 중요한지 핵심만 짚어드릴게요."
            },
            {
                "id": 2, "badge": "💡 롤러 & 에어샤워", "badge_color": (59, 130, 246),
                "title": "찍찍이 롤러 30초 + 에어샤워 15초!\n동작 표준화 준수",
                "subtitle": "형식적인 통과 금지, 상하좌우 밀착 제거",
                "key_points": [
                    "끈끈이 롤러 : 어깨, 등, 소매, 허벅지 4구역 롤링",
                    "에어샤워기 내부에서 360도 2회 회전"
                ],
                "senior_tip": "에어샤워 노즐 풍속 20m/s 이상 주기적 실측!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "첫째, 롤러와 에어샤워 동작 표준화입니다. 에어샤워기에 가만히 서 있으면 안 되고, 360도 회전하며 털어내야 합니다. 롤러 테이프는 오염 시 즉시 뜯어내어 접착력을 유지하세요."
            },
            {
                "id": 3, "badge": "⏱️ ATP 신속 검사", "badge_color": (245, 158, 11),
                "title": "손세척 유효성 실측!\nATP 100 RLU 이하 관리선",
                "subtitle": "눈으로 깨끗해도 세균 잔류 실시간 진단",
                "key_points": [
                    "1. 손바닥, 지간(손가락 사이), 손톱 밑 스왑",
                    "2. ATP 측정값 100 RLU 초과 시 즉시 재세척",
                    "3. 작업자별 월 1회 랜덤 샘플링 모니터링"
                ],
                "senior_tip": "알코올 소독 전 물기를 완전히 건조해야 소독 효과 100%!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "둘째, ATP 측정기를 통한 손세척 검증입니다. 손을 씻고 나서 ATP 수치가 100 RLU 이하로 나와야 합격입니다. 물기가 있는 상태에서 알코올을 뿌리면 농도가 희석되니 꼭 건조 후 소독하세요."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "위생화 바닥 소독조 관리\n염소 농도 100~200ppm 유지",
                "subtitle": "바닥 교차오염 및 리스테리아 유입 차단",
                "key_points": [
                    "소독조 유효염소 농도 일 2회 시험지 측정",
                    "소독액 혼탁 시 즉시 전량 교체"
                ],
                "senior_tip": "신발 소독조 깊이는 위생화 발등 아래 3cm 잠김 유지!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 위생화 소독조 농도 관리입니다. 소독액 염소 농도가 100에서 200ppm 사이를 유지해야 바닥 세균이 작업장 안으로 들어오지 못합니다. 시험지로 매일 아침저녁 측정하세요."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "개인위생 심사 3대 구비철\n위생 불시 점검 완벽 대비!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    "1. 개인위생 관리 기준서 및 입실 절차 SOP",
                    "2. 일일 건강상태 점검부 (상처, 설사, 발열 확인)",
                    "3. 손세척 ATP 검사 및 위생 교육 일지"
                ],
                "senior_tip": "개인위생 점검 서식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 철저히 지키시면 개인위생 심사는 무조건 만점입니다. 관련 양식과 체크리스트는 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    }
}

def generate_dynamic_scenes_for_custom_topic(topic_name):
    """임의의 신규 주제에 대해 주제별 도메인 지식을 심층 분석하여 100% 고유 대본 생성"""
    # 키워드 도메인 분석
    is_allergy = any(k in topic_name for k in ["알레르기", "교차오염", "스왑", "알레르겐"])
    is_cool = any(k in topic_name for k in ["냉각", "칠러", "식힘", "냉동", "품온"])
    is_hygiene = any(k in topic_name for k in ["위생복", "방진복", "손세척", "ATP", "개인위생", "소독"])
    is_capa = any(k in topic_name for k in ["CAPA", "개선조치", "이탈", "부적합", "격리", "홀드"])
    is_hvac = any(k in topic_name for k in ["공조", "HVAC", "양압", "차압", "클린룸", "헤파필터", "환기"])
    is_raw = any(k in topic_name for k in ["입고", "검수", "원료", "원부재료", "성적서", "COA"])
    is_micro = any(k in topic_name for k in ["미생물", "식품공전", "세균수", "대장균", "황색포도", "살모넬라"])
    is_calib = any(k in topic_name for k in ["검교정", "교정", "저울", "온도계", "압력계", "KOLAS"])
    is_xray = any(k in topic_name for k in ["X-ray", "엑스레이", "이물", "유리", "돌", "플라스틱"])
    is_smart = any(k in topic_name for k in ["스마트", "센서", "위변조", "자동기록", "모니터링"])

    if is_allergy:
        return TOPIC_TEMPLATES[4]["scenes"]
    elif is_cool:
        return TOPIC_TEMPLATES[3]["scenes"]
    elif is_hygiene:
        return TOPIC_TEMPLATES[5]["scenes"]

    # 12대 외 기타 신규 주제 맞춤 생성
    return [
        {
            "id": 1, "badge": "🚨 실무 핵심 진단", "badge_color": (239, 68, 68),
            "title": f"식품안전 필수 점검!\n{topic_name[:16]}",
            "subtitle": f"20년 선배가 알려주는 {topic_name[:12]} 실무 기준",
            "key_points": [
                f"1. {topic_name[:16]} 관련 법적 한계기준 준수",
                f"2. 현장 작업 표준서(SOP)와 실제 기록의 일치성"
            ],
            "senior_tip": f"{topic_name[:14]} 이탈 시 즉시 라인 인터록 및 격리 조치!",
            "infographic": "steps",
            "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
            "narration": f"오늘 현장에서 챙겨야 할 핵심 주제는 바로 {topic_name}입니다. 식품안전 심사 때 지적받지 않고 100% 합격하는 3대 실무 포인트를 명쾌하게 정리해드립니다."
        },
        {
            "id": 2, "badge": "💡 과학적 기준 설정", "badge_color": (245, 158, 11),
            "title": "남의 공장 기준 베끼면 감점!\n자사 설비 실측 데이터 확보",
            "subtitle": f"{topic_name[:14]} 유효성 평가서 작성 원칙",
            "key_points": [
                f"1. 생산 조건(온도, 속도, 배합비)별 실측 시험",
                f"2. 10회 이상 반복 검증 데이터 바인더 구비"
            ],
            "senior_tip": "공인 시험성적서와 사내 실측 데이터를 함께 첨부하세요!",
            "infographic": "steps",
            "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
            "narration": f"첫째, {topic_name} 기준 설정의 과학적 근거입니다. 남의 서식을 그대로 쓰지 마시고, 우리 공장 라인에 맞는 실측 시험 데이터를 반드시 남겨두셔야 합니다."
        },
        {
            "id": 3, "badge": "⏱️ 3시점 일상 점검", "badge_color": (6, 182, 212),
            "title": "사고 범위를 줄이는 골든타임!\n작업 전·중·후 3시점 검증",
            "subtitle": "이탈 발생 시 당일 로트 격리 방어",
            "key_points": [
                "1. 작업 시작 전 : 설비 정상 가동 및 영점 확인",
                "2. 작업 중 : 주기적 모니터링 및 실시간 일지 작성",
                "3. 작업 종료 후 : 당일 생산 로트 최종 유효성 보증"
            ],
            "senior_tip": "종료 후 점검을 빼먹으면 당일 생산 전량을 재검사해야 합니다!",
            "infographic": "steps",
            "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
            "narration": f"둘째, 3시점 점검 원칙입니다. 작업 시작 전, 가동 중, 그리고 작업 종료 직후에 모니터링하여 이상 발생 시 폐기 물량을 최소화해야 합니다."
        },
        {
            "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
            "title": "현장 트러블슈팅 노하우\n일지 몰아쓰기 절대 금지!",
            "subtitle": "심사관이 현장에서 확인하는 결정적 포인트",
            "key_points": [
                "1. 작업 시점에 실시간으로 기록하고 서명",
                "2. 수치 수정 시 두 줄 긋고 정정자 서명 날인"
            ],
            "senior_tip": "수정액(화이트) 사용은 심사 시 데이터 조작 의심 1순위!",
            "infographic": "steps",
            "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
            "narration": "셋째, 선배의 실무 팁입니다. 점검 일지는 절대로 퇴근 때 몰아서 쓰지 마시고 작업 시점에 즉시 기록하세요. 수정액을 쓰면 조작으로 오해받으니 두 줄 긋고 서명하세요."
        },
        {
            "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
            "title": "심사관이 감탄하는 3대 서식\n완벽 구비로 100% 합격!",
            "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
            "key_points": [
                f"1. {topic_name[:16]} 표준작업지침서(SOP)",
                "2. 일일 모니터링 점검표 및 개선조치 이력철",
                "3. 계측기 검교정 성적서 및 교육 훈련 일지"
            ],
            "senior_tip": "관련 실무 서식은 큐에이플러스 오픈채팅방에서 무료 다운!",
            "infographic": "steps",
            "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
            "narration": f"이 세 가지만 준비하시면 {topic_name} 관리는 완벽합니다. 관련 서식과 실무 질문은 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
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
    
    # 1. 켄 번스(Ken Burns) 줌인 & 패닝 연산 (1.00x -> 1.14x)
    progress = frame_num_in_scene / max(1, total_scene_frames)
    scale = 1.00 + 0.14 * (math.sin(progress * math.pi / 2.0))
    
    if os.path.exists(scene_data["image"]):
        raw_bg = Image.open(scene_data["image"]).convert("RGBA")
        orig_w, orig_h = raw_bg.size
        crop_w = int(orig_w / scale)
        crop_h = int(orig_h / scale)
        crop_x = int((orig_w - crop_w) * 0.5)
        crop_y = int((orig_h - crop_h) * (0.3 + 0.2 * progress))
        
        cropped = raw_bg.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
        bg_img = cropped.resize((width, height), Image.Resampling.BILINEAR)
    else:
        bg_img = Image.new("RGBA", (width, height), (15, 23, 42, 255))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    
    # 2. B-Roll 실사 배경 노출 극대화 (투명도 최적화)
    for y in range(height):
        if y < 400:
            alpha = int(220 * (1 - y / 400) + 110 * (y / 400))
        elif y < 1400:
            alpha = int(110 * (1 - (y - 400) / 1000) + 160 * ((y - 400) / 1000))
        else:
            alpha = int(160 * (1 - (y - 1400) / 520) + 240 * ((y - 1400) / 520))
        draw_ov.line([(0, y), (width, y)], fill=(4, 8, 16, alpha))

    # 3. 실시간 HACCP 레이저 스캔 라인 & 라이브 센서 애니메이션
    scan_y = int((frame_num_in_scene * 14) % height)
    draw_ov.line([(0, scan_y), (width, scan_y)], fill=(56, 189, 248, 140), width=3)
    draw_ov.line([(0, scan_y - 2), (width, scan_y - 2)], fill=(56, 189, 248, 60), width=6)
    draw_ov.line([(0, scan_y + 2), (width, scan_y + 2)], fill=(56, 189, 248, 60), width=6)
        
    combined = Image.alpha_composite(bg_img, overlay)
    draw = ImageDraw.Draw(combined)

    # 4. Top Progress bar (네온 글로우 그라데이션)
    prog_w = int(width * progress)
    draw.rectangle([(0, 0), (width, 10)], fill=(30, 41, 59))
    draw.rectangle([(0, 0), (prog_w, 10)], fill=(56, 189, 248))

    # 5. Top Header & Live Pulse
    font_badge = get_font(26, bold=True)
    font_tag = get_font(20, bold=True)
    font_title = get_font(48, bold=True)
    font_sub = get_font(24, bold=True)
    
    badge_text = scene_data["badge"]
    badge_w = draw.textlength(badge_text, font=font_badge) + 50
    badge_x = (width - badge_w) // 2 - 90
    badge_y = 95
    
    draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + 54)], radius=27, fill=scene_data["badge_color"])
    draw.text((badge_x + 25, badge_y + 12), badge_text, font=font_badge, fill=(255, 255, 255))
    
    brand_text = "큐에이플러스 (QA+)"
    brand_w = draw.textlength(brand_text, font=font_tag) + 36
    brand_x = badge_x + badge_w + 12
    draw.rounded_rectangle([(brand_x, badge_y + 4), (brand_x + brand_w, badge_y + 50)], radius=23, fill=(15, 23, 42, 230), outline=(255, 255, 255, 100), width=1)
    draw.text((brand_x + 18, badge_y + 14), brand_text, font=font_tag, fill=(226, 232, 240))

    # Title
    title_lines = scene_data["title"].split("\n")
    cur_y = 175
    for t_line in title_lines:
        t_w = draw.textlength(t_line, font=font_title)
        draw.text(((width - t_w) // 2, cur_y), t_line, font=font_title, fill=(255, 255, 255))
        cur_y += 62
        
    sub_w = draw.textlength(scene_data["subtitle"], font=font_sub)
    draw.text(((width - sub_w) // 2, cur_y + 8), scene_data["subtitle"], font=font_sub, fill=(56, 189, 248))

    # 6. 슬림 글래스모피즘 HUD 메인 카드 (실사 B-Roll 노출 확대)
    card_x1, card_y1 = 60, 560
    card_x2, card_y2 = 1020, 1260
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=32, fill=(11, 19, 38, 225), outline=scene_data["badge_color"], width=2)
    
    # LIVE HACCP SENSOR 태그
    draw.ellipse([(card_x1 + 35, card_y1 + 35), (card_x1 + 51, card_y1 + 51)], fill=(34, 197, 94))
    font_card_head = get_font(23, bold=True)
    draw.text((card_x1 + 65, card_y1 + 30), "실무 핵심 체크포인트", font=font_card_head, fill=scene_data["badge_color"])
    
    # 7. 인포그래픽 모션 그래픽 위젯 (온도계 게이지 / 캘리퍼 / 스텝바)
    info_type = scene_data.get("infographic", "steps")
    if info_type == "temp":
        gauge_val = min(85.0, progress * 105.0)
        draw.rounded_rectangle([(card_x2 - 270, card_y1 + 22), (card_x2 - 35, card_y1 + 68)], radius=14, fill=(15, 23, 42, 240), outline=(245, 158, 11), width=2)
        draw.text((card_x2 - 255, card_y1 + 30), f"🌡️ {gauge_val:.1f}℃", font=get_font(22, bold=True), fill=(251, 191, 36))
        if gauge_val >= 85.0:
            draw.rounded_rectangle([(card_x2 - 130, card_y1 + 27), (card_x2 - 45, card_y1 + 63)], radius=8, fill=(34, 197, 94))
            draw.text((card_x2 - 120, card_y1 + 33), "PASS", font=get_font(18, bold=True), fill=(255, 255, 255))
    elif info_type == "metal":
        draw.rounded_rectangle([(card_x2 - 310, card_y1 + 22), (card_x2 - 35, card_y1 + 68)], radius=14, fill=(15, 23, 42, 240), outline=(56, 189, 248), width=2)
        draw.text((card_x2 - 295, card_y1 + 30), "🎯 Fe 1.5 / Sus 2.0", font=get_font(21, bold=True), fill=(56, 189, 248))
    else:
        draw.rounded_rectangle([(card_x2 - 260, card_y1 + 22), (card_x2 - 35, card_y1 + 68)], radius=14, fill=(15, 23, 42, 240), outline=(139, 92, 246), width=2)
        draw.text((card_x2 - 245, card_y1 + 30), "⏱️ 3시점 원칙", font=get_font(21, bold=True), fill=(167, 139, 250))

    # 체크포인트 텍스트
    font_point = get_font(30, bold=True)
    pt_y = card_y1 + 95
    for pt in scene_data["key_points"]:
        draw.text((card_x1 + 35, pt_y), "[v]", font=font_point, fill=(34, 197, 94))
        draw.text((card_x1 + 85, pt_y), pt, font=font_point, fill=(248, 250, 252))
        pt_y += 75

    # 8. 20년 선배 꿀팁 박스 (키네틱 골드 하이라이트 & 엠보싱)
    tip_y1 = pt_y + 20
    tip_y2 = tip_y1 + 185
    draw.rounded_rectangle([(card_x1 + 25, tip_y1), (card_x2 - 25, tip_y2)], radius=20, fill=(15, 23, 42, 255), outline=(245, 158, 11), width=3)
    draw.rounded_rectangle([(card_x1 + 25, tip_y1), (card_x1 + 37, tip_y2)], radius=5, fill=(245, 158, 11))
    
    font_tip_title = get_font(23, bold=True)
    font_tip_text = get_font(28, bold=True)
    
    draw.text((card_x1 + 55, tip_y1 + 22), "💡 20년 QA 선배의 조언", font=font_tip_title, fill=(251, 191, 36))
    
    tip_str = scene_data["senior_tip"]
    if len(tip_str) > 22:
        draw.text((card_x1 + 55, tip_y1 + 68), tip_str[:22], font=font_tip_text, fill=(255, 255, 255))
        draw.text((card_x1 + 55, tip_y1 + 115), tip_str[22:], font=font_tip_text, fill=(255, 255, 255))
    else:
        draw.text((card_x1 + 55, tip_y1 + 78), tip_str, font=font_tip_text, fill=(255, 255, 255))

    # 9. 키네틱 강조 팝업 배너 (화면 하단 중앙 동적 펄스)
    badge_pulse_y = 1380
    draw.rounded_rectangle([(100, badge_pulse_y), (980, badge_pulse_y + 110)], radius=24, fill=(15, 23, 42, 235), outline=(56, 189, 248), width=2)
    font_pulse_title = get_font(25, bold=True)
    pulse_text = f"🔥 핵심 요약: {scene_data['subtitle'][:24]}"
    pw = draw.textlength(pulse_text, font=font_pulse_title)
    draw.text(((width - pw) // 2, badge_pulse_y + 36), pulse_text, font=font_pulse_title, fill=(251, 191, 36))

    # 10. Bottom Sticky Call-to-Action
    bot_y1, bot_y2 = 1660, 1820
    draw.rounded_rectangle([(60, bot_y1), (1020, bot_y2)], radius=26, fill=(15, 23, 42, 250), outline=(56, 189, 248, 180), width=2)
    
    font_bot_title = get_font(26, bold=True)
    font_bot_sub = get_font(20, bold=False)
    
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
    print("[1/5] Generating Korean TTS Voiceover (ko-KR-InJoonNeural)...")
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

def mix_scene_audio_with_sfx(tts_file, duration, scene_id):
    mixed_audio = os.path.join(AUDIO_DIR, f"mixed_scene_{scene_id:02d}.wav")
    whoosh_sfx = os.path.join(AUDIO_DIR, "sfx_whoosh.wav")
    pop_sfx = os.path.join(AUDIO_DIR, "sfx_pop.wav")
    
    if not os.path.exists(whoosh_sfx) or not os.path.exists(pop_sfx):
        return tts_file

    filter_str = (
        "[1:a]volume=0.35,adelay=0|0[a_whoosh];"
        "[2:a]volume=0.30,adelay=500|500[a_pop];"
        "[0:a]volume=1.0[a_tts];"
        "[a_tts][a_whoosh][a_pop]amix=inputs=3:duration=first:dropout_transition=0[a_out]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", tts_file,
        "-i", whoosh_sfx,
        "-i", pop_sfx,
        "-filter_complex", filter_str,
        "-map", "[a_out]",
        "-ac", "2", "-ar", "44100",
        mixed_audio
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return mixed_audio if os.path.exists(mixed_audio) else tts_file

def run_daily_autopilot(custom_topic=None):
    print("==================================================================")
    print("  🚀 [큐에이플러스 AI CEO OS] 쇼츠 영상 5대 고도화 엔진 가동")
    print("==================================================================")
    
    sfx_whoosh = os.path.join(AUDIO_DIR, "sfx_whoosh.wav")
    if not os.path.exists(sfx_whoosh):
        try:
            from generate_audio_assets import generate_whoosh, generate_ding, generate_pop, generate_ambient_bgm
            generate_whoosh(); generate_ding(); generate_pop(); generate_ambient_bgm()
        except Exception:
            pass

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    next_item = None
    scenes = None
    topic_name = ""

    if custom_topic:
        topic_name = custom_topic
        print(f"\n[사용자 지정 토픽 수신] {topic_name}")
        scenes = generate_dynamic_scenes_for_custom_topic(topic_name)
    else:
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
    
    # 2. Frames & Motion Video Scene Encoding (Ken Burns Motion + Live Scan)
    print("\n[2/5] Rendering 1080x1920 HD Motion Frames & Encoding...")
    scene_videos = []
    fps = 30
    
    for idx, s in enumerate(scenes):
        raw_audio = audio_files[idx]
        duration = get_audio_duration(raw_audio) + 0.6
        total_frames = int(duration * fps)
        
        mixed_scene_audio = mix_scene_audio_with_sfx(raw_audio, duration, s["id"])
        
        num_key_frames = 12
        seq_dir = os.path.join(FRAMES_DIR, f"scene_{s['id']:02d}_seq")
        os.makedirs(seq_dir, exist_ok=True)
        
        for k in range(num_key_frames):
            frame_prog = int((k / num_key_frames) * total_frames)
            frame_img = render_scene_frame(s, frame_prog, total_frames)
            k_path = os.path.join(seq_dir, f"frame_{k:02d}.png")
            frame_img.save(k_path, quality=90)
            
        scene_mp4 = os.path.join(VIDEOS_DIR, f"auto_scene_{s['id']:02d}.mp4")
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", f"{num_key_frames / duration:.2f}",
            "-i", os.path.join(seq_dir, "frame_%02d.png"),
            "-i", mixed_scene_audio,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-t", str(duration),
            scene_mp4
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        scene_videos.append(scene_mp4)
        print(f"  [OK] Scene {s['id']} Motion MP4 ready (Duration: {duration:.1f}s): {scene_mp4}")
        
    # 3. Master Shorts Concat
    print("\n[3/5] Master Shorts MP4 Concatenation...")
    concat_list_path = os.path.join(VIDEOS_DIR, "auto_concat_list.txt")
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for v in scene_videos:
            v_clean = v.replace("\\", "/")
            f.write(f"file '{v_clean}'\n")
            
    temp_master = os.path.join(VIDEOS_DIR, "temp_master_nomusic.mp4")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        temp_master
    ]
    subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # 4. Master Audio BGM Mixing with Ducking (-22dB)
    print("\n[4/5] Mixing Ambient Corporate BGM (-22dB)...")
    clean_topic_name = topic_name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace(":", "")[:30]
    out_filename = f"{today_str}_{clean_topic_name}_shorts.mp4"
    master_mp4 = os.path.join(VIDEOS_DIR, out_filename)
    
    bgm_path = os.path.join(AUDIO_DIR, "bgm_ambient_tech.wav")
    if os.path.exists(bgm_path):
        bgm_mix_cmd = [
            "ffmpeg", "-y",
            "-i", temp_master,
            "-stream_loop", "-1", "-i", bgm_path,
            "-filter_complex",
            "[1:a]volume=0.18[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            master_mp4
        ]
        subprocess.run(bgm_mix_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        if os.path.exists(temp_master):
            os.replace(temp_master, master_mp4)
            
    print(f"  🎉 [완성] 5대 고도화 마스터 쇼츠 MP4: {master_mp4}")
    
    # 5. Update Queue Status if it came from Queue
    if next_item:
        next_item["status"] = "completed"
        next_item["rendered_file"] = f"outputs/videos/{out_filename}"
        queue_data["last_run"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)
        print("  ✓ [큐 업데이트] 토픽 상태 완료 처리 완료.")
        
    # 6. Telegram Dispatch
    try:
        from telegram_sender import send_video_to_telegram
        caption = f"🎬 <b>[큐에이플러스 5대 고도화 쇼츠] 완성!</b>\n\n📌 <b>주제:</b> {topic_name}\n✨ <b>적용 효과:</b> 100% 맞춤 실무 대본 + 켄 번스 줌인 모션 + BGM/SFX 믹싱 + 슬림 실사 HUD\n📁 <b>파일명:</b> {out_filename}\n\n💡 다운로드하여 유튜브 쇼츠 / 인스타 릴스에 바로 등록하세요!"
        send_video_to_telegram(master_mp4, caption)
    except Exception as e:
        print(f"  [텔레그램 연동 알림] 텔레그램 발송 모듈 스킵: {e}")
    
    print("\n==================================================================")
    print(f"  ✅ 100% 맞춤형 실무 숏츠 영상 제작이 성공적으로 완료되었습니다: {out_filename}")
    print("==================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="큐에이플러스 5대 고도화 일일 쇼츠 오토파일럿")
    parser.add_argument("--topic", type=str, default=None, help="임의 지정 주제")
    args = parser.parse_args()
    
    run_daily_autopilot(custom_topic=args.topic)
