// Real numbers transcribed from docs/system/experiments/
// results_prompt_comparison.md (Phase 6, run promptcmp_20260711_1408,
// 12-question smoke) and results_prompt_comparison_p6.md (Phase 8,
// live targeted comparisons on real question sets, 2026-07-12).

export type PromptSmokeResult = {
  version: string;
  parseOk: number;
  refusalAcc: number;
  citationValid: number;
  groundedCite: number;
  avgTokens: number;
  avgGenMs: number;
  best?: boolean;
};

export const PROMPT_COMPARISON_PHASE6: PromptSmokeResult[] = [
  { version: "p1_grounded_v1", parseOk: 1.0, refusalAcc: 1.0, citationValid: 1.0, groundedCite: 1.0, avgTokens: 83.4, avgGenMs: 1159, best: true },
  { version: "p5_concise_v1", parseOk: 1.0, refusalAcc: 1.0, citationValid: 1.0, groundedCite: 0.88, avgTokens: 81.2, avgGenMs: 1154 },
  { version: "p3_refusal_aware_v1", parseOk: 1.0, refusalAcc: 0.75, citationValid: 1.0, groundedCite: 1.0, avgTokens: 103.6, avgGenMs: 1349 },
  { version: "p4_self_check_v1", parseOk: 1.0, refusalAcc: 0.50, citationValid: 1.0, groundedCite: 1.0, avgTokens: 111.8, avgGenMs: 1380 },
  { version: "p0_naive_v1", parseOk: 1.0, refusalAcc: 0.50, citationValid: 1.0, groundedCite: 1.0, avgTokens: 120.8, avgGenMs: 1256 },
  { version: "p2_citation_first_v1", parseOk: 1.0, refusalAcc: 0.0, citationValid: 1.0, groundedCite: 0.88, avgTokens: 100.8, avgGenMs: 1237 },
];

/** The 3-step prompt evolution that happened live during Phase 8, each
 * step driven by a real measured problem, not a hypothetical one. */
export const PROMPT_EVOLUTION = [
  {
    version: "p1_grounded_v1",
    period: "Phase 5 → Phase 8 (2026-07-11 → 2026-07-12)",
    role: "Baseline — thắng so sánh Phase 6 (6 variant, 12 câu smoke)",
    finding:
      "Phase 8 full eval (300 câu) đo được Citation Accuracy thấp ở multi_hop (0.625) và ambiguous (0.452) — model có chunk đúng trong top-5 nhưng hay bỏ sót/trích nhầm.",
    metrics: [
      { label: "Citation Acc multi_hop", value: "0.672" },
      { label: "Citation Acc ambiguous", value: "0.451" },
      { label: "Refusal Acc adversarial", value: "0.909" },
    ],
  },
  {
    version: "p6_citation_complete_v1",
    period: "2026-07-12",
    role: "Sửa citation completeness — activate sau so sánh live thật",
    finding:
      "Cải thiện citation accuracy rõ (multi_hop +2.8đ%, ambiguous +8.4đ%) — nhưng full eval sau đó phát hiện HỒI QUY: Refusal Accuracy nhóm adversarial tụt 0.909→0.636. Model vẫn từ chối đúng bản chất nhưng quên gắn cờ refusal vì tìm được đoạn để giải thích.",
    metrics: [
      { label: "Citation Acc multi_hop", value: "0.700", delta: "+0.028" },
      { label: "Citation Acc ambiguous", value: "0.535", delta: "+0.084" },
      { label: "Refusal Acc adversarial", value: "0.636", delta: "-0.273", negative: true },
    ],
  },
  {
    version: "p7_citation_complete_safe_v1",
    period: "2026-07-12",
    role: "Sửa hồi quy — prompt hiện tại đang chạy production",
    finding:
      "Thêm 1 quy tắc tường minh: yêu cầu vi phạm chính sách/an toàn LUÔN đặt refusal=true dù có trích dẫn giải thích được hay không. Verify sạch trên toàn bộ câu adversarial + out_of_scope.",
    metrics: [
      { label: "Refusal Acc adversarial", value: "1.000 (11/11)", delta: "+0.364" },
      { label: "Refusal Acc out_of_scope", value: "1.000 (9/9)" },
      { label: "Kể cả câu p1 & p6 đều sai", value: "q_198 → đúng" },
    ],
  },
] as const;

export const PROMPT_COUNT = 8;
