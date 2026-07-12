// Real numbers transcribed from docs/system/experiments/
// results_evaluation_smoke.md, results_evaluation_full.md and
// results_context_limit_ablation.md (Phase 8, 2026-07-12).

export type MetricRow = {
  label: string;
  value: number | string;
  target?: number | string;
  pass?: boolean;
  unit?: string;
};

/** Smoke run: 50 questions stratified across all 6 categories, prompt=p1. */
export const SMOKE_METRICS: MetricRow[] = [
  { label: "Recall@5", value: 0.905, target: 0.85, pass: true },
  { label: "Context Recall", value: 0.905, target: 0.80, pass: true },
  { label: "Faithfulness (judge)", value: 0.973, target: 0.85, pass: true },
  { label: "Answer Relevance (judge)", value: 0.973, target: 0.80, pass: true },
  { label: "Citation Accuracy", value: 0.838, target: 0.85, pass: false },
  { label: "Refusal Accuracy", value: 0.880, target: 0.90, pass: false },
  { label: "Hallucination Rate (judge)", value: 0.027, target: 0.05, pass: true },
  { label: "p95 latency (generation)", value: "1.40s", target: "6s", pass: true },
  { label: "Avg cost/req", value: "$0.00075", target: "$0.005", pass: true },
];

/** Full run: 298/300 questions, prompt=p6 (before the adversarial-fix p7). */
export const FULL_METRICS: MetricRow[] = [
  { label: "Recall@5", value: 0.934, target: 0.85, pass: true },
  { label: "Context Recall", value: 0.934, target: 0.80, pass: true },
  { label: "Faithfulness (judge)", value: 0.944, target: 0.85, pass: true },
  { label: "Answer Relevance (judge)", value: 0.962, target: 0.80, pass: true },
  { label: "Citation Accuracy", value: 0.781, target: 0.85, pass: false },
  { label: "Refusal Accuracy", value: 0.950, target: 0.90, pass: true },
  { label: "Hallucination Rate (judge)", value: 0.079, target: 0.05, pass: false },
  { label: "Avg cost/req", value: "$0.00087", target: "$0.005", pass: true },
];

export type CategoryRow = {
  category: string;
  n: number;
  recallAt5: number | null;
  refusalAcc: number | null;
  citationAcc: number | null;
  faithfulness: number | null;
};

export const FULL_EVAL_BY_CATEGORY: CategoryRow[] = [
  { category: "adversarial", n: 11, recallAt5: null, refusalAcc: 0.636, citationAcc: null, faithfulness: 0.500 },
  { category: "ambiguous", n: 20, recallAt5: 0.789, refusalAcc: 0.950, citationAcc: 0.546, faithfulness: 0.921 },
  { category: "factoid", n: 216, recallAt5: 0.963, refusalAcc: 0.954, citationAcc: 0.823, faithfulness: 0.965 },
  { category: "multi_hop", n: 30, recallAt5: 0.856, refusalAcc: 1.000, citationAcc: 0.678, faithfulness: 0.900 },
  { category: "out_of_scope", n: 9, recallAt5: null, refusalAcc: 1.000, citationAcc: null, faithfulness: null },
  { category: "procedural", n: 12, recallAt5: 0.917, refusalAcc: 1.000, citationAcc: 0.750, faithfulness: 0.917 },
];

/** Deliberate negative result: raising the number of chunks fed to the
 * model (top_k_after) improved retrieval recall but HURT citation
 * accuracy at generation time — reverted. Kept here because it's a real
 * finding worth showing, not hidden because it didn't "work". */
export const CONTEXT_LIMIT_EXPERIMENT = {
  question: "Tăng số chunk cuối cùng đưa cho model (top_k_after) từ 5 lên 10 có giúp không?",
  retrievalOnly: [
    { limit: 5, recallAll: 0.934, recallAmbiguous: 0.789, recallMultiHop: 0.856 },
    { limit: 7, recallAll: 0.950, recallAmbiguous: 0.842, recallMultiHop: 0.856 },
    { limit: 10, recallAll: 0.963, recallAmbiguous: 0.895, recallMultiHop: 0.889 },
  ],
  generationValidation: [
    { limit: 5, citationAccMultiHop: 0.700 },
    { limit: 10, citationAccMultiHop: 0.650 },
  ],
  verdict:
    "Recall retrieval-only tăng đơn điệu — nhưng đo thật qua generation thì Citation Accuracy GIẢM (nhiều chunk hơn = nhiều distractor hơn cho model). Đã revert về 5. Bài học: số liệu retrieval-only không đủ để đổi production config.",
} as const;

export const EVAL_META = {
  smokeN: 50,
  fullN: 298,
  fullTotal: 300,
  judgeModel: "gemini-3-flash-preview (tier judge)",
} as const;
