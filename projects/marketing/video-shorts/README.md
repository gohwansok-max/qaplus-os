# HACCP CCP 숏츠 영상 (Remotion)

## 생성 파일
- `src/CcpShort.tsx` — 메인 컴포지션 (57초, 1080x1920)
- `src/CcpLimitValidation.tsx` — CCP 한계기준 설정·유효성검증 본편 (정확히 3분, 1080x1920)
- `src/CcpImageOneMinute.tsx` — GPT Image 2 현장 이미지 기반 본편 (정확히 1분, 1080x1920)
- `src/Thumbnail.tsx` — 커버 이미지
- `src/scenes/` — 6개 씬 (Hook, Define, Core1, Core2, Core3, CTA)
- `src/components/` — 재사용 UI (Background, FadeUp, Chip, Hud, SceneShell)
- `src/lib/timeline.ts` — 타임라인 정의
- `src/lib/limitValidationTimeline.ts` — 3분 본편 타임라인 (5,400프레임)
- `src/lib/imageOneMinuteTimeline.ts` — 이미지 본편 타임라인 (1,800프레임)
- `public/assets/` — GPT Image 2 생성 현장 이미지 4종
- `src/theme.ts` — 디자인 토큰

## 대본 출처
`outputs/2026/08/24/[숏츠]_HACCP_CCP_3분완전정복.md`

## 실행

```bash
# 프리뷰 (브라우저에서 실시간 편집)
npm run dev

# MP4 렌더링 (out/ccp-short.mp4)
npm run render

# CCP 한계기준·유효성검증 3분 본편 (out/ccp-limit-validation-3min.mp4)
npm run render:limit

# GPT Image 2 이미지 기반 1분 본편 (out/ccp-image-one-minute.mp4)
npm run render:image

# 썸네일 PNG (out/thumbnail.png)
npm run thumbnail
```

## 특징
- **무음 영상** — 자막만으로 완결, TTS/BGM 없음
- **읽는 속도 기준** — 한 줄당 1.1~1.4초 확보
- **3색 시스템** — 경고(빨강) / 안전(초록) / 강조(노랑)로 시선 집중
- **시스템 폰트** — 맑은 고딕 기반, 렌더 시 네트워크 의존 없음
- **품질 기준 준수** — CTA 1개만 노출 (댓글 "CCP" 남기기)
