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

## Validate ở tầng generation thật — VÀ ĐÃ REVERT

Đổi thử `top_k_after: 5 -> 10`, chạy lại `scripts/run_evaluation.py
--mode targeted --category multi_hop --prompt-version
p7_citation_complete_safe_v1` (30 câu, chạy sạch 100% qua Gemini tertiary
key, không dính Ollama fallback — verify qua cột `fallback_hop` trong
CSV) để đo đúng metric mục tiêu (Citation Accuracy), không chỉ suy luận
từ recall retrieval-only:

| limit | Recall@k (multi_hop) | **Citation Accuracy (multi_hop)** |
|---:|---:|---:|
| 5  | 0.856 | **0.700** |
| 10 | 0.889 | **0.650** |

**Kết quả NGƯỢC với kỳ vọng từ bước retrieval-only:** Recall tăng đúng
như dự đoán (+3.3 điểm %), nhưng Citation Accuracy — metric mục tiêu thật
sự đang cần sửa — GIẢM (-5 điểm %). Diễn giải: đưa nhiều chunk hơn cho
model làm tăng khả năng chunk đúng "có mặt" trong ngữ cảnh, nhưng cũng
tăng số "chunk gây nhiễu" (distractor) khiến model dễ trích nhầm/trích
thừa hơn — đúng loại lỗi mà `p6`/`p7`'s quy tắc 2 ("chỉ trích khi đoạn đó
THỰC SỰ là căn cứ") được thiết kế để giảm, nhưng bị chính việc tăng
`top_k_after` làm khó hơn.

**Quyết định cuối: REVERT `top_k_after` về `5`.** Giữ nguyên phần sửa
prompt (`p6`/`p7`) — phần đó đã chứng minh cải thiện thật cả 2 metric
(Citation Accuracy VÀ Refusal Accuracy) mà không cần đổi retrieval.
Recall-side gap còn lại (đặc biệt ambiguous, procedural — xem bảng trên)
vẫn treo, nhưng "tăng top_k_after" không phải giải pháp đúng cho mục
tiêu Citation Accuracy — cần hướng khác (vd re-retrieval theo từng hop
CÓ CHỌN LỌC chỉ khi câu hỏi được phát hiện là multi-hop, thay vì tăng
context cho MỌI câu hỏi kể cả factoid đơn giản).

**Bài học chính của thí nghiệm này (đáng đưa vào báo cáo khóa luận):**
số liệu retrieval-only (recall@k) không đủ để quyết định thay đổi
production — bắt buộc phải đo thêm 1 bước qua generation thật trước khi
đổi config, vì 2 tầng có thể phản ứng NGƯỢC HƯỚNG NHAU với cùng 1 thay
đổi.
