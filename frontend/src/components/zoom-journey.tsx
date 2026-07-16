"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  Database,
  Grid2x2,
  GitMerge,
  MessageSquareQuote,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";
import { Reveal } from "@/components/reveal";
import { cn } from "@/lib/utils";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

/**
 * ZoomJourney — scrolltelling "đi xuyên vào lõi hệ thống": section được
 * pin lại, cuộn chuột đẩy "camera" tiến sâu qua 5 lớp của pipeline RAG
 * (CSS 3D perspective + translateZ, GSAP ScrollTrigger scrub).
 *
 * Kỹ thuật: một proxy {z} được tween theo scroll; mỗi frame gán transform/
 * opacity trực tiếp vào ref của từng lớp — KHÔNG setState mỗi frame
 * (chỉ setState khi đổi lớp active, tối đa 5 lần/lượt cuộn).
 *
 * GSAP được cô lập trong component này (không trộn với Motion trong cùng
 * cây — đúng quy tắc design skill §8). Mobile/reduced-motion: fallback
 * thẻ dọc tĩnh, không pin.
 */

type Layer = {
  n: string;
  title: string;
  desc: string;
  metrics: string[];
  icon: LucideIcon;
};

const LAYERS: Layer[] = [
  {
    n: "01",
    title: "Nguồn tri thức",
    desc: "10 văn bản quy chế IUH thật — quy chế tín chỉ, thi & đánh giá, sổ tay sinh viên. PDF scan được OCR bằng Gemini multimodal, đối chiếu thủ công từng số liệu.",
    metrics: ["QĐ 1482/QĐ-ĐHCN", "QĐ 610/QĐ-ĐHCN", "Sổ tay SV 2024", "OCR đúng 100% trang bìa"],
    icon: Database,
  },
  {
    n: "02",
    title: "Chunk & Embed",
    desc: "Chunking structure_aware tách theo \"Điều\", giữ nguyên \"Khoản\" — thắng 3 chiến lược khác khi đo thật. Mỗi chunk mang 2 vector: dense 768d (Gemini) + sparse BM25 tự viết.",
    metrics: ["222 chunk", "768 chiều dense", "BM25 tự cài đặt", "4 chiến lược đã so sánh"],
    icon: Grid2x2,
  },
  {
    n: "03",
    title: "Truy hồi lai",
    desc: "Qdrant hybrid search: nhánh dense + nhánh sparse chạy song song rồi hợp nhất bằng DBSF — thắng cả 8 config đã đo, kể cả các config có reranker.",
    metrics: ["recall@5 = 0.932", "DBSF fusion", "p95 retrieval 19ms", "8 config đã đo thật"],
    icon: GitMerge,
  },
  {
    n: "04",
    title: "Sinh câu trả lời",
    desc: "Prompt p7 (vòng lặp thứ 8) qua LiteLLM gateway với 4 chặng fallback. Citation fail-closed: chunk bịa bị loại, câu trả lời mất hết trích dẫn tự hạ thành từ chối.",
    metrics: ["citation acc 0.838", "refusal acc 0.90", "fallback 4 chặng", "9 prompt p0–p8"],
    icon: MessageSquareQuote,
  },
  {
    n: "05",
    title: "Cổng kiểm định",
    desc: "Mọi thay đổi phải qua Quality Gate: 16 kịch bản giả lập, chặn đúng 9/9 thay đổi xấu, 0 false positive. Trace lên Langfuse, metric vào Prometheus/Grafana.",
    metrics: ["precision 1.000", "recall 1.000", "PASS / WARN / BLOCK", "CI chặn thật 1 lần"],
    icon: ShieldCheck,
  },
];

const SPACING = 1000; // px translateZ giữa các lớp
const INTRO = 500; // đoạn đầu dành cho vỏ ("đi xuyên qua vỏ hệ thống")

function layerOpacity(effZ: number): number {
  // hiện dần khi tiến tới, mờ đi khi "bay xuyên qua" camera
  if (effZ < -2100) return 0;
  if (effZ < -800) return (effZ + 2100) / 1300;
  if (effZ < 120) return 1;
  if (effZ < 420) return 1 - (effZ - 120) / 300;
  return 0;
}

export function ZoomJourney() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const layerRefs = useRef<(HTMLDivElement | null)[]>([]);
  const barRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const mm = gsap.matchMedia();

    mm.add("(min-width: 768px) and (prefers-reduced-motion: no-preference)", () => {
      const totalZ = INTRO + SPACING * (LAYERS.length - 1) + 600;
      const proxy = { z: 0 };
      let lastIdx = -1;

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: wrapRef.current,
          start: "top top",
          end: `+=${LAYERS.length * 110}%`,
          scrub: 0.8,
          pin: true,
          anticipatePin: 1,
        },
      });

      tl.to(proxy, {
        z: totalZ,
        ease: "none",
        onUpdate: () => {
          const p = proxy.z;
          // vỏ hệ thống: phóng to + mờ dần trong đoạn INTRO
          if (shellRef.current) {
            const k = Math.min(1, p / INTRO);
            shellRef.current.style.transform = `translate(-50%, -50%) scale(${1 + k * 5})`;
            shellRef.current.style.opacity = String(1 - k);
          }
          LAYERS.forEach((_, i) => {
            const el = layerRefs.current[i];
            if (!el) return;
            const baseZ = -(INTRO + i * SPACING);
            const effZ = baseZ + p;
            el.style.transform = `translate(-50%, -50%) translateZ(${effZ}px)`;
            el.style.opacity = String(layerOpacity(effZ));
            el.style.pointerEvents = effZ > -800 && effZ < 120 ? "auto" : "none";
          });
          if (barRef.current) {
            barRef.current.style.transform = `scaleY(${p / totalZ})`;
          }
          const idx = Math.min(
            LAYERS.length - 1,
            Math.max(0, Math.round((p - INTRO) / SPACING)),
          );
          if (idx !== lastIdx) {
            lastIdx = idx;
            setActive(idx);
          }
        },
      });

      return () => {
        tl.scrollTrigger?.kill();
        tl.kill();
      };
    });

    return () => mm.revert();
  }, []);

  return (
    <section aria-label="Đi vào lõi hệ thống">
      {/* ── Desktop: cảnh 3D pin theo scroll ─────────────────────────── */}
      <div ref={wrapRef} className="relative hidden h-dvh overflow-hidden md:block">
        {/* stage có perspective — mọi lớp là con của nó */}
        <div className="absolute inset-0 [perspective:1200px] [transform-style:preserve-3d]">
          {/* Vỏ hệ thống — thứ ta "bay xuyên qua" đầu tiên */}
          <div
            ref={shellRef}
            className="absolute top-1/2 left-1/2 flex size-[64vmin] -translate-x-1/2 -translate-y-1/2 items-center justify-center will-change-transform"
          >
            <div className="absolute inset-0 rounded-full border border-accent/35" />
            <div className="absolute inset-8 rounded-full border border-dashed border-accent/20" />
            <p className="font-mono text-xs tracking-[0.35em] text-accent/90 uppercase">
              viRAGops · core
            </p>
          </div>

          {LAYERS.map((layer, i) => (
            <div
              key={layer.n}
              ref={(el) => {
                layerRefs.current[i] = el;
              }}
              className="glass-edge absolute top-1/2 left-1/2 w-[min(560px,80vw)] rounded-3xl bg-card/70 p-8 opacity-0 backdrop-blur-xl will-change-transform"
              style={{ transform: "translate(-50%, -50%) translateZ(-4000px)" }}
            >
              <div className="flex items-center gap-3">
                <span className="flex size-11 items-center justify-center rounded-2xl bg-accent/12 text-accent">
                  <layer.icon className="size-5" />
                </span>
                <span className="font-mono text-sm text-accent">{layer.n}</span>
                <h3 className="text-xl font-semibold tracking-tight">{layer.title}</h3>
              </div>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground text-pretty">{layer.desc}</p>
              <div className="mt-5 flex flex-wrap gap-2">
                {layer.metrics.map((m) => (
                  <span
                    key={m}
                    className="rounded-lg border border-accent/15 bg-accent/6 px-2.5 py-1 font-mono text-[11px] text-accent"
                  >
                    {m}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* HUD trái: tiến trình + nhãn lớp */}
        <div className="absolute top-1/2 left-6 z-10 flex -translate-y-1/2 items-stretch gap-4 lg:left-10">
          <div className="relative w-px overflow-hidden rounded-full bg-white/10">
            <div ref={barRef} className="absolute inset-x-0 top-0 h-full origin-top bg-accent" style={{ transform: "scaleY(0)" }} />
          </div>
          <ol className="flex flex-col justify-between gap-4 py-1">
            {LAYERS.map((layer, i) => (
              <li
                key={layer.n}
                className={cn(
                  "flex items-center gap-2.5 font-mono text-xs transition-colors duration-300",
                  i === active ? "text-accent" : "text-muted-foreground/50",
                )}
              >
                <span
                  className={cn(
                    "size-1.5 rounded-full transition-all duration-300",
                    i === active ? "scale-125 bg-accent" : "bg-muted-foreground/40",
                  )}
                />
                {layer.n}
                <span className={cn("transition-opacity duration-300", i === active ? "opacity-100" : "opacity-0")}>
                  {layer.title}
                </span>
              </li>
            ))}
          </ol>
        </div>

        {/* nhãn tiêu đề section — cố định trên cùng của cảnh */}
        <div className="pointer-events-none absolute top-24 left-1/2 z-10 -translate-x-1/2 text-center">
          <p className="text-xs font-semibold tracking-[0.25em] text-accent uppercase">Bên trong vật thể</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
            Một câu hỏi đi qua những gì
          </h2>
        </div>
      </div>

      {/* ── Mobile / reduced-motion: thẻ dọc tĩnh ────────────────────── */}
      <div className="mx-auto max-w-2xl space-y-4 px-4 py-24 md:hidden">
        <Reveal>
          <p className="text-xs font-semibold tracking-[0.25em] text-accent uppercase">Bên trong vật thể</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">Một câu hỏi đi qua những gì</h2>
        </Reveal>
        {LAYERS.map((layer, i) => (
          <Reveal key={layer.n} delay={i * 0.05}>
            <div className="glass-edge rounded-3xl bg-card/70 p-6">
              <div className="flex items-center gap-3">
                <span className="flex size-10 items-center justify-center rounded-xl bg-accent/12 text-accent">
                  <layer.icon className="size-4.5" />
                </span>
                <span className="font-mono text-xs text-accent">{layer.n}</span>
                <h3 className="text-lg font-semibold tracking-tight">{layer.title}</h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{layer.desc}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {layer.metrics.map((m) => (
                  <span key={m} className="rounded-lg border border-accent/15 bg-accent/6 px-2.5 py-1 font-mono text-[11px] text-accent">
                    {m}
                  </span>
                ))}
              </div>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
