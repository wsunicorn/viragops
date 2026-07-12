import {
  Database,
  Search,
  MessagesSquare,
  FileEdit,
  Gauge,
  ShieldCheck,
  Activity,
  Gauge as GaugeIcon,
  MessageCircleWarning,
  type LucideIcon,
} from "lucide-react";
import { RevealGroup, RevealItem } from "@/components/reveal";

const MODULES: { n: number; title: string; role: string; output: string; icon: LucideIcon; done: boolean }[] = [
  { n: 1, title: "DataOps/RAGOps", role: "Ingest, clean, chunk, embed, index, version dữ liệu", output: "data_version, index_version, chunks", icon: Database, done: true },
  { n: 2, title: "Retrieval Experiment", role: "So sánh chunking/retrieval/reranking", output: "best retrieval config, metrics", icon: Search, done: true },
  { n: 3, title: "RAG Runtime", role: "API hỏi-đáp, context assembly, citation, refusal", output: "answer, citations, trace_id", icon: MessagesSquare, done: true },
  { n: 4, title: "PromptOps", role: "Quản lý vòng đời prompt, so sánh phiên bản", output: "prompt_version, comparison", icon: FileEdit, done: true },
  { n: 5, title: "Evaluation Engine", role: "Đánh giá 4 tầng: retrieval/context/generation/ops", output: "eval report, metric scores", icon: Gauge, done: true },
  { n: 6, title: "Quality Gate", role: "Chặn regression trước deploy", output: "PASS / WARN / BLOCK", icon: ShieldCheck, done: false },
  { n: 7, title: "Observability/Cost", role: "Trace, metric, dashboard vận hành", output: "latency, cost, error labels", icon: Activity, done: false },
  { n: 8, title: "Optimization/Routing", role: "Cache, compression, routing, fallback", output: "optimized config", icon: GaugeIcon, done: false },
  { n: 9, title: "Feedback Loop", role: "Thu feedback, phân loại lỗi, cải tiến", output: "improvement backlog", icon: MessageCircleWarning, done: false },
];

export function ArchitectureGrid() {
  return (
    <RevealGroup className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {MODULES.map((m) => (
        <RevealItem key={m.n}>
          <div className="group relative h-full overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] p-5 transition-colors hover:border-primary/30 hover:bg-white/[0.05]">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <m.icon className="size-5" />
              </div>
              <span className="font-mono text-xs text-muted-foreground">Module {m.n}</span>
            </div>
            <h3 className="text-sm font-semibold">{m.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{m.role}</p>
            <p className="mt-3 font-mono text-[11px] text-muted-foreground/70">→ {m.output}</p>
            <span
              className={
                "absolute top-4 right-4 size-1.5 rounded-full " + (m.done ? "bg-accent" : "bg-muted-foreground/40")
              }
              title={m.done ? "Đã triển khai" : "Trong kế hoạch"}
            />
          </div>
        </RevealItem>
      ))}
    </RevealGroup>
  );
}
