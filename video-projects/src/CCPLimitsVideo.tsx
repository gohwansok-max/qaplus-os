import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Sequence, spring } from 'remotion';

interface CCPLimitsVideoProps {
  title: string;
}

export const CCPLimitsVideo: React.FC<CCPLimitsVideoProps> = ({ title }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#ffffff' }}>
      <Sequence from={0} durationInFrames={300}>
        <HookingScene />
      </Sequence>
      <Sequence from={300} durationInFrames={600}>
        <ProblemScene />
      </Sequence>
      <Sequence from={900} durationInFrames={4200}>
        <MainContentScene />
      </Sequence>
      <Sequence from={5100} durationInFrames={300}>
        <CTAScene />
      </Sequence>
    </AbsoluteFill>
  );
};

const HookingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  const scale = spring({ frame, fps, from: 0.8, to: 1, config: { damping: 12 } });
  
  return (
    <AbsoluteFill style={{ 
      backgroundColor: '#FF6B6B',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '80px'
    }}>
      <div style={{
        opacity,
        transform: scale($\{scale}),
        textAlign: 'center'
      }}>
        <h1 style={{
          fontSize: '80px',
          fontWeight: 'bold',
          color: '#ffffff',
          marginBottom: '40px',
          lineHeight: 1.4
        }}>
          CCP 한계기준<br />
          잘못 설정하면?
        </h1>
        <p style={{
          fontSize: '50px',
          color: '#ffffff',
          fontWeight: '600'
        }}>
          인증 탈락 1순위입니다
        </p>
      </div>
    </AbsoluteFill>
  );
};

const ProblemScene: React.FC = () => {
  const frame = useCurrentFrame();
  
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  
  return (
    <AbsoluteFill style={{ 
      backgroundColor: '#4A90E2',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '80px'
    }}>
      <div style={{ opacity, textAlign: 'center' }}>
        <h2 style={{
          fontSize: '70px',
          fontWeight: 'bold',
          color: '#ffffff',
          marginBottom: '60px',
          lineHeight: 1.5
        }}>
          CCP 한계기준이란?
        </h2>
        <p style={{
          fontSize: '48px',
          color: '#ffffff',
          lineHeight: 1.8,
          marginBottom: '40px'
        }}>
          쉽게 말하면<br />
          "여기 넘으면 위험해요"<br />
          라고 정해놓은 선
        </p>
        <p style={{
          fontSize: '42px',
          color: '#FFF9C4',
          fontWeight: '600'
        }}>
          20년 해보니 이거 3가지만<br />
          확실히 잡으면 통과합니다
        </p>
      </div>
    </AbsoluteFill>
  );
};

const MainContentScene: React.FC = () => {
  const frame = useCurrentFrame();
  
  const showPoint1 = frame > 0;
  const showPoint2 = frame > 1400;
  const showPoint3 = frame > 2800;
  
  return (
    <AbsoluteFill style={{ 
      backgroundColor: '#f8f9fa',
      padding: '60px'
    }}>
      {showPoint1 && <Point1 frame={frame} />}
      {showPoint2 && <Point2 frame={frame - 1400} />}
      {showPoint3 && <Point3 frame={frame - 2800} />}
    </AbsoluteFill>
  );
};

const Point1: React.FC<{ frame: number }> = ({ frame }) => {
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  
  return (
    <div style={{ opacity, marginBottom: '80px' }}>
      <div style={{
        backgroundColor: '#FF6B6B',
        padding: '30px',
        borderRadius: '20px',
        marginBottom: '40px'
      }}>
        <h3 style={{
          fontSize: '60px',
          fontWeight: 'bold',
          color: '#ffffff',
          margin: 0
        }}>
          1. 과학적 근거
        </h3>
      </div>
      <div style={{
        fontSize: '44px',
        color: '#2c3e50',
        lineHeight: 2,
        padding: '0 40px'
      }}>
        <p style={{ marginBottom: '30px' }}>
          ✅ 온도 75℃ → 왜 75℃인가?<br />
          → 살모넬라 사멸 온도 근거
        </p>
        <p style={{ marginBottom: '30px' }}>
          ✅ 시간 2분 → 왜 2분인가?<br />
          → D값 계산 근거
        </p>
        <p style={{
          fontSize: '38px',
          color: '#7f8c8d',
          fontStyle: 'italic',
          marginTop: '50px'
        }}>
          출처: FDA Food Code 2022
        </p>
      </div>
    </div>
  );
};

const Point2: React.FC<{ frame: number }> = ({ frame }) => {
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  
  return (
    <div style={{ opacity, marginBottom: '80px' }}>
      <div style={{
        backgroundColor: '#4A90E2',
        padding: '30px',
        borderRadius: '20px',
        marginBottom: '40px'
      }}>
        <h3 style={{
          fontSize: '60px',
          fontWeight: 'bold',
          color: '#ffffff',
          margin: 0
        }}>
          2. 유효성 검증
        </h3>
      </div>
      <div style={{
        fontSize: '44px',
        color: '#2c3e50',
        lineHeight: 2,
        padding: '0 40px'
      }}>
        <p style={{ marginBottom: '30px' }}>
          ✅ 실제로 측정해봐야 합니다<br />
          → 실험실 데이터 3회 반복
        </p>
        <p style={{ marginBottom: '30px' }}>
          ✅ 최악의 조건에서도 OK?<br />
          → 최대 부하량 / 최저 온도 테스트
        </p>
        <p style={{
          fontSize: '38px',
          color: '#7f8c8d',
          fontStyle: 'italic',
          marginTop: '50px'
        }}>
          출처: FSSC22000 v6 매뉴얼
        </p>
      </div>
    </div>
  );
};

const Point3: React.FC<{ frame: number }> = ({ frame }) => {
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  
  return (
    <div style={{ opacity }}>
      <div style={{
        backgroundColor: '#50C878',
        padding: '30px',
        borderRadius: '20px',
        marginBottom: '40px'
      }}>
        <h3 style={{
          fontSize: '60px',
          fontWeight: 'bold',
          color: '#ffffff',
          margin: 0
        }}>
          3. 문서화
        </h3>
      </div>
      <div style={{
        fontSize: '44px',
        color: '#2c3e50',
        lineHeight: 2,
        padding: '0 40px'
      }}>
        <p style={{ marginBottom: '30px' }}>
          ✅ 한계기준 설정 사유서<br />
          → 왜 이 값인지 근거 명시
        </p>
        <p style={{ marginBottom: '30px' }}>
          ✅ 유효성 검증 보고서<br />
          → 실험 결과 + 결론
        </p>
        <p style={{ marginBottom: '30px' }}>
          ✅ 연간 재검증 기록<br />
          → 1년마다 다시 확인
        </p>
        <p style={{
          fontSize: '38px',
          color: '#7f8c8d',
          fontStyle: 'italic',
          marginTop: '50px'
        }}>
          출처: HACCP 적용 매뉴얼
        </p>
      </div>
    </div>
  );
};

const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  
  return (
    <AbsoluteFill style={{ 
      backgroundColor: '#2c3e50',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '80px'
    }}>
      <div style={{ opacity, textAlign: 'center' }}>
        <h2 style={{
          fontSize: '70px',
          fontWeight: 'bold',
          color: '#ffffff',
          marginBottom: '60px'
        }}>
          정리하면
        </h2>
        <p style={{
          fontSize: '48px',
          color: '#ffffff',
          lineHeight: 2,
          marginBottom: '80px'
        }}>
          1️⃣ 과학적 근거<br />
          2️⃣ 유효성 검증<br />
          3️⃣ 문서화
        </p>
        <p style={{
          fontSize: '44px',
          color: '#FFD700',
          fontWeight: '600',
          marginBottom: '60px'
        }}>
          궁금한 거 있으면<br />
          채팅방에서 편하게 물어보세요
        </p>
        <p style={{
          fontSize: '38px',
          color: '#95a5a6'
        }}>
          출처 찾아서 알려드릴게요 👍
        </p>
      </div>
    </AbsoluteFill>
  );
};
