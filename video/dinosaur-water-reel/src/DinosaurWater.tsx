import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import timingData from './generatedTimings.json';

type Timing = {
  id: string;
  text: string;
  start: number;
  end: number;
  emphasis: string;
};

const timings = timingData as Timing[];
const sceneCuts = [0, 105, 205, 315, 420, 535, 650, 770];
const sceneFiles = Array.from({length: 8}, (_, i) => `assets/scene-${i + 1}.jpg`);

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

const HighlightedText: React.FC<{text: string; emphasis: string}> = ({text, emphasis}) => {
  const idx = text.toLowerCase().indexOf(emphasis.toLowerCase());
  if (idx < 0) return <>{text}</>;
  return (
    <>
      {text.slice(0, idx)}
      <span style={{color: '#8eeeff', textShadow: '0 0 28px rgba(92,225,255,.78)'}}>
        {text.slice(idx, idx + emphasis.length)}
      </span>
      {text.slice(idx + emphasis.length)}
    </>
  );
};

const SceneLayer: React.FC<{index: number}> = ({index}) => {
  const frame = useCurrentFrame();
  const start = sceneCuts[index];
  const end = index === sceneCuts.length - 1 ? 990 : sceneCuts[index + 1];
  const fade = 18;
  const fadeIn = index === 0 ? 1 : interpolate(frame, [start, start + fade], [0, 1], clamp);
  const fadeOut = index === sceneCuts.length - 1 ? 1 : interpolate(frame, [end - fade, end], [1, 0], clamp);
  const local = interpolate(frame, [start, end], [0, 1], clamp);
  const scale = 1.055 + local * 0.105;
  const driftX = (index % 2 === 0 ? -1 : 1) * local * 26;
  const driftY = (index % 3 - 1) * local * 18;

  return (
    <AbsoluteFill style={{opacity: fadeIn * fadeOut, overflow: 'hidden'}}>
      <Img
        src={staticFile(sceneFiles[index])}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `translate(${driftX}px, ${driftY}px) scale(${scale})`,
          filter: 'saturate(1.08) contrast(1.06) brightness(.84)',
        }}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(2,8,19,.33) 0%, rgba(2,7,18,.08) 34%, rgba(2,7,18,.42) 69%, rgba(1,4,13,.96) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

const WaterParticles: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {Array.from({length: 34}, (_, i) => {
        const x = (i * 83 + 47) % 1080;
        const baseY = (i * 149 + 90) % 1920;
        const speed = 0.52 + (i % 7) * 0.08;
        const y = (baseY + frame * speed) % 2060 - 70;
        const size = 3 + (i % 5) * 2;
        const opacity = 0.08 + (i % 6) * 0.035;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: size,
              height: size * 1.6,
              borderRadius: '55% 55% 62% 62%',
              background: 'linear-gradient(180deg, rgba(204,249,255,.95), rgba(63,187,255,.08))',
              boxShadow: '0 0 18px rgba(84,221,255,.45)',
              opacity,
              transform: `rotate(${i % 2 ? 9 : -7}deg)`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

const TimeOrb: React.FC = () => {
  const frame = useCurrentFrame();
  const visible = interpolate(frame, [170, 192, 300, 326], [0, 1, 1, 0], clamp);
  const rotation = frame * 0.26;
  const pulse = 1 + Math.sin(frame / 12) * 0.025;
  return (
    <div
      style={{
        position: 'absolute',
        width: 530,
        height: 530,
        left: 275,
        top: 450,
        opacity: visible,
        transform: `scale(${pulse}) rotate(${rotation}deg)`,
      }}
    >
      <svg width="530" height="530" viewBox="0 0 530 530">
        <defs>
          <radialGradient id="orb" cx="50%" cy="45%">
            <stop offset="0%" stopColor="#aef6ff" stopOpacity=".68" />
            <stop offset="45%" stopColor="#37bce9" stopOpacity=".2" />
            <stop offset="100%" stopColor="#041424" stopOpacity="0" />
          </radialGradient>
          <filter id="glow"><feGaussianBlur stdDeviation="7" /></filter>
        </defs>
        <circle cx="265" cy="265" r="208" fill="url(#orb)" />
        <circle cx="265" cy="265" r="214" fill="none" stroke="#8cecff" strokeWidth="2" strokeDasharray="9 18" opacity=".82" />
        <circle cx="265" cy="265" r="178" fill="none" stroke="#ffd987" strokeWidth="1.5" strokeDasharray="4 13" opacity=".56" />
        <circle cx="265" cy="265" r="237" fill="none" stroke="#69dfff" strokeWidth="10" opacity=".1" filter="url(#glow)" />
      </svg>
    </div>
  );
};

const Header: React.FC = () => {
  const frame = useCurrentFrame();
  const reveal = spring({frame, fps: 30, config: {damping: 18, stiffness: 100}});
  return (
    <div
      style={{
        position: 'absolute',
        left: 60,
        right: 60,
        top: 68,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        opacity: reveal,
        transform: `translateY(${(1 - reveal) * -20}px)`,
      }}
    >
      <div style={{display: 'flex', gap: 12, alignItems: 'center'}}>
        <div style={{width: 12, height: 12, borderRadius: 99, background: '#7feaff', boxShadow: '0 0 18px #5fe5ff'}} />
        <div style={{fontFamily: 'Arial, sans-serif', fontWeight: 800, letterSpacing: 4.8, fontSize: 22, color: 'rgba(235,251,255,.92)'}}>
          HISTORIA EN UN VASO
        </div>
      </div>
      <div style={{fontFamily: 'Arial, sans-serif', fontSize: 20, color: 'rgba(235,251,255,.55)', letterSpacing: 2}}>00:33</div>
    </div>
  );
};

const Subtitle: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const item = timings.find((entry) => t >= entry.start && t < entry.end) ?? timings[timings.length - 1];
  const localFrame = Math.max(0, frame - item.start * fps);
  const lifeFrames = Math.max(1, (item.end - item.start) * fps);
  const inAnim = spring({frame: localFrame, fps, config: {damping: 17, stiffness: 150}});
  const outAnim = interpolate(localFrame, [lifeFrames - 8, lifeFrames], [1, 0], clamp);
  const hook = item.id === 'hook';
  const cta = item.id === 'cta';

  return (
    <div
      style={{
        position: 'absolute',
        left: hook ? 68 : 74,
        right: hook ? 68 : 74,
        bottom: cta ? 238 : 238,
        display: 'flex',
        justifyContent: 'center',
        opacity: inAnim * outAnim,
        transform: `translateY(${(1 - inAnim) * 42}px) scale(${0.95 + inAnim * 0.05})`,
      }}
    >
      <div
        style={{
          maxWidth: 940,
          padding: hook ? '30px 36px 34px' : '25px 34px 30px',
          borderRadius: 32,
          background: 'linear-gradient(180deg, rgba(3,13,26,.58), rgba(2,8,18,.86))',
          border: '1px solid rgba(155,235,255,.22)',
          boxShadow: '0 24px 80px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.08)',
          backdropFilter: 'blur(15px)',
          textAlign: 'center',
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontWeight: 900,
          fontSize: hook ? 67 : cta ? 50 : 55,
          lineHeight: 1.08,
          letterSpacing: hook ? -2.4 : -1.2,
          color: '#f5fcff',
          textShadow: '0 3px 16px rgba(0,0,0,.85)',
        }}
      >
        <HighlightedText text={item.text} emphasis={item.emphasis} />
      </div>
    </div>
  );
};

const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const width = interpolate(frame, [0, 989], [0, 100], clamp);
  return (
    <div style={{position: 'absolute', left: 58, right: 58, bottom: 92, height: 7, borderRadius: 99, background: 'rgba(255,255,255,.13)', overflow: 'hidden'}}>
      <div style={{height: '100%', width: `${width}%`, borderRadius: 99, background: 'linear-gradient(90deg, #59dbff, #fff4b1)', boxShadow: '0 0 18px rgba(90,222,255,.75)'}} />
    </div>
  );
};

const AudioBars: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{position: 'absolute', left: 385, right: 385, bottom: 125, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5, opacity: .48}}>
      {Array.from({length: 24}, (_, i) => {
        const h = 6 + Math.abs(Math.sin(frame * 0.18 + i * 0.67)) * (12 + (i % 4) * 4);
        return <div key={i} style={{width: 4, height: h, borderRadius: 99, background: '#a9f3ff'}} />;
      })}
    </div>
  );
};

const FinalBurst: React.FC = () => {
  const frame = useCurrentFrame();
  const p = spring({frame: frame - 925, fps: 30, config: {damping: 12, stiffness: 125}});
  if (frame < 925) return null;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 290, display: 'flex', justifyContent: 'center', opacity: p, transform: `scale(${0.65 + p * 0.35})`}}>
      <div style={{fontFamily: 'Arial, sans-serif', textAlign: 'center', color: '#fff'}}>
        <div style={{fontSize: 34, letterSpacing: 8, fontWeight: 800, color: '#93edff'}}>¿TE VOLÓ LA CABEZA?</div>
        <div style={{fontSize: 92, fontWeight: 950, letterSpacing: -5, marginTop: 8, textShadow: '0 0 38px rgba(101,224,255,.52)'}}>SÍGUENOS</div>
      </div>
    </div>
  );
};

export const DinosaurWater: React.FC = () => {
  const frame = useCurrentFrame();
  const flash = interpolate(frame, [0, 5, 16], [0.75, 0.18, 0], clamp);
  const musicVolume = interpolate(frame, [0, 24, 890, 989], [0, 0.17, 0.17, 0], clamp);

  return (
    <AbsoluteFill style={{backgroundColor: '#020712', overflow: 'hidden'}}>
      {sceneFiles.map((_, index) => <SceneLayer key={index} index={index} />)}
      <AbsoluteFill style={{background: `radial-gradient(circle at 50% 42%, rgba(79,211,255,${0.05 + Math.sin(frame / 27) * 0.018}), transparent 48%)`}} />
      <TimeOrb />
      <WaterParticles />
      <Header />
      <Subtitle />
      <FinalBurst />
      <AudioBars />
      <ProgressBar />
      <AbsoluteFill style={{pointerEvents: 'none', opacity: .13, mixBlendMode: 'screen', backgroundImage: 'repeating-radial-gradient(circle at 30% 20%, rgba(255,255,255,.09) 0 1px, transparent 1px 4px)', backgroundSize: '5px 5px'}} />
      <AbsoluteFill style={{pointerEvents: 'none', background: `rgba(190,247,255,${flash})`}} />
      <Audio src={staticFile('narration.mp3')} volume={1} />
      <Audio src={staticFile('music.wav')} volume={musicVolume} />
    </AbsoluteFill>
  );
};
