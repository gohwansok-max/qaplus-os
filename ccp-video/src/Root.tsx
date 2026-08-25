import { Composition } from 'remotion';
import { CCPVideo } from './CCPVideo';

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="Root"
        component={CCPVideo}
        durationInFrames={5400} // 3분 = 180초 * 30fps = 5400프레임
        fps={30}
        width={1080}
        height={1920} // 세로형 숏폼 비율 (9:16)
      />
    </>
  );
};
