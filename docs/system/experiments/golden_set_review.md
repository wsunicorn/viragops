# Golden Set — Review Log

## Trạng thái

**Batch đầu tiên: 56 câu, `review_status = pending_review` cho toàn bộ.** Đây KHÔNG phải batch đã được duyệt — script sinh dữ liệu (`scripts/seed_golden_set_iuh.py`) chủ động không tự đặt `approved` cho bất kỳ câu nào. Theo quy tắc trong [golden_set_design.md](golden_set_design.md) ("Review thủ công ít nhất 30 câu mẫu"), chỉ domain expert (người thực hiện khóa luận, sinh viên IUH) mới đủ thẩm quyền xác nhận các con số (tín chỉ, điểm số, thời hạn...) là chính xác và cập nhật `review_status → approved`.

## Nguồn gốc dữ liệu

Toàn bộ `ground_truth` trong batch này được copy/diễn giải trực tiếp từ text đã trích xuất/OCR thật (không bịa số liệu) tại `data/processed/iuh/src_20260710/`. Bảng văn bản nguồn:

| document_id | Tên văn bản | Số hiệu / ngày ban hành | Nguồn trích xuất | URL |
|---|---|---|---|---|
| `doc_qd1482_quy_che_tin_chi` | Quy chế đào tạo theo hệ thống tín chỉ | QĐ 1482/QĐ-ĐHCN, 15/11/2021 | `d1_0_...txt` (HTML camnang, không OCR) | https://camnang.iuh.edu.vn/quy-che-dao-tao-theo-he-thong-tin-chi.php |
| `doc_qd610_thi_danh_gia` | Quy chế quản lý công tác thi và đánh giá KQHT | QĐ 610/QĐ-ĐHCN, 21/02/2025 | `d3_quyet-dinh-so-610...txt` (OCR Gemini, PDF scan 28 trang) | https://tqa.iuh.edu.vn/wp-content/uploads/2025/12/Quyet-dinh-so-610-QD-DHCN-... |
| `doc_tqa_phuc_khao` | Quy định phúc khảo (trích Điều 26, 27 QĐ 610) | QĐ 610/QĐ-ĐHCN, 21/02/2025 | `d4_0_...txt` (HTML tqa, không OCR) | https://tqa.iuh.edu.vn/cong-tac-khao-thi/quy-dinh-phuc-khao/ |
| `doc_camnang_dieu_kien_tot_nghiep` | Điều kiện xét tốt nghiệp | Cẩm nang người học (tóm tắt từ QĐ 1482 Điều 33, cập nhật) | `d5_0_...txt` (HTML camnang) | https://camnang.iuh.edu.vn/dieu-kien-xet-tot-nghiep.php |
| `doc_camnang_chuan_tieng_anh` | Quy định chuẩn tiếng Anh | Cẩm nang người học | `d6_0_...txt` (HTML camnang) | https://camnang.iuh.edu.vn/quy-dinh-chuan-tieng-anh.php |
| `doc_camnang_bang_quy_doi_tieng_anh` | Bảng quy đổi điểm chứng chỉ tiếng Anh | Cẩm nang người học | `d6_1_...txt` (HTML camnang) | https://camnang.iuh.edu.vn/bang-quy-doi-diem-chung-chi-tieng-anh.php |

## Phát hiện dữ liệu cần lưu ý khi review

1. **D1 vs D5 khác biệt thuật ngữ:** văn bản gốc QĐ 1482/2021 (Điều 33) dùng cụm "chính quy và **chất lượng cao**", trong khi trang camnang cập nhật (D5, "Điều kiện xét tốt nghiệp") dùng "chính quy và **tăng cường tiếng Anh**". Có thể là đổi tên chương trình theo thời gian hoặc khác nhau giữa 2 chương trình thật. **Cần domain expert xác nhận** đây có phải cùng một chương trình hay là 2 diện khác nhau, trước khi approve các câu q_023, q_024.
2. **D2 (quy chế học vụ) hiện trùng nội dung với D1** — chưa xác định được URL riêng cho "quy chế học vụ" (xem `data_sources_iuh.md` mục ghi chú). Batch này KHÔNG dùng D2 làm nguồn để tránh trích dẫn sai.
3. **Bảng quy đổi tiếng Anh (D6_1)** trích xuất từ HTML dạng bảng bị "phẳng hóa" thành text tuần tự — chỉ dùng các cặp giá trị rõ ràng, không mơ hồ (IELTS↔Bậc, TOEFL iBT Home Edition) để tránh gán nhầm cột. Các câu về TOEIC 4 kỹ năng theo bậc B1 CHƯA được đưa vào vì rủi ro gán sai cột.
4. **q_005, q_027, q_042 (category `procedural`)** là câu suy luận (derive từ ngưỡng số trong văn bản, ví dụ "80 tín chỉ → năm 3") — không phải trích dẫn nguyên văn. Domain expert cần verify phép suy luận đúng.
5. **q_049, q_050 (`data_gap`)** không phải câu "ngoài phạm vi" thật sự — đây là câu ĐÚNG domain (học phí, học bổng IUH) nhưng nguồn hiện có (D7, D8) chỉ là trang danh mục/bị lỗi encoding, chưa có số liệu cụ thể. Refusal ở đây phản ánh giới hạn dữ liệu đã ingest, không phải giới hạn domain — sẽ cần re-classify khi có nguồn đầy đủ hơn.

## Việc còn lại (xem thêm `golden_set_stats.md`)

- [ ] Domain expert review từng câu, đặc biệt các số liệu (tín chỉ, điểm, thời hạn).
- [ ] Xác nhận phát hiện #1 (chất lượng cao vs tăng cường tiếng Anh).
- [ ] Bổ sung câu cho: học phí cụ thể, học bổng cụ thể (sau khi có nguồn), điểm rèn luyện/kỷ luật (sau khi OCR Sổ tay SV thành công).
- [ ] Mở rộng lên 200 câu có đáp án / 30 refusal / 20 adversarial / 30 multi-hop / 20 ambiguous theo đúng cơ cấu 300 câu.
- [ ] Sau Phase 3 (chunking), thay `relevant_chunks: []` bằng chunk_id thật.
