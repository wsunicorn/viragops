# Retrospective — điểm mạnh & nợ kỹ thuật cần quay lại

> Tài liệu sống, cập nhật ở cuối mỗi phase (không phải chỉ 1 lần). Mục đích:
> khi hệ thống đã chạy hết 12 phase, quay lại đây để biết chỗ nào từng là
> đường tắt có chủ đích (cần nâng cấp trước khi dùng số liệu làm báo cáo
> chính thức) và chỗ nào là cách làm nên giữ nguyên. Không lặp lại trạng
> thái "xong bao nhiêu %" — cái đó đã có ở `CHECKLIST_IMPLEMENTATION.md`.
> Tài liệu này trả lời câu hỏi khác: **"làm vậy có ổn không, và nếu chưa
> ổn thì sửa ở đâu."**

## 1. Đã làm tốt — giữ nguyên khi cải thiện phần khác

### Kỷ luật dữ liệu (không bịa, luôn có nguồn thật)
- Mọi ground_truth trong golden set trích/diễn giải trực tiếp từ text đã
  tự tải/OCR — không bao giờ lấy từ tóm tắt search engine. Đã có bằng
  chứng cụ thể việc này cứu 1 lỗi thật: WebSearch tóm tắt học bổng ra
  100%/70%/50%, đọc nguồn thật (D13) thì đúng là 130%/110%/100% — sai
  hoàn toàn, bị chặn TRƯỚC khi vào golden set. Xem
  `experiments/golden_set_review.md` phát hiện #8.
- Khi 1 nguồn có khoảng trống thật (số QĐ học bổng D13, "quy chế học vụ"
  D2 không crawl được), ghi nhận là data gap tường minh
  (`requires_refusal`, risk_tag `data_gap`) thay vì đoán hoặc điền bừa.

### Khả năng phục hồi kỹ thuật (tìm bug thật, tự sửa tận gốc)
- 2 lần data-loss bug trong `extract_text.py` (ghi đè `.txt` đã OCR khi
  rerun cho doc mới) đều được **tự phát hiện** qua kiểm tra chéo (char
  count bất thường), không phải do user báo. Fix có 2 lớp độc lập
  (preserve theo `ocr_applied` flag ở `main()`, + refuse-overwrite theo độ
  dài ở `process_entry()`) — bài học rút ra và ghi lại: *"fix 1 bug
  data-loss phải audit toàn bộ dữ liệu liên quan, không chỉ phần vừa thao
  tác"* (lần đầu chỉ check D8/D9, bỏ sót D3, phải quay lại lần 2).
- `ocr_scanned_pdfs.py`: sau khi mất trắng 1 lần OCR thành công vì crash
  giữa batch, sửa thành ghi manifest ngay sau MỖI document.
- Khi fastembed bị ISP chặn CDN giữa chừng tải (Phase 3) — nhận diện
  ngay đây là CÙNG DẠNG lỗi đã gặp với Docker Hub (Phase 1), không đoán
  mò/retry vô hạn, chuyển hướng sang tự viết BM25 (không phụ thuộc mạng
  ngoài) trong cùng phiên làm việc.

### Kỷ luật checklist trung thực
- Không có mục nào được tick `[x]` mà không có bằng chứng chạy thật đi
  kèm (lệnh đã chạy, số liệu đo được, đường dẫn file kết quả). Khi 1 tiêu
  chí DoD chỉ đạt một phần (vd Phase 2 "300 câu hỏi", Phase 3 "≥10 tài
  liệu"), checklist ghi rõ % thật và lý do — không âm thầm hạ tiêu chí
  hay đánh dấu xong giả.
- Approve golden set qua AI self-review (theo yêu cầu tường minh của
  user) vẫn có audit trail đầy đủ (`reviewed_by`, `reviewed_at`,
  `review_note`) thay vì sửa ngầm field `review_status`, và tài liệu ghi
  rõ đây KHÔNG tương đương domain-expert review.

### Thiết kế cấu hình
- Không hard-code model/tham số trong code — mọi model, chunking param,
  rate limit đều nằm trong `config/*.yaml`, có `*_config_id` bắt buộc
  (validate qua `config_loader.py`). Đổi model chỉ sửa YAML, không đụng
  code runtime.
- Đặt tên version có quy tắc (`data_YYYYMMDD`, `idx_<data>_<embedding>`)
  áp dụng nhất quán từ Phase 2, không phải nghĩ thêm ở Phase 3.
- Qdrant collection đặt tên theo `index_version` thay vì 1 collection cố
  định — cho phép rollback bằng cách trỏ lại `retrieval.yaml`, không cần
  xóa dữ liệu cũ.

### Kiểm chứng bằng chạy thật, không chỉ code+test đơn vị
- Mỗi phase đều có bước "chạy thật trên Docker/API thật" trước khi commit
  (Phase 1: `/health/dependencies` thật; Phase 2: OCR thật tốn quota
  thật; Phase 3: `docker compose up` + ingest thật tốn quota Gemini thật +
  `smoke_retrieval.py` trả kết quả thật) — không dừng ở "test pass".

---

## 2. Cần cải thiện — nợ kỹ thuật, xếp theo mức ưu tiên

### P0 — phải làm trước khi dùng làm baseline/số liệu chính thức cho báo cáo

1. **Golden set mới 76/300 (25%).** Đây là gốc rễ khiến mọi metric ở
   Phase 5+ (recall, faithfulness...) chưa đại diện được cho toàn domain.
   `golden_set_stats.md` có bảng so target theo nhóm (adversarial 2/20,
   refusal thật 4/30, multi-hop 4/30 — chỉ 1 câu multi-hop THẬT qua 2 văn
   bản, còn lại gộp nhiều khoản trong cùng 1 văn bản — ambiguous 1/20).
2. **Golden set chỉ qua AI self-review, chưa qua domain-expert review
   thật.** User (SV IUH) nên tự đối chiếu trải nghiệm thực tế, đặc biệt
   các câu có con số (tín chỉ/điểm/%) — 38 câu có số đã verify khớp nguồn
   nhưng "khớp nguồn" không đồng nghĩa "nguồn đó còn đúng/còn hiệu lực".
3. **`relevant_chunks` trong golden set vẫn trống.** Auto-match citation
   cấp Điểm (vd "Điều 6, Khoản 4.a") với chunk gom theo nhóm Khoản
   (`structure_aware`) chỉ khớp đúng 5/71 câu không-refusal — chưa gán vì
   rủi ro gán sai cao hơn giá trị. Không có `relevant_chunks` = không đo
   được recall@k đúng nghĩa ở Phase 5. **Hướng sửa gợi ý:** viết matcher
   dùng chunk `parent_child` (child = từng Khoản riêng, không gom nhóm)
   làm nguồn linking thay vì `structure_aware`, hoặc parse range
   "Khoản 4-6" để biết Khoản 4 nằm trong đó.

### P1 — nên làm trước khi coi hệ thống "hoàn thành"

4. **9/13 tài liệu được ingest ở Phase 3** — 4 tài liệu còn lại (D2 "quy
   chế học vụ", D7, D9-index, D10, D11) là site-chrome SPA gần như rỗng
   nội dung thật, bị loại có chủ đích. Nhưng **D2 (quy chế học vụ) là nội
   dung thật sự cần** mà vẫn chưa có cách lấy được (pdt.iuh.edu.vn là SPA
   React/Vue, cần Playwright — ngoài scope hiện tại). Đây là khoảng trống
   nội dung thật, không chỉ vấn đề kỹ thuật.
5. **`page_start`/`page_end` luôn `null`** trong mọi chunk — marker trang
   OCR (`--- Trang N ---`) bị xóa ở bước `vietnamese_normalizer.clean_text`
   trước khi tới chunker, nên thông tin trang bị mất. Muốn có page-level
   citation chính xác phải thread page marker qua trước khi strip.
6. **CI chưa cài `dataops`/`ragops` extras** — phát hiện và sửa ngay
   trong phiên này (`.github/workflows/ci.yml` giờ cài
   `.[dev,dataops,ragops]`), nhưng đây là dấu hiệu nên kiểm tra CI thật
   (không chỉ chạy local) mỗi khi thêm optional-dependency group mới.
7. **`tests/integration/` và `tests/e2e/` vẫn trống** — toàn bộ pipeline
   Qdrant/Postgres/Gemini mới được verify bằng chạy tay (`ingest_data.py`,
   `smoke_retrieval.py`), chưa có test tự động hoá lại được (ngay cả ở
   dạng skip-nếu-service-không-chạy). Nếu code thoái hoá sau này sẽ không
   ai phát hiện tới khi chạy tay lại.
8. **BM25 tự viết (`sparse_bm25.py`) chưa được so sánh với 1 baseline đã
   biết đúng** (vd fastembed/rank_bm25) để xác nhận công thức/hashing-trick
   cho kết quả tương đương — mới có unit test kiểm tra tính chất tương
   đối (common term có idf thấp hơn rare term), chưa kiểm tra độ chính
   xác retrieval tuyệt đối so với BM25 chuẩn.
9. **Chunking coverage còn thiếu nội dung:** học phí cụ thể theo
   ngành/năm, thang điểm rèn luyện đầy đủ (Xuất sắc/Tốt/Khá/TB/Yếu/Kém
   theo khoảng điểm) chưa tìm thấy trong bất kỳ nguồn nào đã ingest —
   không phải lỗi chunking, là thiếu nguồn từ Phase 2.

### P2 — cải thiện khi có thời gian, không chặn tiến độ

10. **Token counting dùng `tiktoken cl100k_base`** làm xấp xỉ (không phải
    tokenizer thật của Gemini) — đủ dùng để quyết định ranh giới chunk,
    nhưng không chính xác nếu sau này cần tính cost/latency theo token
    thật.
11. **Không có migration tool cho Postgres** (`sql/schema.sql` áp dụng
    thủ công qua `init_postgres_schema.py`, `CREATE TABLE IF NOT EXISTS`)
    — ổn cho quy mô hiện tại (2 bảng), nhưng nếu schema đổi nhiều lần sẽ
    khó track lịch sử thay đổi.
12. **Môi trường có phần phụ thuộc máy cụ thể của user** (Docker Desktop
    registry-mirror workaround, Ollama cài sẵn dù cuối cùng không dùng) —
    người khác clone repo về sẽ cần tự set up mirror Docker; không ảnh
    hưởng logic nhưng ảnh hưởng "chạy được ngay" cho người review khác.
13. **Retry/backoff cho Gemini API viết riêng lẻ ở từng script**
    (`ocr_scanned_pdfs.py`, `embedder.py` mỗi cái tự có logic retry hơi
    khác nhau) thay vì 1 lớp client dùng chung — chấp nhận được ở quy mô
    hiện tại, nhưng nếu thêm nhiều script gọi Gemini nữa nên rút thành 1
    module `src/common/gemini_client.py`.
14. **Chưa verify các model ID/URL tham khảo dùng trong báo cáo khóa
    luận** (GPT-5.5, Gemma 4, Llama 4...) có tồn tại thật; chưa xóa tham
    chiếu file `llmops_image_prompts.md` không tồn tại; caption ảnh chưa
    khớp tên file `figures/`; chưa export lại `.docx`. Việc này không
    liên quan Phase 3 nhưng vẫn đang mở từ trước — xem
    `[[feedback-user-viet-tieng-viet]]` trong memory.

---

## Cách dùng tài liệu này

- Trước khi bắt đầu 1 phase mới: đọc mục P0/P1 xem có mục nào block phase
  sắp làm không.
- Sau khi hoàn thành Phase 12 (demo cuối): đọc lại toàn bộ mục 2 theo thứ
  tự ưu tiên, xử lý P0 trước khi dùng số liệu cho báo cáo chính thức.
- Mỗi khi 1 mục ở đây được xử lý xong, xoá khỏi danh sách (đừng để "đã
  fix" nằm lẫn với "chưa fix") và ghi 1 dòng vào changelog bên dưới.

## Changelog

- 2026-07-11: Tạo tài liệu, tổng hợp điểm tốt/nợ kỹ thuật từ Phase 1-3.
  Đã fix ngay trong phiên: CI thiếu `dataops`/`ragops` extras (mục P1.6).
