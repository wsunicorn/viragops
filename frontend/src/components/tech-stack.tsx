import { RevealGroup, RevealItem } from "@/components/reveal";

const STACK: { group: string; items: string[] }[] = [
  { group: "Backend", items: ["FastAPI", "Python 3.11", "Pydantic"] },
  { group: "Retrieval", items: ["Qdrant (hybrid dense+sparse)", "Gemini embedding-001", "BM25 tự viết"] },
  { group: "Model Gateway", items: ["LiteLLM proxy", "Gemini 3.1 Flash-Lite / 3 Flash Preview", "Ollama (qwen2.5:7b)"] },
  { group: "PromptOps", items: ["PostgreSQL registry", "8 prompt variant", "Activation policy có kiểm soát"] },
  { group: "Storage", items: ["PostgreSQL", "Qdrant", "Valkey/Redis"] },
  { group: "Frontend", items: ["Next.js (App Router)", "Tailwind CSS v4", "Motion + GSAP + Lenis"] },
];

export function TechStack() {
  return (
    <RevealGroup className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3" stagger={0.06}>
      {STACK.map((s) => (
        <RevealItem key={s.group}>
          <div className="h-full rounded-xl border border-white/10 bg-white/[0.02] p-5">
            <h4 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{s.group}</h4>
            <ul className="mt-3 space-y-1.5">
              {s.items.map((item) => (
                <li key={item} className="text-sm text-foreground/90">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </RevealItem>
      ))}
    </RevealGroup>
  );
}
