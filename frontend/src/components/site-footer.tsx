import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-white/10 px-4 py-10">
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 text-sm text-muted-foreground sm:flex-row">
        <p>viRAGops — Khóa luận tốt nghiệp, nền tảng LLMOps/RAGOps cho RAG hỏi-đáp tiếng Việt.</p>
        <div className="flex items-center gap-5">
          <Link href="/" className="hover:text-foreground">
            Tổng quan
          </Link>
          <Link href="/demo" className="hover:text-foreground">
            Demo
          </Link>
          <Link href="/dashboard" className="hover:text-foreground">
            Thực nghiệm
          </Link>
        </div>
      </div>
    </footer>
  );
}
