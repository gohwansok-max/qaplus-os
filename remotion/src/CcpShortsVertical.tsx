import React from 'react';
import { Composition, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig, Img, staticFile } from 'remotion';

export const SHORTS_TOTAL_FRAMES = 1770; // 59 sec @ 30fps
export const SHORTS_FPS = 30;

export interface ShortsSceneData {
  startFrame: number;
  duration: number;
  badge: string;
  badgeBg: string;
  title: string;
  subtitle: string;
  keyPoints: string[];
  seniorTip: string;
  image: string;
  accent: string;
}

export const KOREAN_SHORTS_SCENES: ShortsSceneData[] = [
  {
    startFrame: 0,
    duration: 330, // 11s
    badge: '🚨 심사관 지적 1위',
    badgeBg: '#ef4444',
    title: 'HACCP 심사 탈락 위기?\n금속검출기 검증 주기!',
    subtitle: '20년 선배가 알려주는 3분 합격 공식',
    keyPoints: [
      '검증 주기 누락 시 당일 생산 전량 보류/폐기',
      '심사관이 현장에서 가장 먼저 확인하는 필수 CCP'
    ],
    seniorTip: '장비 고장 시 회수 범위를 줄이는 골든타임 관리!',
    image: 'assets/broll_metal_line.jpg',
    accent: '#ef4444'
  },
  {
    startFrame: 330,
    duration: 360, // 12s
    badge: '💡 한계기준 설정',
    badgeBg: '#f59e0b',
    title: '남의 기준 베끼면 부적합!\n제품 감도(Effect) 검증 필수',
    subtitle: 'Fe 1.5mm / Sus 2.0mm 설정의 과학적 근거',
    keyPoints: [
      '수분·염분·품온에 따른 감도 영향 실측',
      '신제품/배합비 변경 시 유효성 평가서 구비'
    ],
    seniorTip: '10회 연속 통과 테스트 데이터가 없으면 감점 대상!',
    image: 'assets/broll_test_piece.jpg',
    accent: '#f59e0b'
  },
  {
    startFrame: 690,
    duration: 360, // 12s
    badge: '⏱️ 검증 골든타임',
    badgeBg: '#06b6d4',
    title: '무조건 지켜야 할\n\'3시점 검증 원칙\'',
    subtitle: '사고 났을 때 덤터기 쓸 물량을 차단하는 법',
    keyPoints: [
      '1. 작업 시작 전 : 10분 예열 후 정상 작동 확인',
      '2. 작업 중 (2~3시간) : 라인 가동 중 감도 유지',
      '3. 작업 종료 직후 : 당일 생산 로트 유효성 최종 보증'
    ],
    seniorTip: '종료 후 검증을 빼먹으면 하루 종일 만든 물량 전량 재검사!',
    image: 'assets/broll_smart_haccp.jpg',
    accent: '#06b6d4'
  },
  {
    startFrame: 1050,
    duration: 360, // 12s
    badge: '🔥 20년 선배 꿀팁',
    badgeBg: '#8b5cf6',
    title: '가장자리로 넣으면 낭패!\n\'헤드 정중앙\' 통과 원칙',
    subtitle: '현장 작업자가 가장 많이 실수하는 치명적 포인트',
    keyPoints: [
      '검출기 정중앙이 자기장이 가장 약한 Cold Spot',
      '제품의 가장 두꺼운 중심부에 시편 올려서 통과'
    ],
    seniorTip: '리젝트(Reject) 불합격품 보관함 시건장치 열쇠 확인!',
    image: 'assets/broll_test_piece.jpg',
    accent: '#8b5cf6'
  },
  {
    startFrame: 1410,
    duration: 360, // 12s
    badge: '🏆 합격 체크리스트',
    badgeBg: '#10b981',
    title: '심사관이 감탄하는\n3대 필수 구비 서류',
    subtitle: '이것만 준비하면 HACCP / FSSC22000 100% 통과!',
    keyPoints: [
      '1. 금속검출기 한계기준 설정 및 유효성 평가서',
      '2. 일일 3시점 모니터링 일지 & 이탈 조치 기록',
      '3. 테스트피스 연 1회 검교정 성적서'
    ],
    seniorTip: '궁금한 서식이나 질문은 큐에이플러스 오픈채팅방으로!',
    image: 'assets/broll_audit.jpg',
    accent: '#10b981'
  }
];

export const KoreanShortsCard: React.FC<{ data: ShortsSceneData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Ken Burns scale & pan
  const bgScale = interpolate(frame, [0, data.duration], [1.0, 1.12], { extrapolateRight: 'clamp' });
  const bgTranslateY = interpolate(frame, [0, data.duration], [0, -30], { extrapolateRight: 'clamp' });

  // Spring animation for UI cards
  const entrance = spring({ frame, fps, config: { damping: 14, mass: 0.7, stiffness: 120 } });
  const cardTranslateY = interpolate(entrance, [0, 1], [60, 0]);
  const cardOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        fontFamily: '"Pretendard", "Noto Sans KR", -apple-system, sans-serif',
        backgroundColor: '#070b14'
      }}
    >
      {/* 1. Cinematic Background Image (Ken Burns Animation) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center'
        }}
      >
        <Img
          src={staticFile(data.image)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover'
          }}
        />
        {/* Cinematic Vignette & Gradient Overlays for Crystal Clear Typography */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(180deg, rgba(7,11,20,0.88) 0%, rgba(7,11,20,0.45) 35%, rgba(7,11,20,0.85) 70%, rgba(7,11,20,0.98) 100%)'
          }}
        />
      </div>

      {/* 2. Top Header Section (Badge + Big Title) */}
      <div
        style={{
          position: 'absolute',
          top: 90,
          left: 50,
          right: 50,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '20px',
          zIndex: 10
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span
            style={{
              backgroundColor: data.badgeBg,
              color: '#ffffff',
              padding: '12px 34px',
              borderRadius: '50px',
              fontSize: '28px',
              fontWeight: 900,
              boxShadow: `0 0 25px ${data.badgeBg}aa`,
              border: '2px solid rgba(255,255,255,0.4)',
              letterSpacing: '-0.5px'
            }}
          >
            {data.badge}
          </span>
          <span
            style={{
              backgroundColor: 'rgba(255,255,255,0.15)',
              backdropFilter: 'blur(10px)',
              color: '#e2e8f0',
              padding: '8px 20px',
              borderRadius: '30px',
              fontSize: '22px',
              fontWeight: 700,
              border: '1px solid rgba(255,255,255,0.25)'
            }}
          >
            큐에이플러스 (QA+)
          </span>
        </div>

        <h1
          style={{
            fontSize: '52px',
            fontWeight: 900,
            textAlign: 'center',
            lineHeight: '1.25',
            margin: 0,
            color: '#ffffff',
            whiteSpace: 'pre-line',
            textShadow: '0 4px 25px rgba(0,0,0,0.95), 0 2px 5px rgba(0,0,0,0.8)'
          }}
        >
          {data.title}
        </h1>

        <span
          style={{
            fontSize: '26px',
            fontWeight: 700,
            color: '#38bdf8',
            textAlign: 'center',
            letterSpacing: '-0.3px',
            textShadow: '0 2px 10px rgba(0,0,0,0.8)'
          }}
        >
          {data.subtitle}
        </span>
      </div>

      {/* 3. Center Glassmorphism Key Points Card */}
      <div
        style={{
          position: 'absolute',
          top: 600,
          left: 50,
          right: 50,
          transform: `translateY(${cardTranslateY}px)`,
          opacity: cardOpacity,
          backgroundColor: 'rgba(11, 19, 38, 0.88)',
          backdropFilter: 'blur(24px)',
          border: `3px solid ${data.accent}`,
          borderRadius: '36px',
          padding: '44px 40px',
          display: 'flex',
          flexDirection: 'column',
          gap: '22px',
          boxShadow: `0 20px 60px rgba(0,0,0,0.7), 0 0 40px ${data.accent}44`,
          zIndex: 10
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '18px', height: '18px', borderRadius: '50%', backgroundColor: data.accent, boxShadow: `0 0 12px ${data.accent}` }} />
          <span style={{ fontSize: '26px', fontWeight: 900, color: data.accent, letterSpacing: '0.5px' }}>
            실무 핵심 체크포인트
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {data.keyPoints.map((point, pIdx) => (
            <div key={pIdx} style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
              <span style={{ color: '#22c55e', fontSize: '28px', lineHeight: '1.4', fontWeight: 900 }}>✔</span>
              <span
                style={{
                  fontSize: '32px',
                  fontWeight: 700,
                  lineHeight: '1.45',
                  color: '#f8fafc',
                  margin: 0
                }}
              >
                {point}
              </span>
            </div>
          ))}
        </div>

        {/* 20년 선배 꿀팁 콜아웃 */}
        <div
          style={{
            marginTop: '10px',
            backgroundColor: 'rgba(245, 158, 11, 0.15)',
            borderLeft: '5px solid #f59e0b',
            borderRadius: '16px',
            padding: '20px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px'
          }}
        >
          <span style={{ fontSize: '32px' }}>💡</span>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: '#fbbf24', fontSize: '22px', fontWeight: 900 }}>20년 QA 선배의 조언</span>
            <span style={{ color: '#fef3c7', fontSize: '26px', fontWeight: 700, lineHeight: '1.4' }}>
              {data.seniorTip}
            </span>
          </div>
        </div>
      </div>

      {/* 4. Bottom Sticky Community Banner */}
      <div
        style={{
          position: 'absolute',
          bottom: 90,
          left: 50,
          right: 50,
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(56, 189, 248, 0.7)',
          borderRadius: '30px',
          padding: '28px 36px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '8px',
          boxShadow: '0 15px 50px rgba(0,0,0,0.8), 0 0 25px rgba(56, 189, 248, 0.25)',
          zIndex: 10
        }}
      >
        <span style={{ color: '#38bdf8', fontSize: '28px', fontWeight: 900, letterSpacing: '-0.3px' }}>
          💬 200명 참여 중! 큐에이플러스 오픈채팅방
        </span>
        <span style={{ color: '#cbd5e1', fontSize: '22px', fontWeight: 600 }}>
          매일 무료 인포그래픽 & 실무 Q&A 상시 답변 (100% 무료 나눔)
        </span>
      </div>

      {/* 5. Top Progress Indicator Bar */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '10px',
          backgroundColor: 'rgba(255,255,255,0.2)',
          zIndex: 20
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${((frame) / data.duration) * 100}%`,
            background: 'linear-gradient(90deg, #38bdf8, #818cf8, #f43f5e)'
          }}
        />
      </div>
    </div>
  );
};

export const CcpShortsVertical: React.FC = () => {
  return (
    <>
      {KOREAN_SHORTS_SCENES.map((scene, idx) => (
        <Sequence
          key={idx}
          from={scene.startFrame}
          durationInFrames={scene.duration}
          name={`Scene ${idx + 1} - ${scene.badge}`}
        >
          <KoreanShortsCard data={scene} />
        </Sequence>
      ))}
    </>
  );
};