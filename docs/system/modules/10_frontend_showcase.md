# Module 10 - Frontend Showcase

> Thêm ngoài kế hoạch 9-module gốc (2026-07-12, theo yêu cầu trực tiếp
> user) — không phải một module LLMOps/RAGOps (không quản lý data/prompt/
> eval/quality-gate lifecycle nào), mà là lớp trình bày (presentation
> layer) gọi vào Module 3 (RAG Runtime) và đọc số liệu thật đã có từ
> Module 2/4/5 để showcase toàn bộ project. Đổi từ kế hoạch gốc
> (Streamlit/Gradio, xem `docs/system/04_tech_stack_decisions.md`) sang
> Next.js vì cần chất lượng trình bày cao hơn (animation cuộn trang,
> giao diện đẹp) cho buổi bảo vệ khóa luận.

## Mục tiêu

Xây web app giới thiệu trực quan, sinh động toàn bộ project (kiến trúc,
8 phase đã làm, số liệu thực nghiệm thật) và cho phép demo hỏi-đáp thật
qua RAG runtime — không bịa số liệu, mọi con số/biểu đồ lấy từ report/CSV
thật đã có trong `data/experiments/`, `data/eval/`, `docs/system/
experiments/`.

## Trách nhiệm

- Trình bày kiến trúc 9 module LLMOps/RAGOps + luồng xử lý runtime.
- Trình bày tiến độ 8 phase đã hoàn tất (checklist thật, không phải
  danh sách tính năng dự định).
- Hiển thị số liệu thực nghiệm thật (Phase 4 retrieval, Phase 6 prompt
  comparison, Phase 8 eval) dạng biểu đồ/bảng trực quan.
- Cho phép người dùng gõ câu hỏi thật, gọi `/qa/query` (hoặc `/qa/debug`
  để lấy thêm retrieved chunks), hiển thị answer + citation + refusal
  đúng như hệ thống trả về — không mô phỏng/giả lập câu trả lời.
- KHÔNG được: tự tính toán/làm tròn số liệu khác với report gốc, tự thêm
  tính năng backend mới (frontend chỉ gọi API có sẵn), giả lập response
  khi API lỗi (phải hiển thị lỗi thật).

## Input và output

| Loại | Nội dung |
|---|---|
| Input | FastAPI backend (`/qa/query`, `/qa/debug`, `/health`), số liệu tĩnh từ report Markdown/CSV thật (build-time hoặc fetch) |
| Output | Web app (landing/showcase, QA demo, dashboard thực nghiệm) |
| Storage | Không có storage riêng — stateless, không lưu lịch sử hỏi-đáp phía frontend (trace đã có ở backend qua `trace_id`) |

## Kiến trúc kỹ thuật

- **Framework:** Next.js (App Router), TypeScript.
- **Styling:** Tailwind CSS v4.
- **Animation:** Motion (Framer Motion, component-level) + GSAP/ScrollTrigger
  (choreographed scroll storytelling) + Lenis (smooth scroll physics).
- **UI components:** shadcn/ui làm nền (Radix primitives), Magic UI/
  Aceternity UI cho điểm nhấn hero/feature — dùng có chọn lọc, không phủ
  toàn trang để tránh cảm giác "AI slop" chung chung.
- **Icon:** Lucide.
- **Deploy:** Vercel (ưu tiên cho demo/preview URL) hoặc container Next.js
  riêng trong `docker-compose.yml` (service `frontend`, port 3000).

## 3 trang chính

1. **Landing/showcase** (`/`) — kiến trúc 9 module, luồng xử lý, timeline
   8 phase đã làm (bám sát `CHECKLIST_IMPLEMENTATION.md` thật), điểm nhấn
   kỹ thuật đáng chú ý (vd phát hiện data drift ở golden set, sự cố quota
   3 lần ở Phase 4, hồi quy adversarial ở Phase 8) — đúng những gì đã
   thật sự xảy ra, không tô hồng.
2. **QA demo** (`/demo`) — ô nhập câu hỏi thật, gọi `/qa/query`, hiển thị
   answer + citations (document/section thật) + trạng thái refusal, có
   thể bật debug mode xem retrieved chunks/score.
3. **Dashboard thực nghiệm** (`/dashboard`) — trực quan hoá bằng
   biểu đồ: Phase 4 (so sánh config retrieval/reranking/chunking), Phase 6
   (so sánh 8 prompt variant), Phase 8 (4 tầng eval, primary-vs-fallback,
   theo category) — nguồn dữ liệu là CSV/Markdown thật đã commit, không
   tính lại bằng công thức khác.

## Luồng xử lý

1. Build-time hoặc request-time: đọc report Markdown/CSV thật từ repo
   (qua API route nội bộ hoặc import trực tiếp lúc build) để render
   dashboard — không hard-code số liệu vào component.
2. QA demo: submit câu hỏi → gọi `NEXT_PUBLIC_API_BASE_URL/qa/query` →
   render response thật (kể cả khi refusal/lỗi).
3. Landing page không gọi API — thuần tĩnh, build-time.

## Task triển khai

- Scaffold Next.js project trong `frontend/`.
- Setup Tailwind v4 + shadcn/ui + Lenis + GSAP + Motion.
- Landing/showcase page với scroll-driven sections.
- QA demo page nối API thật.
- Dashboard page đọc report thật, vẽ biểu đồ.
- Responsive (desktop trình chiếu bảo vệ khóa luận là ưu tiên, mobile là
  phụ).
- Thêm service `frontend` vào `docker-compose.yml`.

## Acceptance criteria

- Chạy được `npm run dev` local, nối được API thật (không mock).
- QA demo trả lời đúng như gọi trực tiếp `curl /qa/query` (verify chéo).
- Mọi số liệu trên dashboard khớp chính xác với report gốc trong repo
  (verify bằng cách đối chiếu thủ công ít nhất 5 con số).
- Có animation cuộn trang mượt, không giật/lag trên máy demo thật.
- `docker compose up frontend` chạy được (khi đã build xong).

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Dashboard sai số liệu | Hard-code/copy tay từ report thay vì đọc file thật | Đọc trực tiếp CSV/Markdown, có test đối chiếu |
| QA demo trông "giả" | Mock response khi dev không có API | Luôn nối API thật kể cả lúc dev, dùng `.env.local` trỏ backend local |
| Animation giật máy yếu | Quá nhiều hiệu ứng đồng thời | Giới hạn số scroll-trigger đồng thời, ưu tiên GPU-friendly transform/opacity |
| CORS lỗi khi gọi API | FastAPI chưa bật CORS cho origin frontend | Thêm `CORSMiddleware` vào `src/api/main.py` cho origin dev/prod |

## Checklist hoàn tất

- [ ] Next.js project scaffold xong, chạy `npm run dev` được.
- [ ] Landing/showcase page hoàn chỉnh, đúng số liệu/tiến độ thật.
- [ ] QA demo hoạt động, nối API thật, hiển thị citation/refusal đúng.
- [ ] Dashboard thực nghiệm hoạt động, số liệu khớp report gốc.
- [ ] Animation cuộn trang mượt, đã test trên máy sẽ dùng để demo.
- [ ] Thêm service `frontend` vào `docker-compose.yml`.
- [ ] CORS đã cấu hình đúng cho FastAPI backend.
