# v3 Rollout Plan — 동결 설계

> Phase A는 이번 세션에서 완료. B~D는 이 문서에 설계를 고정하고, 다음 세션에서는 **Edit만** 하면 되도록 실제 파일 경로/섹션명/현재 문구를 박아둠.
> 정찰 기준: 2026-04-09.

---

## Phase A 완료 (2026-04-09)

- `agents/_shared/cognitive-core.md` v3.0 버전 주석 추가 (L1)
- §7 표준 보고 템플릿 v3 9섹션으로 교체 (L167~)
- `agents/_shared/routing-map.yaml` 신설 (10개 route)
- 8명 임원 README: `### D. 보고 템플릿` → `### D. §9 도메인 부록 (v3 스키마 연동)` 제목 정렬
  - cmo L67 / cfo L64 / cto L64 / cdo L67 / coo L64 / cco L64 / cpo L64 / cxo L64
- **누락 로그**: `agents/cso/README.md`에는 A~D 부록 섹션이 없음 → Phase D2에서 신설 필요

---

## Phase B (2주차) — 공유 메모리 + 자동 학습 루프 + Pre-mortem

### B1. 공유 메모리 슬롯
- **생성**: `tasks/session_memo/.gitkeep` (빈 파일)
- **생성**: `tasks/session_memo/README.md` — "세션 간 임원 메모 누적. 파일명: `YYYY-MM-DD_{임원}.md`"
- **수정**: `agents/c-suite-protocol.md` — 파일 하단 (현재 L99 이후)에 `## 공유 메모리 규칙` 섹션 append
  - 내용 초안:
    ```
    ## 공유 메모리 (세션 간 인수인계)
    - Tier 2/3 회의 종료 시 각 임원은 `tasks/session_memo/{date}_{임원}.md`에 3줄 이내 메모 저장
    - 다음 세션 시작 시 김이사가 해당 폴더 스캔 → 관련 메모 자동 로드
    - 14일 이상 지난 메모는 아카이브 이동
    ```

### B2. 자동 학습 루프 (Feedback Routing)
- **수정 대상**: `agents/_shared/cognitive-core.md` §6 (L127~164)
- **현재 §6 구조**: 6.1 lessons 자동 로드 / 6.2 새 교훈 기록 / 6.3 예측 의무
- **추가**: §6.4 신설
  - `old_string`: "→ 6개월 후 **임원별 적중률**이 데이터로 측정 가능.\n\n---"
  - `new_string`:
    ```
    → 6개월 후 **임원별 적중률**이 데이터로 측정 가능.

    ### 6.4 Feedback Routing (CEO 피드백 자동 학습)

    CEO 피드백 발생 시 다음을 자동 수행:
    1. 피드백 대상 임원 식별 → 해당 lessons 파일에 5-Whys 템플릿으로 즉시 append
    2. 동일 도메인 최근 3건 조회 → 반복 패턴이면 "패턴 경보" 태그
    3. 14일 후 재리뷰 일정을 `tasks/predictions.md`에 P-XXX로 등록
    4. 다음 세션 시작 시 김이사가 "미해결 피드백" 섹션으로 선제 브리핑

    ---
    ```

### B3. Pre-mortem §2.5 신설
- **수정 대상**: `agents/_shared/cognitive-core.md` §2 (L44~59)
- **현재**: 2.1 2차적 사고 / 2.2 악마의 변호인 / 2.3 역전 사고 / 2.4 기회비용
- `old_string`: "### 2.4 기회비용 사고 (Opportunity Cost)\n\"이 리소스를 다른 곳에 쓰면 더 나은가?\" 절대 수익이 아닌 **상대 수익**으로 판단.\n\n---"
- `new_string`:
  ```
  ### 2.4 기회비용 사고 (Opportunity Cost)
  "이 리소스를 다른 곳에 쓰면 더 나은가?" 절대 수익이 아닌 **상대 수익**으로 판단.

  ### 2.5 Pre-mortem (사전 부검)
  "6개월 뒤 이 결정이 실패로 판명됐다고 가정하자. 부검 보고서를 지금 써라."
  - 실패 원인 3가지를 과거형으로 기술
  - 각 원인별 사전 차단 장치(Pre-mortem Guard) 1개씩 설계
  - Tier 2/3 결정은 Pre-mortem 의무 / Tier 1은 선택

  ---
  ```

---

## Phase C (3주차) — 충돌 해소 + 라운드 구조 + 예측 추적

### C1. 충돌 해소 5단계 트리
- **대상 파일**: `agents/c-suite-protocol.md` L75 "## 임원 충돌 시 처리" 섹션
- **현재 내용**: 데이터 우선 / 우선순위 매트릭스 / 소수 의견 폐기 금지 (3줄)
- **교체 초안**: 5단계 Escalation Tree
  1. 데이터 일치도 비교 (근거 강도)
  2. 우선순위 매트릭스 적용 (매출 > 접점 > 브랜딩 > 운영)
  3. Pre-mortem 교차 검토 (실패 시나리오가 더 구체적인 쪽)
  4. 김이사 중재 (확신도 % 가중)
  5. CEO 에스컬레이션 (1~4로 해소 불가 시만)

### C2. 라운드 구조 R1.5 삽입
- **대상 파일**: `agents/c-suite-protocol.md` L58 "Tier 3" 섹션
- **현재**: R1 독립 분석 → R2 반박 라운드 → 결론
- **추가**: R1과 R2 사이에 **R1.5 Steelman 라운드** — 각 임원이 다른 임원의 의견 중 가장 강한 것을 골라 보강 (= 약한 반박 방지)

### C3. 예측·책임 추적 시스템
- **생성**: `tasks/predictions/` 폴더 + 9개 파일 (`cso.md`, `cmo.md`, ..., `cxo.md`)
- **생성**: `tasks/predictions/credibility.yaml` — 임원별 적중률 집계 스키마
  ```yaml
  # 스키마 초안
  executives:
    cso: {total: 0, hit: 0, miss: 0, pending: 0, credibility: null}
    cmo: {total: 0, hit: 0, miss: 0, pending: 0, credibility: null}
    # ... 9명
  updated_at: null
  ```
- **연동**: §6.3 예측 의무가 임원별 파일로 자동 라우팅되도록 cognitive-core 업데이트

---

## Phase D (4주차) — 통합 + 재점검 + 릴리스

### D1. collaboration-protocol.md 통합 문서 신설
- **생성**: `agents/collaboration-protocol.md` (현재 없음 — 신설)
- **구조 §1~§8**:
  1. 소집 규칙 (routing-map.yaml 참조)
  2. 병렬 호출 프로토콜 (Task tool)
  3. 충돌 해소 5단계 트리 (C1에서 이관)
  4. 공유 메모리 규칙 (B1에서 이관)
  5. Steelman R1.5 (C2에서 이관)
  6. Pre-mortem 의무 범위 (B3 연동)
  7. 예측·책임 추적 (C3 연동)
  8. CEO 에스컬레이션 기준

### D2. 임원 README 재점검
- **CSO README 부록 신설**: A~D 섹션 추가 (현재 누락)
  - A. CSO 전용 MUST Disagree (이미 본 세션 프롬프트에 정의된 8조건 활용)
  - B. 내면 참모진 4명 (이미 정의됨)
  - C. 판단 렌즈 8개 (C-Suite 매트릭스)
  - D. §9 도메인 부록 (v3 스키마 연동)
- 나머지 8명: D 섹션 내부 보고 템플릿 텍스트가 구 스키마면 v3 9섹션으로 동기화 확인

### D3. tasks/todo.md 업데이트
- G2 게이트에 v3 검증 체크리스트 3개 추가:
  - [ ] 9명 전원 v3 9섹션 보고
  - [ ] routing-map.yaml 10개 route 매칭
  - [ ] Pre-mortem Tier 2/3 의무 준수
- 드라이런 결과 기록란 추가

---

## 리스크 체크리스트 (Phase B~D 실행 전)

- [ ] 임원 캐릭터 톤/참모진 네이밍 보존 (섹션 구조만 변경)
- [ ] 기존 v2 보고서와 역호환 (§9는 선택)
- [ ] routing-map.yaml은 **참고용**, 김이사 판단 override 가능 명시
- [ ] CSO README 부록 추가 시 기존 "캐릭터/역할/핵심질문/판단방식/참모진/작동원칙/호출방법" 섹션 전부 보존
