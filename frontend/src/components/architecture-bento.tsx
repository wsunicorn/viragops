"use client";

import { memo, useEffect, useRef, useState } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "motion/react";
import {
  Database,
  Search,
  MessagesSquare,
  FileEdit,
  Gauge,
  ShieldCheck,
  Activity,
  Zap,
  MessageCircleWarning,
  type LucideIcon,
} from "lucide-react";
import { RevealGroup, RevealItem } from "@/components/reveal";
import { cn } from "@/lib/utils";

/**
 * Bento 2.0 cho 9 module — lưới bất đối xứng (không phải 3 cột đều nhau),
 * mỗi ô có tilt 3D theo con trỏ (useMotionValue/useSpring — không setState
 * mỗi frame) và một vài ô mang micro-animation vĩnh cửu được cô lập trong
 * component memo riêng để không re-render lưới.
 *
 * Trạng thái done: TOÀN BỘ 9 module đã triển khai thật (Phase 1-11).
 */

type Module = {
  n: number;
  title: string;
  role: string;
  output: string;
  icon: LucideIcon;
  span: string; // lg:col-span-*
  widget?: "gate" | "qa" | "pulse";
};

// Lưới 6 cột bất đối xứng (3-3 / 4-2 / 2-2-2 / 3-3) — tránh mẫu "3 cột
// card đều nhau" bị cấm trong design skill.
const MODULES: Module[] = [
  { n: 1, title: "DataOps / RAGOps", role: "Ingest, OCR, chunk, embed, index — mọi dữ liệu có version", output: "data_version · index_version · 222 chunks", icon: Database, span: "lg:col-span-3" },
  { n: 2, title: "Retrieval Experiment", role: "8 config retrieval + 4 chiến lược chunking, đo thật 2 lần", output: "hybrid DBSF · recall@5 = 0.932", icon: Search, span: "lg:col-span-3" },
  { n: 3, title: "RAG Runtime", role: "Hỏi-đáp có trích dẫn, refusal 2 lớp, citation fail-closed — trái tim của hệ thống, mọi module khác phục vụ nó", output: "answer · citations · trace_id", icon: MessagesSquare, span: "lg:col-span-4", widget: "qa" },
  { n: 4, title: "PromptOps", role: "Registry PostgreSQL, activation phải có bằng chứng eval", output: "9 variant p0–p8", icon: FileEdit, span: "lg:col-span-2" },
  { n: 5, title: "Evaluation Engine", role: "Eval 4 tầng qua RagService thật + LLM judge", output: "summary JSON cho gate", icon: Gauge, span: "lg:col-span-2" },
  { n: 6, title: "Quality Gate", role: "Chặn regression trước deploy — đã BLOCK thật trên CI", output: "16 kịch bản · 1.000", icon: ShieldCheck, span: "lg:col-span-2", widget: "gate" },
  { n: 7, title: "Observability / Cost", role: "Langfuse tracing, Prometheus, Grafana 16 panel", output: "latency · cost · errors", icon: Activity, span: "lg:col-span-2", widget: "pulse" },
  { n: 8, title: "Optimization / Routing", role: "Semantic cache, compression, dynamic top-k, auto-routing", output: "O1-O8 đo thật · mặc định tắt có chủ đích", icon: Zap, span: "lg:col-span-3" },
  { n: 9, title: "Feedback Loop", role: "Feedback gắn trace, phân loại lỗi, backlog cải tiến", output: "26 feedback thật · 2 cluster lỗi", icon: MessageCircleWarning, span: "lg:col-span-3" },
];

/* ── Micro-animation vĩnh cửu (memo, cô lập) ────────────────────────── */

const GATE_STATES = [
  { label: "PASS", cls: "text-accent border-accent/30 bg-accent/10" },
  { label: "WARN", cls: "text-amber-300 border-amber-400/30 bg-amber-400/10" },
  { label: "BLOCK", cls: "text-red-300 border-red-400/30 bg-red-400/10" },
] as const;

const GateWidget = memo(function GateWidget() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((v) => (v + 1) % GATE_STATES.length), 2200);
    return () => clearInterval(t);
  }, []);
  const s = GATE_STATES[i];
  return (
    <motion.span
      key={s.label}
      initial={{ opacity: 0, y: 4, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 22 }}
      className={cn("inline-flex rounded-md border px-2 py-0.5 font-mono text-[11px] font-semibold", s.cls)}
    >
      {s.label}
    </motion.span>
  );
});

const QA_LINES = ["“Điều kiện tốt nghiệp cần gì?”", "→ retrieve 5 chunk", "→ trả lời + 3 trích dẫn"] as const;

const QaWidget = memo(function QaWidget() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((v) => (v + 1) % QA_LINES.length), 2400);
    return () => clearInterval(t);
  }, []);
  return (
    <motion.span
      key={i}
      initial={{ opacity: 0, x: 6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 24 }}
      className="inline-block font-mono text-[11px] text-accent/90"
    >
      {QA_LINES[i]}
    </motion.span>
  );
});

const PulseWidget = memo(function PulseWidget() {
  return (
    <span className="flex items-end gap-0.5" aria-hidden>
      {[0, 1, 2, 3, 4].map((i) => (
        <motion.span
          key={i}
          className="w-1 rounded-full bg-accent/70"
          animate={{ height: [4, 12, 5, 14, 4] }}
          transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.18, ease: "easeInOut" }}
        />
      ))}
    </span>
  );
});

/* ── Ô bento với tilt 3D + spotlight border theo con trỏ ─────────────── */

function BentoTile({ m }: { m: Module }) {
  const ref = useRef<HTMLDivElement>(null);
  const px = useMotionValue(0.5);
  const py = useMotionValue(0.5);
  const rx = useSpring(useTransform(py, [0, 1], [4, -4]), { stiffness: 150, damping: 20 });
  const ry = useSpring(useTransform(px, [0, 1], [-4, 4]), { stiffness: 150, damping: 20 });

  function onPointerMove(e: React.PointerEvent) {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    px.set((e.clientX - r.left) / r.width);
    py.set((e.clientY - r.top) / r.height);
    el.style.setProperty("--spot-x", `${e.clientX - r.left}px`);
    el.style.setProperty("--spot-y", `${e.clientY - r.top}px`);
  }

  function onPointerLeave() {
    px.set(0.5);
    py.set(0.5);
  }

  return (
    <motion.div
      ref={ref}
      onPointerMove={onPointerMove}
      onPointerLeave={onPointerLeave}
      style={{ rotateX: rx, rotateY: ry, transformPerspective: 900 }}
      className="group relative h-full overflow-hidden rounded-3xl border border-white/9 bg-white/3 p-6 will-change-transform"
    >
      {/* spotlight theo con trỏ */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(340px circle at var(--spot-x, 50%) var(--spot-y, 50%), oklch(0.83 0.138 172 / 8%), transparent 65%)",
        }}
      />
      <div className="relative">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex size-10 items-center justify-center rounded-xl bg-accent/10 text-accent">
            <m.icon className="size-5" />
          </div>
          <span className="font-mono text-xs text-muted-foreground">M{m.n}</span>
        </div>
        <h3 className="text-sm font-semibold tracking-tight">{m.title}</h3>
        <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{m.role}</p>
        <div className="mt-4 flex min-h-6 items-center justify-between gap-2 border-t border-white/8 pt-3">
          <p className="font-mono text-[11px] text-muted-foreground/70">{m.output}</p>
          {m.widget === "gate" ? <GateWidget /> : null}
          {m.widget === "qa" ? <QaWidget /> : null}
          {m.widget === "pulse" ? <PulseWidget /> : null}
        </div>
        <span className="absolute -top-1 -right-1 flex size-1.5" title="Đã triển khai thật">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-accent opacity-60" />
          <span className="relative inline-flex size-1.5 rounded-full bg-accent" />
        </span>
      </div>
    </motion.div>
  );
}

export function ArchitectureBento() {
  return (
    <RevealGroup className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-6" stagger={0.06}>
      {MODULES.map((m) => (
        <RevealItem key={m.n} className={cn("h-full", m.span)}>
          <BentoTile m={m} />
        </RevealItem>
      ))}
    </RevealGroup>
  );
}
