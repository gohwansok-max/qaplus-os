# Skills (업무 매뉴얼)

> 반복되는 업무를 체계화한 스킬 문서입니다.
> AI 에이전트가 이 매뉴얼을 참고하여 일관된 품질로 업무를 수행합니다.
>
> **각 스킬은 `검수 기준(E1, E2, ...)`을 포함**하여, AI가 결과물을 스스로 채점할 수 있습니다.

---

## 풀 공개 스킬 (5개)

### content/ — 콘텐츠 제작
| 스킬 | 파일 | 해결하는 문제 |
|:---|:---|:---|
| 릴스 대본 | [`content/reels-script/SKILL.md`](content/reels-script/SKILL.md) | "릴스 대본 구조를 모르겠다" — 후킹 12타입 + 역순 작성법, 3버전 + 캡션 3버전 |

### strategy/ — 경영 전략
| 스킬 | 파일 | 해결하는 문제 |
|:---|:---|:---|
| 주간 브리핑 | [`strategy/weekly-briefing/SKILL.md`](strategy/weekly-briefing/SKILL.md) | "회사가 잘 돌아가는지 5분 안에 보고 싶다" — 위험 신호 우선 + 시스템 위생 |
| 월간 사업 리뷰 | [`strategy/monthly-business-review/SKILL.md`](strategy/monthly-business-review/SKILL.md) | "월말마다 멘붕" — OKR/P&L/AI 운영 비용/전략 조정 원스톱 |

### marketing/ — 마케팅+세일즈
| 스킬 | 파일 | 해결하는 문제 |
|:---|:---|:---|
| 세일즈 퍼널 분석 | [`marketing/sales-analysis/SKILL.md`](marketing/sales-analysis/SKILL.md) | "매출이 안 나오는 진짜 원인을 모르겠다" — C.L.O.S.E 5단계 진단 |

### edutech/ — 교육 상품
| 스킬 | 파일 | 해결하는 문제 |
|:---|:---|:---|
| 강의/코스 설계 | [`edutech/course-design/SKILL.md`](edutech/course-design/SKILL.md) | "커리큘럼 막연하다" — L.E.A.R.N 프레임워크 + 완강률 부스터 |

### setup/ — 초기 셋업
| 스킬 | 파일 | 해결하는 문제 |
|:---|:---|:---|
| `/setup` 인터뷰 | [`setup/SKILL.md`](setup/SKILL.md) | "처음 받았는데 뭐부터?" — 사업 인터뷰 → 22개 파일 자동 생성 |

---

## 직접 스킬 추가하기

반복되는 업무를 3번 이상 했다면, 스킬로 만드세요.

### 스킬 작성 구조

```markdown
---
name: my-skill
description: 이 스킬의 한 줄 설명
when_to_use: 호출될 키워드들
user-invocable: true
allowed-tools: Read, Grep, Glob, Write
---

# 스킬 제목

## 언제 쓰는가
## 0단계: 서브에이전트 활성화 (필요 시)
## 1단계: 자산 로드
## 2단계: 작업 수행
## 3단계: 검증 (셀프 체크리스트)

## 검수 기준
| ID | 기준 | 합격 조건 | 가중치 |
|:---|:---|:---|:---:|
| E1 | ... | ... | 필수 |

## 학습 기록
<!-- CEO 피드백 반영 -->
```

---

## 스킬 호출 방식

### 방법 1: 슬래시 커맨드 (권장)
`.claude/commands/` 하위에 연결된 커맨드가 있으면 `/스킬명`.

### 방법 2: 자연어 호출
Claude가 `when_to_use` 키워드를 감지하면 자동 발동.

### 방법 3: 서브에이전트 + 스킬 조합
김이사(cso)나 CMO가 Tier 2 회의 중 스킬 파일을 Read하여 절차를 따름.

---

## 이 레포 vs 본사(에이나우) 스킬 차이

본사는 20+ 개의 스킬을 운영 중입니다. 이 레포는 그 중 **수강생이 즉시 활용 가능한 5개를 풀 공개**합니다. 나머지 스킬(자동 콘텐츠 팩토리, 인터뷰 카드뉴스 등)은 본사 특화 데이터/인프라 의존도가 높아 직접 공개 대신 부트캠프에서 다룹니다.
