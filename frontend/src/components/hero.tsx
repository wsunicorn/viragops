"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { ArrowRight, MessageSquareText, MoveDown } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { HeroVisual } from "@/components/three/hero-visual";
import { PHASES, GOLDEN_SET_STATS } from "@/lib/data/phases";
import { cn } from "@/lib/utils";

const donePhases = PHASES.filter((p) => p.status === "done").length;

const EASE = [0.16, 1, 0.3, 1] as const;

/**
 * Hero bất đối xứng (split 55/45): trái = nội dung căn trái, phải = vật
 * thể 3D thật (React Three Fiber). Không căn giữa, không orb gradient
 * nhiều màu — một accent teal duy nhất.
 */
export function Hero() {
  return (
    <section className="bg-grid relative min-h-dvh overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-linear-to-b from-transparent via-transparent to-background" />

      <div className="relative z-10 mx-auto grid min-h-dvh max-w-7xl grid-cols-1 items-center gap-8 px-4 pt-28 pb-20 lg:grid-cols-[1.1fr_0.9fr] lg:gap-4 lg:pt-20">
        {/* ── Cột nội dung ─────────────────────────────────────────── */}
        <div className="max-w-2xl">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: EASE }}
            className="mb-7 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs text-muted-foreground"
          >
            <span className="relative flex size-1.5">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-accent opacity-75" />
              <span className="relative inline-flex size-1.5 rounded-full bg-accent" />
            </span>
            Khóa luận tốt nghiệp · {donePhases}/12 phase hoàn tất · số liệu thật 100%
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.08, ease: EASE }}
            className="text-5xl leading-[0.98] font-bold tracking-tighter text-balance sm:text-6xl xl:text-7xl"
          >
            RAG tiếng Việt,
            <br />
            vận hành{" "}
            <span className="text-gradient">như production.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.16, ease: EASE }}
            className="mt-7 max-w-xl text-lg leading-relaxed text-muted-foreground text-pretty"
          >
            <span className="font-medium text-foreground">viRAGops</span> quản lý trọn vòng đời hệ thống
            hỏi-đáp quy chế đào tạo IUH: dữ liệu, retrieval, prompt, model, evaluation, quality gate,
            observability và feedback — mỗi thay đổi đều phải đi qua cổng kiểm định bằng số đo thật.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.24, ease: EASE }}
            className="mt-9 flex flex-wrap items-center gap-3"
          >
            <Link href="/demo" className={cn(buttonVariants({ size: "lg" }), "group rounded-full px-6")}>
              <MessageSquareText className="size-4" />
              Thử hỏi-đáp thật
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/dashboard"
              className={cn(
                buttonVariants({ size: "lg", variant: "outline" }),
                "rounded-full border-white/15 px-6",
              )}
            >
              Số liệu thực nghiệm
            </Link>
          </motion.div>

          {/* Chỉ số chính — hàng ngang mono, không đóng khung card */}
          <motion.dl
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.34, ease: EASE }}
            className="mt-14 grid max-w-lg grid-cols-3 divide-x divide-white/10"
          >
            {[
              { v: `${GOLDEN_SET_STATS.total}`, l: "câu golden set" },
              { v: "93.2%", l: "recall@5" },
              { v: `${GOLDEN_SET_STATS.documentCount}`, l: "văn bản IUH thật" },
            ].map((s, i) => (
              <div key={s.l} className={cn("pr-5", i > 0 && "pl-5")}>
                <dt className="sr-only">{s.l}</dt>
                <dd className="font-mono text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                  {s.v}
                </dd>
                <dd className="mt-1 text-xs text-muted-foreground">{s.l}</dd>
              </div>
            ))}
          </motion.dl>
        </div>

        {/* ── Cột vật thể 3D ───────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.1, delay: 0.2, ease: EASE }}
          className="relative h-80 sm:h-105 lg:h-136"
        >
          <HeroVisual />
        </motion.div>
      </div>

      <motion.div
        aria-hidden
        className="absolute bottom-6 left-1/2 z-10 -translate-x-1/2 text-muted-foreground/70"
        animate={{ y: [0, 7, 0] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="flex items-center gap-2 text-xs">
          <MoveDown className="size-3.5" />
          cuộn để đi vào lõi hệ thống
        </div>
      </motion.div>
    </section>
  );
}
