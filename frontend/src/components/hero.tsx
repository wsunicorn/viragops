"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { ArrowRight, ChevronDown, MessageSquareText } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { StatCard } from "@/components/stat-card";
import { RevealGroup } from "@/components/reveal";
import { GOLDEN_SET_STATS, PHASES } from "@/lib/data/phases";
import { cn } from "@/lib/utils";

const donePhases = PHASES.filter((p) => p.status === "done").length;

export function Hero() {
  return (
    <section className="bg-grid relative flex min-h-svh flex-col items-center justify-center overflow-hidden px-4 pt-24 pb-16">
      {/* Ambient gradient orbs */}
      <motion.div
        aria-hidden
        className="absolute -top-32 left-1/4 h-112 w-md rounded-full bg-primary/25 blur-[120px]"
        animate={{ x: [0, 40, 0], y: [0, 30, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden
        className="absolute top-1/3 right-1/4 h-96 w-96 rounded-full bg-accent/20 blur-[120px]"
        animate={{ x: [0, -30, 0], y: [0, -20, 0] }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />
      <div className="pointer-events-none absolute inset-0 bg-linear-to-b from-transparent via-transparent to-background" />

      <div className="relative z-10 mx-auto flex max-w-4xl flex-col items-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs text-muted-foreground"
        >
          <span className="relative flex size-1.5">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-accent opacity-75" />
            <span className="relative inline-flex size-1.5 rounded-full bg-accent" />
          </span>
          Khóa luận tốt nghiệp · LLMOps/RAGOps full-scope · {donePhases}/12 phase hoàn tất
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-5xl leading-[1.05] font-bold tracking-tight text-balance sm:text-6xl md:text-7xl"
        >
          RAG hỏi-đáp tiếng Việt,
          <br />
          <span className="text-gradient">vận hành như production</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="mt-6 max-w-2xl text-lg text-muted-foreground text-pretty"
        >
          <span className="font-medium text-foreground">viRAGops</span> — nền tảng LLMOps/RAGOps đầy đủ
          vòng đời cho hệ thống hỏi-đáp quy chế đào tạo IUH: data pipeline, retrieval experiment, PromptOps,
          evaluation engine, model gateway — mọi con số trên trang này đều là số liệu thật, không mô phỏng.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="mt-9 flex flex-wrap items-center justify-center gap-3"
        >
          <Link href="/demo" className={cn(buttonVariants({ size: "lg" }), "group rounded-full px-6")}>
            <MessageSquareText className="size-4" />
            Thử hỏi-đáp thật
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/dashboard"
            className={cn(buttonVariants({ size: "lg", variant: "outline" }), "rounded-full border-white/15 px-6")}
          >
            Xem số liệu thực nghiệm
          </Link>
        </motion.div>

        <RevealGroup className="mt-16 grid w-full grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard value={`${GOLDEN_SET_STATS.total}`} label="câu hỏi golden set" />
          <StatCard value={`${GOLDEN_SET_STATS.documentCount}`} label="văn bản IUH thật" />
          <StatCard value="93.2%" label="recall@5 retrieval" />
          <StatCard value="8" label="phiên bản prompt (P0-P7)" />
        </RevealGroup>
      </div>

      <motion.div
        aria-hidden
        className="absolute bottom-8 left-1/2 -translate-x-1/2 text-muted-foreground"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
      >
        <ChevronDown className="size-5" />
      </motion.div>
    </section>
  );
}
