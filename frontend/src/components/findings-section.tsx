import { FlaskConical } from "lucide-react";
import { RevealGroup, RevealItem } from "@/components/reveal";
import { FINDINGS } from "@/lib/data/findings";

export function FindingsSection() {
  return (
    <RevealGroup className="grid grid-cols-1 gap-4 md:grid-cols-2" stagger={0.1}>
      {FINDINGS.map((f) => (
        <RevealItem key={f.title}>
          <div className="h-full rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <div className="mb-3 flex items-center gap-2">
              <FlaskConical className="size-4 text-accent" />
              <span className="text-xs font-semibold tracking-wide text-accent uppercase">{f.tag}</span>
            </div>
            <h3 className="text-lg font-semibold text-balance">{f.title}</h3>
            <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground text-pretty">{f.story}</p>
            <p className="mt-4 border-t border-white/10 pt-3 font-mono text-[11px] text-muted-foreground/70">
              {f.evidence}
            </p>
          </div>
        </RevealItem>
      ))}
    </RevealGroup>
  );
}
