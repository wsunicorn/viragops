import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Hero } from "@/components/hero";
import { MetricsMarquee } from "@/components/metrics-marquee";
import { ZoomJourney } from "@/components/zoom-journey";
import { SectionHeading } from "@/components/section-heading";
import { ArchitectureBento } from "@/components/architecture-bento";
import { PhaseTimeline } from "@/components/phase-timeline";
import { FindingsStack } from "@/components/findings-stack";
import { TechStack } from "@/components/tech-stack";
import { SiteFooter } from "@/components/site-footer";
import { Magnetic } from "@/components/magnetic";
import { buttonVariants } from "@/components/ui/button";
import { Reveal } from "@/components/reveal";
import { cn } from "@/lib/utils";

export default function Home() {
  return (
    <>
      <Hero />

      <MetricsMarquee />

      {/* Scrolltelling: cuộn để "bay xuyên vào lõi" pipeline RAG */}
      <ZoomJourney />

      <section className="mx-auto max-w-7xl px-4 py-24 sm:py-32">
        <SectionHeading
          eyebrow="Kiến trúc"
          title="9 module LLMOps/RAGOps"
          description="Hệ thống không chỉ trả lời câu hỏi — quản lý toàn bộ vòng đời dữ liệu, prompt, model, evaluation, và feedback. Cả 9 module đều đã triển khai và verify thật."
        />
        <div className="mt-12">
          <ArchitectureBento />
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-4 py-24 sm:py-32">
        <SectionHeading
          eyebrow="Tiến độ thật"
          title="Hành trình 12 phase"
          description="Mỗi phase đều chạy thật (Docker, API thật, quota Gemini thật) — không chỉ viết code rồi đánh dấu xong."
        />
        <div className="mt-14">
          <PhaseTimeline />
        </div>
      </section>

      <section className="px-4 py-24 sm:py-28">
        <SectionHeading
          className="mx-auto max-w-3xl"
          eyebrow="Kỹ thuật đáng chú ý"
          title="4 câu chuyện kỹ thuật thật"
          description="Một hệ thống LLMOps nghiêm túc phải tự phát hiện lỗi của chính nó — kể cả lỗi do lần sửa trước gây ra. Cuộn để lật từng câu chuyện."
        />
        <div className="mt-10">
          <FindingsStack />
        </div>
      </section>

      <section className="py-24 sm:py-32">
        <SectionHeading className="mx-auto max-w-7xl px-4" eyebrow="Công nghệ" title="Tech stack" />
        <div className="mt-12">
          <TechStack />
        </div>
      </section>

      <section className="px-4 py-24 sm:py-32">
        <Reveal className="glass-edge relative mx-auto max-w-3xl overflow-hidden rounded-[2.5rem] bg-card/70 p-10 text-center backdrop-blur-xl sm:p-14">
          <div
            aria-hidden
            className="pointer-events-none absolute -top-24 left-1/2 size-72 -translate-x-1/2 rounded-full bg-accent/12 blur-[100px]"
          />
          <h2 className="relative text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
            Tự mình thử hệ thống hỏi-đáp thật
          </h2>
          <p className="relative mt-4 text-muted-foreground text-pretty">
            Gõ một câu hỏi về quy chế đào tạo IUH — hệ thống sẽ retrieve, sinh câu trả lời có trích dẫn, và
            từ chối trung thực khi không có căn cứ. Không có câu trả lời nào được dàn dựng trước.
          </p>
          <div className="relative mt-8 flex justify-center">
            <Magnetic>
              <Link href="/demo" className={cn(buttonVariants({ size: "lg" }), "group rounded-full px-7")}>
                Vào trang demo
                <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </Magnetic>
          </div>
        </Reveal>
      </section>

      <SiteFooter />
    </>
  );
}
