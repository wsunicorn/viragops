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
  Hexagon,
  type LucideIcon,
} from "lucide-react";
import { Reveal } from "@/components/reveal";
import { cn } from "@/lib/utils";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

/**
 * "Quyển sách tri thức" — scrolltelling 3D: một cuốn sách thật (CSS 3D,
 * perspective + rotateY từng tờ, GSAP ScrollTrigger scrub) được PIN lại;
 * cuộn chuột mở bìa rồi LẬT TỪNG TRANG, mỗi trang lộ ra một trạm trên lộ
 * trình của 1 câu hỏi: nguồn tri thức → chunk & embed → truy hồi lai →
 * sinh trả lời → cổng kiểm định.
 *
 * Kỹ thuật: mỗi tờ (sheet) là 1 div preserve-3d hinge tại gáy
 * (transform-origin: left center), mặt trước/sau backface-hidden; GSAP
 * tween góc 0→-180° và ghi transform/zIndex/bóng đổ trực tiếp vào ref
 * mỗi frame — KHÔNG setState trong lúc cuộn (chỉ setState khi đổi trang
 * active cho HUD). Trang giấy luôn màu giấy thật (ấm) ở cả 2 theme —
 * sách thật không đổi màu giấy theo dark mode.
 *
 * Mobile / prefers-reduced-motion: fallback thẻ dọc, không pin.
 */

type Layer = {
  n: string;
  title: string;
  desc: string;
  metrics: string[];
  icon: LucideIcon;
  result: string; // in ở MẶT SAU của tờ (hiện bên trang trái sau khi lật)
  resultCaption: string;
};

const LAYERS: Layer[] = [
  {
    n: "01",
    title: "Nguồn tri thức",
    desc: "10 văn bản quy chế IUH thật — quy chế tín chỉ, thi & đánh giá, sổ tay sinh viên. PDF scan được OCR bằng Gemini multimodal, đối chiếu thủ công từng số liệu.",
    metrics: ["QĐ 1482/QĐ-ĐHCN", "QĐ 610/QĐ-ĐHCN", "Sổ tay SV 2024"],
    icon: Database,
    result: "10",
    resultCaption: "văn bản thật, OCR đúng 100% trang bìa",
  },
  {
    n: "02",
    title: "Chunk & Embed",
    desc: "Chunking structure_aware tách theo \"Điều\", giữ nguyên \"Khoản\" — thắng 3 chiến lược khác khi đo thật. Mỗi chunk mang 2 vector: dense 768d (Gemini) + sparse BM25 tự viết.",
    metrics: ["222 chunk", "768 chiều dense", "BM25 tự cài đặt"],
    icon: Grid2x2,
    result: "222",
    resultCaption: "chunk structure_aware, mỗi chunk 2 vector",
  },
  {
    n: "03",
    title: "Truy hồi lai",
    desc: "Qdrant hybrid search: nhánh dense + nhánh sparse chạy song song rồi hợp nhất bằng DBSF — thắng cả 8 config đã đo, kể cả các config có reranker.",
    metrics: ["DBSF fusion", "p95 retrieval 19ms", "8 config đã đo"],
    icon: GitMerge,
    result: "0.932",
    resultCaption: "recall@5 — cao nhất trong 8 config thật",
  },
  {
    n: "04",
    title: "Sinh câu trả lời",
    desc: "Prompt p7 (vòng lặp thứ 8) qua LiteLLM gateway với 4 chặng fallback. Citation fail-closed: chunk bịa bị loại, câu trả lời mất hết trích dẫn tự hạ thành từ chối.",
    metrics: ["refusal acc 0.90", "fallback 4 chặng", "9 prompt p0–p8"],
    icon: MessageSquareQuote,
    result: "0.838",
    resultCaption: "citation accuracy — mọi ý đều phải có nguồn",
  },
  {
    n: "05",
    title: "Cổng kiểm định",
    desc: "Mọi thay đổi phải qua Quality Gate: 16 kịch bản giả lập, chặn đúng 9/9 thay đổi xấu, 0 false positive. Trace lên Langfuse, metric vào Prometheus/Grafana.",
    metrics: ["precision 1.000", "recall 1.000", "PASS / WARN / BLOCK"],
    icon: ShieldCheck,
    result: "PASS",
    resultCaption: "câu trả lời + trích dẫn được trả về người dùng",
  },
];

// giấy thật — cố định cả 2 theme
const PAPER = "#f6f1e6";
const PAPER_DEEP = "#efe8d9";
const INK = "#292317";
const INK_SOFT = "#6b5f49";
const COVER = "#0c4a42";
const COVER_DEEP = "#093832";
const ACCENT_ON_PAPER = "#0f766e";

/* ── Nội dung 1 trang (mặt trước tờ / trang phải) ───────────────────── */
function PageFace({ layer }: { layer: Layer }) {
  return (
    <div
      className="flex size-full flex-col justify-between p-7 sm:p-9"
      style={{ background: `linear-gradient(105deg, ${PAPER_DEEP} 0%, ${PAPER} 12%)`, color: INK }}
    >
      <div>
        <div className="flex items-center gap-3">
          <span
            className="flex size-10 items-center justify-center rounded-xl"
            style={{ background: "#0f766e1f", color: ACCENT_ON_PAPER }}
          >
            <layer.icon className="size-5" />
          </span>
          <span className="font-mono text-sm" style={{ color: ACCENT_ON_PAPER }}>
            {layer.n}
          </span>
        </div>
        <h3 className="mt-4 font-heading text-2xl font-semibold tracking-tight">{layer.title}</h3>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: INK_SOFT }}>
          {layer.desc}
        </p>
      </div>
      <div>
        <div className="flex flex-wrap gap-2">
          {layer.metrics.map((m) => (
            <span
              key={m}
              className="rounded-md px-2 py-1 font-mono text-[11px]"
              style={{ background: "#0f766e14", color: ACCENT_ON_PAPER, border: "1px solid #0f766e2b" }}
            >
              {m}
            </span>
          ))}
        </div>
        <p className="mt-4 border-t pt-2 text-right font-mono text-[10px]" style={{ borderColor: "#29231714", color: INK_SOFT }}>
          trạm {layer.n} / 05
        </p>
      </div>
    </div>
  );
}

/* ── Mặt sau tờ = "kết quả" trạm đó (hiện bên trang trái) ───────────── */
function PageBack({ layer }: { layer: Layer }) {
  return (
    <div
      className="flex size-full flex-col items-center justify-center gap-3 p-8 text-center"
      style={{ background: `linear-gradient(255deg, ${PAPER_DEEP} 0%, ${PAPER} 12%)`, color: INK }}
    >
      <span className="font-mono text-xs tracking-[0.3em] uppercase" style={{ color: INK_SOFT }}>
        trạm {layer.n} · hoàn tất
      </span>
      <div className="font-mono text-6xl font-bold tracking-tight sm:text-7xl" style={{ color: ACCENT_ON_PAPER }}>
        {layer.result}
      </div>
      <p className="max-w-56 text-sm leading-relaxed" style={{ color: INK_SOFT }}>
        {layer.resultCaption}
      </p>
    </div>
  );
}

export function ZoomJourney() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const bookRef = useRef<HTMLDivElement>(null);
  const sheetRefs = useRef<(HTMLDivElement | null)[]>([]);
  const shadeFrontRefs = useRef<(HTMLDivElement | null)[]>([]);
  const shadeBackRefs = useRef<(HTMLDivElement | null)[]>([]);
  const barRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(-1); // -1 = bìa còn đóng

  const SHEETS = LAYERS.length; // tờ 0 = bìa, tờ 1..4 = trạm 01-04 (trạm 05 in sẵn ở đế phải)

  useEffect(() => {
    const mm = gsap.matchMedia();

    mm.add("(min-width: 768px) and (prefers-reduced-motion: no-preference)", () => {
      let lastIdx = -2;

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: wrapRef.current,
          start: "top top",
          end: `+=${SHEETS * 100 + 80}%`,
          scrub: 0.9,
          pin: true,
          anticipatePin: 1,
          onUpdate: (self) => {
            if (barRef.current) barRef.current.style.transform = `scaleY(${self.progress})`;
          },
        },
      });

      // sách khép: dồn sang trái 1/4 để bìa (nửa phải) nằm giữa màn hình
      gsap.set(bookRef.current, { x: "-12.5%" });

      // mở bìa → sách trượt về giữa
      tl.to(bookRef.current, { x: "0%", duration: 1, ease: "power1.inOut" }, 0);

      for (let i = 0; i < SHEETS; i++) {
        const proxy = { angle: 0 };
        tl.to(
          proxy,
          {
            angle: -180,
            duration: 1,
            ease: "power1.inOut",
            onUpdate: () => {
              const el = sheetRefs.current[i];
              if (!el) return;
              const a = proxy.angle;
              el.style.transform = `rotateY(${a}deg)`;
              // thứ tự lớp: đang lật nổi trên cùng; lật xong xếp chồng bên trái
              el.style.zIndex = a <= -179.5 ? String(11 + i) : a < -0.5 ? "30" : String(10 - i);
              // bóng lật trang: đậm nhất khi tờ dựng vuông góc
              const shade = Math.sin((Math.min(Math.abs(a), 180) / 180) * Math.PI);
              const f = shadeFrontRefs.current[i];
              const b = shadeBackRefs.current[i];
              if (f) f.style.opacity = String(shade * 0.38);
              if (b) b.style.opacity = String(shade * 0.3);
              // HUD: trang active = số tờ đã lật quá nửa, trừ bìa
              const idx = a < -90 ? i : i - 1;
              if (idx !== lastIdx) {
                lastIdx = idx;
                setActive(Math.min(idx, LAYERS.length - 1));
              }
            },
          },
          i === 0 ? 0 : ">-0.08",
        );
      }
      // đoạn nghỉ cuối để người xem đọc trang PASS
      tl.to({}, { duration: 0.8 });

      return () => {
        tl.scrollTrigger?.kill();
        tl.kill();
      };
    });

    return () => mm.revert();
  }, [SHEETS]);

  return (
    <section aria-label="Quyển sách tri thức — lộ trình một câu hỏi">
      {/* ── Desktop: sách 3D pin theo scroll ─────────────────────────── */}
      <div ref={wrapRef} className="bg-grid relative hidden h-dvh items-center justify-center overflow-hidden md:flex">
        <div className="pointer-events-none absolute inset-0 bg-linear-to-b from-background via-transparent to-background" />
        {/* quầng sáng sau sách */}
        <div className="pointer-events-none absolute top-1/2 left-1/2 size-184 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/8 blur-[130px]" />

        {/* tiêu đề section */}
        <div className="pointer-events-none absolute top-16 left-1/2 z-10 -translate-x-1/2 text-center">
          <p className="text-xs font-semibold tracking-[0.25em] text-accent uppercase">Quyển sách tri thức</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
            Lộ trình của một câu hỏi
          </h2>
        </div>

        {/* sân khấu 3D */}
        <div className="relative z-5 perspective-[2400px]">
          <div
            ref={bookRef}
            className="relative h-[min(60vh,33rem)] w-[min(86vw,60rem)] transform-3d"
            style={{ transform: "rotateX(0deg)" }}
          >
            {/* nghiêng nhẹ cả cuốn sách */}
            <div className="absolute inset-0 transform-3d transform-[rotateX(10deg)]">
              {/* ĐẾ TRÁI — lớp giấy dưới cùng bên trái */}
              <div
                className="absolute top-0 left-0 h-full w-1/2 rounded-l-2xl"
                style={{ background: PAPER_DEEP, boxShadow: "inset -12px 0 24px -18px rgb(0 0 0 / 0.45)" }}
              />
              {/* ĐẾ PHẢI — trang cuối: trạm 05 in sẵn */}
              <div
                className="absolute top-0 right-0 h-full w-1/2 overflow-hidden rounded-r-2xl"
                style={{ zIndex: 1, boxShadow: "inset 10px 0 24px -18px rgb(0 0 0 / 0.4), 0 30px 60px -20px rgb(0 0 0 / 0.45)" }}
              >
                <PageFace layer={LAYERS[4]} />
              </div>

              {/* CÁC TỜ LẬT — tờ 0 = bìa, tờ 1..4 = trạm 01-04 */}
              {Array.from({ length: SHEETS }).map((_, i) => (
                <div
                  key={i}
                  ref={(el) => {
                    sheetRefs.current[i] = el;
                  }}
                  className="absolute top-0 left-1/2 h-full w-1/2 origin-left will-change-transform transform-3d"
                  style={{ zIndex: 10 - i }}
                >
                  {/* MẶT TRƯỚC */}
                  <div className="absolute inset-0 overflow-hidden rounded-r-2xl backface-hidden">
                    {i === 0 ? (
                      /* BÌA SÁCH */
                      <div
                        className="flex size-full flex-col items-center justify-center gap-5 p-8 text-center"
                        style={{
                          background: `linear-gradient(135deg, ${COVER} 0%, ${COVER_DEEP} 70%)`,
                          border: "1px solid rgb(255 255 255 / 0.08)",
                        }}
                      >
                        <div className="rounded-full border border-white/25 p-4">
                          <Hexagon className="size-7 text-white/90" />
                        </div>
                        <div>
                          <p className="font-mono text-[10px] tracking-[0.4em] text-white/50 uppercase">viRAGops</p>
                          <h3 className="mt-3 font-heading text-3xl font-bold tracking-tight text-white">
                            Sổ tay<br />tri thức
                          </h3>
                        </div>
                        <p className="max-w-52 text-xs leading-relaxed text-white/55">
                          Một câu hỏi về quy chế IUH sẽ đi qua những gì — cuộn để mở sách
                        </p>
                        <div className="absolute inset-3 rounded-xl border border-white/12" aria-hidden />
                      </div>
                    ) : (
                      <PageFace layer={LAYERS[i - 1]} />
                    )}
                    <div
                      ref={(el) => {
                        shadeFrontRefs.current[i] = el;
                      }}
                      className="pointer-events-none absolute inset-0 bg-linear-to-r from-black/50 to-transparent opacity-0"
                      aria-hidden
                    />
                  </div>
                  {/* MẶT SAU (hiện bên trái sau khi lật) */}
                  <div className="absolute inset-0 overflow-hidden rounded-l-2xl backface-hidden transform-[rotateY(180deg)]">
                    {i === 0 ? (
                      /* mặt trong bìa = lời mở */
                      <div
                        className="flex size-full flex-col items-center justify-center gap-4 p-9 text-center"
                        style={{ background: `linear-gradient(255deg, ${PAPER_DEEP} 0%, ${PAPER} 14%)`, color: INK }}
                      >
                        <span className="font-mono text-xs tracking-[0.3em] uppercase" style={{ color: INK_SOFT }}>
                          lời mở
                        </span>
                        <p className="max-w-64 font-heading text-xl leading-snug font-semibold">
                          “Điều kiện tốt nghiệp cần những gì?”
                        </p>
                        <p className="max-w-60 text-sm leading-relaxed" style={{ color: INK_SOFT }}>
                          Từ lúc sinh viên gõ câu hỏi tới lúc nhận câu trả lời có trích dẫn — 5 trạm, mọi con
                          số đều đo thật.
                        </p>
                      </div>
                    ) : (
                      <PageBack layer={LAYERS[i - 1]} />
                    )}
                    <div
                      ref={(el) => {
                        shadeBackRefs.current[i] = el;
                      }}
                      className="pointer-events-none absolute inset-0 bg-linear-to-l from-black/40 to-transparent opacity-0"
                      aria-hidden
                    />
                  </div>
                </div>
              ))}

              {/* GÁY SÁCH */}
              <div
                className="absolute top-0 left-1/2 h-full w-2 -translate-x-1/2"
                style={{ zIndex: 29, background: `linear-gradient(90deg, transparent, rgb(0 0 0 / 0.28), transparent)` }}
                aria-hidden
              />
            </div>
          </div>
        </div>

        {/* HUD trái: tiến trình + nhãn trạm */}
        <div className="absolute top-1/2 left-6 z-10 flex -translate-y-1/2 items-stretch gap-4 lg:left-10">
          <div className="relative w-px overflow-hidden rounded-full bg-foreground/10">
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
      </div>

      {/* ── Mobile / reduced-motion: thẻ dọc tĩnh ────────────────────── */}
      <div className="mx-auto max-w-2xl space-y-4 px-4 py-24 md:hidden">
        <Reveal>
          <p className="text-xs font-semibold tracking-[0.25em] text-accent uppercase">Quyển sách tri thức</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">Lộ trình của một câu hỏi</h2>
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
