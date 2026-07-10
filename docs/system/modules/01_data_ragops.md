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

## Acceptance criteria

- Ingest tối thiểu 10 tài liệu quy chế/FAQ.
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

- [ ] Raw document storage sẵn sàng.
- [ ] Extract text chạy được.
- [ ] Vietnamese normalization chạy được.
- [ ] Có ít nhất 4 chunking strategy.
- [ ] Chunk schema đầy đủ metadata.
- [ ] Embedding/index Qdrant chạy được.
- [ ] Có `data_version` và `index_version`.
- [ ] Có data quality report.
- [ ] Có smoke query kiểm tra retrieval.

