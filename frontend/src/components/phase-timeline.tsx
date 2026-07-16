"use client";

import { motion, useScroll, useTransform } from "motion/react";
import { useRef } from "react";
import { CheckCircle2, CircleDashed, Loader2 } from "lucide-react";
import { PHASES, type PhaseStatus } from "@/lib/data/phases";
import { cn } from "@/lib/utils";

const STATUS_ICON: Record<PhaseStatus, typeof CheckCircle2> = {
  done: CheckCircle2,
  in_progress: Loader2,
  planned: CircleDashed,
};

const STATUS_LABEL: Record<PhaseStatus, string> = {
  done: "Hoàn tất",
  in_progress: "Đang làm",
  planned: "Kế hoạch",
};

export function PhaseTimeline() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 0.8", "end 0.3"] });
  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  return (
    <div ref={ref} className="relative">
      <div className="absolute top-0 bottom-0 left-[15px] w-px bg-foreground/10 sm:left-[19px]" />
      <motion.div
        className="absolute top-0 left-[15px] w-px bg-linear-to-b from-primary to-accent sm:left-[19px]"
        style={{ height: lineHeight }}
      />
      <ol className="space-y-6">
        {PHASES.map((phase, i) => {
          const Icon = STATUS_ICON[phase.status];
          return (
            <motion.li
              key={phase.n}
              initial={{ opacity: 0, x: -16 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ duration: 0.5, delay: (i % 4) * 0.05 }}
              className="relative flex gap-4 pl-0 sm:gap-5"
            >
              <div
                className={cn(
                  "relative z-10 flex size-8 shrink-0 items-center justify-center rounded-full border sm:size-10",
                  phase.status === "done" && "border-accent/40 bg-accent/15 text-accent",
                  phase.status === "in_progress" && "border-primary/40 bg-primary/15 text-primary",
                  phase.status === "planned" && "border-border bg-foreground/5 text-muted-foreground",
                )}
              >
                <Icon className={cn("size-4", phase.status === "in_progress" && "animate-spin")} />
              </div>
              <div className="min-w-0 flex-1 rounded-xl border border-border bg-foreground/2 p-4">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="font-mono text-xs text-muted-foreground">Phase {phase.n}</span>
                  <span className="text-xs text-muted-foreground/70">{phase.weeks}</span>
                  <span
                    className={cn(
                      "ml-auto rounded-full px-2 py-0.5 text-[11px] font-medium",
                      phase.status === "done" && "bg-accent/15 text-accent",
                      phase.status === "in_progress" && "bg-primary/15 text-primary",
                      phase.status === "planned" && "bg-foreground/5 text-muted-foreground",
                    )}
                  >
                    {STATUS_LABEL[phase.status]}
                  </span>
                </div>
                <h3 className="mt-1.5 text-base font-semibold">{phase.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{phase.summary}</p>
                {phase.highlight ? (
                  <p className="mt-2 inline-block rounded-md bg-primary/10 px-2 py-1 font-mono text-xs text-primary">
                    {phase.highlight}
                  </p>
                ) : null}
              </div>
            </motion.li>
          );
        })}
      </ol>
    </div>
  );
}
