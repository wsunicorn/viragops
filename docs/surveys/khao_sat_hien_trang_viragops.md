# BÁO CÁO KHẢO SÁT HIỆN TRẠNG ĐỀ TÀI viRAGops

**Đề tài:** Nền tảng LLMOps/RAGOps toàn vòng đời cho hệ thống hỏi-đáp quy chế đào tạo tiếng Việt (Trường Đại học Công nghiệp TP.HCM — IUH)

**Sinh viên thực hiện:** Nguyễn Ngọc Lân

**Ngày lập báo cáo:** 17/07/2026

**Nguồn đối chiếu:** toàn bộ nội dung dưới đây được đối chiếu trực tiếp với mã nguồn, tài liệu thiết kế (docs/llmops_thesis_blueprint.md, docs/system/) và 6 báo cáo thực nghiệm thật (docs/system/experiments/) trong repository của đề tài. Mọi con số đều là kết quả đo thật, không phải số minh họa.

## 1. Hệ thống đang làm được gì? Đã là LLMOps/RAGOps chưa?

### 1.1. Tiến độ tổng thể

Đề tài chia thành 12 phase. Đến thời điểm báo cáo: **Phase 1 đến 11 đã hoàn tất toàn bộ**; Phase 12 đã xong phần kỹ thuật (đủ 6/6 báo cáo thực nghiệm và tổng hợp trả lời câu hỏi nghiên cứu RQ1-RQ5), phần còn lại là viết các chương báo cáo khóa luận và slide bảo vệ.

Chín module trong kiến trúc đều đã được cài đặt và kiểm chứng bằng cách chạy thật (không phải bản vẽ kế hoạch):

| Module | Trạng thái | Kết quả chính đã đo được |
|---|---|---|
| 1. DataOps/RAGOps | Hoàn tất | 10 văn bản IUH thật, OCR bằng Gemini multimodal, 222 chunk, mọi dữ liệu có version (data_version/index_version) |
| 2. Retrieval Experiment | Hoàn tất | 8 cấu hình retrieval + 4 chiến lược chunking đo thật 2 lần; hybrid DBSF thắng, recall@5 = 0.932 |
| 3. RAG Runtime | Hoàn tất | API hỏi-đáp có trích dẫn Điều/Khoản, từ chối 2 lớp, trích dẫn fail-closed (chunk bịa bị loại) |
| 4. PromptOps | Hoàn tất | Registry PostgreSQL, 9 phiên bản prompt (p0-p8), kích hoạt bắt buộc có bằng chứng đánh giá |
| 5. Evaluation Engine | Hoàn tất | Đánh giá 4 tầng qua đúng đường chạy production + LLM judge; đã chạy full 300 câu |
| 6. Quality Gate (CI/CD) | Hoàn tất | 16 kịch bản kiểm chứng: precision = recall = 1.000; đã chặn (BLOCK) thật 1 lần trên GitHub Actions |
| 7. Observability/Cost | Hoàn tất | Langfuse Cloud tracing, Prometheus + Grafana 16 panel, 4 alert rule, chi phí/độ trễ theo từng câu hỏi |
| 8. Optimization/Routing | Hoàn tất | Semantic cache, context compression, dynamic top-k, auto-routing — đo qua thí nghiệm O1-O8 trước khi cân nhắc bật |
| 9. Feedback Loop | Hoàn tất | 26 feedback thật từ lỗi đánh giá thật, phân cụm lỗi, 1 vòng cải tiến khép kín có đo trước/sau |

### 1.2. Những gì demo được, trực quan được trên frontend hiện tại

Frontend (Next.js) hiện có 3 trang, chạy được ngay bằng lệnh trong README:

- **Trang tổng quan:** vật thể 3D "cuốn sổ tay quy chế" (WebGL), mục scrolltelling "Quyển sách tri thức" — cuộn chuột để mở bìa và lật từng trang, mỗi trang là một trạm trên lộ trình của một câu hỏi (nguồn tri thức → chunk & embed → truy hồi lai → sinh trả lời → cổng kiểm định) kèm số liệu thật của trạm đó; lưới 9 module; timeline 12 phase; 4 câu chuyện kỹ thuật thật.
- **Trang demo hỏi-đáp:** gọi thẳng API backend thật — người xem tự đặt câu hỏi và nhận câu trả lời kèm trích dẫn đúng Điều/Khoản, thanh confidence, chi phí/độ trễ/token của chính lần gọi đó; khi thiếu căn cứ hệ thống từ chối trung thực.
- **Trang thực nghiệm:** số liệu thật của Phase 4/6/8 (so sánh 8 config retrieval, so sánh prompt, đánh giá theo nhóm câu hỏi), 4 chỉ số chốt của dự án.

![Trang tổng quan: vật thể 3D "cuốn sổ tay quy chế" và các chỉ số thật](images/web_home_hero.png)

*Hình 1. Trang tổng quan — vật thể 3D "cuốn sổ tay quy chế" (corpus của hệ thống) và các chỉ số thật.*

![Demo hỏi-đáp thật: câu trả lời kèm trích dẫn Điều 6 Khoản 4, confidence, chi phí và độ trễ thật](images/web_demo_real_answer.png)

*Hình 2. Demo hỏi-đáp thật — câu hỏi về tín chỉ được trả lời kèm trích dẫn "Điều 6, Khoản 4" của QĐ 1482, cùng metadata thật của lần gọi (model, token, độ trễ 3.017ms, chi phí 0,000826 USD, trace_id).*

### 1.3. Cần thêm gì để trực quan trọn vẹn quy trình từ đầu đến cuối

Ba khoảng trống chính (đều đã có API/dữ liệu phía backend, chỉ thiếu giao diện):

1. Trang thực nghiệm mới trực quan số liệu Phase 4/6/8 — chưa nối số liệu Phase 9-12 (hiệu quả quality gate, phân loại lỗi, so sánh model/provider, tối ưu O1-O8).
2. Chưa có màn hình theo dõi "một request đi qua pipeline" ngay trong frontend — trace chi tiết hiện xem qua Langfuse Cloud và Grafana (công cụ ngoài).
3. Chưa có giao diện quản trị cho các API đã tồn tại (prompt registry, feedback queue) — chi tiết ở mục 3.

### 1.4. Đã là LLMOps/RAGOps chưa?

Đối chiếu với các trụ cột thường được chấp nhận của LLMOps/RAGOps, hệ thống đã có đủ và đều đã chạy thật: (1) versioning toàn diện — dữ liệu, index, prompt, cấu hình model đều có phiên bản; (2) thí nghiệm có kiểm soát và báo cáo lại được — 6 nhóm thực nghiệm; (3) đánh giá tự động nhiều tầng với LLM judge; (4) cổng chất lượng chặn hồi quy trong CI/CD — đã chặn thật; (5) quan sát hệ thống — trace, metric, alert, chi phí; (6) vòng phản hồi khép kín — feedback thật sinh cải tiến, cải tiến phải qua đánh giá và gate; (7) tối ưu vận hành — cache/nén/định tuyến, đo trước khi bật.

Điểm khác biệt so với một hệ LLMOps sản xuất công nghiệp (nêu rõ để không nói quá): triển khai một máy (Docker Compose, chưa có môi trường staging/production tách biệt); nhà cung cấp model giới hạn ở Gemini và Ollama cục bộ (không có key OpenAI/Anthropic); kích hoạt/rollback prompt có chính sách kiểm soát nhưng thao tác cuối vẫn do con người bấm. **Kết luận: ở quy mô khóa luận, hệ thống đã là một vòng đời LLMOps/RAGOps hoàn chỉnh và chứng minh được bằng số liệu; chưa phải hạ tầng production đa môi trường.**

## 2. Mức độ bám sát blueprint và tính cần thiết của việc trực quan hóa quy trình

### 2.1. Bám sát blueprint

File docs/llmops_thesis_blueprint.md là bản thiết kế gốc (9 module, 12 phase, 6 nhóm thực nghiệm, RQ1-RQ5). Hệ thống thực tế bám đúng khung này: 9/9 module đã dựng đúng vai trò thiết kế; 12 phase đi đúng trình tự; đủ 6/6 báo cáo thực nghiệm; RQ1-RQ5 đã được trả lời bằng số liệu thật trong docs/system/experiments/results_research_questions.md (trong đó ghi rõ câu nào trả lời trọn vẹn, câu nào chỉ trả lời được một phần và vì sao).

Các điểm lệch so với blueprint đều **có chủ đích, có lý do được ghi lại** tại thời điểm quyết định:

| Blueprint dự kiến | Thực tế triển khai | Lý do |
|---|---|---|
| So sánh GPT-5.x, Claude, Llama 4, Gemma 4 | Gemini (2 model) + Ollama qwen2.5:7b | Không có API key OpenAI/Anthropic; GPU 4GB không tự host được model lớn — so sánh chỉ thực hiện trên những gì có thật |
| Langfuse tự host | Langfuse Cloud (free tier) | Tự host cần thêm 4 container nặng; máy phát triển hạn chế tài nguyên |
| MLflow theo dõi thí nghiệm | Báo cáo CSV/Markdown có cấu trúc | MLflow chưa từng được nối dây thật trong repo; báo cáo file bám sát nhu cầu khóa luận hơn |
| Frontend Streamlit/Gradio ở Phase 12 | Next.js đầy đủ, bắt đầu sớm từ giữa Phase 8 | Yêu cầu trực tiếp về chất lượng trình diễn |

### 2.2. Đã trực quan hóa quá trình cho người xem chưa? Việc này có cần thiết không?

Đã trực quan một phần: mục "Quyển sách tri thức" cho người xem thấy lộ trình 5 trạm của một câu hỏi kèm số liệu từng trạm; timeline 12 phase kể lại tiến trình xây dựng; trang thực nghiệm cho xem số liệu so sánh. Chưa trực quan phần vòng đời vận hành (gate chặn thế nào, trace một request, vòng feedback) — phần này hiện nằm ở công cụ ngoài (Grafana, Langfuse, GitHub Actions).

![Mục "Quyển sách tri thức" — cuộn chuột lật trang, mỗi trang một trạm của pipeline kèm số liệu thật](images/web_knowledge_book.png)

*Hình 3. Mục "Quyển sách tri thức" trên trang chủ — đang lật giữa trạm 02 và 03; trang trái in kết quả trạm đã qua (222 chunk), trang phải là trạm kế tiếp (truy hồi lai).*

Về tính cần thiết: **cần**. Với đề tài mà đóng góp chính là *quy trình vận hành* (Ops) chứ không chỉ là một chatbot, phần trực quan quy trình chính là cách ngắn nhất để hội đồng thấy được sản phẩm thật sự. Đề xuất bổ sung (đã nằm trong kế hoạch phần còn lại của Phase 12): thêm tab Phase 9-12 vào trang thực nghiệm và một mục "giải phẫu một request" hiển thị trace thật.

## 3. Người dùng quản lý hệ thống như thế nào? Đã có giao diện điều khiển hợp nhất chưa?

Hiện trạng: **vòng đời của mọi thành phần đều quản lý được, nhưng qua API + dòng lệnh + công cụ chuyên dụng, chưa có một Admin Console hợp nhất.** Cụ thể:

| Thành phần | Quản lý được gì hiện nay | Qua kênh nào | Đã có UI riêng chưa |
|---|---|---|---|
| Dữ liệu | Tải nguồn, OCR, làm sạch, chunk, embed, index lại toàn bộ; mỗi lần ra data_version/index_version mới | Bộ script CLI (download_sources, ocr_scanned_pdfs, ingest_data...) | Chưa |
| Cập nhật dữ liệu mới | Làm được nhưng **thủ công** (chạy script khi nguồn thay đổi); chưa có lịch tự động crawl-phát hiện thay đổi | CLI | Chưa |
| Prompt | Tạo phiên bản, xem diff, kích hoạt (bắt buộc kèm bằng chứng đánh giá hoặc override có ghi log), tự archive bản cũ | REST API /prompts | Chưa |
| Model/provider | Đổi model từng tier, thêm nhà cung cấp, cấu hình 4 chặng fallback, ngân sách | File cấu hình YAML (model_gateway.yaml, litellm_config.yaml) + khởi động lại gateway | Chưa |
| Feedback | Nhận feedback gắn trace, phân loại lỗi tự động, hàng đợi duyệt, xuất backlog cải tiến | REST API /feedback | Chưa |
| Đánh giá & gate | Chạy đánh giá smoke/full/targeted, so với baseline, quyết định PASS/WARN/BLOCK | CLI + tự động trong CI | GitHub Actions UI |
| Quan sát vận hành | 16 panel metric, 4 alert, trace từng request, chi phí | Grafana + Langfuse Cloud + Prometheus | Có (công cụ ngoài) |

Đánh giá trung thực: phần "điều khiển" gần nhất với một dashboard hiện nay là Grafana/Langfuse, nhưng đó là *đọc số liệu*, không phải *thao tác quản trị*. Một **Admin Console hợp nhất** (quản lý data version và kích hoạt ingest, duyệt feedback, kích hoạt prompt, chuyển provider) là hạng mục tương lai có tính khả thi cao vì backend đã có sẵn phần lớn API; việc còn lại chủ yếu là xây giao diện — đây là điểm phù hợp để trao đổi với giảng viên về mức độ ưu tiên so với thời gian còn lại.

## 4. Khó khăn khi xây dựng và cách khắc phục

Các khó khăn dưới đây đều là sự cố thật đã gặp và được ghi lại trong nhật ký triển khai (docs/system/CHECKLIST_IMPLEMENTATION.md):

| Khó khăn | Biểu hiện thật | Cách khắc phục |
|---|---|---|
| Mạng/ISP chặn CDN | Không pull được Docker Hub; không tải được model reranker/fastembed từ HuggingFace | Dùng registry mirror cho Docker; tự cài đặt BM25 chuẩn (không phụ thuộc mạng ngoài) thay cho thư viện tải model |
| Tài liệu nguồn là PDF scan | 5/10 văn bản trọng yếu (QĐ 610, Sổ tay SV...) không có lớp text | OCR bằng Gemini multimodal, đối chiếu thủ công; 2 tài liệu bị model từ chối OCR (recitation) phải chờ quota và thử lại nhiều lần |
| Mất dữ liệu do script ghi đè | Kết quả OCR bị xóa khi chạy lại pipeline (xảy ra 2 lần) | Ghi manifest ngay sau từng tài liệu; thêm lớp bảo vệ "không bao giờ ghi đè file text bằng bản ngắn hơn hẳn" |
| Hạn ngạch API free-tier | Cạn quota Gemini nhiều lần trong một ngày chạy thí nghiệm (giới hạn 1.000 request-item/ngày/key) | Dùng 5 API key; gateway 4 chặng fallback (3 key Gemini → Ollama cục bộ); cache embedding và cache điểm judge; xếp lịch chạy đánh giá |
| Website nguồn là SPA/chặn crawler | pdt.iuh.edu.vn trả app-shell rỗng rồi chặn 403 | Dùng bản mirror server-rendered ở các trang khoa/cẩm nang của trường |
| Model cục bộ yếu | qwen3:4b "suy nghĩ" 77-90 giây/câu; qwen2.5:7b tự rút gọn chuỗi chunk_id dài khiến trích dẫn không khớp | Đo thật để chọn lại model; sửa parser trích dẫn cho phép khớp hậu tố **chỉ khi duy nhất** (giữ nguyên tắc fail-closed) |
| Sửa lỗi này sinh lỗi khác | Prompt p6 tăng độ chính xác trích dẫn nhưng làm tụt refusal accuracy nhóm adversarial 0.909 xuống 0.636 | Chạy đánh giá full 300 câu bắt được hồi quy; sửa bằng p7; đây trở thành minh chứng sống cho giá trị của evaluation + gate |
| Nhiều giải pháp "hợp lý" hóa ra sai | Tăng số chunk đưa vào model, per-hop retrieval, prompt tự-kiểm-tra — cả 3 đều làm giảm chất lượng khi đo thật | Nguyên tắc "đo trước khi đổi mặc định": mọi thay đổi qua đánh giá + gate; kết quả âm tính được ghi lại công khai thay vì giấu |
| Hạ tầng máy trạm không ổn định | Docker Desktop tự sập 3 lần trong quá trình làm | Khởi động lại và kiểm tra health toàn chuỗi; trang demo nay có thẻ hướng dẫn khắc phục khi backend offline |

## 5. Thử thách nghiên cứu và cách thực hiện

1. **Không có ground truth tiếng Việt cho miền quy chế đào tạo.** Cách làm: tự xây golden set 300 câu đúng cơ cấu thiết kế (200 trả lời được / 30 từ chối do thiếu dữ liệu / 20 đối kháng-ngoài phạm vi / 30 nhiều bước / 20 mơ hồ); kiểm tra chéo bằng quy trình AI self-review 2 vòng có audit trail; chính quy trình này phát hiện và sửa lỗi trong golden set (ví dụ một đáp án chuẩn sai mà model trả lời đúng hơn) và một trường hợp "data drift" thật (bảng quy đổi IELTS cũ so với bản hiện hành trên trang trường).
2. **Đo lường sao cho không tự lừa.** Mọi kết luận lấy từ lần chạy thật qua đúng đường production; tách riêng số liệu bị nhiễu hạ tầng (fallback do cạn quota) khỏi số liệu chất lượng; ghi chú tường minh giới hạn cấu trúc của metric (Context Precision có trần cấu trúc do mẫu số cố định) thay vì đọc nhầm thành hệ thống kém.
3. **LLM chấm LLM có đáng tin?** Judge dùng rubric rời rạc 0/0,5/1 để giảm nhiễu tự chấm, có cache điểm, và đã đo thêm mức đồng thuận với một judge thứ hai rẻ hơn; báo cáo ghi rõ đây là cận dưới/cận trên chứ không phải chân lý.
4. **Nghiên cứu trên tài nguyên hạn chế.** Free-tier + GPU 4GB buộc thiết kế 2 tầng smoke (50 câu)/full (300 câu), cache embedding-judge, và cỡ mẫu nhỏ có kiểm soát cho các thí nghiệm tốn quota (O1-O8 dùng n=15; so sánh model n=10) — giới hạn thống kê được ghi rõ trong từng báo cáo.
5. **Trung thực với kết quả âm tính.** Ba hướng cải tiến nghe hợp lý đã bị số liệu bác bỏ và đều được công bố như một phát hiện (bài học phương pháp luận: trực giác thiết kế trong LLMOps sai thường xuyên — quy trình đo lường chính là cơ chế bắt lỗi trực giác).

![Biểu đồ so sánh 8 cấu hình retrieval từ số liệu thật](../figures/fig_retrieval_comparison_real.png)

*Hình 4. So sánh 8 cấu hình retrieval trên 249 câu thật — hybrid DBSF thắng mọi cấu hình, kể cả các cấu hình có reranker (biểu đồ sinh từ số liệu đã công bố trong báo cáo thực nghiệm).*

## 6. Khi thành sản phẩm: từng vai trò làm được gì trên hệ thống?

### 6.1. Đã làm được ngay hôm nay

| Vai trò | Làm được gì |
|---|---|
| Sinh viên (end-user) | Hỏi đáp quy chế bằng tiếng Việt tự nhiên; nhận câu trả lời kèm trích dẫn đúng văn bản-Điều-Khoản; thấy độ tin cậy; được từ chối trung thực thay vì bị trả lời bịa; gửi phản hồi gắn với đúng lần hỏi (qua API) |
| Người xem/hội đồng | Xem toàn cảnh kiến trúc, lộ trình một câu hỏi, tiến độ 12 phase và số liệu thực nghiệm thật trên web; tự tay thử hệ thống ở trang demo |
| Kỹ sư vận hành | Theo dõi 16 panel metric + 4 alert (Grafana), soi trace từng request (Langfuse), xem chi phí; chạy đánh giá và gate bằng CLI; CI tự chạy đánh giá và chặn thay đổi xấu khi push code |
| Quản trị viên | Quản lý vòng đời prompt qua API có chính sách; duyệt hàng đợi feedback và xuất backlog cải tiến; tái tạo dữ liệu/index có version bằng script; đổi model/provider qua cấu hình |

### 6.2. Lộ trình bổ sung để tròn vai một sản phẩm (đề xuất, theo thứ tự ưu tiên)

1. Nối số liệu Phase 9-12 vào trang thực nghiệm và thêm mục "giải phẫu một request" (trace trực quan trong frontend).
2. Nút gửi feedback ngay trên trang demo (API đã có sẵn).
3. Admin Console hợp nhất: duyệt feedback, kích hoạt prompt, quản lý data version/ingest, chuyển provider.
4. Tự động hóa cập nhật dữ liệu: lịch crawl định kỳ, phát hiện thay đổi, re-index và **bắt buộc qua quality gate trước khi index mới được dùng** (đúng triết lý hiện có của hệ thống).
5. Xác thực người dùng + rate-limit khi mở ra ngoài; mở rộng so sánh đa nhà cung cấp khi có API key.

## 7. Tóm tắt gửi giảng viên

Hệ thống đã là một vòng đời LLMOps/RAGOps hoàn chỉnh ở quy mô khóa luận, bám sát blueprint, mọi kết luận có số liệu thật và tái lập được; phần demo trực quan đã kể được "lộ trình một câu hỏi" và số liệu thực nghiệm cốt lõi. Khoảng trống lớn nhất hiện nay không nằm ở backend mà ở tầng trình diễn/quản trị: trực quan hóa các phase vận hành (9-12) và một giao diện quản trị hợp nhất. Sinh viên đề xuất trao đổi với thầy về mức ưu tiên giữa: (a) hoàn thiện các chương báo cáo khóa luận, (b) bổ sung trực quan Phase 9-12 lên frontend, (c) xây Admin Console — trong quỹ thời gian còn lại của Phase 12.
