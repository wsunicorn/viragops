# Golden Set — Review Log

## Trạng thái

**Batch 2 (2026-07-11): 69 câu, `review_status = pending_review` cho toàn bộ.** Đây KHÔNG phải batch đã được duyệt — script sinh dữ liệu (`scripts/seed_golden_set_iuh.py`) chủ động không tự đặt `approved` cho bất kỳ câu nào. Theo quy tắc trong [golden_set_design.md](golden_set_design.md) ("Review thủ công ít nhất 30 câu mẫu"), chỉ domain expert (người thực hiện khóa luận, sinh viên IUH) mới đủ thẩm quyền xác nhận các con số (tín chỉ, điểm số, thời hạn...) là chính xác và cập nhật `review_status → approved`.

**Thay đổi so với batch 1 (56 câu):** quota Gemini free tier đã reset, OCR lại thành công D8 (miễn giảm học phí, 10.4K ký tự) và D9 (Sổ tay SV 2024, 84.6K ký tự, 82 trang, 6 batch). Tìm thêm nguồn D13 (quy định học bổng thật, mirror site khoa vì pdt.iuh.edu.vn là SPA không crawl được — xem mục 3). Thêm 13 câu mới (q_057–q_069) và **sửa q_050** (trước đây là refusal do thiếu nguồn, nay có dữ liệu thật).

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
| `doc_hd05_mien_giam_hp` | Hướng dẫn miễn, giảm học phí và hỗ trợ chi phí học tập 2025-2026 | HD 05/HD-ĐHCN, 18/09/2025 | `d8_hu...txt` (OCR Gemini, PDF scan 5 trang) | https://ctsv.iuh.edu.vn/... (xem D8 trong `data_sources_iuh.yaml`) |
| `doc_sotay_2024` | Sổ tay Sinh viên IUH 2024 | không ghi số hiệu riêng (tổng hợp trích từ QĐ 2008/2023, QĐ 589/2021) | `d9_so-tay...txt` (OCR Gemini, PDF scan 82 trang, 6 batch) | https://tqa.iuh.edu.vn/thong-bao/so-tay-sinh-vien-cua-iuh-nam-2024/ |
| `doc_faet_hoc_bong_2024` | Quy định về việc cấp xét học bổng (áp dụng từ khóa 2024) | không thấy số QĐ trong bản trích (mẫu để trống "...../QĐ-ĐHCN ngày .... năm 2023") | `d13_0_...txt` (HTML server-rendered, không OCR) | https://faet.iuh.edu.vn/news.html@detail@271@585@... (mirror; bản gốc pdt.iuh.edu.vn/quy-che-xet-hoc-bong/ là SPA không crawl được) |

**Số hiệu quyết định mới phát hiện trong Sổ tay SV 2024** (chưa có trong bảng D1-D13 gốc, ghi nhận để tra cứu sau):
- **QĐ 2008/QĐ-ĐHCN, 24/08/2023** — Quy chế Công tác sinh viên (khen thưởng, kỷ luật, nhiệm vụ/quyền SV).
- **QĐ 589/QĐ-ĐHCN, 27/04/2021** — Nội quy học đường (thẻ SV, trang phục, giờ giấc, hành vi cấm).

## Phát hiện dữ liệu cần lưu ý khi review

1. **D1 vs D5 khác biệt thuật ngữ:** văn bản gốc QĐ 1482/2021 (Điều 33) dùng cụm "chính quy và **chất lượng cao**", trong khi trang camnang cập nhật (D5, "Điều kiện xét tốt nghiệp") dùng "chính quy và **tăng cường tiếng Anh**". Có thể là đổi tên chương trình theo thời gian hoặc khác nhau giữa 2 chương trình thật. **Cần domain expert xác nhận** đây có phải cùng một chương trình hay là 2 diện khác nhau, trước khi approve các câu q_023, q_024.
2. **D2 (quy chế học vụ) hiện trùng nội dung với D1 — nguyên nhân đã xác định: pdt.iuh.edu.vn là SPA** (React/Vue), mọi URL con trả về cùng 1 "app shell" ~482KB qua HTTP GET tĩnh, không chứa nội dung bài viết thật. Xem chi tiết `data_sources_iuh.md` mục 7. Batch này KHÔNG dùng D2 làm nguồn để tránh trích dẫn sai. Cần headless browser (Playwright, ngoài scope hiện tại) hoặc user tự tải thủ công nếu muốn nội dung "quy chế học vụ" riêng biệt.
3. **Bảng quy đổi tiếng Anh (D6_1)** trích xuất từ HTML dạng bảng bị "phẳng hóa" thành text tuần tự — chỉ dùng các cặp giá trị rõ ràng, không mơ hồ (IELTS↔Bậc, TOEFL iBT Home Edition) để tránh gán nhầm cột. Các câu về TOEIC 4 kỹ năng theo bậc B1 CHƯA được đưa vào vì rủi ro gán sai cột.
4. **q_005, q_027, q_042 (category `procedural`)** là câu suy luận (derive từ ngưỡng số trong văn bản, ví dụ "80 tín chỉ → năm 3") — không phải trích dẫn nguyên văn. Domain expert cần verify phép suy luận đúng.
5. **q_049 (`data_gap`)** không phải câu "ngoài phạm vi" thật sự — đây là câu ĐÚNG domain (học phí IUH theo ngành/năm cụ thể) nhưng nguồn hiện có chưa có số liệu chi tiết theo ngành. Refusal ở đây phản ánh giới hạn dữ liệu đã ingest, không phải giới hạn domain.
6. **⚠️ Đã xảy ra sự cố mất dữ liệu và đã fix (2026-07-11):** `scripts/extract_text.py` từng ghi đè vô điều kiện các file `.txt` đã OCR khi rerun để xử lý document mới (D13), xóa mất 84K+10K ký tự của D8/D9. Đã sửa để giữ nguyên (`preserve`) entry có `ocr_applied=True` thay vì tái xử lý. Đã OCR lại thành công cả D8 và D9.
7. **`doc_faet_hoc_bong_2024` (D13) là bản mirror**, không phải trang gốc chính thức của Phòng Đào tạo (pdt.iuh.edu.vn/quy-che-xet-hoc-bong/ — SPA không crawl được). Nội dung khớp với tiêu đề "Quy định về việc cấp xét học bổng (Áp dụng từ khóa 2024)" niêm yết chính thức, nhưng **số quyết định (QĐ .../QĐ-ĐHCN) bị để trống trong bản mirror** — cần domain expert xác nhận số hiệu thật nếu cần trích dẫn chính xác tuyệt đối.
8. **Search engine summary KHÔNG đáng tin để làm ground truth:** khi tra cứu mức học bổng A/B/C, kết quả tóm tắt từ search engine ban đầu cho ra 100%/70%/50%, nhưng khi tải và đọc trực tiếp trang nguồn (D13) thì số liệu thật là **130%/110%/100%** — sai lệch hoàn toàn. Bài học: mọi ground_truth trong golden set này đều lấy từ text đã tự tải/OCR, không bao giờ từ tóm tắt search engine.

## Việc còn lại (xem thêm `golden_set_stats.md`)

- [ ] Domain expert review từng câu, đặc biệt các số liệu (tín chỉ, điểm, thời hạn, %).
- [ ] Xác nhận phát hiện #1 (chất lượng cao vs tăng cường tiếng Anh).
- [ ] Xác nhận số QĐ thật cho quy định học bổng (phát hiện #7).
- [ ] Bổ sung câu cho: học phí cụ thể theo ngành/năm (vẫn thiếu), thang điểm rèn luyện đầy đủ (Xuất sắc/Tốt/Khá/TB/Yếu/Kém theo khoảng điểm — chưa tìm thấy trong D9).
- [ ] Mở rộng lên 200 câu có đáp án / 30 refusal / 20 adversarial / 30 multi-hop / 20 ambiguous theo đúng cơ cấu 300 câu.
- [ ] Sau Phase 3 (chunking), thay `relevant_chunks: []` bằng chunk_id thật.
