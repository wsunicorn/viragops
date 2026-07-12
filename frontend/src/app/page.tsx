import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Hero } from "@/components/hero";
import { SectionHeading } from "@/components/section-heading";
import { ArchitectureGrid } from "@/components/architecture-grid";
import { PhaseTimeline } from "@/components/phase-timeline";
import { FindingsSection } from "@/components/findings-section";
import { TechStack } from "@/components/tech-stack";
import { SiteFooter } from "@/components/site-footer";
import { buttonVariants } from "@/components/ui/button";
import { Reveal } from "@/components/reveal";
import { cn } from "@/lib/utils";

export default function Home() {
  return (
    <>
      <Hero />

      <section className="mx-auto max-w-6xl px-4 py-24 sm:py-32">
        <SectionHeading
          eyebrow="Kiến trúc"
          title="9 module LLMOps/RAGOps"
          description="Hệ thống không chỉ trả lời câu hỏi — quản lý toàn bộ vòng đời dữ liệu, prompt, model, evaluation, và feedback. Chấm xanh = đã triển khai thật, không phải bản vẽ kế hoạch."
        />
        <div className="mt-12">
          <ArchitectureGrid />
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

      <section className="mx-auto max-w-6xl px-4 py-24 sm:py-32">
        <SectionHeading
          eyebrow="Kỹ thuật đáng chú ý"
          title="4 câu chuyện kỹ thuật thật"
          description="Một hệ thống LLMOps nghiêm túc phải tự phát hiện lỗi của chính nó — kể cả lỗi do lần sửa trước gây ra. Đây là ghi nhận trung thực, không phải highlight reel."
        />
        <div className="mt-12">
          <FindingsSection />
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-24 sm:py-32">
        <SectionHeading eyebrow="Công nghệ" title="Tech stack" />
        <div className="mt-12">
          <TechStack />
        </div>
      </section>

      <section className="px-4 py-24 sm:py-32">
        <Reveal className="mx-auto max-w-3xl rounded-3xl border border-white/10 bg-linear-to-br from-primary/15 via-white/2 to-accent/10 p-10 text-center sm:p-14">
          <h2 className="text-3xl font-semibold text-balance sm:text-4xl">Tự mình thử hệ thống hỏi-đáp thật</h2>
          <p className="mt-4 text-muted-foreground text-pretty">
            Gõ một câu hỏi về quy chế đào tạo IUH — hệ thống sẽ retrieve, sinh câu trả lời có trích dẫn, và từ
            chối trung thực khi không có căn cứ. Không có câu trả lời nào được dàn dựng trước.
          </p>
          <Link
            href="/demo"
            className={cn(buttonVariants({ size: "lg" }), "group mt-8 rounded-full px-7")}
          >
            Vào trang demo
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </Reveal>
      </section>

      <SiteFooter />
    </>
  );
}
