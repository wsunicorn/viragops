# Kết quả: ablation `reranker.top_k_after` (số chunk cuối cùng đưa cho model)

> Sinh 2026-07-12 khi điều tra tiếp phần retrieval-side của gap Citation
> Accuracy multi-hop/ambiguous (sau khi đã sửa golden set + activate
> `p6_citation_complete_v1`, xem `results_prompt_comparison_p6.md`).
> Retrieval-only, dùng embedding cache có sẵn (`data/experiments/
> query_embeddings_data_20260712.json`) — **$0 API cost**, không cần
> generation/judge.

## Vì sao đặt câu hỏi này

Đọc trace thật của các câu multi-hop bị chấm citation sai (xem
`results_prompt_comparison_p6.md` mục "Vì sao có candidate này") cho thấy
phần lớn KHÔNG phải lỗi retrieval — chunk đúng đã có trong top-5 — nhưng
1 nhóm nhỏ (q_069, q_129, q_180, q_199, q_201) thì đúng là retrieval-miss
thật: hop thứ 2 của câu hỏi không lọt top-5 dù top-1 tổng thể (BM25+dense
fusion) đã đúng hướng. Câu hỏi: nếu tăng số chunk cuối cùng đưa cho model
(hiện `top_k_after=5`), có "vớt" được các hop bị thiếu không, và có làm
giảm chất lượng ở category khác không?

## Kết quả — recall@k theo category, 249 câu có căn cứ

| limit | __all__ | factoid (n=188) | multi_hop (n=30) | ambiguous (n=19) | procedural (n=12) |
|---:|---:|---:|---:|---:|---:|
| 5  | 0.934 | 0.963 | 0.856 | 0.789 | 0.917 |
| 7  | 0.950 | 0.979 | 0.856 | 0.842 | 0.917 |
| 10 | 0.963 | 0.984 | 0.889 | **0.895** | 0.917 |

- **Tăng đơn điệu ở mọi category có thay đổi** — không category nào giảm
  khi tăng limit (đúng kỳ vọng toán học: tập con của top-10 luôn chứa
  top-5, recall không thể giảm). MRR giữ nguyên/nhích lên nhẹ ở mọi mức
  (không kèm theo bảng ở đây, xem script) — xếp hạng không bị xáo trộn.
- **Ambiguous cải thiện nhiều nhất** (+10.6 điểm % từ limit 5→10) —
  khớp với citation_accuracy thấp nhất đo được ở category này
  (0.451-0.535 tùy prompt).
- **Procedural KHÔNG đổi ở mọi mức** (12 câu, luôn 0.917) — phần miss còn
  lại của category này nằm ngoài cả top-10, là retrieval-miss thật sự sâu
  hơn (BM25/dense không xếp hạng đủ cao), không phải vấn đề cutoff — tăng
  limit không giải quyết được, cần fix khác (vd query rewriting).
- **Multi_hop chỉ cải thiện rõ ở limit=10** (0.856→0.889), không đổi ở
  limit=7 — 2 hop của câu hỏi này thường cách nhau khá xa trong ranking,
  cần buffer đủ lớn mới vớt được.

## Quyết định

Đổi `config/retrieval.yaml` → `reranker.top_k_after: 5` thành `10` — bằng
chứng retrieval-side rõ ràng, không có category nào bị hại. Đánh đổi cần
theo dõi (chưa đo được ở bước retrieval-only này, cần validate qua
generation thật):
- **Context Precision** (đã thấp do giới hạn cấu trúc, xem
  `results_evaluation_full.md`) sẽ càng thấp hơn (mẫu số tăng gấp đôi) —
  chấp nhận được, đã biết đây không phải chỉ số đáng tin ở hệ thống này.
- **Token/latency/cost** tăng do prompt dài hơn (gần gấp đôi số chunk) —
  cần đo lại p95 latency + cost/req thật sau khi đổi, so với target
  <=6s/<=$0.005 hiện đang ĐẠT thoải mái (p95=1.49s, cost=$0.0009/req ở
  limit=5) nên còn nhiều dư địa.
- **Citation Accuracy ở tầng GENERATION** (không chỉ retrieval) cần
  validate lại thật — nhiều chunk hơn có thể giúp model trích đủ hơn,
  nhưng cũng có thể làm model phân tâm/trích nhầm nhiều hơn. Kế hoạch:
  chạy lại `scripts/run_evaluation.py --mode targeted` cho multi_hop +
  ambiguous với limit=10 sau khi full eval baseline (limit=5, p6) hoàn
  tất, để tránh tranh chấp quota giữa 2 lần chạy song song.

**Trạng thái tại thời điểm ghi tài liệu này: `results_evaluation_full.md`
(full 300 câu, p6, limit=5) đang chạy nền, sẽ dùng làm baseline "trước"
để so sánh với limit=10 "sau".**
