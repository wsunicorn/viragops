# Golden Set — Review Log

## Trạng thái

**Batch 3 (2026-07-11): 76 câu, `review_status = approved` cho toàn bộ — theo yêu cầu trực tiếp của user.**

### Audit trail approval

- **Người/hệ thống duyệt:** `ai_self_review` (Claude, theo yêu cầu tường minh của user: "mở rộng thêm câu hỏi... tự approve luôn cho tôi luôn nha").
- **Công cụ:** `scripts/approve_golden_set.py --reviewer ai_self_review`, ghi `reviewed_by`/`reviewed_at`/`review_note` vào từng item — không sửa `review_status` âm thầm.
- **Phương pháp verify trước khi approve** (không chỉ đọc lướt):
  1. Kiểm tra chéo tự động: mọi `document_id` trong `relevant_documents`/`expected_citations` đều tồn tại trong registry `DOCS` của seed script (0 lỗi/76 câu).
  2. Đối chiếu số liệu tự động: trích mọi con số trong `ground_truth`, kiểm tra xuất hiện trong file nguồn tương ứng (38/76 câu có số liệu — 0 sai lệch thật; 2 "issue" ban đầu là q_013/q_027, xác nhận đúng thiết kế vì đây là số ví dụ minh họa cho câu `procedural`, không phải trích dẫn verbatim).
  3. Đối chiếu cụm từ đặc trưng cho các claim phủ định/phức hợp (vd q_066 "miễn giảm học phí không áp dụng cho học lại/học bổ sung/ngành thứ 2" — verify từng cụm có trong nguồn).
  4. Giải quyết 2 điểm mơ hồ đã ghi ở batch trước bằng tra cứu bổ sung (xem mục "Phát hiện dữ liệu" bên dưới).
- **Giới hạn cần biết:** đây là AI self-review có phương pháp, **không tương đương domain-expert review đầy đủ** như quy tắc gốc trong [golden_set_design.md](golden_set_design.md) yêu cầu ("Review thủ công ít nhất 30 câu mẫu" — ngụ ý người có kiến thức nền, khả năng đối chiếu thực tế đã trải nghiệm với tư cách sinh viên IUH, thứ mà AI không có). Khuyến nghị: domain expert (user) vẫn nên spot-check trước khi dùng batch này làm baseline chính thức cho báo cáo khóa luận — đặc biệt 2 mục còn treo trong phần "Phát hiện dữ liệu" bên dưới (số QĐ học bổng D13 chưa xác nhận).

**Lịch sử batch:**
- Batch 1 (56 câu): pending_review.
- Batch 2 (69 câu): thêm OCR D8/D9 thành công (quota reset), tìm D13, thêm 13 câu — vẫn pending_review.
- Batch 3 (76 câu, batch này): khôi phục D3 (bị mất do bug ghi đè lần 2), thêm 7 câu từ Điều 20-24 QĐ 610 (quy trình chấm thi) + 1 câu học bổng doanh nghiệp, giải quyết 2 điểm mơ hồ, **approve toàn bộ theo yêu cầu user**.

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

1. **[ĐÃ GIẢI QUYẾT 2026-07-11] D1 vs D5 khác biệt thuật ngữ:** văn bản gốc QĐ 1482/2021 (Điều 33) dùng cụm "chính quy và **chất lượng cao**", trong khi trang camnang cập nhật (D5) dùng "chính quy và **tăng cường tiếng Anh**". Đã xác nhận qua tra cứu: đây LÀ CÙNG một chương trình — Bộ GD&ĐT ban hành Thông tư 11/2023 bãi bỏ Thông tư 23/2014 (khái niệm "chương trình chất lượng cao"); các trường thuộc hệ thống (gồm IUH) đổi tên chương trình này thành "chương trình tăng cường tiếng Anh" từ khóa 2023-2024 trở đi. q_023, q_024 dùng thuật ngữ hiện hành ("tăng cường tiếng Anh") theo D5 — chính xác và nhất quán với tên gọi hiện tại.
2. **D2 (quy chế học vụ) hiện trùng nội dung với D1 — nguyên nhân đã xác định: pdt.iuh.edu.vn là SPA** (React/Vue), mọi URL con trả về cùng 1 "app shell" ~482KB qua HTTP GET tĩnh, không chứa nội dung bài viết thật. Xem chi tiết `data_sources_iuh.md` mục 7. Batch này KHÔNG dùng D2 làm nguồn để tránh trích dẫn sai. Cần headless browser (Playwright, ngoài scope hiện tại) hoặc user tự tải thủ công nếu muốn nội dung "quy chế học vụ" riêng biệt.
3. **Bảng quy đổi tiếng Anh (D6_1)** trích xuất từ HTML dạng bảng bị "phẳng hóa" thành text tuần tự — chỉ dùng các cặp giá trị rõ ràng, không mơ hồ (IELTS↔Bậc, TOEFL iBT Home Edition) để tránh gán nhầm cột. Các câu về TOEIC 4 kỹ năng theo bậc B1 CHƯA được đưa vào vì rủi ro gán sai cột.
4. **q_005, q_027, q_042 (category `procedural`)** là câu suy luận (derive từ ngưỡng số trong văn bản, ví dụ "80 tín chỉ → năm 3") — không phải trích dẫn nguyên văn. Domain expert cần verify phép suy luận đúng.
5. **q_049 (`data_gap`)** không phải câu "ngoài phạm vi" thật sự — đây là câu ĐÚNG domain (học phí IUH theo ngành/năm cụ thể) nhưng nguồn hiện có chưa có số liệu chi tiết theo ngành. Refusal ở đây phản ánh giới hạn dữ liệu đã ingest, không phải giới hạn domain.
6. **⚠️ Sự cố mất dữ liệu xảy ra 2 LẦN, đã fix cả 2 lớp (2026-07-11):** `scripts/extract_text.py` từng ghi đè vô điều kiện file `.txt` đã OCR khi rerun để xử lý document mới (D13) — lần 1 xóa mất kết quả D8/D9, đã fix bằng cách preserve entry có `ocr_applied=True`. Nhưng fix lần 1 không đủ: **D3 (QĐ 610) cũng là nạn nhân của lần ghi đè ĐẦU TIÊN (trước khi fix) nhưng bị bỏ sót khi khôi phục** (chỉ để ý D8/D9 lúc đó) — phát hiện muộn hơn khi cố tra cứu thêm nội dung D3. Đã khôi phục D3 (65.4K/63.8K ký tự) và thêm **lớp bảo vệ thứ 2** trong `extract_text.py`: không bao giờ ghi đè file `.txt` có sẵn bằng bản trích xuất ít hơn hẳn (>2x, >500 ký tự), bất kể cờ `ocr_applied` có đồng bộ đúng hay không. Bài học: khi fix 1 bug data-loss, phải audit TOÀN BỘ dữ liệu liên quan, không chỉ phần vừa thao tác.
7. **`doc_faet_hoc_bong_2024` (D13) là bản mirror**, không phải trang gốc chính thức của Phòng Đào tạo (pdt.iuh.edu.vn/quy-che-xet-hoc-bong/ — SPA không crawl được). Nội dung khớp với tiêu đề "Quy định về việc cấp xét học bổng (Áp dụng từ khóa 2024)" niêm yết chính thức (đã kiểm chứng chéo qua nhiều nguồn tìm kiếm độc lập, nội dung nhất quán), nhưng **số quyết định (QĐ .../QĐ-ĐHCN) bị để trống trong chính bản gốc trên website IUH** (không phải lỗi crawl của chúng tôi — đã thử tìm số hiệu qua nhiều kênh, kể cả 1 PDF liên quan `HD-02-2024.pdf` nhưng không xác nhận được) — vẫn còn treo, cần domain expert xác nhận nếu cần trích dẫn số hiệu chính xác tuyệt đối.
8. **Search engine summary KHÔNG đáng tin để làm ground truth:** khi tra cứu mức học bổng A/B/C, kết quả tóm tắt từ search engine ban đầu cho ra 100%/70%/50%, nhưng khi tải và đọc trực tiếp trang nguồn (D13) thì số liệu thật là **130%/110%/100%** — sai lệch hoàn toàn. Bài học: mọi ground_truth trong golden set này đều lấy từ text đã tự tải/OCR, không bao giờ từ tóm tắt search engine.

## Việc còn lại (xem thêm `golden_set_stats.md`)

- [x] ~~Domain expert review từng câu~~ → **Đã approve qua AI self-review theo yêu cầu user (2026-07-11)**, xem audit trail đầu file. Vẫn khuyến nghị domain expert spot-check trước khi dùng chính thức.
- [x] Xác nhận phát hiện #1 (chất lượng cao vs tăng cường tiếng Anh) — đã giải quyết.
- [ ] Xác nhận số QĐ thật cho quy định học bổng (phát hiện #7) — vẫn treo, số hiệu bị thiếu ngay trên nguồn gốc.
- [ ] Bổ sung câu cho: học phí cụ thể theo ngành/năm (vẫn thiếu), thang điểm rèn luyện đầy đủ (Xuất sắc/Tốt/Khá/TB/Yếu/Kém theo khoảng điểm — chưa tìm thấy trong D9).
- [ ] Mở rộng lên 200 câu có đáp án / 30 refusal / 20 adversarial / 30 multi-hop / 20 ambiguous theo đúng cơ cấu 300 câu.
- [ ] Sau Phase 3 (chunking), thay `relevant_chunks: []` bằng chunk_id thật.
