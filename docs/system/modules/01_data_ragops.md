# Module 1 - DataOps/RAGOps

## Mục tiêu

Xây pipeline quản lý vòng đời tài liệu tiếng Việt từ nguồn thô đến vector index có version. Module này quyết định chất lượng nền của toàn bộ hệ thống RAG, vì retrieval và generation đều phụ thuộc vào dữ liệu sạch, chunk đúng và metadata đầy đủ.

## Trách nhiệm

- Ingest tài liệu từ PDF/DOCX/HTML/FAQ.
- Trích xuất văn bản, OCR nếu cần.
- Làm sạch header/footer, lỗi encoding, nhiễu OCR.
- Chuẩn hóa tiếng Việt: Unicode, dấu, khoảng trắng, viết tắt phổ biến.
- Chunking theo fixed, recursive, structure-aware, parent-child.
- Gắn metadata cho document và chunk.
- Tạo embedding và index version.
- Kiểm tra data quality và index freshness.
- Xuất artifact để evaluation và experiment dùng lại.

## Input và output

| Loại | Nội dung |
|---|---|
| Input | Raw documents, source metadata, domain config |
| Output | processed documents, chunks, embeddings, `data_version`, `index_version` |
| Storage | MinIO/S3, PostgreSQL, Qdrant, DVC |

## Component nội bộ

- `document_loader`: đọc PDF/DOCX/HTML/text.
- `ocr_processor`: xử lý PDF scan nếu có.
- `text_cleaner`: loại nhiễu, sửa encoding, chuẩn hóa khoảng trắng.
- `vietnamese_normalizer`: chuẩn hóa Unicode, dấu, casing, token hints.
- `metadata_extractor`: trích `document_id`, page, section, effective_date.
- `chunker`: tạo chunk theo nhiều strategy.
- `embedder`: gọi embedding model.
- `indexer`: ghi vector vào Qdrant.
- `quality_checker`: kiểm tra duplicate, missing metadata, empty chunk.
- `version_manager`: tạo version và manifest.

## Luồng xử lý

1. Nhận danh sách tài liệu nguồn.
2. Tạo `source_version`.
3. Extract text theo từng tài liệu.
4. Clean và normalize tiếng Việt.
5. Extract metadata cấu trúc.
6. Chunk theo strategy được chọn.
7. Kiểm tra chất lượng chunk.
8. Tạo embedding.
9. Ghi Qdrant collection/index.
10. Ghi manifest gồm `data_version`, `chunking_config`, `embedding_model`, `index_version`.
11. Trigger evaluation nếu dữ liệu thay đổi đáng kể.

## Task triển khai

- Tạo schema document/chunk trong PostgreSQL.
- Tạo thư mục artifact cho raw, processed, chunks, manifests.
- Implement loader cho PDF text và DOCX trước.
- Thêm OCR sau khi pipeline text chạy ổn.
  - **Quyết định (2026-07-10):** dùng Gemini multimodal (`gemini-3.1-flash-lite`,
    input PDF trực tiếp qua `types.Part.from_bytes`) thay vì Tesseract truyền
    thống. Script: `scripts/ocr_scanned_pdfs.py` — tự chia batch 15 trang cho
    tài liệu dài (dùng `pypdf.PdfWriter` cắt sub-PDF), retry per-model theo
    thứ tự primary→fallback đọc từ `config/model_gateway.yaml`, ghi manifest
    ngay sau mỗi document (không đợi hết batch) để không mất kết quả nếu
    crash giữa chừng.
  - **Kết quả thật đã chạy trên snapshot `src_20260710`:**
    - ✅ **QĐ 610/QĐ-ĐHCN** (28 trang, quyết định thi & đánh giá KQHT — quan
      trọng nhất) OCR thành công 100%, cả 2 bản, ~65K/64K ký tự, giữ đúng số
      hiệu/ngày/Điều-Khoản/bảng biểu dạng markdown.
    - ✅ Thông báo đăng ký học phần HK1 2026-2027 (D10, 2 trang) OCR sạch.
    - ❌ **Sổ tay sinh viên 2024** (D9, 82 trang) và 1 bản PDF hướng dẫn miễn
      giảm học phí (D8) bị Gemini chặn với `finish_reason=RECITATION` — model
      nghi ngờ output trùng khớp verbatim với dữ liệu training, từ chối trả
      lời. Đã thử: đổi model (flash-lite ↔ flash-preview), giảm xuống 1
      trang/lần — vẫn bị chặn nhất quán trên nội dung này. Giả thuyết: văn
      bản trích dẫn nhiều luật/nghị định phổ biến (NĐ 81/2021, QĐ 66/2013)
      dễ bị flag hơn quy chế nội bộ IUH riêng biệt như QĐ 610.
    - ⚠️ **Rate limit thật đo được:** `gemini-3-flash-preview` free tier chỉ
      **20 request/ngày** (không phải theo phút) — dễ cạn khi dùng làm
      fallback cho nhiều batch/retry. Cần theo dõi khi mở rộng OCR sang tài
      liệu khác.
  - **Việc còn lại:** D9 (Sổ tay SV) và 1 file D8 cần thử lại khi quota reset
    (ngày hôm sau), hoặc coi là nguồn phụ — D8 đã có bản thay thế
    (`hd02-2025-pdf.pdf`, text lấy được nhưng lỗi font encoding, đọc được
    một phần) và D9 các trang giới thiệu thường ít giá trị citation hơn nội
    dung quy chế. Nếu Gemini tiếp tục chặn, phương án dự phòng là Tesseract
    + `vie` language pack cho riêng 2 tài liệu này.
- Implement 4 chunking strategy: fixed, recursive, structure-aware, parent-child.
- Implement quality checks: empty text, duplicate chunk, missing source, chunk quá dài/quá ngắn.
- Implement embedding BGE-M3 hoặc provider embedding đã chọn.
- Implement Qdrant collection naming theo `index_version`.
- Implement DVC/manifest tracking.

**Đã triển khai và chạy thật (2026-07-11):**

- `src/dataops/vietnamese_normalizer.py` — NFC normalize, xóa marker OCR
  (`--- Trang N ---`, `--- [batch ...] ---`), `normalize_for_search()`
  (lowercase, GIỮ dấu — "hoc" và "học" là 2 từ khác nhau).
- `src/dataops/chunker.py` — cả 4 strategy. `structure_aware` (mặc định
  index) tách theo `Điều N.` (giữ nguyên Khoản/Điểm bên trong, khớp
  citation dạng "Điều 6, Khoản 4"); Điều quá dài (>600 token) tự cắt tiếp
  theo nhóm Khoản. **Phát hiện quan trọng khi chạy trên dữ liệu thật:**
  ~5/9 tài liệu (trang camnang.iuh.edu.vn, D5/D13...) KHÔNG có heading
  "Điều N." — chỉ là danh sách đánh số thường — nên `structure_aware` có
  fallback tự động sang chunk theo đoạn văn (paragraph-window) cho các
  tài liệu này, đảm bảo mọi document đều có chunk thay vì biến mất khỏi
  index. `parent_child` dùng chung logic tách Điều/Khoản (parent = Điều,
  child = từng Khoản).
- `src/dataops/metadata_extractor.py` — nạp registry 9 document từ
  `DOCS` trong `scripts/seed_golden_set_iuh.py` (cùng nguồn với golden
  set, đảm bảo `document_id` khớp nhau). Cố ý KHÔNG ingest thêm các file
  khác trong `processed_manifest.json` (D2, D7, D9-index, D10, D11) — đọc
  trực tiếp thấy đây chủ yếu là app-shell SPA của pdt.iuh.edu.vn/
  stsv.iuh.edu.vn (menu/tin tức lặp lại), gần như không có nội dung quy
  chế thật — index vào sẽ làm nhiễu retrieval thay vì tăng coverage thật.
  => **9 tài liệu**, dưới ngưỡng khuyến nghị ≥10 (xem "Acceptance
  criteria" bên dưới) — chấp nhận đánh đổi chất lượng thay vì độn số.
- `src/dataops/embedder.py` — dense embedding qua Gemini API
  (`gemini-embedding-001`, 768d, `task_type` RETRIEVAL_DOCUMENT/
  RETRIEVAL_QUERY riêng cho index/query theo thiết kế asymmetric của
  Gemini). **Rate limit đo thật:** free tier tính MỖI text trong 1 lệnh
  batch là 1 request (không phải 1 lệnh = 1 request) — quota
  100 request/phút, batch 100 lấp đầy quota ngay lập tức. Dùng batch ≤80 +
  chờ ≥65s giữa batch (xem `config/model_gateway.yaml`).
- `src/dataops/sparse_bm25.py` — **BGE-M3/fastembed đổi hướng giữa
  chừng:** dự định dùng fastembed's `Qdrant/bm25` nhưng
  huggingface.co resolve-endpoint bị ISP reset kết nối giữa chừng tải
  (cùng dạng lỗi CDN đã gặp với Docker Hub CloudFront ở Phase 1) — tự
  viết BM25 chuẩn (Robertson/Sparck Jones) với hashing-trick qua `mmh3`,
  không phụ thuộc mạng ngoài, phù hợp corpus nhỏ.
- `src/dataops/indexer.py` — Qdrant named vectors (`dense` + `sparse`),
  collection đặt tên theo `index_version` (không ghi đè, cho phép
  rollback), hybrid search qua Query API RRF fusion server-side
  (`qdrant-client>=1.10`, khớp `qdrant server v1.15.4`).
- `sql/schema.sql` + `scripts/init_postgres_schema.py` — bảng
  `documents`/`chunks` trong Postgres làm metadata registry (vector +
  payload retrieval vẫn ở Qdrant).
- `scripts/ingest_data.py` — orchestrator đầy đủ, đã chạy thật thành
  công trên snapshot `src_20260710`: **9 document → 220 chunk
  structure_aware → 0 lỗi critical (114 warning, chủ yếu
  `missing_section` cho 5 tài liệu fallback — đúng như kỳ vọng, không
  phải bug) → 220 vector 768d → Qdrant collection
  `viragops_iuh_idx_20260711_geminiembedding001` → Postgres (9 docs,
  220 chunks)**. Cả 4 strategy đều xuất file JSONL riêng
  (`data/chunks/{strategy}_data_20260711.jsonl`) để Phase 4 so sánh,
  nhưng chỉ `structure_aware` được embed + index.
- `scripts/smoke_retrieval.py` — test thật với câu hỏi "Điều kiện tốt
  nghiệp đại học cần bao nhiêu tín chỉ" trả về đúng
  `doc_qd1482_quy_che_tin_chi, Điều 6, Khoản 4` (định nghĩa tín chỉ) và
  `doc_camnang_dieu_kien_tot_nghiep` (điều kiện tốt nghiệp) trong top 5 —
  hybrid dense+sparse RRF hoạt động đúng, dù chưa có reranker (Phase 4).
- **Việc còn lại (không phải bug, ghi nhận trung thực):**
  `relevant_chunks` trong golden set vẫn để trống — thử khớp tự động
  citation `expected_citations[].section` (vd "Điều 6, Khoản 4.a") với
  `chunk.section` chỉ khớp chính xác 5/71 câu vì `structure_aware` gom
  chunk theo NHÓM Khoản khi Điều quá dài (vd "Điều 6, Khoản 4-6") trong
  khi golden set trích tới cấp Điểm — cần logic parse range hoặc chuyển
  sang `parent_child` (chunk theo từng Khoản riêng) để khớp chính xác
  hơn; không tự động gán ẩu để tránh gán sai relevant_chunks.

## Acceptance criteria

- Ingest tối thiểu 10 tài liệu quy chế/FAQ. **9/10 đạt được (xem lý do ở
  trên — ưu tiên chất lượng, không độn tài liệu SPA-shell rỗng nội dung).**
- Mỗi document có metadata bắt buộc.
- Mỗi chunk có `chunk_id`, `document_id`, `text`, `section`, `page`, `token_count`.
- Tạo được Qdrant index và query thử trả về chunks.
- Có manifest version cho mỗi lần ingest.
- Data quality report không có lỗi critical.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Chunk mất ngữ cảnh | Chunking fixed cắt ngang Điều/Khoản | Dùng structure-aware hoặc parent-child |
| Retrieval sai vì OCR | Text nhiễu, mất dấu | Thêm OCR cleanup và normalization |
| Citation sai | Metadata page/section thiếu | Bắt buộc metadata validation |
| Index cũ | Source thay đổi nhưng chưa reindex | Freshness check theo `source_version` |

## Checklist hoàn tất

- [x] Raw document storage sẵn sàng (`data/raw/iuh/src_20260710/`, Phase 2).
- [x] Extract text chạy được (`scripts/extract_text.py`, Phase 2).
- [x] Vietnamese normalization chạy được (`src/dataops/vietnamese_normalizer.py`).
- [x] Có ít nhất 4 chunking strategy (`src/dataops/chunker.py`: fixed, recursive, structure_aware, parent_child).
- [x] Chunk schema đầy đủ metadata *(trừ `page_start`/`page_end` — chưa track qua bước normalize, để `null`; xem golden_set_review.md)*.
- [x] Embedding/index Qdrant chạy được — 220 chunk, collection `viragops_iuh_idx_20260711_geminiembedding001`.
- [x] Có `data_version` và `index_version` — `data_20260711` / `idx_20260711_geminiembedding001`, gán vào `config/retrieval.yaml`.
- [x] Có data quality report — `data/chunks/quality_report_data_20260711.json`, 0 critical.
- [x] Có smoke query kiểm tra retrieval — `scripts/smoke_retrieval.py`, kết quả đúng domain.

