# Golden Set Design

## Mục tiêu

Tạo bộ golden set 300 câu hỏi tiếng Việt để đánh giá hệ thống RAG trên domain **Quy chế đào tạo + Sổ tay/FAQ sinh viên của Trường Đại học Công nghiệp TP.HCM (IUH)**. Golden set là nền tảng cho retrieval experiment, generation evaluation, quality gate và báo cáo định lượng.

Danh sách văn bản nguồn IUH và ánh xạ category ↔ nguồn xem [data_sources_iuh.md](data_sources_iuh.md). Category ở mục dưới đây được chuẩn hóa theo văn bản IUH thực tế (tín chỉ, thi/phúc khảo, rèn luyện, học bổng, học phí/miễn giảm, chuẩn tiếng Anh, tốt nghiệp...).

## Cơ cấu 300 câu

| Nhóm | Số lượng | Mục tiêu |
|---|---:|---|
| Câu hỏi có đáp án | 200 | Kiểm tra factoid, procedural, policy QA |
| Câu hỏi không có đáp án | 30 | Kiểm tra refusal |
| Câu hỏi adversarial | 20 | Kiểm tra prompt injection/ngoài domain |
| Câu hỏi multi-hop | 30 | Kiểm tra tổng hợp nhiều chunk |
| Câu hỏi ambiguous | 20 | Kiểm tra clarification hoặc nêu giả định |

## Category đề xuất

- học phí;
- tín chỉ;
- điều kiện tốt nghiệp;
- đăng ký môn học;
- học lại/cải thiện;
- cảnh báo học vụ;
- bảo lưu;
- chuyển ngành;
- xét học bổng;
- kỷ luật;
- lịch học/lịch thi nếu tài liệu có;
- câu hỏi ngoài phạm vi.

## Quy trình tạo

1. Chọn tài liệu nguồn đã ingest.
2. Tạo danh sách chủ đề theo Điều/Khoản/Mục.
3. Sinh câu hỏi nháp.
4. Gắn ground truth answer.
5. Gắn relevant chunks.
6. Gắn expected citations.
7. Gắn category/difficulty/risk tags.
8. Review thủ công.
9. Chạy thử retrieval baseline.
10. Sửa các case thiếu căn cứ hoặc mapping sai.

## Quy tắc chất lượng

- Mỗi câu có đáp án phải có ít nhất một relevant chunk.
- Ground truth không được chứa thông tin ngoài tài liệu.
- Expected citation phải trỏ đúng document/section.
- Câu hỏi refusal phải thật sự không có căn cứ trong tài liệu.
- Câu adversarial không được quá độc hại, chỉ cần đủ kiểm tra guardrail.
- Câu multi-hop phải cần ít nhất 2 chunks.
- Câu ambiguous phải có lý do mập mờ rõ ràng.

## Split sử dụng

| Split | Số câu | Mục đích |
|---|---:|---|
| smoke | 50 | CI nhanh |
| full | 300 | nightly eval và milestone |
| retrieval_debug | 100 | debug retrieval |
| adversarial | 20 | guardrail test |
| human_review_sample | 30 | kiểm chứng judge |

## Deliverable

- `golden_set.jsonl`
- `golden_set_review.md`
- `relevant_chunks_mapping.csv`
- `golden_set_stats.md`

