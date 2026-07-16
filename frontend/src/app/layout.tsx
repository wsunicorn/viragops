import type { Metadata } from "next";
import { Space_Grotesk, Manrope, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { SmoothScrollProvider } from "@/components/smooth-scroll-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { Navbar } from "@/components/navbar";

// Bộ phông hiện đại, CẢ 3 đều có subset "vietnamese" thật trên Google
// Fonts (không dựa vào fallback glyph latin-ext như Geist trước đây):
// Space Grotesk = display/heading (cá tính kỹ thuật), Manrope = body
// (geometric, dễ đọc), JetBrains Mono = số liệu/code.
const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin", "vietnamese"],
});

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin", "vietnamese"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin", "vietnamese"],
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
    // suppressHydrationWarning: next-themes đổi class trên <html> trước
    // hydration (và browser extension cũng có thể sửa attribute ở đây) —
    // đây là mismatch có chủ đích ở đúng 1 phần tử này, không lan xuống con.
    <html
      lang="vi"
      suppressHydrationWarning
      className={`${spaceGrotesk.variable} ${manrope.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-background text-foreground">
        <ThemeProvider>
          <SmoothScrollProvider>
            <Navbar />
            <main className="flex-1">{children}</main>
          </SmoothScrollProvider>
          {/* film grain — fixed + pointer-events-none, không repaint khi cuộn */}
          <div className="noise-overlay" aria-hidden />
        </ThemeProvider>
      </body>
    </html>
  );
}
