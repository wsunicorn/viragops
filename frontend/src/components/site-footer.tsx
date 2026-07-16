import Link from "next/link";
import { Hexagon } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="relative overflow-hidden border-t border-white/8 px-4 pt-14 pb-10">
      <div className="mx-auto max-w-5xl">
        <div className="flex flex-col justify-between gap-8 sm:flex-row sm:items-end">
          <div className="max-w-md">
            <p className="flex items-center gap-2 text-sm font-semibold tracking-tight">
              <Hexagon className="size-4 text-accent" aria-hidden />
              vi<span className="text-accent">RAG</span>ops
            </p>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              Khóa luận tốt nghiệp — nền tảng LLMOps/RAGOps cho RAG hỏi-đáp tiếng Việt. Được xây và đo
              hoàn toàn bằng dữ liệu thật; kết quả âm tính được công bố thay vì giấu đi.
            </p>
          </div>
          <nav className="flex items-center gap-6 text-sm text-muted-foreground">
            <Link href="/" className="transition-colors hover:text-foreground">
              Tổng quan
            </Link>
            <Link href="/demo" className="transition-colors hover:text-foreground">
              Demo
            </Link>
            <Link href="/dashboard" className="transition-colors hover:text-foreground">
              Thực nghiệm
            </Link>
          </nav>
        </div>
        <p className="mt-10 border-t border-white/8 pt-5 font-mono text-[11px] text-muted-foreground/50">
          every change goes through the gate · 12 phase · 6 experiment · 300 câu golden set
        </p>
      </div>
    </footer>
  );
}
