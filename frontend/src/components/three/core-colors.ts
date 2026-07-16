// Bảng màu cho vật thể 3D theo theme — file riêng KHÔNG import three.js,
// để hero-visual.tsx (bundle chính) đọc được mà không phá vỡ code-splitting
// của dynamic import ssr:false.

export type CoreColors = {
  cover: string;
  coverEdge: string;
  page: string;
  particle: string;
  glow: string;
  ambient: number;
};

export const DARK_COLORS: CoreColors = {
  cover: "#115e59",
  coverEdge: "#134e4a",
  page: "#ece9e2",
  particle: "#5eead4",
  glow: "#2dd4bf",
  ambient: 0.55,
};

export const LIGHT_COLORS: CoreColors = {
  cover: "#0f766e",
  coverEdge: "#115e59",
  page: "#fffdf6",
  particle: "#0d9488",
  glow: "#14b8a6",
  ambient: 0.95,
};
