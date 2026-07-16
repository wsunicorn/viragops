"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Send, FileText, CircleAlert, CircleCheck, CircleX, Loader2, Wifi, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Reveal } from "@/components/reveal";
import { EXAMPLE_QUESTIONS } from "@/lib/data/example-questions";
import { askQuestion, checkHealth, ApiError, type QAResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function DemoPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QAResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apiUp, setApiUp] = useState<boolean | null>(null);

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
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Có lỗi không xác định xảy ra.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 pt-32 pb-24">
      <Reveal>
        <div className="mb-2 flex items-center gap-2">
          <h1 className="text-3xl font-semibold tracking-tight">Demo hỏi-đáp thật</h1>
          <ApiStatusBadge status={apiUp} />
        </div>
        <p className="text-muted-foreground text-pretty">
          Gọi trực tiếp <code className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-xs">/qa/query</code> của
          FastAPI backend — retrieval Qdrant thật, sinh câu trả lời qua LiteLLM gateway thật, không mô phỏng.
          Câu trả lời có thể chậm (vài giây tới hơn chục giây) tuỳ tầng model đang phục vụ.
        </p>
      </Reveal>

      <Reveal delay={0.1} className="mt-6 flex flex-wrap gap-2">
        {EXAMPLE_QUESTIONS.map((ex) => (
          <button
            key={ex.question}
            onClick={() => {
              setQuestion(ex.question);
              handleSubmit(ex.question);
            }}
            disabled={loading}
            className="rounded-full border border-white/10 bg-white/3 px-3.5 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground disabled:opacity-40"
          >
            <span className="mr-1.5 font-mono text-accent">{ex.category}</span>
            {ex.question.length > 46 ? ex.question.slice(0, 46) + "…" : ex.question}
          </button>
        ))}
      </Reveal>

      <Reveal delay={0.15} className="mt-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="relative"
        >
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Nhập câu hỏi về quy chế đào tạo IUH..."
            rows={3}
            className="resize-none rounded-2xl border-white/10 bg-white/3 pr-14 text-base"
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
            className="absolute right-3 bottom-3 rounded-full"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          </Button>
        </form>
      </Reveal>

      <div className="mt-8">
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
          ) : null}
        </AnimatePresence>
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

function LoadingCard() {
  // Skeleton shimmer ĐÚNG bố cục của ResponseCard (không dùng spinner
  // tròn chung chung) — không giật layout khi câu trả lời thật về.
  return (
    <Card className="gap-4 border-white/10 bg-white/2 p-6" aria-busy>
      <div className="flex items-center justify-between">
        <div className="shimmer h-4 w-36 rounded-md bg-white/6" />
        <div className="shimmer h-3 w-40 rounded-md bg-white/5" />
      </div>
      <div className="space-y-2.5">
        <div className="shimmer h-4 w-full rounded-md bg-white/6" />
        <div className="shimmer h-4 w-[92%] rounded-md bg-white/6" />
        <div className="shimmer h-4 w-[78%] rounded-md bg-white/6" />
      </div>
      <div className="space-y-2 border-t border-white/10 pt-4">
        <div className="shimmer h-3 w-24 rounded-md bg-white/5" />
        <div className="shimmer h-14 w-full rounded-lg bg-white/4" />
        <div className="shimmer h-14 w-full rounded-lg bg-white/4" />
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

function ResponseCard({ response }: { response: QAResponse }) {
  return (
    <Card
      className={cn(
        "gap-4 border-white/10 bg-white/3 p-6",
        response.refusal && "border-amber-500/25 bg-amber-500/4",
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {response.refusal ? (
            <CircleX className="size-4 text-amber-400" />
          ) : (
            <CircleCheck className="size-4 text-accent" />
          )}
          <span className="text-sm font-medium">{response.refusal ? "Từ chối trả lời" : "Trả lời có căn cứ"}</span>
        </div>
        <span className="font-mono text-[11px] text-muted-foreground/60">{response.trace_id}</span>
      </div>

      <p className="text-base leading-relaxed text-pretty">{response.answer}</p>

      {response.citations.length > 0 ? (
        <div className="space-y-2 border-t border-white/10 pt-4">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Trích dẫn ({response.citations.length})
          </p>
          {response.citations.map((c, i) => (
            <motion.div
              key={c.chunk_id + i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 24, delay: 0.15 + i * 0.09 }}
              className="flex items-start gap-2.5 rounded-lg bg-white/3 p-3"
            >
              <FileText className="mt-0.5 size-3.5 shrink-0 text-accent" />
              <div className="min-w-0 text-sm">
                <p className="font-medium">{c.document_id}</p>
                {c.section ? <p className="text-muted-foreground">{c.section}</p> : null}
                {c.quote ? <p className="mt-1 line-clamp-2 text-xs text-muted-foreground/70 italic">“{c.quote}”</p> : null}
              </div>
            </motion.div>
          ))}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-x-5 gap-y-1.5 border-t border-white/10 pt-4 font-mono text-[11px] text-muted-foreground/70">
        <span>model: {response.model.model}</span>
        <span>provider: {response.model.provider}</span>
        <span>tokens: {response.usage.input_tokens}→{response.usage.output_tokens}</span>
        <span>latency: {response.usage.latency_ms}ms</span>
        <span>cost: ${response.usage.cost_usd.toFixed(6)}</span>
      </div>
    </Card>
  );
}
