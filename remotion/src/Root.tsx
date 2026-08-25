import React from 'react';
import { Composition } from 'remotion';
import { CcpValidationVideo, TOTAL_FRAMES, FPS } from './CcpValidationVideo';
import { CcpShortsVertical, SHORTS_TOTAL_FRAMES, SHORTS_FPS } from './CcpShortsVertical';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* 16:9 Horizontal Full Master (1920x1080, 3분) */}
      <Composition
        id="CcpValidationMaster"
        component={CcpValidationVideo}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />

      {/* 9:16 Vertical YouTube Shorts (1080x1920, 59초) */}
      <Composition
        id="CcpShortsVertical"
        component={CcpShortsVertical}
        durationInFrames={SHORTS_TOTAL_FRAMES}
        fps={SHORTS_FPS}
        width={1080}
        height={1920}
      />
    </>
  );
};