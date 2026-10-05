import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { FlowScene } from "../types";
import { COLOR, FONT } from "../theme";
import { fade, pop } from "../anim";

/** 공정 흐름 — 단계가 위에서 아래로 순차 점등하고 연결선이 그려진다 */
export const Flow: React.FC<{ s: FlowScene }> = ({ s }) => {
  const f = useCurrentFrame();
  const n = s.steps.length;
  const per = Math.max(14, Math.floor((s.durationFrames - 40) / n));
  const active = Math.min(n - 1, Math.floor(Math.max(0, f - 14) / per));
  return (
    <AbsoluteFill style={{ fontFamily: FONT, alignItems: "center", justifyContent: "center", paddingTop: 120, paddingBottom: 420 }}>
      <div style={{ fontSize: 60, fontWeight: 900, color: COLOR.text, marginBottom: 56, opacity: fade(f), letterSpacing: -2 }}>{s.title}</div>
      <div style={{ width: 900, position: "relative" }}>
        {s.steps.map((t, i) => {
          const at = 14 + i * per;
          const on = f >= at;
          const cur = i === active;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", height: 170, position: "relative" }}>
              {i < n - 1 && (
                <div style={{ position: "absolute", left: 54, top: 120, width: 6, height: 100, background: "rgba(255,255,255,0.12)" }}>
                  <div style={{ width: 6, height: `${Math.min(1, Math.max(0, (f - at - 6) / 12)) * 100}%`, background: COLOR.cyan }} />
                </div>
              )}
              <div style={{ width: 114, height: 114, borderRadius: "50%", flex: "none", display: "grid", placeItems: "center", fontSize: 54, fontWeight: 900, background: on ? COLOR.cyan : "rgba(255,255,255,0.08)", color: on ? "#06202B" : COLOR.dim, transform: `scale(${on ? 0.9 + pop(f, at) * 0.1 : 0.9})`, boxShadow: cur ? `0 0 50px ${COLOR.cyan}` : "none" }}>{i + 1}</div>
              <div style={{ marginLeft: 34, flex: 1, fontSize: 52, fontWeight: 700, lineHeight: 1.25, color: on ? COLOR.text : COLOR.dim, padding: "20px 30px", borderRadius: 26, background: cur ? "rgba(34,211,238,0.14)" : COLOR.panel, border: `2px solid ${cur ? COLOR.cyan : COLOR.line}`, opacity: on ? 1 : 0.4, transform: `translateX(${on ? 0 : 40}px)` }}>{t}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
