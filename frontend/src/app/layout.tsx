import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SmoothScrollProvider } from "@/components/smooth-scroll-provider";
import { Navbar } from "@/components/navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  // Geist ships cyrillic/latin/latin-ext only (no dedicated "vietnamese"
  // subset in next/font/google) — latin-ext covers Vietnamese combining
  // diacritics well enough via fallback glyph composition.
  subsets: ["latin", "latin-ext"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "viRAGops — LLMOps/RAGOps cho hỏi-đáp tiếng Việt",
  description:
    "Nền tảng LLMOps/RAGOps full-scope cho hệ thống hỏi-đáp quy chế đào tạo IUH bằng RAG — data pipeline, retrieval experiments, PromptOps, evaluation engine, model gateway, số liệu thực nghiệm thật.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="vi"
      className={`${geistSans.variable} ${geistMono.variable} dark h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-background text-foreground">
        <SmoothScrollProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
        </SmoothScrollProvider>
        {/* film grain — fixed + pointer-events-none, không repaint khi cuộn */}
        <div className="noise-overlay" aria-hidden />
      </body>
    </html>
  );
}
