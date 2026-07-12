// Real phase status transcribed from docs/system/CHECKLIST_IMPLEMENTATION.md
// (2026-07-12). Update this file by hand whenever the checklist changes —
// intentionally not auto-parsed at build time to keep this simple, but
// every number/claim here must trace back to that file.

export type PhaseStatus = "done" | "in_progress" | "planned";

export type Phase = {
  n: number;
  weeks: string;
  title: string;
  status: PhaseStatus;
  summary: string;
  highlight?: string;
};

export const PHASES: Phase[] = [
  {
    n: 1,
    weeks: "Tuần 1-2",
    title: "Khởi tạo project & chuẩn hóa tài liệu",
    status: "done",
    summary:
      "Skeleton FastAPI, health/dependencies probe cho 5 service, config loader, Docker Compose 4 service lõi, CI ruff+pytest.",
  },
  {
    n: 2,
    weeks: "Tuần 3-4",
    title: "Chuẩn bị dữ liệu & golden set",
    status: "done",
    summary:
      "300/300 câu hỏi golden set đúng cơ cấu thiết kế (200 có đáp án / 30 refusal / 20 adversarial / 30 multi-hop / 20 ambiguous), toàn bộ đã qua AI self-review 2 batch có phương pháp và approved.",
    highlight: "300/300 câu, 100% approved",
  },
  {
    n: 3,
    weeks: "Tuần 5-6",
    title: "DataOps/RAGOps pipeline",
    status: "done",
    summary:
      "10 văn bản IUH thật, 4 chiến lược chunking, embedding Gemini dense 768d + BM25 tự viết, index Qdrant hybrid dense+sparse.",
    highlight: "10 tài liệu · 222 chunk (structure_aware)",
  },
  {
    n: 4,
    weeks: "Tuần 7-8",
    title: "Retrieval Experiment Layer",
    status: "done",
    summary:
      "8 config retrieval/reranking + 4 chiến lược chunking, chạy thật 2 lần (71 câu rồi 249 câu sau khi mở rộng golden set) — kết luận nhất quán cả 2 lần.",
    highlight: "hybrid DBSF thắng, recall@5 = 0.932",
  },
  {
    n: 5,
    weeks: "Tuần 9-10",
    title: "RAG Runtime",
    status: "done",
    summary:
      "/qa/query, /qa/debug, /qa/traces — citation fail-closed (chunk bịa bị drop), refusal 2 lớp (pre-LLM thiếu context, post-LLM citation không hợp lệ).",
  },
  {
    n: 6,
    weeks: "Tuần 11",
    title: "PromptOps",
    status: "done",
    summary:
      "Registry PostgreSQL, 8 prompt variant (P0-P7), activation yêu cầu eval_result_id thật — không cho phép activate không căn cứ.",
    highlight: "8 prompt variant, so sánh thật",
  },
  {
    n: 7,
    weeks: "Tuần 12",
    title: "Model Gateway",
    status: "done",
    summary:
      "LiteLLM proxy, fallback 4 chặng mỗi tier: Gemini key 1 → key 2 → key 3 → Ollama local (qwen2.5:7b) — thêm chặng thứ 3 giữa Phase 8 khi 2 key đầu cạn quota cùng lúc.",
    highlight: "4-hop fallback, đo thật cả 4 chặng",
  },
  {
    n: 8,
    weeks: "Tuần 13-14",
    title: "Evaluation Engine",
    status: "done",
    summary:
      "Eval 4 tầng (retrieval/context/generation/operations) qua RagService thật. Phát hiện + sửa 2 vòng: gap citation accuracy multi-hop/ambiguous, rồi hồi quy refusal ở adversarial do chính bản sửa đầu gây ra.",
    highlight: "Phát hiện & sửa 1 hồi quy thật",
  },
  {
    n: 9,
    weeks: "Tuần 15-16",
    title: "CI/CD Quality Gate",
    status: "planned",
    summary: "Chặn regression trước deploy dựa trên kết quả Evaluation Engine.",
  },
  {
    n: 10,
    weeks: "Tuần 17-18",
    title: "Observability & Cost Monitoring",
    status: "planned",
    summary: "Trace, metric, dashboard vận hành (Langfuse/OpenTelemetry/Prometheus).",
  },
  {
    n: 11,
    weeks: "Tuần 19-20",
    title: "Feedback Loop & Optimization",
    status: "planned",
    summary: "Thu feedback người dùng thật, phân loại lỗi, backlog cải tiến có kiểm soát.",
  },
  {
    n: 12,
    weeks: "Tuần 21-24",
    title: "Thực nghiệm, báo cáo, đóng gói demo",
    status: "in_progress",
    summary:
      "Frontend showcase (trang này) bắt đầu sớm giữa Phase 8 theo yêu cầu trực tiếp — phần còn lại: 6 experiment report tổng hợp, báo cáo khóa luận.",
  },
];

export const GOLDEN_SET_STATS = {
  total: 300,
  answerable: 200,
  refusalDataGap: 30,
  adversarialTotal: 20,
  adversarialPromptInjection: 11,
  outOfScope: 9,
  multiHop: 30,
  ambiguous: 20,
  approvedPct: 100,
  documentCount: 10,
  chunkCount: 222,
} as const;
