// Thin client for the real FastAPI backend — mirrors src/rag/schemas.py
// exactly (contracts/api_contracts.md). No mocking: every field here maps
// 1:1 to what /qa/query actually returns.

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type QARequest = {
  question: string;
  session_id?: string | null;
  user_id?: string;
  domain?: string;
  mode?: "cheap" | "balanced" | "strong";
  debug?: boolean;
};

export type Citation = {
  document_id: string;
  chunk_id: string;
  section?: string | null;
  page?: number | null;
  quote?: string | null;
};

export type ModelInfo = {
  provider: string;
  model: string;
  routing_policy: string;
};

export type Usage = {
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  latency_ms: number;
};

export type QAResponse = {
  request_id: string;
  trace_id: string;
  answer: string;
  citations: Citation[];
  confidence: number | null;
  refusal: boolean;
  model: ModelInfo;
  usage: Usage;
};

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function askQuestion(req: QARequest): Promise<QAResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/qa/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
  } catch {
    throw new ApiError(
      `Không kết nối được API backend tại ${API_BASE_URL}. Backend (FastAPI + Qdrant + LiteLLM) có đang chạy không?`,
    );
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail?.message ?? body?.detail ?? detail;
    } catch {
      /* body not JSON */
    }
    throw new ApiError(`API lỗi (${res.status}): ${detail}`, res.status);
  }

  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

export { API_BASE_URL };
