"use client";

import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Send,
  FileText,
  CircleAlert,
  CircleCheck,
  CircleX,
  Loader2,
  Wifi,
  WifiOff,
  RotateCw,
  TerminalSquare,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Reveal } from "@/components/reveal";
import { EXAMPLE_QUESTIONS } from "@/lib/data/example-questions";
import { askQuestion, checkHealth, ApiError, API_BASE_URL, type QAResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function DemoPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QAResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apiUp, setApiUp] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(false);

  const recheck = useCallback(() => {
    setChecking(true);
    checkHealth().then((up) => {
      setApiUp(up);
      setChecking(false);
    });
  }, []);

  useEffect(() => {
    checkHealth().then(setApiUp);
  }, []);

  async function handleSubmit(q?: string) {
    const finalQuestion = (q ?? question).trim();
    if (!finalQuestion || loading) return;
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const res = await askQuestion({ question: finalQuestion, mode: "balanced" });
      setResponse(res);
      setApiUp(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Có lỗi không xác định xảy ra.");
      checkHealth().then(setApiUp);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-grid relative min-h-dvh">
      <div className="pointer-events-none absolute inset-0 bg-linear-to-b from-transparent via-background/60 to-background" />
      <div className="relative mx-auto max-w-6xl px-4 pt-32 pb-24">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-[5fr_7fr] lg:gap-12">
          {/* ── Cột trái: nhập câu hỏi ─────────────────────────────── */}
          <div>
            <Reveal>
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <h1 className="text-3xl font-semibold tracking-tight">Hỏi-đáp thật</h1>
                <ApiStatusBadge status={apiUp} />
              </div>
              <p className="text-muted-foreground text-pretty">
                Gọi trực tiếp{" "}
                <code className="rounded bg-foreground/10 px-1.5 py-0.5 font-mono text-xs">/qa/query</code> của
                FastAPI backend — retrieval Qdrant thật, model qua LiteLLM gateway thật, không dàn dựng.
              </p>
            </Reveal>

            {apiUp === false ? <OfflineHelp checking={checking} onRetry={recheck} /> : null}

            <Reveal delay={0.1} className="mt-6">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSubmit();
                }}
                className="glass-edge relative rounded-3xl bg-card/60 p-2 backdrop-blur-xl"
              >
                <Textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Nhập câu hỏi về quy chế đào tạo IUH..."
                  rows={3}
                  className="resize-none rounded-2xl border-0 bg-transparent pr-14 text-base shadow-none focus-visible:ring-0"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit();
                    }
                  }}
                />
                <Button
                  type="submit"
                  size="icon"
                  disabled={loading || !question.trim()}
                  aria-label="Gửi câu hỏi"
                  className="absolute right-3 bottom-3 rounded-full transition-transform active:scale-95"
                >
                  {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                </Button>
              </form>
            </Reveal>

            <Reveal delay={0.16} className="mt-5">
              <p className="mb-2.5 text-xs font-semibold tracking-[0.15em] text-muted-foreground uppercase">
                Thử nhanh một câu
              </p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_QUESTIONS.map((ex) => (
                  <button
                    key={ex.question}
                    onClick={() => {
                      setQuestion(ex.question);
                      handleSubmit(ex.question);
                    }}
                    disabled={loading}
                    className="cursor-pointer rounded-full border border-border bg-foreground/3 px-3.5 py-1.5 text-left text-xs text-muted-foreground transition-all hover:border-accent/40 hover:text-foreground active:scale-[0.98] disabled:opacity-40"
                  >
                    <span className="mr-1.5 font-mono text-accent">{ex.category}</span>
                    {ex.question.length > 44 ? ex.question.slice(0, 44) + "…" : ex.question}
                  </button>
                ))}
              </div>
            </Reveal>

            <Reveal delay={0.22} className="mt-8">
              <div className="rounded-2xl border border-border bg-foreground/2 p-4 text-xs leading-relaxed text-muted-foreground">
                <p className="flex items-center gap-1.5 font-semibold text-foreground">
                  <Sparkles className="size-3.5 text-accent" />
                  Hệ thống có thể TỪ CHỐI — và đó là tính năng
                </p>
                <p className="mt-1.5">
                  Trích dẫn fail-closed: chunk bịa bị loại; câu trả lời mất hết trích dẫn tự hạ thành từ
                  chối. Câu ngoài phạm vi tài liệu sẽ được từ chối trung thực thay vì bịa.
                </p>
              </div>
            </Reveal>
          </div>

          {/* ── Cột phải: kết quả ──────────────────────────────────── */}
          <div className="lg:pt-14">
            <AnimatePresence mode="wait">
              {loading ? (
                <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <LoadingCard />
                </motion.div>
              ) : error ? (
                <motion.div key="error" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                  <ErrorCard message={error} />
                </motion.div>
              ) : response ? (
                <motion.div key="response" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                  <ResponseCard response={response} />
                </motion.div>
              ) : (
                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <EmptyState />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}

function ApiStatusBadge({ status }: { status: boolean | null }) {
  if (status === null) return null;
  return status ? (
    <Badge variant="outline" className="gap-1.5 border-accent/30 text-accent">
      <Wifi className="size-3" /> API online
    </Badge>
  ) : (
    <Badge variant="outline" className="gap-1.5 border-destructive/40 text-destructive">
      <WifiOff className="size-3" /> API offline
    </Badge>
  );
}

/** Khi backend chưa chạy: nói rõ nguyên nhân thường gặp + lệnh khởi động
 * thật (khớp README) + nút thử lại — thay vì chỉ một badge đỏ im lặng. */
function OfflineHelp({ checking, onRetry }: { checking: boolean; onRetry: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-5 rounded-2xl border border-destructive/25 bg-destructive/5 p-4"
    >
      <div className="flex items-start gap-3">
        <TerminalSquare className="mt-0.5 size-4 shrink-0 text-destructive" />
        <div className="min-w-0 text-sm">
          <p className="font-medium">
            Không kết nối được backend tại <code className="font-mono text-xs">{API_BASE_URL}</code>
          </p>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            Nguyên nhân thường gặp: chưa chạy API, hoặc Docker Desktop chưa bật (Qdrant/Postgres/LiteLLM
            chết theo). Khởi động từ thư mục gốc repo:
          </p>
          <pre className="mt-2 overflow-x-auto rounded-lg bg-foreground/6 p-2.5 font-mono text-[11px] leading-relaxed">
            {`docker compose up -d qdrant postgres valkey litellm
uvicorn src.api.main:app --port 8000`}
          </pre>
          <Button size="sm" variant="outline" onClick={onRetry} disabled={checking} className="mt-3 gap-1.5 rounded-full">
            <RotateCw className={cn("size-3.5", checking && "animate-spin")} />
            Kiểm tra lại
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

function EmptyState() {
  return (
    <div className="glass-edge flex min-h-80 flex-col items-center justify-center gap-4 rounded-3xl bg-card/40 p-10 text-center backdrop-blur-sm">
      <div className="relative">
        <div className="absolute inset-0 m-auto size-16 rounded-full bg-accent/15 blur-2xl" aria-hidden />
        <motion.div
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          className="relative flex size-14 items-center justify-center rounded-2xl border border-accent/25 bg-accent/10 text-accent"
        >
          <FileText className="size-6" />
        </motion.div>
      </div>
      <div>
        <p className="font-medium">Chưa có câu hỏi nào</p>
        <p className="mt-1 max-w-64 text-sm text-muted-foreground">
          Kết quả sẽ hiện ở đây — kèm trích dẫn đúng Điều/Khoản và metadata thật của lần gọi.
        </p>
      </div>
    </div>
  );
}

function LoadingCard() {
  // Skeleton shimmer ĐÚNG bố cục của ResponseCard (không dùng spinner
  // tròn chung chung) — không giật layout khi câu trả lời thật về.
  return (
    <Card className="glass-edge gap-4 border-0 bg-card/60 p-6 backdrop-blur-xl" aria-busy>
      <div className="flex items-center justify-between">
        <div className="shimmer h-4 w-36 rounded-md bg-foreground/6" />
        <div className="shimmer h-3 w-40 rounded-md bg-foreground/5" />
      </div>
      <div className="space-y-2.5">
        <div className="shimmer h-4 w-full rounded-md bg-foreground/6" />
        <div className="shimmer h-4 w-[92%] rounded-md bg-foreground/6" />
        <div className="shimmer h-4 w-[78%] rounded-md bg-foreground/6" />
      </div>
      <div className="space-y-2 border-t border-border pt-4">
        <div className="shimmer h-3 w-24 rounded-md bg-foreground/5" />
        <div className="shimmer h-14 w-full rounded-lg bg-foreground/4" />
        <div className="shimmer h-14 w-full rounded-lg bg-foreground/4" />
      </div>
      <p className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="size-3.5 animate-spin text-accent" />
        Đang retrieve context và gọi model thật — vài giây tới hơn chục giây tuỳ tầng model.
      </p>
    </Card>
  );
}

function ErrorCard({ message }: { message: string }) {
  return (
    <Card className="border-destructive/30 bg-destructive/5 p-6">
      <div className="flex items-start gap-3">
        <CircleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
        <div>
          <p className="text-sm font-medium text-destructive">Không lấy được câu trả lời</p>
          <p className="mt-1 text-sm text-muted-foreground">{message}</p>
        </div>
      </div>
    </Card>
  );
}

function ConfidenceMeter({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="text-[11px] text-muted-foreground">confidence</span>
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-foreground/8">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.round(value * 100)}%` }}
          transition={{ type: "spring", stiffness: 90, damping: 20, delay: 0.3 }}
          className="h-full rounded-full bg-accent"
        />
      </div>
      <span className="font-mono text-[11px] text-accent">{value.toFixed(2)}</span>
    </div>
  );
}

function ResponseCard({ response }: { response: QAResponse }) {
  return (
    <Card
      className={cn(
        "glass-edge gap-4 border-0 bg-card/60 p-6 backdrop-blur-xl",
        response.refusal && "bg-amber-500/4",
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {response.refusal ? (
            <CircleX className="size-4 text-amber-400" />
          ) : (
            <CircleCheck className="size-4 text-accent" />
          )}
          <span className="text-sm font-medium">{response.refusal ? "Từ chối trả lời" : "Trả lời có căn cứ"}</span>
        </div>
        {response.confidence != null && !response.refusal ? <ConfidenceMeter value={response.confidence} /> : null}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="text-base leading-relaxed text-pretty whitespace-pre-line"
      >
        {response.answer}
      </motion.p>

      {response.citations.length > 0 ? (
        <div className="space-y-2 border-t border-border pt-4">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Trích dẫn ({response.citations.length})
          </p>
          {response.citations.map((c, i) => (
            <motion.div
              key={c.chunk_id + i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 24, delay: 0.15 + i * 0.09 }}
              className="group flex items-start gap-2.5 rounded-xl border border-transparent bg-foreground/3 p-3 transition-colors hover:border-accent/20"
            >
              <FileText className="mt-0.5 size-3.5 shrink-0 text-accent" />
              <div className="min-w-0 text-sm">
                <p className="font-medium">{c.document_id}</p>
                {c.section ? <p className="text-muted-foreground">{c.section}</p> : null}
                {c.quote ? (
                  <p className="mt-1 line-clamp-2 text-xs text-muted-foreground/70 italic group-hover:line-clamp-none">
                    “{c.quote}”
                  </p>
                ) : null}
              </div>
            </motion.div>
          ))}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-x-5 gap-y-1.5 border-t border-border pt-4 font-mono text-[11px] text-muted-foreground/70">
        <span>model: {response.model.model}</span>
        <span>provider: {response.model.provider}</span>
        <span>
          tokens: {response.usage.input_tokens}→{response.usage.output_tokens}
        </span>
        <span>latency: {response.usage.latency_ms}ms</span>
        <span>cost: ${response.usage.cost_usd.toFixed(6)}</span>
        <span className="text-muted-foreground/50">{response.trace_id}</span>
      </div>
    </Card>
  );
}
