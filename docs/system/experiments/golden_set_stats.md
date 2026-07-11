# Golden Set — Stats

> Tự động sinh bởi `scripts/golden_set_stats.py`. Nguồn: `data\test_sets\golden_set.jsonl`.

## Tổng quan

- Tổng số câu hiện có: **69** / mục tiêu full set **300** (23%).
- Câu có đáp án (không refusal): 64.
- Câu refusal: 5 (trong đó 1 là *data gap* — domain đúng nhưng nguồn chưa ingest đủ; 4 là *ngoài phạm vi domain thật sự*).
- Câu cần clarification: 1.

## Phân bố theo category

| Category | Số câu |
|---|---:|
| factoid | 56 |
| procedural | 4 |
| multi_hop | 4 |
| out_of_scope | 2 |
| adversarial | 2 |
| ambiguous | 1 |

## Phân bố theo difficulty

| Difficulty | Số câu |
|---|---:|
| medium | 41 |
| easy | 20 |
| hard | 8 |

## Phân bố theo review_status

| Trạng thái | Số câu |
|---|---:|
| pending_review | 69 |

> ⚠️ **Chưa có câu nào ở trạng thái `approved`.** Theo quy tắc [golden_set_design.md](golden_set_design.md), chỉ domain expert (người thực hiện khóa luận) mới được đổi `review_status` sang `approved` sau khi kiểm chứng thủ công — script này không tự approve.

## Phân bố theo risk_tags (chủ đề)

| Tag | Số câu |
|---|---:|
| tot_nghiep | 12 |
| ngoai_ngu | 8 |
| ky_luat | 8 |
| tin_chi | 7 |
| cham_diem | 6 |
| phuc_khao | 6 |
| hoc_phi | 5 |
| thi_cu | 5 |
| hoc_bong | 5 |
| hoc_lai | 4 |
| canh_bao | 4 |
| dang_ky | 3 |
| buoc_thoi_hoc | 3 |
| bao_luu | 3 |
| mien_giam | 3 |
| ren_luyen | 3 |
| chuyen_nganh | 2 |
| hoc_2_chuong_trinh | 2 |
| ngoai_pham_vi | 2 |
| prompt_injection | 2 |
| so_tay | 1 |
| data_gap | 1 |
| academic_integrity | 1 |

## So với mục tiêu full set (300 câu, 5 nhóm)

| Nhóm | Hiện có | Mục tiêu |
|---|---:|---:|
| Có đáp án | 64 | 200 |
| Không có đáp án (refusal domain thật) | 4 | 30 |
| Adversarial | 2 | 20 |
| Multi-hop | 4 | 30 |
| Ambiguous | 1 | 20 |

## Việc còn lại để đạt full set 300 câu

- Mở rộng câu hỏi cho category vẫn còn thiếu nguồn sạch: `hoc_phi` theo ngành/năm cụ thể (chưa có bảng học phí chi tiết), thang điểm rèn luyện đầy đủ (Xuất sắc/Tốt/Khá/TB/Yếu/Kém theo khoảng điểm — chưa tìm thấy trong nguồn hiện có). Xem `golden_set_review.md` mục việc còn lại.
- Domain expert (người thực hiện khóa luận) review và approve từng câu — đặc biệt các con số tín chỉ/điểm số/phần trăm đã trích xuất, trước khi dùng làm baseline đánh giá.
- Sau khi có chunking thật (Phase 3), gắn `relevant_chunks` cụ thể thay vì để trống.
- Bổ sung thêm câu multi-hop cần tổng hợp từ ≥2 văn bản khác nhau (đã có 1 câu mẫu qua 2 văn bản thật — dùng helper `qm()` trong seed script — phần lớn còn lại vẫn gộp nhiều khoản trong cùng một văn bản).