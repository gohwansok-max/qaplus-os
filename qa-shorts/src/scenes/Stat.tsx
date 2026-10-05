import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { StatScene } from "../types";
import { COLOR, FONT } from "../theme";
import { fade, pop } from "../anim";

/** "−18℃" "2.0mm" "30분" 처럼 첫 숫자 덩어리를 카운트업한다. 숫자가 없으면 그대로 팝인. */
export const Stat: React.FC<{ s: StatScene }> = ({ s }) => {
  const f = useCurrentFrame();
  const m = s.value.match(/^(.*?)(-?\d+(?:\.\d+)?)(.*)$/);
  const prog = interpolate(f, [8, 38], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const eased = 1 - Math.pow(1 - prog, 3);
  let shown = s.value;
  if (m) {
    const target = parseFloat(m[2]);
    const dec = (m[2].split(".")[1] || "").length;
    shown = `${m[1]}${(target * eased).toFixed(dec)}${m[3]}`;
  }
  const R = 330, C = 2 * Math.PI * R;
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", fontFamily: FONT, paddingBottom: 380 }}>
      <div style={{ fontSize: 46, fontWeight: 700, color: COLOR.cyan, marginBottom: 40, opacity: fade(f, 0) }}>{s.label}</div>
      <div style={{ position: "relative", width: 720, height: 720, display: "grid", placeItems: "center", transform: `scale(${0.85 + pop(f) * 0.15})` }}>
        <svg width={720} height={720} style={{ position: "absolute" }}>
          <circle cx={360} cy={360} r={R} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={26} />
          <circle cx={360} cy={360} r={R} fill="none" stroke={COLOR.amber} strokeWidth={26} strokeLinecap="round" strokeDasharray={C} strokeDashoffset={C * (1 - eased * 0.82)} transform="rotate(-90 360 360)" />
        </svg>
        <div style={{ fontSize: shown.length > 7 ? 120 : 170, fontWeight: 900, color: COLOR.text, letterSpacing: -4, textAlign: "center" }}>{shown}</div>
      </div>
      <div style={{ marginTop: 44, fontSize: 52, fontWeight: 700, color: COLOR.text, textAlign: "center", maxWidth: 900, lineHeight: 1.3, opacity: fade(f, 30) }}>{s.caption}</div>
      {s.note ? <div style={{ marginTop: 18, fontSize: 34, color: COLOR.dim, opacity: fade(f, 40) }}>{s.note}</div> : null}
    </AbsoluteFill>
  );
};
