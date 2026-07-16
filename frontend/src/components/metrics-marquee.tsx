// Kinetic marquee các số liệu THẬT — mỗi số trace về report trong
// docs/system/experiments/ (không có số trang trí). CSS animation thuần
// (translateX -50% loop khép kín), pause khi hover, tắt khi
// prefers-reduced-motion (globals.css).

const METRICS: { value: string; label: string }[] = [
  { value: "0.932", label: "recall@5 · hybrid DBSF" },
  { value: "300/300", label: "câu golden set approved" },
  { value: "0.90", label: "refusal accuracy · p7" },
  { value: "1.29s", label: "p95 latency · smoke eval" },
  { value: "1.000", label: "gate precision & recall · 16 kịch bản" },
  { value: "222", label: "chunk structure_aware" },
  { value: "$0.0009", label: "chi phí / câu hỏi" },
  { value: "9", label: "prompt variant p0–p8" },
  { value: "4-hop", label: "fallback Gemini ×3 → Ollama" },
  { value: "107", label: "lỗi thật được phân loại" },
];

export function MetricsMarquee() {
  const items = [...METRICS, ...METRICS]; // nhân đôi cho vòng lặp khép kín
  return (
    <div className="marquee-mask relative overflow-hidden border-y border-border py-4">
      <div className="marquee-track gap-10" style={{ "--marquee-duration": "48s" } as React.CSSProperties}>
        {items.map((m, i) => (
          <div key={i} className="flex shrink-0 items-baseline gap-2.5" aria-hidden={i >= METRICS.length}>
            <span className="font-mono text-lg font-semibold text-accent">{m.value}</span>
            <span className="text-sm whitespace-nowrap text-muted-foreground">{m.label}</span>
            <span className="ml-7 text-muted-foreground/30">·</span>
          </div>
        ))}
      </div>
    </div>
  );
}
