// Tech stack — 2 dải marquee ngược chiều (kinetic), pill mono. Nội dung
// là stack THẬT của repo (pyproject.toml, docker-compose.yml,
// frontend/package.json), không liệt kê công nghệ không dùng.

const ROW_A = [
  "FastAPI", "Python 3.11", "Qdrant · hybrid dense+sparse", "Gemini embedding-001",
  "BM25 tự viết", "LiteLLM gateway", "Gemini 3.1 Flash-Lite", "Gemini 3 Flash Preview",
  "Ollama · qwen2.5:7b", "PostgreSQL", "Valkey",
];

const ROW_B = [
  "Langfuse Cloud", "Prometheus", "Grafana", "GitHub Actions CI",
  "Docker Compose", "Next.js App Router", "React Three Fiber", "Tailwind CSS v4",
  "Motion", "GSAP ScrollTrigger", "Lenis",
];

function MarqueeRow({ items, reverse, duration }: { items: string[]; reverse?: boolean; duration: string }) {
  const doubled = [...items, ...items];
  return (
    <div className="marquee-mask overflow-hidden">
      <div
        className={`marquee-track items-center gap-3 py-2 ${reverse ? "marquee-reverse" : ""}`}
        style={{ "--marquee-duration": duration } as React.CSSProperties}
      >
        {doubled.map((item, i) => (
          <span
            key={i}
            aria-hidden={i >= items.length}
            className="shrink-0 rounded-full border border-border bg-foreground/3 px-4 py-2 font-mono text-sm whitespace-nowrap text-foreground/85"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

export function TechStack() {
  return (
    <div className="space-y-3">
      <MarqueeRow items={ROW_A} duration="56s" />
      <MarqueeRow items={ROW_B} duration="48s" reverse />
    </div>
  );
}
