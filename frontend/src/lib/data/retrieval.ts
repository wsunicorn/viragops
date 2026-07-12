// Real numbers transcribed from docs/system/experiments/
// results_retrieval_reranking.md and results_chunking_ablation.md
// (run 20260712_0723 UTC, 249 questions, data_version=data_20260712).

export type RetrievalConfigResult = {
  config: string;
  mode: string;
  rerank: string;
  recallAt5: number;
  hitRate: number;
  mrr: number;
  ndcgAt5: number;
  p50Ms: number;
  p95Ms: number;
  best?: boolean;
};

export const RETRIEVAL_RERANKING_RESULTS: RetrievalConfigResult[] = [
  { config: "hybrid_dbsf_pre40", mode: "hybrid_dbsf", rerank: "none", recallAt5: 0.932, hitRate: 0.944, mrr: 0.791, ndcgAt5: 0.815, p50Ms: 6.1, p95Ms: 18.8, best: true },
  { config: "hybrid_rrf_rerank_gemini", mode: "hybrid_rrf", rerank: "gemini_listwise", recallAt5: 0.928, hitRate: 0.940, mrr: 0.748, ndcgAt5: 0.780, p50Ms: 998.9, p95Ms: 61023.1 },
  { config: "hybrid_dbsf_pre20", mode: "hybrid_dbsf", rerank: "none", recallAt5: 0.926, hitRate: 0.936, mrr: 0.790, ndcgAt5: 0.813, p50Ms: 5.7, p95Ms: 17.6 },
  { config: "hybrid_rrf_pre20", mode: "hybrid_rrf", rerank: "none", recallAt5: 0.906, hitRate: 0.920, mrr: 0.759, ndcgAt5: 0.783, p50Ms: 5.7, p95Ms: 19.5 },
  { config: "hybrid_rrf_pre40", mode: "hybrid_rrf", rerank: "none", recallAt5: 0.906, hitRate: 0.920, mrr: 0.761, ndcgAt5: 0.785, p50Ms: 6.3, p95Ms: 19.7 },
  { config: "dense_rerank_gemini", mode: "dense", rerank: "gemini_listwise", recallAt5: 0.894, hitRate: 0.904, mrr: 0.724, ndcgAt5: 0.754, p50Ms: 961.4, p95Ms: 1197.9 },
  { config: "dense_top5", mode: "dense", rerank: "none", recallAt5: 0.882, hitRate: 0.896, mrr: 0.657, ndcgAt5: 0.699, p50Ms: 4.7, p95Ms: 21.8 },
  { config: "sparse_bm25_top5", mode: "sparse", rerank: "none", recallAt5: 0.865, hitRate: 0.876, mrr: 0.708, ndcgAt5: 0.734, p50Ms: 4.1, p95Ms: 19.1 },
];

export const CHUNKING_ABLATION_RESULTS: RetrievalConfigResult[] = [
  { config: "structure_aware", mode: "hybrid_rrf", rerank: "none", recallAt5: 0.906, hitRate: 0.920, mrr: 0.763, ndcgAt5: 0.787, p50Ms: 5.4, p95Ms: 18.7, best: true },
  { config: "fixed", mode: "hybrid_rrf", rerank: "none", recallAt5: 0.871, hitRate: 0.876, mrr: 0.659, ndcgAt5: 0.700, p50Ms: 7.0, p95Ms: 27.7 },
  { config: "parent_child", mode: "hybrid_rrf", rerank: "none", recallAt5: 0.871, hitRate: 0.885, mrr: 0.756, ndcgAt5: 0.779, p50Ms: 5.4, p95Ms: 20.4 },
  { config: "recursive", mode: "hybrid_rrf", rerank: "none", recallAt5: 0.857, hitRate: 0.861, mrr: 0.642, ndcgAt5: 0.686, p50Ms: 7.0, p95Ms: 24.9 },
];

export const RETRIEVAL_META = {
  nQuestions: 249,
  evalK: 5,
  dataVersion: "data_20260712",
  chunkCounts: { fixed: 437, recursive: 366, structure_aware: 222, parent_child: 536 },
} as const;
