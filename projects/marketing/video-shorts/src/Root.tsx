import React from "react";
import { Composition, Still } from "remotion";
import { CcpShort } from "./CcpShort";
import { CcpLimitValidation } from "./CcpLimitValidation";
import { CcpImageOneMinute } from "./CcpImageOneMinute";
import { Thumbnail } from "./Thumbnail";
import { SIZE } from "./theme";
import { TOTAL_FRAMES } from "./lib/timeline";
import { LIMIT_TOTAL_FRAMES } from "./lib/limitValidationTimeline";
import { IMAGE_ONE_MINUTE_TOTAL_FRAMES } from "./lib/imageOneMinuteTimeline";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="CcpShort"
      component={CcpShort}
      durationInFrames={TOTAL_FRAMES}
      fps={SIZE.fps}
      width={SIZE.width}
      height={SIZE.height}
    />
    <Composition
      id="CcpLimitValidation"
      component={CcpLimitValidation}
      durationInFrames={LIMIT_TOTAL_FRAMES}
      fps={SIZE.fps}
      width={SIZE.width}
      height={SIZE.height}
    />
    <Composition
      id="CcpImageOneMinute"
      component={CcpImageOneMinute}
      durationInFrames={IMAGE_ONE_MINUTE_TOTAL_FRAMES}
      fps={SIZE.fps}
      width={SIZE.width}
      height={SIZE.height}
    />
    <Still id="Thumbnail" component={Thumbnail} width={1080} height={1920} />
  </>
);
