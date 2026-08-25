# execution/ — 비즈니스 로직 스크립트

> 매출 분석, 콘텐츠 데이터 수집, KPI 계산 등 **숫자를 다루는 스크립트** 자리.
> Zero-Inference Rule: AI는 숫자를 직접 계산하지 않고, 이 폴더의 스크립트 결과를 인용합니다.

## 구조 (예시)

```
execution/
├── reels_calculate_metrics.py   ← 릴스 지표 계산
├── youtube_fetch_stats.py       ← 유튜브 데이터 수집
├── sheets_sync.py               ← Google Sheets 동기화
├── ads_performance_check.py     ← 광고 성과 체크
└── sanitize_for_public.py       ← 민감정보 마스킹 (이미 포함)
```

## 왜 이 폴더가 중요한가

**Zero-Inference Rule** 때문입니다:

- ❌ AI가 "대략 50만원 정도일 것 같습니다"라고 추론 → 잘못된 의사결정
- ✅ AI가 `execution/sales_calculate.py`를 호출 → 실제 데이터 → 정확한 보고

## 김이사가 사용하는 방식

```
CEO: "이번 달 매출 분석해줘"
김이사: "execution/sales_monthly.py 실행 필요합니다"
       → 스크립트 실행
       → 결과 데이터 받음
       → 분석 보고서 작성
```

## 처음 만들 스크립트 추천

1. **데이터 수집기** — 인스타/유튜브/카페 데이터 자동 수집
2. **매출 계산기** — 일별/월별 매출 집계
3. **KPI 대시보드** — 핵심 지표 한눈에

## 포함된 도구

- **`sanitize_for_public.py`** — 민감정보(API 키, 실명, 연락처) 마스킹 검사. GitHub 푸시 전 실행 권장.
