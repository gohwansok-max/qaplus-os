# qa-shorts — QA+ 일일 모션그래픽 쇼츠 (Remotion)

주제 1개 → 씬 JSON(LLM) → Edge-TTS → Remotion 렌더 → 1080x1920 MP4 (40~60초)

| 씬 | 용도 |
|:--|:--|
| hook | 3초 후킹 (질문/반전) |
| stat | 출처 근거 수치 카운트업 (출처에 없는 숫자면 검증 단계에서 탈락) |
| flow | 공정·절차 순차 점등 |
| compare | 흔한 실수 ↔ 올바른 방법 |
| checklist | 체크 애니메이션 |
| outro | 오늘의 한 줄 + 무료 오픈채팅 안내 |

- 파이프라인: `python scripts/qa_motion_shorts.py --topic "주제"`
- 일일 자동: `.github/workflows/daily_qa_video.yml` → `daily_qa_autopilot.py` (QA_RENDERER=remotion 기본, `legacy`로 롤백)
- 스키마 예시: `sample/script.json` / 스튜디오 미리보기: `npm run dev`
- 폰트는 시스템 `fonts-noto-cjk` 사용 (렌더 시 외부 다운로드 없음)

## LLM 연결 (Claude 구독 전용)
- 대본은 **Claude 구독 모델(Claude Code CLI)만** 작성합니다. 시크릿: `CLAUDE_CODE_OAUTH_TOKEN` ← 로컬에서 `claude setup-token`
- 다른 모델·로컬 대체 대본으로 조용히 넘어가지 않습니다. Claude 생성이 실패하면 워크플로우가 실패하고 텔레그램 알림이 갑니다. (임시 허용: `QA_ALLOW_FALLBACK=1`)
- 인포그래픽 본문: `knowledge/infographic_texts.json`(Drive OCR, 큐 id별)을 1차 자료로 대본 프롬프트에 주입. 본문이 없거나 80자 미만이면 공식 출처만 사용.
