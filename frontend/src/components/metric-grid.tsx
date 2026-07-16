import { Check, X } from "lucide-react";
import { RevealGroup, RevealItem } from "@/components/reveal";
import type { MetricRow } from "@/lib/data/eval";
import { cn } from "@/lib/utils";

export function MetricGrid({ metrics }: { metrics: MetricRow[] }) {
  return (
    <RevealGroup className="grid grid-cols-2 gap-3 sm:grid-cols-3" stagger={0.04}>
      {metrics.map((m) => (
        <RevealItem key={m.label}>
          <div
            className={cn(
              "h-full rounded-xl border p-4",
              m.pass === undefined
                ? "border-border bg-foreground/2"
                : m.pass
                  ? "border-accent/20 bg-accent/[0.04]"
                  : "border-amber-500/25 bg-amber-500/[0.04]",
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-xs text-muted-foreground">{m.label}</span>
              {m.pass !== undefined ? (
                m.pass ? (
                  <Check className="size-3.5 shrink-0 text-accent" />
                ) : (
                  <X className="size-3.5 shrink-0 text-amber-400" />
                )
              ) : null}
            </div>
            <div className="mt-1.5 text-xl font-semibold">{m.value}</div>
            {m.target !== undefined ? (
              <div className="mt-0.5 font-mono text-[11px] text-muted-foreground/60">target {m.target}</div>
            ) : null}
          </div>
        </RevealItem>
      ))}
    </RevealGroup>
  );
}
