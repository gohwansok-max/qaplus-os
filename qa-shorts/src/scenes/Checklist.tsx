import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { ChecklistScene } from "../types";
import { COLOR, FONT } from "../theme";
import { fade, pop } from "../anim";

export const Checklist: React.FC<{ s: ChecklistScene }> = ({ s }) => {
  const f = useCurrentFrame();
  const per = Math.max(16, Math.floor((s.durationFrames - 50) / s.items.length));
  return (
    <AbsoluteFill style={{ fontFamily: FONT, alignItems: "center", justifyContent: "center", paddingTop: 120, paddingBottom: 420 }}>
      <div style={{ fontSize: 60, fontWeight: 900, color: COLOR.text, marginBottom: 56, opacity: fade(f), letterSpacing: -2 }}>{s.title}</div>
      {s.items.map((t, i) => {
        const at = 14 + i * per;
        const k = pop(f, at);
        const tick = Math.min(1, Math.max(0, (f - at - 6) / 10));
        return (
          <div key={i} style={{ width: 920, display: "flex", alignItems: "center", gap: 30, margin: "16px 0", padding: "30px 38px", borderRadius: 30, background: COLOR.panel, border: `2px solid ${tick > 0.9 ? COLOR.safe : COLOR.line}`, opacity: fade(f, at), transform: `translateY(${(1 - k) * 50}px)` }}>
            <svg width={84} height={84} viewBox="0 0 84 84" style={{ flex: "none" }}>
              <rect x={4} y={4} width={76} height={76} rx={20} fill={tick > 0.9 ? COLOR.safe : "none"} stroke={COLOR.safe} strokeWidth={5} />
              <path d="M22 44 L37 58 L62 28" fill="none" stroke="#06121C" strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={80} strokeDashoffset={80 * (1 - tick)} />
            </svg>
            <div style={{ fontSize: 50, fontWeight: 700, color: COLOR.text, lineHeight: 1.28 }}>{t}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
