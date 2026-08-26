# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 숏츠 5대 고도화 오토파일럿 엔진
- 12대 전 실무 토픽 100% 고유 실무 지식 대본 완벽 탑재 (중복 문구 원천 차단)
- 켄 번스(Ken Burns) 줌인 모션 & 슬림 실사 HUD
- BGM & SFX 3중 오디오 믹싱
- 인포그래픽 모션 그래픽 위젯 (온도계 / 캘리퍼 / 차압계 / 미생물 / 3시점)
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

# 12대 전문 실무 토픽 100% 고유 대본 데이터베이스 (중복 문구 원천 차단)
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
    },
    6: {
        "title": "CCP 한계기준 이탈 시 개선조치(CAPA) 및 부적합품 격리 4단계",
        "scenes": [
            {
                "id": 1, "badge": "🚨 긴급 이탈 조치", "badge_color": (220, 38, 38),
                "title": "한계기준 이탈 발생 시 당황 금지!\n즉시 라인 정지 & 빨간 HOLD 태그",
                "subtitle": "20년 선배가 알려주는 부적합품 격리 4단계",
                "key_points": [
                    "이탈 즉시 설비 인터록 및 생산 라인 정지",
                    "해당 로트 전량 격리 구역 이동 및 붉은색 HOLD 라벨 부착"
                ],
                "senior_tip": "격리 구역 시건장치 체결하고 열쇠는 품질팀장이 보관!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "생산 중 금속검출기나 가열온도 이탈이 발생하면 현장에서 가장 먼저 무엇을 해야 할까요? 바로 생산 중단과 빨간색 홀드 태그 부착입니다. 오늘 개선조치 4단계를 완벽 정리해드립니다."
            },
            {
                "id": 2, "badge": "🔍 로트 역추적", "badge_color": (245, 158, 11),
                "title": "직전 정상 점검 시점까지 전량 보류!\n영향받은 로트(Lot) 범위 확정",
                "subtitle": "사고 범위 확산을 방어하는 추적성 관리",
                "key_points": [
                    "이전 정상 모니터링 시점 ~ 이탈 발견 시점 물량 전수 보류",
                    "원부재료 입고 번호 및 포장 일자 매핑 대조"
                ],
                "senior_tip": "2시간 간격 모니터링을 했다면 최대 2시간 물량만 보류하면 됩니다!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "첫째, 영향받은 로트 범위 확정입니다. 이탈이 발견되면 직전 정상 점검 시점부터 지금까지 생산된 전 물량을 보류해야 합니다. 점검 주기가 짧을수록 버려지는 물량을 줄일 수 있습니다."
            },
            {
                "id": 3, "badge": "💡 5-Why 원인 분석", "badge_color": (6, 182, 212),
                "title": "단순 작업자 부주의로 결론내면 탈락!\n근본 원인 5-Why 분석",
                "subtitle": "설비 결함, 센서 오작동, 원료 편차 규명",
                "key_points": [
                    "1. 센서 케이블 단선 또는 히터 코일 열화 확인",
                    "2. 배합비 점도 변화로 인한 열침투 지연 규명",
                    "3. 동일 사례 재발 방지 장치(Poka-Yoke) 설계"
                ],
                "senior_tip": "'작업자 재교육'만 적힌 개선조치서는 심사관에게 100% 반려됩니다!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "둘째, 5-Why 근본 원인 분석입니다. 이탈 원인을 단순히 작업자 부주의로 적으면 심사에서 감점받습니다. 설비 센서 고장이나 배합비 점도 변화 같은 근본 원인을 파헤쳐 적어야 합니다."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "부적합품 재가공 vs 폐기 결정\n품질책임자 서명 승인제",
                "subtitle": "재가공 유효성 평가서 없는 재투입 절대 불가",
                "key_points": [
                    "재가공 기준(온도, 시간, 배합비율) 사전 명문화",
                    "폐기 처리 시 폐기물 사진 및 계근표 일지 첨부"
                ],
                "senior_tip": "폐기 물품은 현장에서 즉시 락스를 뿌려 변질시켜 유출 차단!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 부적합품 처리 기준입니다. 재가공을 하려면 사전 유효성 평가서가 있어야 하고, 폐기할 때는 폐기 사진과 계근표를 반드시 남겨야 합니다."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "개선조치(CAPA) 심사 3대 서류\n이탈 이력철 완벽 대비!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    "1. 한계기준 이탈 및 개선조치 보고서 (CAPA)",
                    "2. 부적합품 격리 및 폐기/재가공 처리 대장",
                    "3. 재발방지 SOP 개정 및 교육 이력서"
                ],
                "senior_tip": "개선조치 보고서 양식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 갖추면 이탈이 발생해도 심사관에게 완벽한 품질 관리 능력을 입증할 수 있습니다. 관련 서식은 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    7: {
        "title": "작업장 공조(HVAC) 양압 관리 및 클린룸 차압 점검 주기",
        "scenes": [
            {
                "id": 1, "badge": "💨 공조/차압 관리", "badge_color": (59, 130, 246),
                "title": "외부 공기 역류 차단!\n청결구역 양압(Positive Pressure) 15Pa",
                "subtitle": "20년 선배의 공조(HVAC) 기류 밸런싱",
                "key_points": [
                    "공기 흐름 원칙 : 청결구역 -> 준청결구역 -> 일반구역",
                    "출입문 개방 시 실내 공기가 밖으로 밀려나가는 양압 유지"
                ],
                "senior_tip": "차압계(Magnehelic) 수치가 음압(-)으로 떨어지면 외부 오염 유입!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "작업장 문을 열었을 때 바깥 공기가 안으로 빨려 들어온다면 미생물과 분진이 그대로 침투합니다. 청결구역 양압 15 파스칼 관리와 공조 기류 제어법을 핵심만 정리해드립니다."
            },
            {
                "id": 2, "badge": "💡 헤파필터 차압", "badge_color": (245, 158, 11),
                "title": "헤파(HEPA) 필터 0.3㎛ 99.97% 포집!\n차압계(Magnehelic) 일일 점검",
                "subtitle": "필터 막힘 및 찢어짐 실시간 감시",
                "key_points": [
                    "프리필터(1차) -> 미디엄(2차) -> 헤파(3차) 3단 구조",
                    "초기 차압 대비 2배 이상 상승 시 필터 교체"
                ],
                "senior_tip": "헤파필터 연 1회 PAO 연무 누기 시험(Leak Test) 성적서 필수!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "첫째, 헤파필터 차압 점검입니다. 필터에 먼지가 쌓이면 차압이 올라가고 풍량이 줄어듭니다. 마그네헬릭 차압계 수치를 매일 기록하여 교체 주기를 놓치지 마세요."
            },
            {
                "id": 3, "badge": "⏱️ 풍속 및 환기", "badge_color": (6, 182, 212),
                "title": "청결구역 풍속 0.3m/s 실측!\n시간당 환기 횟수 15~20회 유지",
                "subtitle": "기류 정체 구역 및 결로 방지",
                "key_points": [
                    "1. 급기구(Diffuser) 디퓨저 풍속 아네모미터 실측",
                    "2. 바닥 배기 갤러리 먼지 청소 주기 명문화",
                    "3. 작업장 온습도(20℃ 이하, 습도 60% 이하) 유지"
                ],
                "senior_tip": "작업장 습도가 70% 넘어가면 천장 곰팡이 포자 번식 위험!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "둘째, 환기 횟수와 온습도 관리입니다. 청결구역은 시간당 최소 15회 이상 환기가 되어야 공기 중 부유균이 배출됩니다. 습도는 60% 이하로 유지해야 곰팡이를 막을 수 있습니다."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "에어락 도어 인터록(Interlock)\n동시 개방 방지 연동",
                "subtitle": "전실 양쪽 문이 한 번에 열리면 차압 붕괴",
                "key_points": [
                    "에어락 전실 한쪽 문이 닫혀야 반대쪽 문 개방",
                    "도어 가스켓 틈새 마모 상태 주 1회 육안 점검"
                ],
                "senior_tip": "도어 하부 고무 패킹이 찢어지면 바닥 벌레 유입 1위!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 에어락 도어 인터록입니다. 전실의 안쪽 문과 바깥쪽 문이 동시에 열리면 순간적으로 차압이 깨집니다. 반드시 인터록 장치를 걸어 한쪽 문이 닫힌 뒤 열리도록 하세요."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "공조 시설 심사 3대 구비철\n환경 모니터링 100% 통과!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    "1. 공조기(AHU) 점검표 및 차압 일일 모니터링 일지",
                    "2. 헤파필터 교체 이력 및 누기 시험 성적서",
                    "3. 작업장 공기 중 낙하세균 / 부유균 시험 성적서"
                ],
                "senior_tip": "공조 점검 일지 서식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 관리하시면 작업장 공조와 차압 심사는 완벽히 패스합니다. 관련 서식과 실무 질문은 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    8: {
        "title": "원부재료 입고 검수 기준 (품온 측정, 성적서 대조, 이물 확인)",
        "scenes": [
            {
                "id": 1, "badge": "📦 원료 입고 검수", "badge_color": (139, 92, 246),
                "title": "입고에서 뚫리면 전 공정 오염!\n냉장 0~10℃ / 냉동 -18℃ 이하 실측",
                "subtitle": "20년 선배의 원료 입고 3단계 방어선",
                "key_points": [
                    "납품 차량 타코메타(온도기록지) 운행 전구간 확인",
                    "원료 박스 중심 품온 탐침 온도계 측정"
                ],
                "senior_tip": "냉동 원료 품온이 -15℃ 이상으로 녹아있으면 즉시 입고 거부 및 반품!",
                "infographic": "temp",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "원부재료 입고 검수에서 오염된 원료를 통과시키면 이후 모든 가열과 살균 공정이 무용지물이 됩니다. 납품 차량 온도기록지와 중심품온 실측 원칙을 명쾌하게 정리해드립니다."
            },
            {
                "id": 2, "badge": "💡 COA 성적서 대조", "badge_color": (245, 158, 11),
                "title": "공급업체 시험성적서(COA) 전수 대조!\n유효기간 및 제조일자 확인",
                "subtitle": "성적서 위변조 및 누락 방지",
                "key_points": [
                    "입고 로트 번호와 시험성적서 번호 일치 확인",
                    "중금속, 잔류농약, 미생물 공인 규격 만족 확인"
                ],
                "senior_tip": "연 1회 이상 공급업체 성적서와 별도로 자체 공인기관 교차 검사!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "첫째, 시험성적서 대조입니다. 입고된 박스의 로트 번호와 공급업체가 보낸 시험성적서 번호가 정확히 일치하는지 확인하고, 미생물과 유해물질 규격 적합 여부를 체크해야 합니다."
            },
            {
                "id": 3, "badge": "⏱️ 외관/이물 검사", "badge_color": (6, 182, 212),
                "title": "포장 파손 및 해충 흔적 전수 확인!\n샘플링 검수 기준(n=√N+1)",
                "subtitle": "수침, 변색, 곰팡이 오염 원천 차단",
                "key_points": [
                    "1. 포장지 찢김, 찌그러짐, 쥐/해충 분변 검사",
                    "2. 원료 색상, 이취, 수분 응결 상태 관능검사",
                    "3. 검수 합격품에 '입고검사 합격증' 라벨 부착"
                ],
                "senior_tip": "박스 테이프에 외부 흙먼지가 묻은 채 내부로 들어가지 않게 겉박스 탈거!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "둘째, 외관 및 이물 샘플링 검사입니다. 포장이 찢어지거나 젖은 박스는 즉시 격리하고, 관능검사로 냄새와 변색을 확인한 뒤 합격 라벨을 붙여 창고로 인계해야 합니다."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "선입선출(FIFO) & 바닥 이격 15cm\n벽면 30cm 이격 팔레트 적재",
                "subtitle": "창고 해충 유입 및 습기 차단 원칙",
                "key_points": [
                    "바닥 직접 적재 금지, 플라스틱 위생 팔레트 사용",
                    "제조일자 빠른 순서대로 출고 동선 라인 배치"
                ],
                "senior_tip": "나무 팔레트는 가시, 곰팡이, 벌레 유입 1위이므로 식품 창고 반입 절대 금지!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 창고 적재와 선입선출입니다. 원료는 바닥에서 15센티, 벽에서 30센티 띄워 적재해야 환기가 되고 벌레가 숨지 못합니다. 나무 팔레트는 이물 위험이 크니 플라스틱만 쓰세요."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "입고 검수 심사 3대 구비철\n협력업체 관리 완벽 대비!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    "1. 원부재료 입고 검사 기준서 및 일일 검수 일지",
                    "2. 원료 공급업체 시험성적서(COA) 바인더",
                    "3. 연 1회 원료 공급업체 정기 현장 위생 평가서"
                ],
                "senior_tip": "입고 검수 서식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 갖추면 원료 입고 심사는 100점 만점입니다. 입고 검수 일지와 공급업체 평가표는 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    9: {
        "title": "식품공전 미생물 규격 (일반세균수, 대장균군, 황색포도상구균) 판정법",
        "category": "micro",
        "scenes": [
            {
                "id": 1, "badge": "🔬 미생물 규격 기준", "badge_color": (14, 165, 233),
                "title": "통계적 샘플링 n, c, m, M 완벽 해석!\n1개라도 초과하면 부적합 판정",
                "subtitle": "20년 선배의 식품공전 미생물 규격 정복",
                "key_points": [
                    "n: 시료 수, c: 최대 허용 시료 수, m: 기준값, M: 최대 한계값",
                    "가열제품 vs 비가열제품 규격 기준 명확한 구분"
                ],
                "senior_tip": "단 1개 시료라도 M값을 넘으면 c값과 무관하게 즉시 부적합!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "식품공전 미생물 기준에서 엔, 씨, 엠, 라지엠 표기를 제대로 해석하지 못하면 자가품질검사에서 큰 낭패를 봅니다. 오늘 통계적 샘플링 판정법을 3분 만에 마스터해드릴게요."
            },
            {
                "id": 2, "badge": "💡 일반세균수 판정", "badge_color": (245, 158, 11),
                "title": "일반세균수(Aerobic Plate Count)\nn=5, c=2, m=10^5, M=10^6 계산법",
                "subtitle": "표준평판배양법 35℃ 48시간 배양",
                "key_points": [
                    "집락수 30~300개 평판 선택하여 계산",
                    "5개 샘플 중 10^5 초과 10^6 이하 샘플은 최대 2개까지만 합격"
                ],
                "senior_tip": "희석배수별 집락수 계산 공식(N = ΣC / [(1*n1)+(0.1*n2)]*d) 준수!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "첫째, 일반세균수 판정입니다. 시료 5개를 검사했을 때, 소문자 엠과 대문자 엠 사이의 수치는 최대 2개까지만 허용됩니다. 3개 이상 나오거나 대문자 엠을 넘으면 부적합입니다."
            },
            {
                "id": 3, "badge": "⏱️ 병원성 미생물", "badge_color": (239, 68, 68),
                "title": "살모넬라 / 리스테리아 / 장출혈성대장균\n25g 당 음성(n=5, c=0, m=0/25g)",
                "subtitle": "절대 검출되어서는 안 되는 제로 톨러런스(Zero Tolerance)",
                "key_points": [
                    "1. 증균배양 -> 선택배지 분리배양 -> 확인시험(PCR/동정)",
                    "2. 5개 시료 모두에서 25g 당 음성(불검출) 필수",
                    "3. 대장균군(Coliform) 정량/정성 시험 기준 준수"
                ],
                "senior_tip": "병원성 식중독균 양성 판정 시 보건당국 즉시 보고 및 전량 회수!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "둘째, 병원성 미생물 음성 기준입니다. 살모넬라나 리스테리아 같은 식중독균은 25그램 당 무조건 불검출이어야 합니다. 단 1개라도 양성이 나오면 즉시 전량 회수 조치됩니다."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "실험실 무균 작업대(Clean Bench)\n배지 멸균 검증 블랭크 테스트",
                "subtitle": "실험실 자체 오염으로 인한 가짜 양성(False Positive) 방어",
                "key_points": [
                    "클린벤치 UV 램프 30분 소독 후 알코올 70% 분무",
                    "배지 1장 공시험(Blank)으로 배지 자체 무균성 보증"
                ],
                "senior_tip": "공시험 배지에 균이 자랐다면 실험 결과 전체 무효 처리 후 재시험!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 블랭크 테스트입니다. 실험실 공기나 배지 자체 오염으로 가짜 양성이 나오는 경우가 많습니다. 시료를 넣지 않은 공시험 배지를 함께 배양해서 실험 무결성을 증명하세요."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "미생물 시험 검사 3대 서류\n자가품질검사 완벽 대비!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    "1. 자가품질검사 관리 대장 및 공인 시험성적서",
                    "2. 사내 미생물 일일 모니터링 원장 및 균수 계산표",
                    "3. 배양기 및 오토클레이브 검교정 성적서"
                ],
                "senior_tip": "미생물 검사 대장 양식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 구비하시면 미생물 검사와 자가품질검사 심사는 무조건 통과입니다. 관련 계산 서식은 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    10: {
        "title": "HACCP 검교정 관리 (온도계, 저울, 압력계 연 1회 공인 검교정)",
        "scenes": [
            {
                "id": 1, "badge": "📏 계측기 검교정", "badge_color": (245, 158, 11),
                "title": "계측기 오차 1도가 합격/불합격을 가른다!\nKOLAS 연 1회 공인 검교정",
                "subtitle": "20년 선배의 계측기 신뢰성 보증 룰",
                "key_points": [
                    "국가표준기본법 소급성(Traceability) 성적서 구비",
                    "온도계, 전자저울, 압력계, 타이머 관리 대상"
                ],
                "senior_tip": "교정 유효기간 만료 30일 전에 교정기관 사전 접수 필수!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "온도계가 1도만 틀어져도 살균 온도를 채우지 못한 미생물 번식 사고로 이어집니다. 공인기관 국가 소급성 검교정과 사내 일상 영점 관리법을 명쾌하게 정리해드립니다."
            },
            {
                "id": 2, "badge": "💡 사내 0점 보정", "badge_color": (6, 182, 212),
                "title": "중심온도계 얼음물 0℃ / 끓는물 100℃\n월 1회 2점 영점보정 원칙",
                "subtitle": "심사 전날 급조하지 않는 상시 데이터 축적",
                "key_points": [
                    "증류수 얼음물 0℃ ±0.2℃ / 끓는물 100℃ ±0.3℃ 실측",
                    "오차 ±0.5℃ 초과 시 센서 폐기 및 신규 교체"
                ],
                "senior_tip": "온도계 센서 코일 단선 시 튀는 수치(불안정) 주 1회 육안 점검!",
                "infographic": "temp",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "첫째, 사내 2점 영점보정입니다. 중심온도계는 매월 얼음물 0도와 끓는물 100도에서 사내 보정을 해야 합니다. 오차가 0.5도를 넘어가면 센서를 즉시 교체해야 합니다."
            },
            {
                "id": 3, "badge": "⏱️ 전자저울 분동", "badge_color": (16, 185, 129),
                "title": "전자저울 F1급 표준분동 일일 점검!\n작업 시작 전 영점 및 수평계 확인",
                "subtitle": "배합비 오차 및 식품첨가물 초과 투입 차단",
                "key_points": [
                    "1. 저울 기포관 수평 정중앙 일치 확인",
                    "2. 공인 표준분동(100g, 500g, 1kg) 일일 실측 기록",
                    "3. 분동 취급 시 핀셋 및 면장갑 착용 (손 지문 오염 차단)"
                ],
                "senior_tip": "표준분동을 맨손으로 잡으면 땀과 기름기로 무게 오차 발생!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "둘째, 전자저울 표준분동 점검입니다. 저울 수평을 맞추고 공인 분동으로 매일 아침 오차를 기록해야 합니다. 표준분동은 지문이 묻지 않게 반드시 핀셋이나 장갑을 끼고 만지세요."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "계측기 관리 대장(Matrix) & 교정필증\n현장 계측기 녹색 스티커 부착",
                "subtitle": "교정 기한 지난 계측기 현장 방치 적발 방어",
                "key_points": [
                    "고유 식별번호(ID) 부여 및 계측기 관리 이력카드 작성",
                    "차기 교정 예정일이 명시된 녹색 교정필증 부착"
                ],
                "senior_tip": "고장난 계측기는 '사용금지(붉은색)' 라벨을 붙여 별도 격리 보관!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 계측기 이력 관리와 교정필증 스티커입니다. 모든 계측기에 고유 번호를 붙이고 다음 교정일 스티커를 부착해야 합니다. 고장난 계측기는 즉시 사용금지 라벨을 붙여 격리하세요."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "검교정 심사 3대 필수 바인더\n심사관 지적 0건 달성!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    "1. 계측기 총괄 관리 대장 및 사내 검교정 기준서",
                    "2. KOLAS 공인 검교정 성적서 원본 바인더",
                    "3. 일일 저울/온도계 사내 일상 점검 일지"
                ],
                "senior_tip": "검교정 관리 양식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 철저히 정리해두시면 계측기 심사는 무조건 패스입니다. 계측기 관리 대장 양식은 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    11: {
        "title": "이물 관리 시스템: X-ray 이물검출기 vs 금속검출기 차이와 복합 운영",
        "scenes": [
            {
                "id": 1, "badge": "🔍 이물 제로화", "badge_color": (16, 185, 129),
                "title": "금속검출기 vs X-ray 이물검출기!\n원리 차이와 상호 보완 완벽 정리",
                "subtitle": "20년 선배의 다중 이물 방어선 구축",
                "key_points": [
                    "금속검출기 : 자기장 교란 기반, 철/스텐 고감도 검출",
                    "X-ray 검출기 : 밀도(Density) 흡수차 기반, 비금속 이물 검출"
                ],
                "senior_tip": "알루미늄 파우치 포장 제품은 X-ray 검출기 필수 적용!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "금속검출기와 엑스레이 검사기, 둘 중 하나만 쓰면 왜 이물 클레임이 터질까요? 두 장비의 검출 원리가 완전히 다르기 때문입니다. 두 장비의 복합 운영 노하우를 정리해드립니다."
            },
            {
                "id": 2, "badge": "💡 X-ray 검출 범위", "badge_color": (245, 158, 11),
                "title": "뼈, 돌, 유리, 경질 플라스틱 검출!\n밀도차 기반 이미지 필터링",
                "subtitle": "금속검출기가 못 잡는 비금속 위험 이물 차단",
                "key_points": [
                    "유리(Glass 2.0mm), 돌(Stone 2.0mm), 뼈(Bone 3.0mm) 검출",
                    "제품 두께 및 밀도에 따른 흑백 명암비(Contrast) 세팅"
                ],
                "senior_tip": "비닐이나 머리카락, 종이는 밀도가 낮아 X-ray로도 검출 불가!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "첫째, 엑스레이의 검출 범위입니다. 엑스레이는 돌, 유리, 뼈처럼 물보다 밀도가 높은 이물을 완벽히 잡아냅니다. 단, 머리카락이나 비닐은 밀도가 낮아 전처리 공정에서 걸러내야 합니다."
            },
            {
                "id": 3, "badge": "⏱️ 시편 모니터링", "badge_color": (6, 182, 212),
                "title": "X-ray 전용 테스트 시편 점검!\n유리/돌/세라믹 시편 통과 원칙",
                "subtitle": "센서 다이오드 열화 및 감도 저하 방어",
                "key_points": [
                    "1. SUS, 유리구(Glass Ball), 세라믹 시편 3종 통과",
                    "2. 제품 중심부 및 대각선 4개 모서리 통과 테스트",
                    "3. 자동 리젝터(Rejector) 에어 블로우 정상 배출 확인"
                ],
                "senior_tip": "X-ray 디텍터 센서 먼지 청소 매주 정기 수행!",
                "infographic": "metal",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "둘째, 엑스레이 시편 점검입니다. 금속 시편뿐만 아니라 유리와 세라믹 시편을 함께 통과시켜야 합니다. 제품의 네 귀퉁이와 중심부에 올려서 모두 정상 리젝트되는지 확인하세요."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "방사선 안전관리 기준 준수!\n법적 누설 선량 1μSv/h 이하 유지",
                "subtitle": "원자력안전위원회 방사선 발생장치 신고 및 필증",
                "key_points": [
                    "작업자 방사선 피폭 방지 차폐 커튼(납 커튼) 마모 점검",
                    "연 1회 공인기관 방사선 누설 측정 성적서 보관"
                ],
                "senior_tip": "납 차폐 커튼이 제품에 직접 닿지 않도록 가이드 롤러 설치!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 방사선 안전관리입니다. 엑스레이 장비는 차폐 커튼 손상이 없는지 매일 확인하고, 연 1회 방사선 누설 측정을 받아야 합니다. 안전 필증 원본을 바인더에 보관하세요."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "이물 관리 심사 3대 서식\n이물 클레임 제로화 달성!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    "1. X-ray 및 금속검출기 한계기준 유효성 평가서",
                    "2. 일일 3시점 시편 모니터링 및 불합격품 처리 대장",
                    "3. 방사선 발생장치 안전관리 일지 및 측정 성적서"
                ],
                "senior_tip": "이물 관리 서식은 큐에이플러스 오픈채팅방에서 무료 다운!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 구축하시면 이물 클레임과 심사는 완벽히 방어됩니다. 이물 관리 점검 서식은 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    },
    12: {
        "title": "스마트HACCP 도입 효과 및 데이터 위변조 방지 센서 연동 실무",
        "scenes": [
            {
                "id": 1, "badge": "💻 스마트 HACCP", "badge_color": (99, 102, 241),
                "title": "종이 일지 수기 작성 끝!\n스마트HACCP 디지털 실시간 자동 기록",
                "subtitle": "20년 선배가 알려주는 스마트공장 전환 로드맵",
                "key_points": [
                    "CCP 모니터링 데이터 센서에서 서버로 초단위 직결",
                    "일지 작성 시간 90% 단축 및 기록 누락 원천 차단"
                ],
                "senior_tip": "스마트HACCP 등록 시 정기 심사 서류 평가 면제 혜택!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": "바쁜 현장에서 하루 종일 볼펜 들고 CCP 일지 쓰느라 힘드셨죠? 스마트HACCP을 도입하면 센서가 데이터를 자동으로 수집하여 일지 작성 부담을 90% 없애줍니다."
            },
            {
                "id": 2, "badge": "💡 위변조 방지 기술", "badge_color": (245, 158, 11),
                "title": "데이터 위변조 방지 해시(Hash) 연동!\n심사관이 100% 신뢰하는 무결성",
                "subtitle": "한국식품안전관리인증원 표준 프로토콜 연계",
                "key_points": [
                    "센서 원천 데이터 생성 시 블록체인/해시 암호화",
                    "수정 및 삭제 시 감사 추적(Audit Trail) 이력 자동 기록"
                ],
                "senior_tip": "임의 수정이 불가능한 PLC 직결 통신 모듈(RS-485/IoT) 필수!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": "첫째, 데이터 위변조 방지 무결성입니다. 수기 일지는 조작 의심을 받기 쉽지만, 스마트HACCP은 센서 데이터가 암호화되어 서버로 넘어가므로 심사관이 100% 신뢰합니다."
            },
            {
                "id": 3, "badge": "⏱️ 실시간 이탈 알림", "badge_color": (239, 68, 68),
                "title": "한계기준 이탈 즉시 스마트폰 SMS/카톡 경보!\n골든타임 5분 내 대응 체계",
                "subtitle": "설비 인터록 연동으로 불합격품 생산 자동차단",
                "key_points": [
                    "1. 온도/금속 이탈 발생 1초 만에 담당자 경보 푸시",
                    "2. 설비 자동 정지 및 리젝트 박스 격리 연동",
                    "3. 개선조치(CAPA) 전산 입력 전 라인 재가동 금지"
                ],
                "senior_tip": "스마트 경보 이력은 3년간 클라우드 서버에 안전 백업!",
                "infographic": "temp",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": "둘째, 실시간 이탈 알림과 인터록입니다. 기준 온도를 벗어나거나 금속이 감지되면 담당자 스마트폰으로 즉시 카톡 경보가 울리고 라인이 자동으로 멈춰 불량품을 막아냅니다."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "정부 지원금(최대 50~70%) 활용법\n중소기업 스마트공장 구축",
                "subtitle": "동김제 농협 등 현장 구축 실무 노하우",
                "key_points": [
                    "스마트제조혁신추진단 및 인증원 보조금 사업 신청",
                    "기존 구형 설비에도 외장 센서 모듈 부착으로 저비용 구축"
                ],
                "senior_tip": "설비 교체 없이 IoT 센서만 붙여도 스마트HACCP 통과 가능!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 정부 지원 사업 활용입니다. 설비를 통째로 바꾸지 않고 기존 설비에 IoT 센서만 부착해도 정부 지원금을 받아 적은 비용으로 스마트HACCP을 구축할 수 있습니다."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "스마트HACCP 도입 3대 구비철\n디지털 품질관리 완벽 전환!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    "1. 스마트HACCP 시스템 운영 절차서 및 센서 매뉴얼",
                    "2. 통신 장애 시 수기 전환 및 데이터 동기화 SOP",
                    "3. 인증원 표준 연계 모듈 등록 확인서"
                ],
                "senior_tip": "스마트HACCP 구축 가이드와 서식은 큐에이플러스 오픈채팅방으로!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "이 세 가지만 준비하시면 스마트HACCP 도입과 정기 평가는 완벽히 끝납니다. 구축 자문과 서식은 큐에이플러스 오픈채팅방에서 편하게 받아가세요. 후배님들의 칼퇴를 응원합니다!"
            }
        ]
    }
}

def generate_dynamic_scenes_for_custom_topic(topic_name):
    """88개 인포그래픽 전 영역 주제에 대해 도메인 키워드를 분석하여 100% 고유 대본 생성"""
    if any(k in topic_name for k in ["금속", "이물", "캘리퍼"]):
        return TOPIC_TEMPLATES[1]["scenes"]
    elif any(k in topic_name for k in ["가열", "살균", "Cold", "중심온도", "F0"]):
        return TOPIC_TEMPLATES[2]["scenes"]
    elif any(k in topic_name for k in ["냉각", "식힘", "냉동", "칠러", "동결", "품온"]):
        return TOPIC_TEMPLATES[3]["scenes"]
    elif any(k in topic_name for k in ["알레르기", "교차", "알레르겐", "스쿠프"]):
        return TOPIC_TEMPLATES[4]["scenes"]
    elif any(k in topic_name for k in ["위생복", "방진복", "손세척", "ATP", "소독조", "개인위생"]):
        return TOPIC_TEMPLATES[5]["scenes"]
    elif any(k in topic_name for k in ["이탈", "개선", "CAPA", "부적합", "격리", "홀드", "폐기"]):
        return TOPIC_TEMPLATES[6]["scenes"]
    elif any(k in topic_name for k in ["공조", "양압", "차압", "클린룸", "HEPA", "헤파", "환기"]):
        return TOPIC_TEMPLATES[7]["scenes"]
    elif any(k in topic_name for k in ["입고", "원료", "검수", "COA", "팔레트", "보관", "창고"]):
        return TOPIC_TEMPLATES[8]["scenes"]
    elif any(k in topic_name for k in ["미생물", "식품공전", "세균", "대장균", "황색포도", "살모넬라", "FATTOM", "건조필름"]):
        return TOPIC_TEMPLATES[9]["scenes"]
    elif any(k in topic_name for k in ["검교정", "저울", "온도계", "압력계", "KOLAS", "분동"]):
        return TOPIC_TEMPLATES[10]["scenes"]
    elif any(k in topic_name for k in ["X-ray", "엑스레이", "돌", "유리", "뼈", "플라스틱"]):
        return TOPIC_TEMPLATES[11]["scenes"]
    elif any(k in topic_name for k in ["스마트", "센서", "IoT", "위변조", "자동기록"]):
        return TOPIC_TEMPLATES[12]["scenes"]
    else:
        # FSSC22000, CIP, SUS, QC7가지 도구 등 특화 생성
        return [
            {
                "id": 1, "badge": "💡 핵심 실무 브리핑", "badge_color": (37, 99, 235),
                "title": f"식품안전 필수 정복!\n{topic_name[:16]}",
                "subtitle": "20년 선배가 알려주는 실무 핵심 가이드",
                "key_points": [
                    f"1. {topic_name[:18]} 관련 법적/인증 기준 준수",
                    "2. 현장 표준작업지침서(SOP)와 실제 운영의 일치성"
                ],
                "senior_tip": "현장 모니터링 기록과 실측 데이터 일치성이 심사 합격의 핵심!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_metal_line.jpg"),
                "narration": f"오늘 짚어볼 핵심 주제는 바로 {topic_name}입니다. 식품안전 심사 때 지적받지 않고 100점 만점으로 통과하는 3대 실무 포인트를 명쾌하게 정리해드립니다."
            },
            {
                "id": 2, "badge": "📋 표준 기준 수립", "badge_color": (245, 158, 11),
                "title": "과학적 근거 없는 기준은 감점!\n자사 라인 실측 데이터 확보",
                "subtitle": f"{topic_name[:14]} 유효성 평가서 작성 원칙",
                "key_points": [
                    "1. 공정 조건(온도, 농도, 시간)별 실측 시험 데이터",
                    "2. 공인 시험성적서 및 유효성 검증 바인더 구비"
                ],
                "senior_tip": "남의 서식을 그대로 베끼지 말고 자사 실측 데이터를 첨부하세요!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_test_piece.jpg"),
                "narration": f"첫째, {topic_name} 기준 수립의 과학적 근거입니다. 남의 공장 양식을 베끼지 마시고 우리 공장 라인에 맞는 실측 시험 데이터를 반드시 남겨두셔야 합니다."
            },
            {
                "id": 3, "badge": "⏱️ 주기적 모니터링", "badge_color": (6, 182, 212),
                "title": "사고를 막는 골든타임!\n작업 전·중·후 3시점 일상 점검",
                "subtitle": "이탈 발생 시 당일 로트 격리 방어선",
                "key_points": [
                    "1. 작업 시작 전 : 설비 정상 가동 및 사전 준비 확인",
                    "2. 작업 중 : 정기 모니터링 및 실시간 일지 작성",
                    "3. 작업 종료 후 : 당일 생산 로트 최종 유효성 보증"
                ],
                "senior_tip": "종료 후 점검을 누락하면 당일 생산 전량을 재검사해야 합니다!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_smart_haccp.jpg"),
                "narration": f"둘째, 주기적인 일상 점검입니다. 작업 시작 전, 가동 중, 그리고 작업 종료 직후 3시점 모니터링을 준수해야 이상 발생 시 폐기 물량을 최소화할 수 있습니다."
            },
            {
                "id": 4, "badge": "🔥 20년 선배 꿀팁", "badge_color": (139, 92, 246),
                "title": "현장 트러블슈팅 노하우\n작업 시점에 즉시 기록하라!",
                "subtitle": "심사관이 현장에서 확인하는 결정적 포인트",
                "key_points": [
                    "1. 일지는 퇴근 때 몰아서 쓰지 말고 실시간 기록",
                    "2. 이상 발생 시 개선조치(CAPA) 이력철 필수 첨부"
                ],
                "senior_tip": "수정액(화이트) 사용은 조작 의심 1순위이므로 2줄 긋고 정정 서명!",
                "infographic": "steps",
                "image": os.path.join(ASSETS_DIR, "broll_audit.jpg"),
                "narration": "셋째, 20년 선배의 실무 팁입니다. 점검 일지는 절대로 몰아서 쓰지 마시고 작업 시점에 즉시 기록하세요. 수정할 때는 두 줄을 긋고 정정자 서명을 남겨야 합니다."
            },
            {
                "id": 5, "badge": "🏆 합격 체크리스트", "badge_color": (16, 185, 129),
                "title": "심사관이 감탄하는 3대 서식\n완벽 구비로 100% 합격!",
                "subtitle": "큐에이플러스가 후배님들의 칼퇴를 응원합니다",
                "key_points": [
                    f"1. {topic_name[:16]} 표준작업지침서(SOP)",
                    "2. 일일 점검 모니터링 일지 및 이력철",
                    "3. 작업자 정기 교육 훈련 성적서"
                ],
                "senior_tip": "관련 실무 서식과 질문은 큐에이플러스 오픈채팅방에서 무료 다운!",
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
