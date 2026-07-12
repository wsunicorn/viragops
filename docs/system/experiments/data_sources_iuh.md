# Nguồn dữ liệu domain — Quy chế đào tạo + FAQ sinh viên IUH

> **Domain đã chốt:** Quy chế đào tạo đại học + Sổ tay/FAQ sinh viên của **Trường Đại học Công nghiệp Thành phố Hồ Chí Minh (IUH)**.
> File này là "single source" cho việc thu thập, phiên bản hóa và ánh xạ dữ liệu nguồn IUH vào golden set. Đọc cùng [golden_set_design.md](golden_set_design.md) và [../modules/01_data_ragops.md](../modules/01_data_ragops.md).

## 1. Phạm vi dữ liệu

**Trong phạm vi:** văn bản chính thức do IUH ban hành liên quan đào tạo đại học chính quy và đời sống học vụ sinh viên: quy chế đào tạo tín chỉ, quy chế học vụ, quy chế thi/đánh giá, điểm rèn luyện, học bổng, học phí/miễn giảm, điều kiện tốt nghiệp, chuẩn tiếng Anh, đăng ký học phần, quy trình – biểu mẫu học vụ, sổ tay/cẩm nang người học.

**Ngoài phạm vi (giai đoạn đầu):** đào tạo sau đại học (thạc sĩ/tiến sĩ), đào tạo quốc tế/liên kết, tuyển sinh, nội dung marketing/tin tức sự kiện. Có thể thêm sau nếu cần domain phụ.

> **Lưu ý quan trọng:** Nhiều quy chế IUH là bản triển khai của văn bản Bộ GD&ĐT (ví dụ Thông tư 08/2021/TT-BGDĐT về đào tạo trình độ đại học theo tín chỉ; quy chế công tác sinh viên). **Golden set và citation phải trỏ về văn bản do IUH ban hành** (số quyết định IUH), không trỏ thẳng vào thông tư gốc, để giữ tính nhất quán của domain và đo Citation Accuracy đúng.

## 2. Bản đồ website nguồn IUH

| # | Site | Đơn vị / vai trò | Nội dung chính | Format | Ưu tiên |
|---|---|---|---|---|---|
| S1 | [camnang.iuh.edu.vn](https://camnang.iuh.edu.vn/) | Cẩm nang người học | Quy chế tín chỉ, điều kiện tốt nghiệp, chuẩn/quy đổi tiếng Anh, hướng dẫn cổng SV & LMS, hoạt động phong trào, cơ sở & phân hiệu | **HTML sạch, có cấu trúc** | **Cao nhất** |
| S2 | [pdt.iuh.edu.vn](https://pdt.iuh.edu.vn/) | Phòng Đào tạo | Quy chế đào tạo tín chỉ, quy chế học vụ, quy định xét học bổng, hướng dẫn đăng ký học phần, quy trình + biểu mẫu học vụ | HTML + PDF | **Cao** |
| S3 | [ctsv.iuh.edu.vn](https://ctsv.iuh.edu.vn/) | Phòng Công tác chính trị & Hỗ trợ SV | Sổ tay sinh viên, quy chế công tác sinh viên, điểm rèn luyện, chính sách miễn/giảm học phí & hỗ trợ | HTML + PDF | **Cao** |
| S4 | [tqa.iuh.edu.vn](https://tqa.iuh.edu.vn/) | Phòng Khảo thí & ĐBCL | Quy chế quản lý công tác thi & đánh giá kết quả học tập, quy định phúc khảo | HTML + PDF | **Cao** |
| S5 | [stsv.iuh.edu.vn](https://stsv.iuh.edu.vn/) | Sổ tay sinh viên điện tử | Sổ tay sinh viên bản điện tử (tổng hợp) | HTML/web app | Trung bình |
| S6 | [iuh.edu.vn](https://iuh.edu.vn/) | Cổng chính | Thông báo chính sách, giới thiệu đơn vị, văn bản mới | HTML | Trung bình |
| S7 | [ipe.iuh.edu.vn](https://ipe.iuh.edu.vn/vi/van-ban-tien-ich/qui-che-quy-dinh/) | Viện Đào tạo QT & sau ĐH | Quy chế/quy định, mẫu đơn học vụ (một phần dùng chung) | PDF | Thấp (đa phần ngoài scope) |
| S8 | Site khoa: [faet.iuh.edu.vn](https://faet.iuh.edu.vn/), [ce.iuh.edu.vn](https://ce.iuh.edu.vn/) | Các khoa | Bản sao/tóm tắt quy chế, học bổng, "quy định quan trọng cho SV" | HTML | Thấp (đối chiếu) |

## 3. Danh mục văn bản cần thu thập (ưu tiên)

| ID | Văn bản / trang nguồn | Site | Nhóm chủ đề | Ghi chú thu thập |
|---|---|---|---|---|
| D1 | Quy chế đào tạo theo hệ thống tín chỉ | S1 [link](https://camnang.iuh.edu.vn/quy-che-dao-tao-theo-he-thong-tin-chi.php), S2 [link](https://pdt.iuh.edu.vn/quy-che-dao-tao) | tín chỉ, học phần, đăng ký, học lại | Lấy bản HTML camnang trước (sạch), đối chiếu bản pdt |
| D2 | Quy chế học vụ | S2 [link](https://pdt.iuh.edu.vn/quy-che-hoc-vu/) | học vụ, cảnh báo, buộc thôi học, bảo lưu | Kiểm tra HTML vs PDF đính kèm |
| D3 | Quy chế quản lý công tác thi & đánh giá KQHT 2025 (QĐ 610/QĐ-ĐHCN) | S4 [link](https://tqa.iuh.edu.vn/quy-che-quan-ly-cong-tac-thi/) | thi cử, chấm điểm, đánh giá học phần | Tải PDF quyết định; ghi số hiệu + năm |
| D4 | Quy định phúc khảo | S4 [link](https://tqa.iuh.edu.vn/cong-tac-khao-thi/quy-dinh-phuc-khao/) | phúc khảo, khiếu nại điểm | Quy trình + thời hạn |
| D5 | Điều kiện xét tốt nghiệp | S1 [link](https://camnang.iuh.edu.vn/dieu-kien-xet-tot-nghiep.php) | tốt nghiệp, tín chỉ tích lũy | HTML sạch |
| D6 | Quy định chuẩn tiếng Anh + bảng quy đổi | S1 [link](https://camnang.iuh.edu.vn/quy-dinh-chuan-tieng-anh.php), [quy đổi](https://camnang.iuh.edu.vn/bang-quy-doi-diem-chung-chi-tieng-anh.php) | chuẩn đầu ra, ngoại ngữ | Có bảng → dùng table-aware chunking |
| D7 | Quy định xét, cấp học bổng khuyến khích học tập | S2 [link](https://pdt.iuh.edu.vn/quy-che-xet-hoc-bong/) | học bổng loại A/B/C, điều kiện GPA/rèn luyện | Đối chiếu bản khoa (S8) |
| D8 | Chính sách miễn/giảm học phí & hỗ trợ chi phí học tập | S3 [link](https://ctsv.iuh.edu.vn/), S6 | học phí, miễn giảm, đối tượng chính sách | Ghi rõ năm học + nghị định tham chiếu |
| D9 | Quy chế công tác sinh viên + đánh giá điểm rèn luyện + kỷ luật | S3 | rèn luyện, khen thưởng, kỷ luật | Thang điểm rèn luyện, 4 mức kỷ luật |
| D10 | Hướng dẫn đăng ký học phần | S2 [link](https://pdt.iuh.edu.vn/thong-bao/huong-dan-dang-ky-hoc-phan/) | đăng ký môn, rút môn, thời khóa biểu | Hướng dẫn thao tác cổng SV |
| D11 | Quy trình giải quyết học vụ + biểu mẫu sinh viên | S2 [link](https://pdt.iuh.edu.vn/van-ban-tien-ich/bieu-mau-sinh-vien/) | đơn từ, quy trình, bảo lưu, chuyển ngành | Nhiều biểu mẫu PDF |
| D12 | Sổ tay sinh viên / Cẩm nang (tổng hợp) | S1, S3 [link](https://ctsv.iuh.edu.vn/news.html@detail@150@592@So-tay-sinh-vien), S5 | tổng hợp đời sống học vụ, FAQ | Nguồn sinh nhiều câu hỏi FAQ |

## 4. Chiến lược crawl & ingest

1. **Ưu tiên HTML có cấu trúc (S1 camnang)**: parse trực tiếp theo section/heading → không cần OCR, citation theo mục rõ ràng. Đây là bộ tài liệu nền để chạy pipeline sớm (Phase 3).
2. **PDF text (S2, S3, S4)**: tải PDF quyết định/quy chế; ưu tiên PDF có text layer. Trích theo Điều/Khoản/Điểm bằng structure-aware chunking.
3. **PDF scan (nếu có)**: đưa qua OCR (`ocr_processor` trong Module 1), sau đó normalization tiếng Việt; đánh dấu `ocr=true` trong metadata để theo dõi OCR noise score.
4. **Bảng biểu (D6 quy đổi điểm, biểu học phí)**: dùng table-aware chunking; giữ nguyên cấu trúc hàng/cột để tránh mất ngữ nghĩa.
5. **Chống trùng lặp giữa các site**: cùng một quy chế có thể xuất hiện ở camnang + pdt + site khoa. Chọn **một bản canonical** cho mỗi văn bản (ưu tiên site chủ quản: đào tạo→S2, thi→S4, CTSV→S3, tổng hợp→S1), gắn `is_canonical=true`; các bản còn lại chỉ dùng đối chiếu, không index trùng.

## 5. Metadata & phiên bản hóa nguồn

Mỗi tài liệu nguồn (theo [../contracts/data_schemas.md](../contracts/data_schemas.md)) phải ghi:

- `document_id`, `title`, `source_uri` (URL/đường dẫn file), `source_type` (html/pdf/pdf_scan);
- `source_version` (snapshot ngày tải, ví dụ `src_20260710`), `retrieved_at`, `effective_date` (ngày hiệu lực văn bản), `issuing_unit` (S1–S8), `official_number` (số QĐ/TT nếu có);
- `is_canonical`, `ocr` (true/false), `domain = university_regulation_iuh`.

**Snapshot & tái lập:** vì quy chế IUH thay đổi theo năm học, mỗi lần thu thập tạo một snapshot bất biến trong MinIO/S3 và commit manifest qua DVC. Golden set gắn với `source_version` cụ thể để kết quả thực nghiệm tái lập được.

## 6. Ánh xạ category golden set ↔ nguồn IUH

Cập nhật danh mục category trong [golden_set_design.md](golden_set_design.md) theo dữ liệu IUH thực tế:

| Category golden set | Văn bản nguồn chính | Loại câu hỏi tiêu biểu |
|---|---|---|
| Tín chỉ & học phần | D1 | "Một học phần có tối đa bao nhiêu tín chỉ?" |
| Điều kiện tốt nghiệp | D5, D1 | "Cần tích lũy bao nhiêu tín chỉ để xét tốt nghiệp?" |
| Đăng ký môn học | D10, D1 | "Thời gian rút học phần không bị điểm F là khi nào?" |
| Học lại / cải thiện | D1, D2 | "Điểm F có được đăng ký học cải thiện không?" |
| Cảnh báo học vụ / buộc thôi học | D2 | "Bị cảnh báo học vụ mấy lần thì buộc thôi học?" |
| Thi & đánh giá học phần | D3 | "Điểm tổng kết học phần được tính theo trọng số nào?" |
| Phúc khảo | D4 | "Thời hạn nộp đơn phúc khảo là bao nhiêu ngày?" |
| Điểm rèn luyện & kỷ luật | D9 | "Bị kỷ luật cảnh cáo thì rèn luyện tối đa loại gì?" |
| Học bổng | D7 | "Điều kiện GPA để xét học bổng loại A?" |
| Học phí & miễn giảm | D8 | "Đối tượng nào được miễn 100% học phí?" |
| Chuẩn tiếng Anh | D6 | "IELTS 5.0 quy đổi tương đương chứng chỉ nội bộ nào?" |
| Bảo lưu / chuyển ngành | D11, D2 | "Thủ tục bảo lưu kết quả học tập gồm những bước nào?" |
| Câu hỏi ngoài phạm vi (refusal) | — | Câu hỏi không có trong bất kỳ văn bản IUH nào |

## 7. Rủi ro & xử lý

| Rủi ro | Mức | Xử lý |
|---|---|---|
| Văn bản trùng nhiều bản/nhiều năm | Cao | Chọn bản canonical + `effective_date` mới nhất; ghi rõ năm áp dụng |
| PDF scan chất lượng kém | Trung bình | OCR + normalization; ưu tiên bản HTML camnang trước |
| Quy chế cập nhật giữa kỳ khóa luận | Trung bình | Cố định 1 snapshot cho toàn bộ thực nghiệm; ghi ngày freeze |
| Bản quyền / điều khoản sử dụng | Thấp-TB | Tài liệu công khai, dùng cho nghiên cứu học thuật; ghi nguồn + ngày truy cập; không phát tán lại bản gốc ngoài demo |
| Trộn nhầm văn bản Bộ GD&ĐT với văn bản IUH | Trung bình | Citation chỉ trỏ văn bản IUH; ghi tham chiếu thông tư gốc ở metadata, không ở citation |
| Nội dung site khoa lỗi thời | Thấp | Chỉ dùng đối chiếu, không index làm canonical |
| **pdt.iuh.edu.vn là SPA (React/Vue)** — xác nhận 2026-07-11: mọi URL con (`/quy-che-hoc-vu/`, `/quy-che-dao-tao`, `/danh-sach/*`...) trả về cùng một "app shell" HTML ~482KB qua HTTP GET tĩnh, không chứa nội dung bài viết thật (client-side render). Đây là lý do D1/D2 từng bị ghi nhận trùng nội dung. | Cao (chặn crawl tự động cho toàn bộ pdt.iuh.edu.vn) | Không dùng httpx GET tĩnh cho pdt.iuh.edu.vn sub-page. Phương án: (a) headless browser (Playwright) — chưa triển khai, ngoài scope hiện tại; (b) dùng bản mirror server-rendered ở site khoa (faet.iuh.edu.vn, ce.iuh.edu.vn...) làm nguồn thay thế khi có — đã áp dụng cho D13 (học bổng); (c) tài liệu quyết định gốc dạng PDF vẫn tải được bình thường qua link trực tiếp (không qua SPA routing). |
| **Xác nhận lại 2026-07-12 (mở rộng golden set 76→300):** D2 (`d2_0_quy-che-hoc-vu.txt` trong `src_20260710`) giống hệt byte-by-byte `d1_1` — không phải app-shell rỗng mà là nội dung quy chế THẬT nhưng đánh số Điều khác `d1_0` đang index, không xác minh được số quyết định trong phần trích xuất. D7 (`d7_0_...txt`), D11 (`d11_0/1_...txt`), D12 (`d12_0_...txt`) xác nhận **rỗng/chỉ có khung điều hướng** (D12 thậm chí 0 byte). `curl -k` trực tiếp vào pdt.iuh.edu.vn cũng nhận HTTP 403 (trang chặn bot/WAF), không phải app-shell như mô tả ban đầu — tức pdt.iuh.edu.vn hiện CHẶN CẢ request tĩnh, không chỉ render client-side. | Cao (D2/D7/D11/D12 không dùng được cho golden set batch 4) | Verify riêng bằng fetch trực tiếp `camnang.iuh.edu.vn` (WebFetch/curl, không bị chặn) xác nhận QĐ1482 vẫn là quy chế đào tạo hiện hành (khớp `d1_0`) — D2 không dùng làm nguồn mới để tránh trộn lẫn 2 phiên bản. D10 (đăng ký học phần) cũng gặp vấn đề tương tự nhưng **giải quyết được**: fetch trực tiếp `camnang.iuh.edu.vn/huong-dan-dang-ky-hoc-phan.php` (S1, không bị chặn) → lưu thành D14 (`doc_camnang_dangky_hocphan`), đã ingest. D7/D11/D12 vẫn treo, cần Playwright hoặc liên hệ trực tiếp Phòng Đào tạo. |

## 8. Checklist thu thập (bổ sung cho Phase 2)

- [ ] Tải & lưu snapshot D1–D12 vào MinIO `raw/iuh/<source_version>/`.
- [ ] Ghi metadata nguồn đầy đủ cho mỗi document (mục 5).
- [ ] Xác định bản canonical cho mỗi văn bản trùng.
- [ ] Đánh dấu tài liệu cần OCR.
- [ ] Chuẩn hóa danh mục category golden set theo mục 6.
- [ ] Chốt `source_version` freeze cho toàn bộ thực nghiệm.
- [ ] Ghi bảng "văn bản → số hiệu → năm hiệu lực → URL" vào `golden_set_review.md`.

> **Nguồn tham khảo (đã tra ngày 2026-07-10):** [camnang.iuh.edu.vn](https://camnang.iuh.edu.vn/), [pdt.iuh.edu.vn/quy-che-dao-tao](https://pdt.iuh.edu.vn/quy-che-dao-tao), [pdt.iuh.edu.vn/quy-che-hoc-vu](https://pdt.iuh.edu.vn/quy-che-hoc-vu/), [pdt.iuh.edu.vn/quy-che-xet-hoc-bong](https://pdt.iuh.edu.vn/quy-che-xet-hoc-bong/), [ctsv.iuh.edu.vn](https://ctsv.iuh.edu.vn/), [tqa.iuh.edu.vn/quy-che-quan-ly-cong-tac-thi](https://tqa.iuh.edu.vn/quy-che-quan-ly-cong-tac-thi/), [tqa.iuh.edu.vn/cong-tac-khao-thi/quy-dinh-phuc-khao](https://tqa.iuh.edu.vn/cong-tac-khao-thi/quy-dinh-phuc-khao/), [stsv.iuh.edu.vn](https://stsv.iuh.edu.vn/), [iuh.edu.vn](https://iuh.edu.vn/). Cần kiểm tra lại link còn sống và tải bản chính thức trước khi ingest.
