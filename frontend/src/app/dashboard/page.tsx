import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Reveal } from "@/components/reveal";
import { SectionHeading } from "@/components/section-heading";
import { MetricGrid } from "@/components/metric-grid";
import { RetrievalChart } from "@/components/charts/retrieval-chart";
import { PromptChart } from "@/components/charts/prompt-chart";
import { CategoryChart } from "@/components/charts/category-chart";
import { SiteFooter } from "@/components/site-footer";
import { RETRIEVAL_RERANKING_RESULTS, CHUNKING_ABLATION_RESULTS, RETRIEVAL_META } from "@/lib/data/retrieval";
import { PROMPT_COMPARISON_PHASE6, PROMPT_EVOLUTION } from "@/lib/data/prompts";
import { SMOKE_METRICS, FULL_METRICS, FULL_EVAL_BY_CATEGORY, CONTEXT_LIMIT_EXPERIMENT, EVAL_META } from "@/lib/data/eval";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 pt-32 pb-24">
      <Reveal>
        <h1 className="text-3xl font-semibold tracking-tight">Số liệu thực nghiệm thật</h1>
        <p className="mt-3 max-w-2xl text-muted-foreground text-pretty">
          Mọi con số dưới đây đọc trực tiếp từ report thật trong repo (
          <code className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-xs">docs/system/experiments/</code>) —
          không tính lại bằng công thức khác.
        </p>
      </Reveal>

      <Tabs defaultValue="retrieval" className="mt-10">
        <TabsList className="w-full sm:w-auto">
          <TabsTrigger value="retrieval">Retrieval (Phase 4)</TabsTrigger>
          <TabsTrigger value="prompt">PromptOps (Phase 6-8)</TabsTrigger>
          <TabsTrigger value="eval">Evaluation (Phase 8)</TabsTrigger>
        </TabsList>

        <TabsContent value="retrieval" className="mt-8 space-y-14">
          <section>
            <SectionHeading
              title="So sánh 8 config retrieval/reranking"
              description={`${RETRIEVAL_META.nQuestions} câu có căn cứ · recall@${RETRIEVAL_META.evalK} · data_version=${RETRIEVAL_META.dataVersion}`}
            />
            <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-4 sm:p-6">
              <RetrievalChart data={RETRIEVAL_RERANKING_RESULTS} />
            </div>
            <p className="mt-4 text-sm text-muted-foreground text-pretty">
              <span className="font-medium text-accent">hybrid_dbsf_pre40</span> thắng — recall@5=0.932. Gemini
              listwise rerank không vượt qua được DBSF và có p95 latency 61 giây/câu khi bị rate-limit thật — lý do
              thật để KHÔNG bật reranker trong production, không phải vì rerank luôn làm giảm chất lượng.
            </p>
          </section>

          <section>
            <SectionHeading
              title="Chunking ablation"
              description="4 chiến lược chunk hoá cùng 1 bộ câu hỏi, cùng retrieval config."
            />
            <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-4 sm:p-6">
              <RetrievalChart data={CHUNKING_ABLATION_RESULTS} />
            </div>
            <p className="mt-4 text-sm text-muted-foreground text-pretty">
              <span className="font-medium text-accent">structure_aware</span> (tách theo &quot;Điều&quot;, giữ
              nguyên &quot;Khoản&quot;) thắng — đúng với trực giác domain pháp lý/quy chế.
            </p>
          </section>
        </TabsContent>

        <TabsContent value="prompt" className="mt-8 space-y-14">
          <section>
            <SectionHeading
              title="So sánh 6 prompt variant ban đầu (Phase 6)"
              description="12 câu smoke, đo refusal accuracy — p1_grounded_v1 thắng, trở thành baseline."
            />
            <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-4 sm:p-6">
              <PromptChart data={PROMPT_COMPARISON_PHASE6} />
            </div>
          </section>

          <section>
            <SectionHeading
              title="Hành trình 3 bước: p1 → p6 → p7"
              description="Prompt tiến hoá qua Phase 8 khi eval engine phát hiện gap, rồi phát hiện chính bản sửa gây hồi quy."
            />
            <ol className="mt-8 space-y-4">
              {PROMPT_EVOLUTION.map((step, i) => (
                <li key={step.version} className="relative rounded-2xl border border-white/10 bg-white/[0.02] p-5 sm:p-6">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="flex size-7 items-center justify-center rounded-full bg-primary/15 font-mono text-xs text-primary">
                      {i + 1}
                    </span>
                    <code className="font-mono text-sm text-accent">{step.version}</code>
                    <span className="text-xs text-muted-foreground">{step.period}</span>
                  </div>
                  <p className="mt-2 text-sm font-medium">{step.role}</p>
                  <p className="mt-1.5 text-sm text-muted-foreground text-pretty">{step.finding}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {step.metrics.map((m) => (
                      <span
                        key={m.label}
                        className={cn(
                          "rounded-lg border px-2.5 py-1.5 font-mono text-[11px]",
                          "negative" in m && m.negative
                            ? "border-amber-500/25 bg-amber-500/[0.06] text-amber-300"
                            : "border-accent/20 bg-accent/[0.06] text-accent",
                        )}
                      >
                        {m.label}: {m.value}
                        {"delta" in m && m.delta ? ` (${m.delta})` : ""}
                      </span>
                    ))}
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </TabsContent>

        <TabsContent value="eval" className="mt-8 space-y-14">
          <section>
            <SectionHeading
              title="Smoke (50 câu) vs Full (298/300 câu)"
              description={`Eval 4 tầng qua RagService thật · judge model: ${EVAL_META.judgeModel}`}
            />
            <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
              <div>
                <p className="mb-3 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                  Smoke — {EVAL_META.smokeN} câu, prompt p1
                </p>
                <MetricGrid metrics={SMOKE_METRICS} />
              </div>
              <div>
                <p className="mb-3 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                  Full — {EVAL_META.fullN}/{EVAL_META.fullTotal} câu, prompt p6
                </p>
                <MetricGrid metrics={FULL_METRICS} />
              </div>
            </div>
          </section>

          <section>
            <SectionHeading title="Theo category (full eval)" />
            <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-4 sm:p-6">
              <CategoryChart data={FULL_EVAL_BY_CATEGORY} />
            </div>
            <p className="mt-4 text-sm text-muted-foreground text-pretty">
              adversarial refusal_acc=0.636 trong run này — đây là hồi quy p6 gây ra, đã sửa bằng p7 (xem tab
              PromptOps). Số liệu ở đây giữ nguyên bản gốc thay vì chỉnh lại, để đúng tinh thần &quot;báo cáo trung
              thực&quot;.
            </p>
          </section>

          <section>
            <SectionHeading eyebrow="Kết quả âm tính" title="Thử tăng context, rồi revert" />
            <div className="mt-8 rounded-2xl border border-amber-500/20 bg-amber-500/[0.03] p-6">
              <p className="text-sm font-medium">{CONTEXT_LIMIT_EXPERIMENT.question}</p>
              <div className="mt-4 grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <p className="mb-2 text-xs text-muted-foreground">Retrieval-only recall (mọi category tăng)</p>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-muted-foreground">
                        <th className="text-left font-normal">limit</th>
                        <th className="text-right font-normal">all</th>
                        <th className="text-right font-normal">ambiguous</th>
                        <th className="text-right font-normal">multi_hop</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono">
                      {CONTEXT_LIMIT_EXPERIMENT.retrievalOnly.map((r) => (
                        <tr key={r.limit} className="border-t border-white/10">
                          <td className="py-1.5">{r.limit}</td>
                          <td className="py-1.5 text-right">{r.recallAll.toFixed(3)}</td>
                          <td className="py-1.5 text-right">{r.recallAmbiguous.toFixed(3)}</td>
                          <td className="py-1.5 text-right">{r.recallMultiHop.toFixed(3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div>
                  <p className="mb-2 text-xs text-muted-foreground">Generation thật (Citation Acc multi_hop)</p>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-muted-foreground">
                        <th className="text-left font-normal">limit</th>
                        <th className="text-right font-normal">citation acc</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono">
                      {CONTEXT_LIMIT_EXPERIMENT.generationValidation.map((r) => (
                        <tr key={r.limit} className="border-t border-white/10">
                          <td className="py-1.5">{r.limit}</td>
                          <td
                            className={cn(
                              "py-1.5 text-right",
                              r.limit === 10 ? "text-amber-400" : "text-accent",
                            )}
                          >
                            {r.citationAccMultiHop.toFixed(3)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <p className="mt-5 text-sm text-muted-foreground text-pretty">{CONTEXT_LIMIT_EXPERIMENT.verdict}</p>
            </div>
          </section>
        </TabsContent>
      </Tabs>

      <div className="mt-24">
        <SiteFooter />
      </div>
    </div>
  );
}
