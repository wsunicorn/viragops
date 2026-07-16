// Theme dùng chung cho mọi biểu đồ recharts — sửa bug tooltip "chữ bị
// khuất bởi nền": contentStyle trước đây hard-code nền tối palette cũ mà
// KHÔNG set màu chữ (recharts mặc định chữ xám đậm → chìm trong nền tối,
// còn ở light mode thì nền tooltip lại tối lạc lõng). Tooltip là div HTML
// nên CSS variable hoạt động đầy đủ → tự đổi theo theme.
//
// Màu trục/lưới/legend đặt bằng CSS rule trong globals.css (SVG
// presentation attribute không hỗ trợ var(), nhưng CSS rule thì override
// được attribute — xem mục "Recharts theme" trong globals.css).

import type { CSSProperties } from "react";

export const TOOLTIP_CONTENT_STYLE: CSSProperties = {
  background: "var(--popover)",
  border: "1px solid var(--border)",
  borderRadius: 12,
  color: "var(--popover-foreground)",
  fontSize: 12,
  boxShadow: "0 12px 32px -12px rgb(0 0 0 / 0.35)",
  padding: "8px 12px",
};

export const TOOLTIP_LABEL_STYLE: CSSProperties = {
  color: "var(--popover-foreground)",
  fontWeight: 600,
  marginBottom: 4,
};

export const TOOLTIP_ITEM_STYLE: CSSProperties = {
  color: "var(--popover-foreground)",
};

// nổi trên mọi card/glass panel xung quanh
export const TOOLTIP_WRAPPER_STYLE: CSSProperties = {
  zIndex: 40,
  outline: "none",
};

// xám trung tính mờ — nhìn được trên cả nền sáng lẫn tối (cursor là SVG
// rect nhận attribute, không dùng var() được)
export const CURSOR_FILL = { fill: "rgba(128,128,128,0.14)" } as const;

export const MONO_TICK = { fontSize: 11, fontFamily: "var(--font-jetbrains-mono)" } as const;
