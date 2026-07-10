import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { SCENES, type Group, type Token } from "../timings";
import { AQUA, F, GOLD, WHITE, hexToRgba } from "../theme";

const FONT = "'Archivo Black', 'Noto Color Emoji', sans-serif";

// ------------------------------------------------------ Palabra karaoke
const Word: React.FC<{ tok: Token }> = ({ tok }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sf = F(tok.s);
  const ef = F(tok.e);
  const revealed = frame >= sf;
  const isEmoji = tok.f.includes("e");
  const mega = tok.f.includes("m");
  const accent = tok.f.includes("a") ? AQUA : tok.f.includes("g") ? GOLD : null;
  const pop = revealed
    ? spring({
        frame: frame - sf,
        fps,
        config: { damping: 11, stiffness: 260, mass: 0.6 },
      })
    : 0;
  const activeNow = frame >= sf && frame <= ef + 2;
  const scale = (0.72 + 0.28 * pop) * (activeNow ? 1.09 : 1);
  const pulse = mega && accent ? 0.55 + 0.25 * Math.sin(frame / 5) : 0.6;
  const glow =
    revealed && (accent || activeNow)
      ? `, 0 0 36px ${accent ? hexToRgba(accent, pulse) : "rgba(255,255,255,0.35)"}`
      : "";
  return (
    <span
      style={{
        fontFamily: FONT,
        fontSize: mega ? 112 : 78,
        lineHeight: 1.14,
        color: isEmoji ? undefined : revealed ? (accent ?? WHITE) : "rgba(255,255,255,0.4)",
        opacity: revealed ? 1 : 0.35,
        transform: `scale(${scale}) translateY(${(1 - pop) * 12}px)`,
        textShadow: isEmoji
          ? "0 6px 26px rgba(0,0,0,0.55)"
          : `0 5px 26px rgba(0,0,0,0.92), 0 2px 6px rgba(0,0,0,0.85)${glow}`,
        display: "inline-block",
        letterSpacing: 1.5,
        whiteSpace: "pre",
      }}
    >
      {tok.t}
    </span>
  );
};

// --------------------------------------------- Contador 4,000,000,000
const CounterNumber: React.FC<{ startFrame: number }> = ({ startFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = Math.max(0, frame - startFrame);
  const dur = 34;
  const p = interpolate(t, [0, dur], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.exp),
  });
  const val = Math.round(4_000_000_000 * p);
  const landed = t >= dur;
  const punch = landed
    ? spring({
        frame: t - dur,
        fps,
        config: { damping: 10, stiffness: 210, mass: 0.7 },
      })
    : 1;
  const scale = landed ? 1 + 0.14 * (1 - punch) : 0.98;
  return (
    <div
      style={{
        fontFamily: FONT,
        fontSize: 138,
        letterSpacing: 2,
        background: "linear-gradient(180deg, #FFE9A8 8%, #FFC53D 55%, #E88A0C)",
        WebkitBackgroundClip: "text",
        backgroundClip: "text",
        color: "transparent",
        transform: `scale(${scale})`,
        filter: `drop-shadow(0 6px 22px rgba(0,0,0,0.85)) drop-shadow(0 0 34px rgba(255,180,40,${landed ? 0.55 : 0.3}))`,
        whiteSpace: "nowrap",
      }}
    >
      {val.toLocaleString("es-MX")}
    </div>
  );
};

// -------------------------------------------------------- Captions main
export const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  let group: Group | null = null;
  for (const scene of SCENES) {
    for (const g of scene.groups) {
      if (frame >= F(g.start) - 3 && frame < F(g.end)) {
        group = g;
        break;
      }
    }
    if (group) {
      break;
    }
  }
  if (!group) {
    return null;
  }

  const gStart = F(group.start) - 3;
  const enter = spring({
    frame: frame - gStart,
    fps,
    config: { damping: 13, stiffness: 190, mass: 0.7 },
  });
  const counterTok = group.tokens.find((tk) => tk.f.includes("counter"));
  const hasMega = group.tokens.some((tk) => tk.f.includes("m"));
  const top = counterTok ? 1000 : hasMega ? 1030 : 1075;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: 20,
          right: 20,
          top: top - 130,
          height: 520,
          background:
            "radial-gradient(ellipse 62% 52% at 50% 50%, rgba(1,10,18,0.55), transparent 74%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 54,
          right: 54,
          top,
          display: "flex",
          flexDirection: counterTok ? "column" : "row",
          flexWrap: counterTok ? "nowrap" : "wrap",
          justifyContent: "center",
          alignItems: "center",
          columnGap: 24,
          rowGap: 12,
          textAlign: "center",
          transform: `translateY(${(1 - enter) * 48}px) scale(${0.9 + 0.1 * enter})`,
          opacity: Math.min(1, enter * 1.4),
        }}
      >
        {counterTok ? (
          <>
            <CounterNumber startFrame={F(counterTok.s)} />
            <div
              style={{
                display: "flex",
                columnGap: 24,
                justifyContent: "center",
                marginTop: 6,
              }}
            >
              {group.tokens
                .filter((tk) => !tk.f.includes("counter"))
                .map((tk, i) => (
                  <Word key={i} tok={tk} />
                ))}
            </div>
          </>
        ) : (
          group.tokens.map((tk, i) => <Word key={i} tok={tk} />)
        )}
      </div>
    </AbsoluteFill>
  );
};
