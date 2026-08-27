---
name: blog-osmu
description: QA+ 블로그 자동화 팀장 스킬. 주제 1개(또는 큐에서 자동 선택)를 받아 blog-researcher → blog-writer → blog-image → blog-assembler 4개 서브에이전트를 순서대로 지휘해 Blogger에 바로 발행 가능한 최종본을 만든다. "블로그 자동화", "블로그 글 만들어줘", "오늘 블로그" 요청에 사용.
user-invocable: true
allowed-tools: Read, Write, Grep, Glob, Bash
---

# blog-osmu — QA+ 블로그 자동화 팀장

> 유튜브 쇼츠 자동화(`daily_qa_autopilot.py`)와 같은 주제 자산(`knowledge/qa_topics_queue.json`)을 공유하는
> **블로그 전용 OSMU 파이프라인**. 4명의 서브에이전트를 순서대로 소집한다.

---

## 팀 구성

| 순서 | 서브에이전트 | 역할 |
|:---:|:---|:---|
| 1 | `blog-researcher` | 법령/뉴스/유튜브/타블로그 리서치 (출처 필수) |
| 2 | `blog-writer` | `blog-style-guide.md` 문체로 본문 작성 |
| 3 | `blog-image` | 본문 캡션 기반 이미지 프롬프트/생성 |
| 4 | `blog-assembler` | Blogger용 최종 HTML 조립 + 검수 |

## 주제 선택 로직

1. CEO가 주제를 직접 지정하면 그 주제를 사용한다.
2. 지정하지 않으면 `knowledge/qa_topics_queue.json`에서 `status: "pending"`인 항목 중 **아직 블로그로 만들지 않은 것**을 선택한다.
   - "블로그로 만들었는지"는 해당 날짜의 `outputs/{연도}/{월}/{일}/blog_log.json`에 같은 `topic`이 있는지로 판단한다 (video 파이프라인의 `status`/`rendered_file` 필드는 절대 수정하지 않는다).
3. 큐에 마땅한 주제가 없으면 CEO에게 최근 뉴스/트렌드 기반 신규 주제 후보 3개를 제안하고 선택을 받는다 — 임의로 주제를 만들어 진행하지 않는다.

## 실행 순서 (무중단 원칙)

`공통.md`의 "무중단 실행 원칙"에 따라 Phase 1→4를 중간 승인 없이 이어서 실행한다. 단, CEO가 "단계별로 확인할게"라고 명시하면 각 단계 후 결과를 보고하고 대기한다.

1. `blog-researcher` 소집 → 리서치 산출물 생성
2. `blog-writer` 소집 (리서치 산출물을 입력으로 전달) → 본문 산출물 생성
3. `blog-image` 소집 (본문의 `image_captions` 전달) → 이미지 산출물 생성
4. `blog-assembler` 소집 (본문 + 이미지 전달) → 최종 HTML + `blog_log.json` 갱신

## 완료 후 보고

```markdown
## 블로그 자동화 완료: {주제}

- 최종본: outputs/{연도}/{월}/{일}/[블로그최종]_{주제}.html
- 검수 결과: [전항목 합격 | N건 플래그]
- 다음 행동: 이 HTML을 Blogger 편집기(HTML 모드)에 붙여넣고 이미지 업로드 후 직접 발행해주세요.
```

## 검수 기준
| ID | 기준 | 합격 조건 |
|:---|:---|:---:|
| P1 | 4단계 전부 실행 | 리서치→글쓰기→이미지→조립 산출물 모두 존재 |
| P2 | blog-assembler 검수(A1~A5) 통과 | 필수 항목 전체 합격 |
| P3 | 주제 중복 없음 | 같은 날짜에 동일 topic으로 blog_log.json 중복 기록 없음 |

## 향후 확장 (미구성 — 별도 승인 필요)
- n8n을 통한 Blogger 임시저장 자동 업로드 (Blogger API 연동 + 계정 인증 필요, 사용자 직접 설정)
- 매일 아침 자동 실행 스케줄 (`scheduled-tasks` MCP 또는 GitHub Actions cron — 기존 `daily_qa_video.yml` 패턴 참고 가능)

## 호출 방법
```
"블로그 자동화" / "오늘 블로그 만들어줘" / "블로그 글 만들어줘 [주제]"
```
