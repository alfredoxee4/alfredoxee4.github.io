import { FPS } from "./timings";

export const AQUA = "#3EE8FF";
export const GOLD = "#FFC53D";
export const WHITE = "#FFFFFF";
export const BG = "#03141F";

export const F = (s: number): number => Math.round(s * FPS);

export const hexToRgba = (hex: string, a: number): string => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${a})`;
};
