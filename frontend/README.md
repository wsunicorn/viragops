# viRAGops frontend

Showcase/demo web app cho project — xem `docs/system/modules/10_frontend_showcase.md`
ở repo gốc để biết bối cảnh kiến trúc đầy đủ. Next.js (App Router) +
Tailwind CSS v4 + Motion + GSAP/ScrollTrigger + Lenis + shadcn/ui.

## Chạy local

```bash
npm install
npm run dev
```

Mặc định gọi API tại `http://localhost:8000` (đổi qua
`NEXT_PUBLIC_API_BASE_URL` trong `.env.local`). Cần backend thật đang
chạy để `/demo` hoạt động — không có chế độ mock:

```bash
# ở thư mục gốc repo, terminal khác
docker compose up -d postgres qdrant valkey litellm
uvicorn src.api.main:app --port 8000
```

## 3 trang

- `/` — landing/showcase: kiến trúc, timeline 12 phase, số liệu thật.
- `/demo` — hỏi-đáp thật, gọi `/qa/query`.
- `/dashboard` — số liệu thực nghiệm (Phase 4/6/8), đọc từ
  `src/lib/data/*.ts` (transcribe thủ công từ report thật trong
  `docs/system/experiments/` — xem comment đầu mỗi file để biết nguồn).

## Cập nhật số liệu

Khi có report thực nghiệm mới, sửa trực tiếp `src/lib/data/*.ts` — mỗi
file ghi rõ nguồn report gốc trong comment đầu file. Không tính lại số
liệu bằng công thức khác với report.

## Build production

```bash
npm run build && npm start
# hoặc, từ thư mục gốc repo:
docker compose up -d --build frontend
```
