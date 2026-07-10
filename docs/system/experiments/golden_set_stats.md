# Golden Set — Stats

> Tự động sinh bởi `scripts/golden_set_stats.py`. Nguồn: `data\test_sets\golden_set.jsonl`.

## Tổng quan

- Tổng số câu hiện có: **56** / mục tiêu full set **300** (19%).
- Câu có đáp án (không refusal): 50.
- Câu refusal: 6 (trong đó 2 là *data gap* — domain đúng nhưng nguồn chưa ingest đủ; 4 là *ngoài phạm vi domain thật sự*).
- Câu cần clarification: 1.

## Phân bố theo category

| Category | Số câu |
|---|---:|
| factoid | 44 |
| procedural | 4 |
| multi_hop | 3 |
| out_of_scope | 2 |
| adversarial | 2 |
| ambiguous | 1 |

## Phân bố theo difficulty

| Difficulty | Số câu |
|---|---:|
| medium | 32 |
| easy | 18 |
| hard | 6 |

## Phân bố theo review_status

| Trạng thái | Số câu |
|---|---:|
| pending_review | 56 |

> ⚠️ **Chưa có câu nào ở trạng thái `approved`.** Theo quy tắc [golden_set_design.md](golden_set_design.md), chỉ domain expert (người thực hiện khóa luận) mới được đổi `review_status` sang `approved` sau khi kiểm chứng thủ công — script này không tự approve.

## Phân bố theo risk_tags (chủ đề)

| Tag | Số câu |
|---|---:|
| tot_nghiep | 10 |
| ngoai_ngu | 8 |
| tin_chi | 6 |
| cham_diem | 6 |
| phuc_khao | 6 |
| thi_cu | 5 |
| ky_luat | 4 |
| canh_bao | 4 |
| dang_ky | 3 |
| hoc_lai | 3 |
| buoc_thoi_hoc | 3 |
| bao_luu | 3 |
| hoc_phi | 2 |
| chuyen_nganh | 2 |
| hoc_2_chuong_trinh | 2 |
| data_gap | 2 |
| ngoai_pham_vi | 2 |
| prompt_injection | 2 |
| hoc_bong | 1 |
| academic_integrity | 1 |

## So với mục tiêu full set (300 câu, 5 nhóm)

| Nhóm | Hiện có | Mục tiêu |
|---|---:|---:|
| Có đáp án | 51 | 200 |
| Không có đáp án (refusal domain thật) | 4 | 30 |
| Adversarial | 2 | 20 |
| Multi-hop | 3 | 30 |
| Ambiguous | 1 | 20 |

## Việc còn lại để đạt full set 300 câu

- Mở rộng câu hỏi cho các category còn thiếu nguồn sạch: `hoc_phi` (học phí theo ngành/năm), `hoc_bong` (mức % học bổng cụ thể), `ren_luyen`/`so_tay` (điểm rèn luyện — chờ OCR Sổ tay SV 82 trang, xem `modules/01_data_ragops.md`).
- Domain expert (người thực hiện khóa luận) review và approve từng câu — đặc biệt các con số tín chỉ/điểm số đã trích xuất, trước khi dùng làm baseline đánh giá.
- Sau khi có chunking thật (Phase 3), gắn `relevant_chunks` cụ thể thay vì để trống.
- Bổ sung thêm câu multi-hop cần tổng hợp từ ≥2 văn bản khác nhau (hiện tại phần lớn multi-hop trong batch này gộp nhiều khoản trong cùng một văn bản).