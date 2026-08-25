import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
} from 'remotion';

// 씬 구성 (3분 = 180초)
// 1. 인트로 (0-5초)
// 2. CCP란? (5-25초)
// 3. 한계기준 설정 (25-85초)
// 4. 유효성 검증 (85-160초)
// 5. 아웃트로 (160-180초)

const BRAND_COLOR = '#FF6B35';
const BG_COLOR = '#1A1A2E';
const TEXT_COLOR = '#FFFFFF';

// 인트로 씬
const IntroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({
    frame,
    fps,
    config: {
      damping: 100,
    },
  });

  const subtitleOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG_COLOR,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 60,
      }}
    >
      <div
        style={{
          transform: `scale(${titleScale})`,
          textAlign: 'center',
        }}
      >
        <h1
          style={{
            fontSize: 80,
            fontWeight: 'bold',
            color: BRAND_COLOR,
            margin: 0,
            lineHeight: 1.2,
          }}
        >
          CCP 한계기준
        </h1>
        <h2
          style={{
            fontSize: 60,
            fontWeight: 'bold',
            color: TEXT_COLOR,
            margin: '20px 0 0 0',
          }}
        >
          설정 & 검증
        </h2>
      </div>
      <p
        style={{
          fontSize: 40,
          color: TEXT_COLOR,
          opacity: subtitleOpacity,
          marginTop: 60,
          textAlign: 'center',
        }}
      >
        3분 완전정복
      </p>
    </AbsoluteFill>
  );
};

// CCP 정의 씬
const CCPDefinitionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 20], [0, 1]);
  const box1Offset = interpolate(frame, [30, 60], [100, 0]);
  const box2Offset = interpolate(frame, [50, 80], [100, 0]);
  const box3Offset = interpolate(frame, [70, 100], [100, 0]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG_COLOR,
        padding: 60,
        flexDirection: 'column',
      }}
    >
      <h2
        style={{
          fontSize: 70,
          fontWeight: 'bold',
          color: BRAND_COLOR,
          margin: '40px 0',
          opacity: titleOpacity,
        }}
      >
        CCP란?
      </h2>

      <div style={{ flex: 1, justifyContent: 'center', display: 'flex', flexDirection: 'column', gap: 40 }}>
        <div
          style={{
            backgroundColor: '#2E2E3E',
            padding: 40,
            borderRadius: 20,
            transform: `translateX(${box1Offset}px)`,
          }}
        >
          <h3 style={{ fontSize: 50, color: BRAND_COLOR, margin: '0 0 20px 0' }}>
            Critical Control Point
          </h3>
          <p style={{ fontSize: 40, color: TEXT_COLOR, margin: 0, lineHeight: 1.5 }}>
            중요관리점
          </p>
        </div>

        <div
          style={{
            backgroundColor: '#2E2E3E',
            padding: 40,
            borderRadius: 20,
            transform: `translateX(${box2Offset}px)`,
          }}
        >
          <p style={{ fontSize: 38, color: TEXT_COLOR, margin: 0, lineHeight: 1.6 }}>
            식품안전 위해요소를<br/>
            <span style={{ color: BRAND_COLOR, fontWeight: 'bold' }}>예방·제거·감소</span>시키는<br/>
            필수 관리 단계
          </p>
        </div>

        <div
          style={{
            backgroundColor: '#2E2E3E',
            padding: 40,
            borderRadius: 20,
            transform: `translateX(${box3Offset}px)`,
          }}
        >
          <p style={{ fontSize: 38, color: TEXT_COLOR, margin: 0, lineHeight: 1.6 }}>
            예: 가열, 냉각, 금속검출
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// 한계기준 설정 씬
const CriticalLimitScene: React.FC = () => {
  const frame = useCurrentFrame();

  const titleOpacity = interpolate(frame, [0, 20], [0, 1]);
  const step1Opacity = interpolate(frame, [30, 60], [0, 1]);
  const step2Opacity = interpolate(frame, [150, 180], [0, 1]);
  const step3Opacity = interpolate(frame, [300, 330], [0, 1]);
  const step4Opacity = interpolate(frame, [450, 480], [0, 1]);
  const step5Opacity = interpolate(frame, [600, 630], [0, 1]);
  const summaryOpacity = interpolate(frame, [750, 780], [0, 1]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG_COLOR,
        padding: 60,
        flexDirection: 'column',
      }}
    >
      <h2
        style={{
          fontSize: 70,
          fontWeight: 'bold',
          color: BRAND_COLOR,
          margin: '40px 0 60px 0',
          opacity: titleOpacity,
        }}
      >
        한계기준 설정 5단계
      </h2>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 30, justifyContent: 'center' }}>
        <div style={{ opacity: step1Opacity, backgroundColor: '#2E2E3E', padding: 35, borderRadius: 15 }}>
          <h3 style={{ fontSize: 48, color: BRAND_COLOR, margin: '0 0 15px 0' }}>
            1. 법적 기준 확인
          </h3>
          <p style={{ fontSize: 36, color: TEXT_COLOR, margin: 0, lineHeight: 1.5 }}>
            식품공전, 축산물공전 확인
          </p>
        </div>

        <div style={{ opacity: step2Opacity, backgroundColor: '#2E2E3E', padding: 35, borderRadius: 15 }}>
          <h3 style={{ fontSize: 48, color: BRAND_COLOR, margin: '0 0 15px 0' }}>
            2. 과학적 근거 수집
          </h3>
          <p style={{ fontSize: 36, color: TEXT_COLOR, margin: 0, lineHeight: 1.5 }}>
            논문, FDA, Codex 등 참고
          </p>
        </div>

        <div style={{ opacity: step3Opacity, backgroundColor: '#2E2E3E', padding: 35, borderRadius: 15 }}>
          <h3 style={{ fontSize: 48, color: BRAND_COLOR, margin: '0 0 15px 0' }}>
            3. 현장 적용 가능성
          </h3>
          <p style={{ fontSize: 36, color: TEXT_COLOR, margin: 0, lineHeight: 1.5 }}>
            설비 능력, 측정 가능 여부
          </p>
        </div>

        <div style={{ opacity: step4Opacity, backgroundColor: '#2E2E3E', padding: 35, borderRadius: 15 }}>
          <h3 style={{ fontSize: 48, color: BRAND_COLOR, margin: '0 0 15px 0' }}>
            4. 수치화
          </h3>
          <p style={{ fontSize: 36, color: TEXT_COLOR, margin: 0, lineHeight: 1.5 }}>
            온도, 시간, pH 등 측정 가능
          </p>
        </div>

        <div style={{ opacity: step5Opacity, backgroundColor: '#2E2E3E', padding: 35, borderRadius: 15 }}>
          <h3 style={{ fontSize: 48, color: BRAND_COLOR, margin: '0 0 15px 0' }}>
            5. 문서화
          </h3>
          <p style={{ fontSize: 36, color: TEXT_COLOR, margin: 0, lineHeight: 1.5 }}>
            HACCP 계획서에 명시
          </p>
        </div>

        <div style={{ opacity: summaryOpacity, backgroundColor: BRAND_COLOR, padding: 40, borderRadius: 15, marginTop: 30 }}>
          <p style={{ fontSize: 42, color: '#FFFFFF', margin: 0, fontWeight: 'bold', textAlign: 'center' }}>
            쉽게 말하면: 안전하다고<br/>증명할 수 있는 숫자 정하기
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// 유효성 검증 씬
const ValidationScene: React.FC = () => {
  const frame = useCurrentFrame();

  const titleOpacity = interpolate(frame, [0, 20], [0, 1]);
  const type1Opacity = interpolate(frame, [40, 70], [0, 1]);
  const type2Opacity = interpolate(frame, [200, 230], [0, 1]);
  const type3Opacity = interpolate(frame, [360, 390], [0, 1]);
  const exampleOpacity = interpolate(frame, [520, 550], [0, 1]);
  const tipOpacity = interpolate(frame, [680, 710], [0, 1]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG_COLOR,
        padding: 60,
        flexDirection: 'column',
      }}
    >
      <h2
        style={{
          fontSize: 70,
          fontWeight: 'bold',
          color: BRAND_COLOR,
          margin: '40px 0 60px 0',
          opacity: titleOpacity,
        }}
      >
        유효성 검증 3가지
      </h2>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 40, justifyContent: 'center' }}>
        <div style={{ opacity: type1Opacity, backgroundColor: '#2E2E3E', padding: 40, borderRadius: 15 }}>
          <h3 style={{ fontSize: 52, color: BRAND_COLOR, margin: '0 0 20px 0' }}>
            1. 과학적 검증
          </h3>
          <p style={{ fontSize: 38, color: TEXT_COLOR, margin: 0, lineHeight: 1.5 }}>
            논문, 실험 데이터로<br/>
            "이 기준이 안전하다" 증명
          </p>
        </div>

        <div style={{ opacity: type2Opacity, backgroundColor: '#2E2E3E', padding: 40, borderRadius: 15 }}>
          <h3 style={{ fontSize: 52, color: BRAND_COLOR, margin: '0 0 20px 0' }}>
            2. 현장 검증
          </h3>
          <p style={{ fontSize: 38, color: TEXT_COLOR, margin: 0, lineHeight: 1.5 }}>
            우리 현장에서 실제로<br/>
            이 기준 지킬 수 있는지 테스트
          </p>
        </div>

        <div style={{ opacity: type3Opacity, backgroundColor: '#2E2E3E', padding: 40, borderRadius: 15 }}>
          <h3 style={{ fontSize: 52, color: BRAND_COLOR, margin: '0 0 20px 0' }}>
            3. 모니터링 검증
          </h3>
          <p style={{ fontSize: 38, color: TEXT_COLOR, margin: 0, lineHeight: 1.5 }}>
            기록이 정확한지,<br/>
            관리가 제대로 되는지 확인
          </p>
        </div>

        <div style={{ opacity: exampleOpacity, backgroundColor: '#3A3A4E', padding: 40, borderRadius: 15 }}>
          <h4 style={{ fontSize: 44, color: BRAND_COLOR, margin: '0 0 15px 0' }}>
            예시: 가열 CCP
          </h4>
          <p style={{ fontSize: 36, color: TEXT_COLOR, margin: 0, lineHeight: 1.6 }}>
            중심온도 75℃ 1분 → 논문 확인 ✓<br/>
            실제 측정 3회 테스트 ✓<br/>
            기록지 점검 ✓
          </p>
        </div>

        <div style={{ opacity: tipOpacity, backgroundColor: BRAND_COLOR, padding: 40, borderRadius: 15 }}>
          <p style={{ fontSize: 42, color: '#FFFFFF', margin: 0, fontWeight: 'bold', textAlign: 'center' }}>
            💡 검증 없이 한계기준만<br/>
            설정하면 심사 탈락!
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// 아웃트로 씬
const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: {
      damping: 100,
    },
  });

  const ctaOpacity = interpolate(frame, [60, 90], [0, 1]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG_COLOR,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 60,
      }}
    >
      <div style={{ textAlign: 'center', transform: `scale(${scale})` }}>
        <h2
          style={{
            fontSize: 70,
            fontWeight: 'bold',
            color: BRAND_COLOR,
            margin: 0,
            lineHeight: 1.3,
          }}
        >
          오늘 하나만<br/>
          기억하세요
        </h2>
        <p
          style={{
            fontSize: 50,
            color: TEXT_COLOR,
            marginTop: 60,
            lineHeight: 1.5,
          }}
        >
          한계기준 = 숫자<br/>
          유효성 검증 = 증거
        </p>
      </div>

      <div
        style={{
          opacity: ctaOpacity,
          position: 'absolute',
          bottom: 120,
          textAlign: 'center',
        }}
      >
        <p
          style={{
            fontSize: 38,
            color: TEXT_COLOR,
            margin: 0,
          }}
        >
          궁금한 거 있으면<br/>
          편하게 물어보세요
        </p>
        <div
          style={{
            marginTop: 30,
            padding: '25px 50px',
            backgroundColor: BRAND_COLOR,
            borderRadius: 50,
            display: 'inline-block',
          }}
        >
          <p style={{ fontSize: 42, color: '#FFFFFF', margin: 0, fontWeight: 'bold' }}>
            1:1 컨설팅 신청
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// 메인 컴포지션
export const CCPVideo: React.FC = () => {
  return (
    <AbsoluteFill>
      <Sequence from={0} durationInFrames={150}>
        <IntroScene />
      </Sequence>
      <Sequence from={150} durationInFrames={600}>
        <CCPDefinitionScene />
      </Sequence>
      <Sequence from={750} durationInFrames={1800}>
        <CriticalLimitScene />
      </Sequence>
      <Sequence from={2550} durationInFrames={2250}>
        <ValidationScene />
      </Sequence>
      <Sequence from={4800} durationInFrames={600}>
        <OutroScene />
      </Sequence>
    </AbsoluteFill>
  );
};
