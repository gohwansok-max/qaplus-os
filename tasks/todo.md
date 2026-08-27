# 할 일 목록 (Tasks & To-Do)

> 마지막 업데이트: 2026-08-25  
> AI CEO OS와 함께 관리하는 작업 리스트입니다.

---

## 🚀 완료된 핵심 작업 (Completed)

- [x] `/setup` 12개 질문 정밀 인터뷰 및 AI CEO OS 두뇌 구축
- [x] `CLAUDE.md`, `context/` 5개 지침서, `CEO/` 목표 관리 문서 구축
- [x] 한국 식품공장 기준(파란색 일체형 방진복) B-Roll 이미지 4종 생성
- [x] 20년 선배 한국어 음성(TTS: ko-KR-InJoonNeural) 합성 파이프라인 구축
- [x] 1080x1920 세로형 쇼츠 MP4 비디오 렌더러 및 고대비 텍스트 가독성 최적화
- [x] **일일 자동 발행 오토파일럿 엔진 구축 (`scripts/daily_qa_autopilot.py`)**
- [x] **30일치 HACCP/QA 토픽 큐 데이터베이스 구축 (`knowledge/qa_topics_queue.json`)**
- [x] **원클릭 수동 실행기 (`scripts/run_daily_now.bat`) & 윈도우 스케줄러 등록기 (`scripts/register_daily_scheduler.ps1`) 구비**

---

## 📋 앞으로 운영할 루틴

- [ ] 매일 아침 자동 생성된 `outputs/videos/` 폴더의 MP4 영상을 유튜브 쇼츠 / 인스타 릴스 / 오픈채팅방에 업로드
- [ ] 신규 실무 토픽이나 다루고 싶은 주제를 `knowledge/qa_topics_queue.json`에 추가

## 🆕 2026-08-27 — 블로그 자동화 팀 구축 (진행 중)

- [x] `qaplus-haccp.blogspot.com` 실제 게시글 분석 → `projects/marketing/context/blog-style-guide.md` 작성
- [x] Blogger/Google SEO 리서치 → `projects/marketing/context/blog-seo-guide.md` 작성
- [x] 서브에이전트 4개 구축: `blog-researcher`, `blog-writer`, `blog-image`, `blog-assembler` (`.claude/agents/`)
- [x] 팀장 스킬 `projects/marketing/skills/blog-osmu/SKILL.md` 작성 (4단계 오케스트레이션)
- [ ] **미검증**: 실제로 `blog-osmu`를 1회 실행해 최종 HTML까지 나오는지 확인 (아직 실행 안 해봄)
- [ ] Blogger 발행은 사용자 본인이 직접 (계정 인증 필요 — 자동화 불가)
- [ ] n8n 연동은 보류 (사용자 요청: "n8n은 나중에")
- [ ] **주의**: `D:\다운로드(D)\텔레그램 자동화 폴더\qaplus-os`는 같은 저장소의 중복 로컬 클론 — 이 G드라이브 위치가 정본. D: 사본은 정리 필요 (사용자 확인 후 삭제 권장)

## 🆕 2026-08-27 (계속) — n8n 완전 자동화 + 텔레그램 연동 준비

- [x] GitHub Actions 뼈대 `.github/workflows/daily_blog.yml` 생성 — **비활성 상태(cron 주석 처리)**, repository_dispatch(`generate_blog`)만 열어둠
- [x] n8n 임포트용 워크플로 `n8n-workflows/daily-blog-trigger.json` 생성 (Schedule Trigger → GitHub dispatches API 호출)
- [ ] **블로킹**: 다른 세션이 만드는 `scripts/daily_blog_autopilot.py` (Claude API 글 생성 + Blogger API 발행) 완성 대기 중
- [ ] 스크립트 완성 후: daily_blog.yml의 스크립트 경로 확정 + cron 주석 해제
- [ ] n8n 크레덴셜 설정 필요: GitHub PAT(`QA_DISPATCH_TOKEN`과 동일한 값)를 n8n의 `githubDispatchToken` 크레덴셜로 등록 — **사용자 본인이 직접** (Secret 값은 재조회 불가)
- [ ] Blogger API 자동 발행을 쓰려면 `BLOGGER_BLOG_ID` / `BLOGGER_CLIENT_ID` / `BLOGGER_CLIENT_SECRET` / `BLOGGER_REFRESH_TOKEN` GitHub Secret 등록 필요 (Google OAuth 동의 절차 — 사용자 직접)
