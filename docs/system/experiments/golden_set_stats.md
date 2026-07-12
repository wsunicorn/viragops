# Golden Set — Stats

> Tự động sinh bởi `scripts/golden_set_stats.py`. Nguồn: `data\test_sets\golden_set.jsonl`.

## Tổng quan

- Tổng số câu hiện có: **300** / mục tiêu full set **300** (100%).
- Câu có đáp án (không refusal): 250.
- Câu refusal: 50 (trong đó 30 là *data gap* — domain đúng nhưng nguồn chưa ingest đủ; 20 là *ngoài phạm vi domain thật sự*).
- Câu cần clarification: 20.

## Phân bố theo category

| Category | Số câu |
|---|---:|
| factoid | 218 |
| multi_hop | 30 |
| ambiguous | 20 |
| procedural | 12 |
| adversarial | 11 |
| out_of_scope | 9 |

## Phân bố theo difficulty

| Difficulty | Số câu |
|---|---:|
| medium | 167 |
| hard | 69 |
| easy | 64 |

## Phân bố theo review_status

| Trạng thái | Số câu |
|---|---:|
| pending_review | 224 |
| approved | 76 |

## Phân bố theo risk_tags (chủ đề)

| Tag | Số câu |
|---|---:|
| thi_cu | 74 |
| data_gap | 30 |
| hoc_phi | 27 |
| tot_nghiep | 26 |
| cham_diem | 25 |
| ngoai_ngu | 17 |
| ky_luat | 17 |
| phuc_khao | 16 |
| hoc_bong | 16 |
| mien_giam | 15 |
| tin_chi | 14 |
| dang_ky | 11 |
| prompt_injection | 11 |
| ren_luyen | 9 |
| ngoai_pham_vi | 9 |
| thi_truc_tuyen | 9 |
| canh_bao | 8 |
| buoc_thoi_hoc | 8 |
| chuyen_nganh | 8 |
| hoc_lai | 7 |
| bao_luu | 7 |
| so_tay | 6 |
| hoc_2_chuong_trinh | 6 |
| academic_integrity | 5 |
| chuyen_doi_tin_chi | 4 |
| lien_thong | 3 |
| gia_han | 2 |
| ho_tro_sv | 2 |
| dao_tao_truc_tuyen | 1 |
| thoi_hoc | 1 |
| khen_thuong | 1 |

## So với mục tiêu full set (300 câu, 5 nhóm)

| Nhóm | Hiện có | Mục tiêu |
|---|---:|---:|
| Có đáp án | 200 | 200 |
| Không có đáp án (data gap, refusal trong domain) | 30 | 30 |
| Adversarial (gồm out_of_scope: 9) | 20 | 20 |
| Multi-hop | 30 | 30 |
| Ambiguous | 20 | 20 |

## Việc còn lại

- `relevant_chunks` đã gán cho 249/250 câu có căn cứ tài liệu (99.6% nếu > 0) qua `scripts/link_relevant_chunks.py` — phần còn lại (nếu có) là lexical-miss, xem `data/test_sets/relevant_chunks_report.md`.
- Học phí cụ thể theo ngành/năm và số QĐ học bổng D13 vẫn là data gap thật (chưa có nguồn sạch) — xem `golden_set_review.md` mục việc còn lại.
- Theo `review_status`: 224 câu vẫn `pending_review` — chưa qua domain-expert hay AI self-review có phương pháp. Khuyến nghị domain expert spot-check trước khi dùng làm baseline chính thức cho báo cáo khóa luận, đặc biệt các con số tín chỉ/điểm số/phần trăm.