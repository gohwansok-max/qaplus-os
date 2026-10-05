import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { COLOR, H, W } from "./theme";

export const Background: React.FC = () => {
  const f = useCurrentFrame();
  const drift = (f * 0.6) % 90;
  const o1 = Math.sin(f / 55) * 80;
  const o2 = Math.cos(f / 70) * 100;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(120% 80% at 50% 0%, #0E2A47 0%, ${COLOR.bg} 55%, ${COLOR.bgDeep} 100%)` }}>
      <div style={{ position: "absolute", left: -200 + o1, top: 200, width: 700, height: 700, borderRadius: "50%", background: "radial-gradient(circle, rgba(34,211,238,0.22), transparent 65%)" }} />
      <div style={{ position: "absolute", right: -240 + o2, top: 1100, width: 800, height: 800, borderRadius: "50%", background: "radial-gradient(circle, rgba(251,191,36,0.12), transparent 65%)" }} />
      <svg width={W} height={H} style={{ position: "absolute", opacity: 0.5 }}>
        <defs>
          <pattern id="g" width="90" height="90" patternUnits="userSpaceOnUse" patternTransform={`translate(0 ${drift})`}>
            <path d="M 90 0 L 0 0 0 90" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="2" />
          </pattern>
        </defs>
        <rect width={W} height={H} fill="url(#g)" />
      </svg>
    </AbsoluteFill>
  );
};
