"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import { FlaskConical } from "lucide-react";
import { FINDINGS } from "@/lib/data/findings";

/**
 * Sticky scroll stack: mỗi "câu chuyện kỹ thuật" là một thẻ lớn dính lại
 * gần đỉnh viewport; thẻ sau trượt lên đè thẻ trước, thẻ bị đè thu nhỏ
 * nhẹ + tối dần — cảm giác xếp chồng vật lý. Motion useScroll per-card,
 * transform-only (không animate width/height).
 */

function StackCard({ i, total }: { i: number; total: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const f = FINDINGS[i];
  // tiến độ của ĐOẠN sau thẻ này (thẻ kế tiếp đang trườn lên đè)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.94 - (total - i) * 0.004]);
  const brightness = useTransform(scrollYProgress, [0, 1], [1, 0.55]);
  const filter = useTransform(brightness, (b) => `brightness(${b})`);

  return (
    <div ref={ref} className="h-[55vh] sm:h-[60vh]">
      <motion.article
        style={{ scale, filter, top: `calc(6rem + ${i * 1.25}rem)` }}
        className="glass-edge sticky mx-auto max-w-3xl overflow-hidden rounded-3xl bg-card p-7 will-change-transform sm:p-10"
      >
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <FlaskConical className="size-4 text-accent" />
            <span className="text-xs font-semibold tracking-[0.15em] text-accent uppercase">{f.tag}</span>
          </div>
          <span className="font-mono text-xs text-muted-foreground/60">
            {String(i + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
          </span>
        </div>
        <h3 className="text-2xl font-semibold tracking-tight text-balance sm:text-3xl">{f.title}</h3>
        <p className="mt-4 max-w-[65ch] text-base leading-relaxed text-muted-foreground text-pretty">
          {f.story}
        </p>
        <p className="mt-6 border-t border-white/8 pt-4 font-mono text-xs text-muted-foreground/70">
          {f.evidence}
        </p>
      </motion.article>
    </div>
  );
}

export function FindingsStack() {
  return (
    <div className="pb-[10vh]">
      {FINDINGS.map((f, i) => (
        <StackCard key={f.title} i={i} total={FINDINGS.length} />
      ))}
    </div>
  );
}
