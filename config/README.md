# Config & quy ước versioning

Mọi provider/model/threshold nằm trong config, **không hard-code trong code**. Schema chuẩn: [docs/system/contracts/config_schemas.md](../docs/system/contracts/config_schemas.md).

| File | Vai trò | Dùng từ phase |
|---|---|---|
| `retrieval.yaml` | Chiến lược retrieval/fusion/rerank | 4 |
| `prompts.yaml` | Prompt active + policy citation/refusal | 5-6 |
| `model_gateway.yaml` | Tier model, fallback, budget, rate limit | 7 |
| `quality_gate.yaml` | Ngưỡng critical/warning + regression | 9 |

## Quy ước đặt version (bắt buộc, xem CHECKLIST cross-phase)

| Artifact | Format | Ví dụ |
|---|---|---|
| Data | `data_YYYYMMDD[_rev]` | `data_20260715` |
| Source snapshot | `src_YYYYMMDD` | `src_20260710` |
| Index | `idx_<data>_<embedding>` | `idx_20260715_bge_m3` |
| Prompt | `p<N>_<tên>_v<K>` | `p3_refusal_v2` |
| Retrieval config | `<mô_tả>_v<K>` | `hybrid_rrf_rerank_v1` |
| Gateway config | `gateway_<tên>_v<K>` | `gateway_default_v1` |
| Eval run | `eval_<timestamp>` | `eval_20260801_1430` |
| Gate run | `gate_<timestamp>` | `gate_20260801_1431` |
| Golden set | `golden_YYYYMMDD` | `golden_20260720` |

Quy tắc: version chỉ tăng, không sửa đè; mọi kết quả thực nghiệm phải ghi đủ bộ (data, index, prompt, retrieval, gateway, golden set) để tái lập.
