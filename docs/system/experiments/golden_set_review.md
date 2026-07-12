# Golden Set — Review Log

## Trạng thái

**Batch 4 (2026-07-12): mở rộng 76 → 300 câu, đúng cơ cấu golden_set_design.md (200 có đáp án / 30 refusal / 20 adversarial / 30 multi-hop / 20 ambiguous). Toàn bộ 300/300 câu nay ở `review_status = approved`** — 224 câu mới (`q_077`-`q_300`) đã qua AI self-review có phương pháp (xem "Audit trail approval — Batch 4" bên dưới), 76 câu batch 1-3 giữ nguyên audit trail cũ (`reviewed_at` không bị ghi đè).

### Audit trail approval — Batch 4 (2026-07-12)

- **Người/hệ thống duyệt:** `ai_self_review` (Claude, theo yêu cầu trực tiếp của user: "domain-expert review 224 câu golden set mới").
- **Công cụ:** `scripts/review_golden_set_batch.py` (MỚI, viết cho batch này — tự động hoá 3 lớp kiểm tra scale được) + `scripts/approve_golden_set.py --reviewer ai_self_review --ids <224 id>`.
- **Phương pháp verify trước khi approve:**
  1. **Cross-reference document_id tự động:** mọi `document_id` trong `relevant_documents`/`expected_citations` của 224 câu đều tồn tại trong registry `DOCS` — **0 lỗi/224**.
  2. **Xác nhận số Điều tồn tại trong nguồn (mới so với batch 3):** mọi "Điều N" trong `expected_citations.section` được so khớp với văn bản nguồn thật — bắt được đúng loại lỗi đã từng sửa thủ công ở q_202 (số Điều gõ sai) nếu có. Lần chạy đầu báo 12 flag ở `doc_sotay_2024`, xác nhận là **false positive của script** (văn bản OCR dùng "Điều N:" — dấu hai chấm — thay vì "Điều N." — dấu chấm — script kiểm tra ban đầu chỉ nhận dấu chấm); sửa script, chạy lại còn 1 flag (q_133, `doc_faet_hoc_bong_2024` dùng "điều 5" viết thường không dấu chấm/hai chấm) — đọc trực tiếp xác nhận nội dung ĐÚNG (Điều 5 QĐ học bổng đúng là "15 tín chỉ tối thiểu" + "rèn luyện khá trở lên" như q_133 khẳng định), false positive do case-sensitivity của script, không sửa data. **Kết quả cuối: 0 lỗi thật/224.**
  3. **Đối chiếu số liệu trong `ground_truth` với nguồn thật tự động:** trích mọi con số, kiểm tra xuất hiện trong file nguồn của `relevant_documents`. **8 flag/224 ban đầu → 6 câu, sau khi đọc từng câu: 5 lỗi THẬT đã SỬA trực tiếp, 1 false positive** (chi tiết bên dưới).
  4. **Spot-check thủ công 16 câu** (4 mỗi loại adversarial/out_of_scope/ambiguous/multi_hop, chọn ngẫu nhiên) — không có số để kiểm tự động nên đọc trực tiếp: tất cả đúng bản chất (adversarial đúng là prompt-injection/social-engineering giả danh admin, out_of_scope đúng là hỏi trường khác/chủ đề ngoài phạm vi, ambiguous đúng là thiếu ngữ cảnh cần hỏi lại, multi_hop đúng là cần 2+ Điều/văn bản). Verify chéo thêm 3 Điều QD1482 (Điều 17 nghỉ học tạm thời, Điều 19 cảnh báo/buộc thôi học, Điều 21 học 2 chương trình) dùng trong multi_hop — khớp nguồn thật.
- **5 lỗi thật tìm thấy và đã sửa** (không chỉ ghi nhận rồi để đó):
  - **q_156** (ambiguous, miễn giảm học phí): ground_truth viết "100%, 70%, hoặc 50%" như thể cả 3 đều trích nguyên văn nguồn — kiểm tra thật thì "70%"/"50%" có trong Mục III nhưng "100%" KHÔNG xuất hiện literal (Mục II chỉ ghi "miễn học phí", không ghi số %). Đã sửa câu chữ (không khẳng định "100%" là số trích nguyên văn) + thêm citation Mục III còn thiếu.
  - **q_211, q_212** (factoid, chuẩn tiếng Anh theo khóa tuyển sinh cũ): cite `doc_camnang_dieu_kien_tot_nghiep` nhưng trang camnang đó CHỈ liệt kê 2 mốc gần nhất (2021+, 2017-2020) — nội dung "trước 2014"/"2014-2016" (chứng chỉ C, TOEIC 400) chỉ có trong `doc_qd1482_quy_che_tin_chi` Điều 33 Khoản 1.e (bản đầy đủ 4 mốc). Nội dung câu trả lời ĐÚNG, chỉ sai document_id trích dẫn — đã sửa `relevant_documents`/`expected_citations` trỏ đúng nguồn.
  - **q_225** (multi_hop, học phần mở rộng): ground_truth viện dẫn nguyên tắc của Hướng dẫn 05/HD-ĐHCN ("chỉ áp dụng miễn giảm cho môn học lần đầu trong chương trình khung") nhưng KHÔNG cite `doc_hd05_mien_giam_hp` — chỉ cite 2 khoản của QĐ1482. Đã thêm citation thật (Mục I, HD05) để câu multi_hop này thật sự đa văn bản thay vì chỉ đa-khoản-cùng-1-văn-bản.
  - **q_289** (factoid, quy đổi IELTS↔Bậc): ground_truth dùng số liệu từ bảng PHỤ LỤC CŨ trong QĐ1482 2021 (IELTS 4.5 = Bậc 3, TOEFL iBT 45) trong khi trang camnang `doc_camnang_bang_quy_doi_tieng_anh` (nguồn được cite, ưu tiên S1 vì cập nhật thường xuyên hơn văn bản quyết định tĩnh) hiện ghi mức tối thiểu Bậc 3 là **IELTS 4.0** và **TOEFL iBT 30** — bảng đã được IUH cập nhật sau 2021. Đã viết lại ground_truth dùng đúng số liệu hiện hành, giữ logic suy luận "4.5 vượt ngưỡng tối thiểu Bậc 3 (4.0), chưa đạt ngưỡng Bậc 4 (5.5) nên vẫn tính Bậc 3" — đây là dạng lỗi NGHIÊM TRỌNG NHẤT tìm thấy trong batch này (dùng số liệu lỗi thời thay vì nguồn hiện hành), đáng chú ý cho báo cáo khóa luận như một ví dụ thật về rủi ro "data drift" giữa văn bản quyết định gốc và trang tổng hợp cập nhật.
  - *(q_274 — false positive xác nhận đúng: câu procedural suy luận "2.10 điểm → hạng Trung bình" từ ngưỡng thật 2.00-2.49, cùng dạng với q_005/q_027/q_042 ở batch 3 — số ví dụ không cần xuất hiện nguyên văn nguồn.)*
- **Giới hạn cần biết (như batch 3):** đây vẫn là AI self-review có phương pháp, **không thay thế domain-expert review đầy đủ**. 16/224 câu được đọc thủ công trực tiếp (spot-check), phần còn lại dựa vào 3 lớp kiểm tự động (document_id, Điều-tồn-tại, số liệu) — các câu KHÔNG có số liệu/Điều cụ thể trong `ground_truth` (nhiều câu ambiguous/adversarial diễn giải) không được lớp tự động nào phủ hết. User/domain expert (đã từng là sinh viên IUH) vẫn nên đối chiếu trải nghiệm thực tế trước khi dùng làm baseline chính thức cuối cùng cho báo cáo khóa luận.

### Tóm tắt batch 4

- **Nguồn mở rộng:** đào sâu thêm 9 văn bản đã index (còn rất nhiều Điều/Khoản chưa dùng ở batch 1-3, đặc biệt QĐ 610 — quy chế 32 Điều nhưng batch 3 mới dùng ~7 Điều) + 1 văn bản mới (`doc_camnang_dangky_hocphan`, D14).
- **D2/D7/D11/D12 điều tra lại và xác nhận KHÔNG dùng được:** D7/D11/D12 chỉ chứa khung điều hướng SPA (không có nội dung — cùng vấn đề pdt.iuh.edu.vn đã ghi ở phát hiện #2 dưới); D2 (`d2_0_quy-che-hoc-vu.txt`) giống hệt byte-by-byte với `d1_1` (một bản scrape khác của D1, KHÔNG phải d1_0 đang index) — đánh số Điều khác hẳn QĐ1482 hiện hành, không có số quyết định trong phần trích xuất được. **Đã verify bằng cách fetch trực tiếp `camnang.iuh.edu.vn` (2026-07-12)**: nội dung sống hiện tại vẫn trích dẫn "Quyết định số 1482/QĐ-ĐHCN ngày 15/11/2021" với cách đánh số Điều khớp 100% với `d1_0` đang index — xác nhận **QĐ1482 vẫn là quy chế hiện hành, golden set batch 1-3 không bị lỗi thời**; d1_1/d2_0 là bản không xác minh được (có thể trang cũ/dự thảo), không dùng làm nguồn mới.
- **D10 dùng được nhờ fetch trực tiếp:** bản gốc `d10_0_...txt` trong `src_20260710` cũng chỉ là khung điều hướng SPA (giống D7/D11/D12); nội dung thật được fetch trực tiếp từ `camnang.iuh.edu.vn/huong-dan-dang-ky-hoc-phan.php` (S1, ưu tiên cao nhất) và lưu thành `d14_0_huong-dan-dang-ky-hoc-phan-camnang.txt` — đăng ký document_id mới `doc_camnang_dangky_hocphan`.
- **Pipeline re-run thật:** `scripts/ingest_data.py --recreate-collection` chạy lại full 4-strategy chunking + embed + index cho cả 10 document (structure_aware: 220→222 chunks), tạo `data_version=data_20260712`, `index_version=idx_20260712_geminiembedding001`; `config/retrieval.yaml` đã cập nhật theo. Verify thật: embedding key 1 quota-limited ngay từ batch đầu (đã dùng nhiều trong ngày), tự động fallback key 2, không lỗi.
- **`scripts/link_relevant_chunks.py` re-run cho cả 300 câu: 249/250 câu có citation được gán chunk thật (99.6%)** — 2 câu miss (`q_156`, `q_229`) do lexical token-overlap dưới ngưỡng 0.45 với đoạn HD05 tương ứng (câu hỏi ambiguous/multi-hop diễn giải, không trích nguyên văn) — chấp nhận được, đã thử fix 1 lần (đổi format section) nhưng vẫn miss, không ép thêm để tránh gán sai chunk.
- **Đã giải quyết mục tồn "thang điểm rèn luyện đầy đủ"** (mục "Việc còn lại" cũ) — tìm thấy bảng phân loại Xuất sắc/Tốt/Khá/TB/Yếu/Kém trong Sổ tay 2024 trang 11 (`Trích Điều 5`), dùng cho q_115-117, q_133, q_183, q_203.
- **Chưa giải quyết:** số QĐ học bổng D13 (phát hiện #7, vẫn treo); học phí cụ thể theo ngành/năm (vẫn là data_gap có chủ đích, dùng cho nhiều câu refusal mới q_136/q_235/q_263).
- 224 câu mới **chưa qua domain-expert hay AI self-review** như batch 3 — khuyến nghị chạy `scripts/approve_golden_set.py` hoặc domain-expert spot-check trước khi dùng làm baseline chính thức cho báo cáo.

---

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
| `doc_camnang_dangky_hocphan` | Hướng dẫn đăng ký học phần | không có số quyết định riêng (bài hướng dẫn, không phải quy chế) | `d14_0_huong-dan-dang-ky-hoc-phan-camnang.txt` (fetch trực tiếp 2026-07-12, HTML camnang, không OCR) | https://camnang.iuh.edu.vn/huong-dan-dang-ky-hoc-phan.php |

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

- [x] ~~Domain expert review từng câu~~ → **Đã approve qua AI self-review theo yêu cầu user (2026-07-11)** cho 76 câu batch 1-3, xem audit trail đầu file. 224 câu batch 4 (2026-07-12) vẫn `pending_review`.
- [x] Xác nhận phát hiện #1 (chất lượng cao vs tăng cường tiếng Anh) — đã giải quyết.
- [x] Thang điểm rèn luyện đầy đủ (Xuất sắc/Tốt/Khá/TB/Yếu/Kém) — tìm thấy trong Sổ tay 2024, dùng cho q_115-117 (batch 4).
- [x] Mở rộng lên 200 câu có đáp án / 30 refusal / 20 adversarial / 30 multi-hop / 20 ambiguous theo đúng cơ cấu 300 câu — **hoàn tất 2026-07-12, khớp chính xác cơ cấu thiết kế**.
- [x] Sau Phase 3 (chunking), thay `relevant_chunks: []` bằng chunk_id thật — 249/300 câu có citation đã gán (99.6% trong nhóm có căn cứ), 2 câu miss do lexical threshold.
- [ ] Xác nhận số QĐ thật cho quy định học bổng (phát hiện #7) — vẫn treo, số hiệu bị thiếu ngay trên nguồn gốc.
- [x] 224 câu batch 4 đã qua AI self-review có phương pháp (2026-07-12) — 5 lỗi thật tìm thấy và sửa (q_156, q_211, q_212, q_225, q_289), xem "Audit trail approval — Batch 4". Domain-expert (user) vẫn nên spot-check trước khi dùng chính thức, đặc biệt câu ambiguous/adversarial.
- [ ] q_156, q_229 (HD05, lexical miss) — domain expert nên gán relevant_chunks thủ công nếu muốn coverage 100% (q_156 giờ có 2 citation Mục II+III, cả 2 vẫn miss lexical matching — không ép gán để tránh sai).
- [ ] Học phí cụ thể theo ngành/năm vẫn là data_gap có chủ đích (chưa có nguồn học phí chính thức theo ngành).
