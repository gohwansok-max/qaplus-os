import React from 'react';
import { Composition, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

export const TOTAL_FRAMES = 5400; // 3 min @ 30fps
export const FPS = 30;
export const SCENE_FRAMES = 900;

export interface SceneData {
  id: number;
  category: string;
  title: string;
  color: string;
  script: string;
  points: string[];
}

export const SCENES_DATA: SceneData[] = [
  {
    id: 1,
    category: 'STEP 1 • 기초 개념',
    title: '한계기준(Critical Limit)의 본질 & 운용한계(OL)',
    color: '#06b6d4',
    script: '식품안전 HACCP의 핵심, CCP 한계기준은 위해요소를 허용 수준 이하로 제어하기 위한 절대적인 과학적 수치 기준입니다.',
    points: [
      '한계기준(CL): 위해요소 제어를 위한 절대 마지노선 (위반 시 즉시 공정 중단 및 격리)',
      '운용한계(OL): CL 이탈을 사전에 방지하기 위한 자사 안전 완충 마진(Buffer)',
      '안전 영역 vs 위험 영역의 명확한 경계선 설정 및 모니터링'
    ]
  },
  {
    id: 2,
    category: 'STEP 2 • 설정 방법론',
    title: '한계기준 설정 4단계 표준 프로세스',
    color: '#3b82f6',
    script: '한계기준은 4단계 프로세스로 설정합니다: 위해요소 특정 -> 관리 파라미터 선정 -> 과학적 근거 확보 -> 한계치 확정.',
    points: [
      'Step 1. 위해요소 명확화 (생물학적, 화학적, 물리적)',
      'Step 2. 관리지표 선정 (온도, 시간, 압력, 수분활성도, 이물 규격)',
      'Step 3. 과학적/법적 근거 데이터 확보 (식약처 고시, 학술 논문, D/z값)',
      'Step 4. 한계치(수치) 확정 (작업자가 판정 가능한 단일 수치)'
    ]
  },
  {
    id: 3,
    category: 'STEP 3 • 검증 철학',
    title: '유효성 검증(Validation) vs 일상 검증(Verification)',
    color: '#8b5cf6',
    script: '유효성 검증(Validation)은 사전 타당성 입증이고, 일상 검증(Verification)은 사후 이행 확인입니다.',
    points: [
      'Validation (사전 타당성): "우리가 세운 기준이 정말로 세균을 사멸시키는가?"',
      'Verification (사후 이행확인): "작업자가 규정대로 매일 기록하고 이행하는가?"',
      '임상시험을 통한 약효 입증 vs 복약 준수 확인의 대비'
    ]
  },
  {
    id: 4,
    category: 'STEP 4 • 실증 기법',
    title: '유효성 검증 3대 핵심 방법론',
    color: '#10b981',
    script: '유효성 검증 3대 방법은 문헌 조사, 공장 열분포/열침투 실증 시험, 그리고 미생물 챌린지 테스트입니다.',
    points: [
      '1. 과학 문헌 및 법규 데이터 (식약처 표준공정 모델, SCI급 논문)',
      '2. 공장 실증 실험 (다채널 센서 Cold Spot 열침투, F0값 계산)',
      '3. 미생물 챌린지 테스트 (5-Log / 99.999% 사멸 입증)'
    ]
  },
  {
    id: 5,
    category: 'STEP 5 • 실무 사례',
    title: '현장 실무 사례 분석: 가열살균 & 금속검출',
    color: '#f59e0b',
    script: '가열살균은 중심온도 85℃ 1분 유지, 금속검출은 Fe 1.2mm / SUS 1.5mm 100% 감지 및 취출을 입증해야 합니다.',
    points: [
      '가열살균 CCP: 제품 중심부(Cold Spot) 실시간 품온 측정 및 Cpk >= 1.33 입증',
      '금속검출 CCP: Fe 1.2mm, SUS 1.5mm 테스트피스 전/중/후단 통과 시험',
      '감지 즉시 컨베이어 정지 또는 에어 킥커 정상 분리'
    ]
  },
  {
    id: 6,
    category: 'STEP 6 • 유지관리 & 요약',
    title: '재검증(Re-validation) & 심사 3대 체크리스트',
    color: '#ec4899',
    script: '원료나 설비 변경 시 반드시 재유효성검증을 실시해야 하며, 종합 보고서, 실측 차트, 검교정 성적서를 구비해야 합니다.',
    points: [
      '재검증 4대 트리거: 원료 배합비 변경, 설비 교체, 생산량 증설, 위해요소 신규 발생',
      '심사 필수 3대 서류: 유효성검증 보고서, Cold Spot 실측 로그, 국가공인 계측기 검교정 성적서',
      '20년 선배의 원칙: "기록되지 않은 것은 존재하지 않고, 증명되지 않은 기준은 무효다!"'
    ]
  }
];

export const SceneCard: React.FC<{ data: SceneData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({ frame, fps, config: { damping: 14, mass: 0.8, stiffness: 100 } });
  const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const translateY = interpolate(entrance, [0, 1], [60, 0]);

  return (
    <div style={{ width: 1920, height: 1080, backgroundColor: '#0b0f19', color: '#f8fafc', padding: '50px 80px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'rgba(30, 41, 59, 0.8)', padding: '16px 32px', borderRadius: '16px', border: '1px solid #334155' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <span style={{ backgroundColor: data.color, color: '#020617', padding: '8px 20px', borderRadius: '10px', fontWeight: 'bold', fontSize: '22px' }}>{data.category}</span>
          <h1 style={{ fontSize: '32px', fontWeight: 800, margin: 0 }}>{data.title}</h1>
        </div>
        <span style={{ color: '#94a3b8', fontSize: '22px', fontFamily: 'monospace' }}>HACCP MASTER • Scene {data.id} / 6</span>
      </div>
      <div style={{ opacity, transform: `translateY(${translateY}px)`, backgroundColor: 'rgba(30, 41, 59, 0.9)', border: `3px solid ${data.color}`, borderRadius: '24px', padding: '50px 60px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        <h2 style={{ fontSize: '34px', fontWeight: 700, color: data.color, margin: 0 }}>실무 핵심 체크포인트</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {data.points.map((pt, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '18px', fontSize: '26px', lineHeight: '1.5', color: '#e2e8f0' }}>
              <span style={{ color: data.color, fontWeight: 'bold' }}>✓</span>
              <span>{pt}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '2px solid rgba(6, 182, 212, 0.4)', borderRadius: '18px', padding: '24px 36px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <span style={{ color: '#06b6d4', fontWeight: 'bold', fontSize: '20px' }}>🎙️ 실무 내레이션:</span>
        <p style={{ margin: 0, fontSize: '24px', color: '#ffffff', fontWeight: 500 }}>{data.script}</p>
      </div>
    </div>
  );
};

export const CcpValidationVideo: React.FC = () => {
  return (
    <>
      {SCENES_DATA.map((scene, idx) => (
        <Sequence key={scene.id} from={idx * SCENE_FRAMES} durationInFrames={SCENE_FRAMES} name={`Scene ${scene.id} - ${scene.title}`}>
          <SceneCard data={scene} />
        </Sequence>
      ))}
    </>
  );
};

export const RemotionRoot: React.FC = () => {
  return <Composition id="CcpValidationMaster" component={CcpValidationVideo} durationInFrames={TOTAL_FRAMES} fps={FPS} width={1920} height={1080} />;
};