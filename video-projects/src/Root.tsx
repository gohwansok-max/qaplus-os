import { Composition } from 'remotion';
import { CCPLimitsVideo } from './CCPLimitsVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CCPLimitsVideo"
        component={CCPLimitsVideo}
        durationInFrames={5400} // 3분 = 180초 * 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          title: 'CCP 한계기준 설정 완전정복',
        }}
      />
    </>
  );
};
