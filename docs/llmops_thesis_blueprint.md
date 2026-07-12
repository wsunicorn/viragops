# KHÓA LUẬN TỐT NGHIỆP — BẢN THIẾT KẾ FULL-SCOPE

# Nghiên cứu, xây dựng và đánh giá nền tảng LLMOps/RAGOps toàn diện cho hệ thống hỏi đáp tài liệu tiếng Việt dựa trên Retrieval-Augmented Generation

**Tiếng Anh:** *Design, Implementation, and Evaluation of a Full-Scope LLMOps/RAGOps Platform for Vietnamese Document Question Answering based on Retrieval-Augmented Generation*

> **Bản cập nhật full-scope — 02/06/2026:** Đề tài được triển khai theo hướng làm đầy đủ toàn bộ 9 module LLMOps/RAGOps thay vì thu hẹp thành bản rút gọn. Vì người thực hiện có nhiều thời gian và có thể dùng AI coding để tăng tốc phần cài đặt, phạm vi hợp lý hơn là một hệ thống production-like đầy đủ, có phân kỳ triển khai, thực nghiệm định lượng, quality gate, observability, model gateway, feedback loop và tối ưu chi phí/độ trễ. Các mục "hướng phát triển" chỉ còn là cải tiến sau khi hệ thống full-scope đã hoàn tất, không phải phần bị loại khỏi đề tài.
>
> **Nguồn cập nhật chính:** OpenAI API model docs, Anthropic Claude model docs, Google Gemini API docs, Meta Llama 4 release, Qwen3 release, Google Gemma 4 release, Langfuse self-hosting v3 docs, LiteLLM gateway docs, Qdrant hybrid search docs, OpenTelemetry GenAI semantic conventions, McKinsey State of AI 2025, OWASP Top 10 for LLM Applications 2025, DeepEval/RAGAS documentation và các benchmark tiếng Việt gần đây như CSConDa, VLegal-Bench, ViRanker.

---

## PHẦN I — TỔNG QUAN ĐỀ TÀI

### 1.1 Bối cảnh và động lực nghiên cứu

#### 1.1.1 Sự bùng nổ của LLM trong doanh nghiệp

Kể từ khi ChatGPT ra mắt cuối năm 2022, các mô hình ngôn ngữ lớn (Large Language Models — LLM) đã nhanh chóng trở thành công cụ trung tâm trong nhiều lĩnh vực: hỗ trợ khách hàng, phân tích tài liệu, tự động hóa quy trình, tạo nội dung và ra quyết định. Các doanh nghiệp, tổ chức giáo dục, cơ quan pháp lý và y tế đều đang tìm cách tích hợp LLM vào hệ thống vận hành hàng ngày.

Tuy nhiên, phần lớn các ứng dụng LLM hiện nay vẫn đang ở **mức demo hoặc prototype**. Khoảng cách giữa một chatbot "chạy được" trong môi trường phát triển và một hệ thống LLM "vận hành được" trong môi trường production là **rất lớn**. Khoảng cách này chính là nơi mà **LLMOps** đóng vai trò thiết yếu.

#### 1.1.2 Retrieval-Augmented Generation (RAG) — một kiến trúc ứng dụng phổ biến

RAG là một trong các kiến trúc được sử dụng rộng rãi nhất để xây dựng ứng dụng LLM trên dữ liệu riêng (private data). Thay vì fine-tune model trên toàn bộ dữ liệu (tốn kém và khó cập nhật), RAG cho phép:

- **Truy xuất** (Retrieve): Tìm các đoạn tài liệu liên quan từ cơ sở dữ liệu vector.
- **Tăng cường** (Augment): Đưa các đoạn tài liệu tìm được vào prompt.
- **Sinh** (Generate): LLM sinh câu trả lời dựa trên context được cung cấp.

Mô hình này giải quyết được nhiều hạn chế của LLM thuần: hallucination (sinh thông tin sai), knowledge cutoff (thiếu thông tin mới), và lack of domain specificity (thiếu chuyên môn ngành).

Tuy nhiên, RAG cũng đem lại **những thách thức vận hành riêng** mà LLM thuần không có:

| Thách thức RAG | Mô tả |
|---|---|
| **Retrieval failure** | Không lấy được đoạn tài liệu đúng, dẫn đến câu trả lời sai hoặc không đầy đủ |
| **Context poisoning** | Tài liệu truy xuất chứa thông tin nhiễu, lỗi thời hoặc mâu thuẫn |
| **Hallucination despite context** | LLM sinh thông tin ngoài context mặc dù đã có tài liệu đúng |
| **Stale data** | Tài liệu nguồn thay đổi nhưng vector index chưa được cập nhật |
| **Chunk boundary issues** | Thông tin quan trọng bị chia cắt giữa hai chunk |
| **Prompt sensitivity** | Thay đổi nhỏ trong prompt dẫn đến thay đổi lớn trong chất lượng |
| **Cost unpredictability** | Token usage dao động mạnh tùy theo context length và model |
| **Latency variance** | Thời gian phản hồi phụ thuộc vào nhiều tầng (retrieval + generation) |

#### 1.1.3 LLMOps — MLOps cho thời đại LLM

**LLMOps** (Large Language Model Operations) là tập hợp các thực hành, công cụ và quy trình để **phát triển, đánh giá, triển khai, giám sát và cải tiến liên tục** các ứng dụng LLM trong toàn bộ vòng đời hệ thống.

LLMOps kế thừa tinh thần của MLOps nhưng có những **khác biệt căn bản**:

| Khía cạnh | MLOps truyền thống | LLMOps |
|---|---|---|
| **Model artifact** | File model (.pkl, .pt, .onnx) | API endpoint hoặc large checkpoint |
| **Training** | Thường xuyên retrain | Chủ yếu dùng prompting, ít fine-tune |
| **Prompt** | Không có | Thành phần trung tâm, cần version hóa |
| **Input/Output** | Có cấu trúc (tabular, image) | Phi cấu trúc (text tự nhiên) |
| **Đánh giá** | Metric xác định (accuracy, F1, AUC) | Metric phi xác định (faithfulness, relevance) — cần LLM-as-a-Judge |
| **Dữ liệu ngoài** | Không có | RAG: cần quản lý external data lifecycle |
| **Chi phí** | Chủ yếu training/infra | Chủ yếu token-based API cost |
| **Latency** | Dự đoán được | Biến động mạnh theo context length |
| **Safety** | Bias, fairness | + Prompt injection, PII leakage, hallucination |
| **Reproducibility** | Seed + data = kết quả giống | Non-deterministic output ngay cả với cùng input |

#### 1.1.4 RAGOps — mở rộng LLMOps cho hệ thống RAG

**RAGOps** là một nhánh mở rộng của LLMOps, tập trung vào việc quản lý **vòng đời dữ liệu ngoài** (external data lifecycle) trong hệ thống RAG. RAGOps nhấn mạnh rằng chất lượng của hệ thống RAG phụ thuộc không chỉ vào LLM và prompt, mà còn vào:

- **Chất lượng dữ liệu nguồn** (data quality)
- **Chiến lược chunking** (cách chia tài liệu)
- **Chất lượng embedding** (representation quality)
- **Độ tươi của vector index** (freshness)
- **Chiến lược retrieval** (dense, sparse, hybrid)
- **Tính nhất quán giữa các phiên bản dữ liệu** (data versioning)

Khi tài liệu nguồn thay đổi (cập nhật quy chế, sửa đổi luật, thêm FAQ mới), toàn bộ pipeline RAG cần được **tái đánh giá** — và đây là lúc RAGOps phát huy vai trò.

#### 1.1.5 Thách thức đặc thù với tiếng Việt

Hệ thống RAG tiếng Việt gặp thêm các thách thức riêng:

| Thách thức | Chi tiết |
|---|---|
| **Tokenization** | Tiếng Việt là ngôn ngữ đơn lập (isolating), ranh giới từ không rõ ràng. Các mô hình đa ngôn ngữ có thể tokenize không tối ưu |
| **Embedding quality** | Embedding models đa ngôn ngữ có thể kém chính xác trên tiếng Việt so với tiếng Anh |
| **Dấu thanh** | Viết thiếu dấu, sai dấu ảnh hưởng đến retrieval (ví dụ: "luật" vs "luat") |
| **Tài liệu PDF** | Nhiều tài liệu hành chính, pháp luật tiếng Việt ở dạng PDF scan, chất lượng OCR kém |
| **Cấu trúc văn bản** | Tài liệu pháp luật, quy chế có cấu trúc phân cấp phức tạp (Điều, Khoản, Điểm) |
| **Benchmark còn hạn chế và phân mảnh** | Đã có thêm một số benchmark/dataset tiếng Việt hoặc đa ngôn ngữ liên quan, nhưng vẫn thiếu benchmark RAG chuẩn cho từng domain với snapshot tài liệu, ground-truth chunks và tiêu chí đánh giá thống nhất |

Một số nguồn mới làm bối cảnh cho phần benchmark gồm CSConDa cho hội thoại hỗ trợ khách hàng tiếng Việt, VLegal-Bench cho năng lực pháp lý tiếng Việt, ViRanker cho reranking tiếng Việt và MIRAGE-Bench cho đánh giá RAG đa ngôn ngữ. Điều này làm cho phát biểu "hoàn toàn thiếu benchmark" không còn chính xác; khoảng trống hợp lý hơn là **thiếu benchmark RAG tiếng Việt có kiểm soát theo domain cụ thể**.

#### 1.1.6 Đánh giá khả thi full-scope và chiến lược triển khai

Đánh giá cập nhật cho thấy đề tài **khả thi theo hướng full-scope nếu triển khai theo từng pha kỹ thuật có kiểm soát**, thay vì tự giới hạn ở bản rút gọn. Lý do:

- Bối cảnh thị trường phù hợp: McKinsey State of AI 2025 ghi nhận AI được dùng rộng hơn nhưng phần lớn tổ chức vẫn ở giai đoạn thử nghiệm/pilot hoặc mới bắt đầu scale, nên bài toán đưa RAG từ demo sang vận hành có kiểm soát vẫn thực tế.
- Rủi ro kỹ thuật đúng trọng tâm: OWASP Top 10 for LLM Applications 2025 tiếp tục nhấn mạnh prompt injection, sensitive information disclosure, vector/embedding weaknesses và unbounded consumption, đều liên quan trực tiếp đến RAG/LLMOps.
- Công cụ đã trưởng thành hơn nhưng phức tạp hơn: Langfuse v3 self-host không còn là một container đơn giản dựa trên Postgres; cần web, worker, Postgres, ClickHouse, Redis/Valkey và S3/Blob store. Phần observability vì vậy nên được đưa vào scope chính nhưng triển khai đúng kiến trúc, có thể bắt đầu bằng local Compose rồi nâng lên instance ổn định.
- Model landscape thay đổi nhanh: GPT-5.5/GPT-5.4-mini, Claude Opus 4.8/Sonnet 4.6, Gemini 3/2.5, Llama 4, Qwen3 và Gemma 4 làm cho việc hard-code một model duy nhất không còn phù hợp. Cách hợp lý là dùng model gateway, benchmark theo snapshot tại thời điểm thực nghiệm và giữ cấu hình có thể thay thế provider.
- Coding effort có thể giảm đáng kể nhờ AI-assisted development, nhưng effort nghiên cứu vẫn nằm ở thiết kế benchmark, dữ liệu golden set, phân tích lỗi, kiểm định quality gate và diễn giải kết quả. Vì vậy đề tài nên mở rộng scope kỹ thuật nhưng vẫn giữ thước đo thành công bằng số liệu định lượng.

**Kết luận điều chỉnh:** khóa luận cam kết triển khai đầy đủ 9 module: DataOps/RAGOps, Retrieval Experiment, RAG Runtime, PromptOps, Evaluation Engine, CI/CD Quality Gate, Observability/Cost Monitoring, Model Gateway/Provider Routing và Feedback Loop/Continuous Improvement. Hệ thống không cần đạt chuẩn HA/enterprise thật, nhưng phải đủ production-like để đo chất lượng, chi phí, độ trễ, lỗi retrieval, hallucination, regression và tác động của từng thay đổi.

---

### 1.2 Xác định vấn đề nghiên cứu

#### Vấn đề trung tâm

Đa số hệ thống RAG tiếng Việt hiện nay chỉ dừng ở mức demo:

- [Đang có] Chatbot "hoạt động" trên bộ tài liệu nhỏ
- [Thiếu] Không biết câu trả lời có chính xác không
- [Thiếu] Không biết retrieval có lấy đúng tài liệu không
- [Thiếu] Không phát hiện được hallucination
- [Thiếu] Sửa prompt không kiểm soát → chất lượng giảm mà không hay
- [Thiếu] Không theo dõi được latency, chi phí, lỗi
- [Thiếu] Không có quy trình kiểm thử trước khi deploy
- [Thiếu] Không biết phiên bản nào của prompt/model/data tạo ra câu trả lời cụ thể
- [Thiếu] Khi dữ liệu thay đổi, không biết câu trả lời nào bị ảnh hưởng

#### Câu hỏi nghiên cứu tổng quát

> **Làm thế nào để xây dựng một pipeline LLMOps toàn diện giúp hệ thống RAG tiếng Việt có thể được đánh giá, giám sát, kiểm thử, tối ưu và cải tiến một cách có hệ thống trong môi trường gần production?**

---

### 1.3 Mục tiêu khóa luận

#### Mục tiêu chính

Xây dựng một **nền tảng LLMOps/RAGOps full-scope** cho hệ thống RAG tiếng Việt, đủ để chứng minh toàn bộ quy trình vận hành có kiểm soát thay vì chỉ xây chatbot demo. Hệ thống cho phép:

1. **Ingest, làm sạch và version hóa** tài liệu với kiểm soát chất lượng dữ liệu cơ bản
2. **Thực nghiệm và so sánh** nhiều chiến lược chunking, embedding, sparse/dense/hybrid retrieval và reranking
3. **Quản lý prompt lifecycle** bằng versioning, prompt registry, offline comparison và simulated/controlled A/B testing
4. **Định tuyến model/provider** qua model gateway, có fallback, budget, rate limit và policy chọn model theo độ khó câu hỏi
5. **Đánh giá tự động 4 tầng** (retrieval → context → generation → operations) bằng golden set tiếng Việt đủ lớn
6. **Kiểm thử trước triển khai** bằng CI/CD quality gate để block deploy khi regression
7. **Giám sát sau triển khai** bằng tracing, metrics, dashboard vận hành 12+ panel và cost/latency tracking
8. **Thu thập feedback và cải tiến liên tục** bằng nhãn lỗi, human review queue và vòng lặp cập nhật prompt/data/retrieval
9. **Phát hiện lỗi chính** gồm retrieval failure, hallucination, prompt regression, stale data, high latency, cost spike, prompt injection và provider degradation

#### Mục tiêu cụ thể

| STT | Mục tiêu | Kết quả đầu ra |
|---|---|---|
| 1 | Xây dựng hệ thống RAG hỏi đáp tiếng Việt | Web/API demo, pipeline xử lý tài liệu |
| 2 | Thiết kế DataOps/RAGOps pipeline | Data validation, versioning, chunk metadata, index freshness |
| 3 | Xây dựng Retrieval Experiment Layer | So sánh 15+ cấu hình chunking/retrieval/reranking |
| 4 | Triển khai PromptOps đầy đủ | Prompt registry, 6+ prompt variants, prompt diff, offline comparison, simulated A/B |
| 5 | Xây dựng Evaluation Engine | RAGAS/DeepEval/custom metrics, LLM-as-a-Judge, human review sampling |
| 6 | Xây dựng CI/CD Quality Gate | GitHub Actions pass/fail/block deploy, regression report, rollback policy |
| 7 | Xây dựng Observability + Cost Dashboard | Tracing, latency, token/cost, retrieval hit rate, error labels, drift/freshness |
| 8 | Xây dựng Model Gateway | LiteLLM/provider adapter, fallback, budget, rate limit, routing theo policy |
| 9 | Xây dựng Feedback Loop | User feedback, error clustering, issue queue, continuous improvement experiment |

---

### 1.4 Phạm vi nghiên cứu

#### Trong phạm vi (IN SCOPE)

- Hệ thống RAG hỏi đáp tài liệu **tiếng Việt** trên **một domain cụ thể**
- Pipeline LLMOps/RAGOps đầy đủ 9 module: Data/RAGOps, Retrieval Experiment, RAG Runtime, PromptOps, Evaluation, Quality Gate, Observability/Cost, Model Gateway và Feedback Loop
- So sánh có kiểm soát nhiều cấu hình RAG bằng thực nghiệm định lượng
- Deploy bằng Docker/Docker Compose đầy đủ; có thể bổ sung K3s/Kubernetes local nếu cần minh họa vận hành nâng cao
- Sử dụng 1-2 model runtime chính, 1-2 model judge/evaluator và 2-4 model/provider phụ để so sánh chi phí/chất lượng
- Self-host hoặc cấu hình thực tế cho Langfuse v3, Prometheus/Grafana, Qdrant, Redis/Valkey, PostgreSQL, ClickHouse và MinIO/S3
- A/B testing ở mức offline/simulated và có thiết kế controlled rollout nếu có traffic thật

#### Ngoài phạm vi (OUT OF SCOPE)

| Không làm | Lý do |
|---|---|
| Fine-tuning LLM lớn (full fine-tune) | Tốn GPU, ngoài trọng tâm LLMOps |
| Huấn luyện foundation model từ đầu | Không phù hợp tài nguyên khóa luận |
| HA production thật với SLA, autoscaling và disaster recovery | Cần hạ tầng doanh nghiệp, không phải mục tiêu nghiên cứu chính |
| Bảo mật cấp enterprise hoàn chỉnh (SSO, RBAC đa tenant, audit pháp lý đầy đủ) | Có thể thiết kế nhưng không bắt buộc chứng minh trong demo |
| Mobile app | Tập trung vào backend + pipeline |
| Cam kết traffic người dùng thật | Nếu không có người dùng thật, dùng log giả lập và human review sampling |

#### Dữ liệu đề xuất

Chọn **một domain chính** và có thể thêm domain phụ để demo khả năng tổng quát:

| Domain | Ưu điểm | Nguồn dữ liệu |
|---|---|---|
| **Quy chế đào tạo đại học** (Khuyến nghị) | Câu trả lời cần căn cứ chính xác, nhiều câu hỏi thực tế, dễ tạo test set | Quy chế đào tạo, FAQ sinh viên, văn bản học vụ |
| Văn bản pháp luật | Cần độ chính xác cao, phù hợp đánh giá hallucination | Luật, nghị định, thông tư |
| Tài liệu công ty giả lập | Gần production doanh nghiệp nhất | Chính sách HR, quy trình, onboarding |
| Hướng dẫn kỹ thuật | Có tính ứng dụng cao | Tài liệu API, sổ tay kỹ thuật |

> [!TIP]
> **Khuyến nghị**: Chọn "Quy chế đào tạo + FAQ sinh viên" làm domain chính. Đây là domain quen thuộc, dễ tạo bộ test câu hỏi, và câu trả lời cần căn cứ rõ ràng — rất phù hợp để đánh giá groundedness và phát hiện hallucination.

---

### 1.5 Đóng góp của đề tài

| STT | Đóng góp | Loại |
|---|---|---|
| 1 | Kiến trúc LLMOps/RAGOps full-scope 9 module cho hệ thống RAG tiếng Việt production-like | Thiết kế hệ thống |
| 2 | Framework đánh giá 4 tầng với bộ metric toàn diện | Phương pháp đánh giá |
| 3 | Kết quả thực nghiệm so sánh 15+ cấu hình RAG trên dữ liệu tiếng Việt | Thực nghiệm |
| 4 | CI/CD quality gate cho ứng dụng LLM/RAG | Công cụ vận hành |
| 5 | Bộ dữ liệu benchmark QA tiếng Việt cho domain được chọn | Dataset |
| 6 | Hệ thống demo production-like có thể tái sử dụng | Sản phẩm kỹ thuật |

---

## PHẦN II — CƠ SỞ LÝ THUYẾT

### 2.1 Large Language Models (LLM)

#### 2.1.1 Kiến trúc Transformer

LLM hiện đại dựa trên kiến trúc Transformer (Vaswani et al., 2017) với cơ chế self-attention cho phép model nắm bắt quan hệ giữa các token trong chuỗi đầu vào. Model landscape thay đổi rất nhanh, vì vậy khóa luận nên ghi model theo **phiên bản kiểm chứng tại thời điểm thực nghiệm** thay vì hard-code một model duy nhất trong toàn bộ báo cáo. Các nhóm model đáng chú ý tại thời điểm cập nhật:

| Model | Nhà phát triển | Loại | Đặc điểm |
|---|---|---|---|
| GPT-5.5, GPT-5.4, GPT-5.4 mini, GPT-5 mini | OpenAI | Proprietary API | Phù hợp runtime/judge; GPT-5.4 mini là lựa chọn cost-aware cho workload lớn |
| Gemini 3 Flash Preview, Gemini 2.5 Flash/Pro | Google | Proprietary API | Context dài, multimodal; cần phân biệt stable, preview, latest và experimental |
| Claude Opus 4.8, Claude Sonnet 4.6, Claude Haiku 4.5 | Anthropic | Proprietary API | Mạnh cho reasoning/judge; model ID là snapshot/pinned theo docs mới |
| Llama 4 Scout/Maverick | Meta | Open-weight | Có thể self-host nếu đủ GPU; phù hợp so sánh open-weight ở mức giới hạn |
| Qwen3 / Qwen3-2507 | Alibaba/Qwen | Open-weight | Hỗ trợ tiếng Việt, nhiều kích thước, Apache 2.0; phù hợp local/API-compatible endpoint |
| Gemma 4 | Google DeepMind | Open-weight | Nhỏ/hiệu quả, Apache 2.0, phù hợp edge/local demo |

> **Khuyến nghị cho khóa luận:** dùng GPT-5.4 mini hoặc GPT-5 mini làm runtime mặc định, GPT-5.5 hoặc Claude Sonnet/Opus làm judge khi cần, BGE-M3 làm embedding chính, và thêm một open-weight model như Qwen3/Gemma 4/Llama 4 để so sánh định tính nếu tài nguyên cho phép.

#### 2.1.2 Prompting

Prompt là **giao diện chính** giữa con người và LLM. Trong hệ thống RAG, prompt bao gồm:

```
[System Instruction]
Bạn là trợ lý hỏi đáp tài liệu. Chỉ trả lời dựa trên context được cung cấp.
Nếu không tìm thấy thông tin, hãy nói rõ.

[Context]
{retrieved_chunks}

[User Question]
{user_query}

[Output Format]
Trả lời ngắn gọn, chính xác. Trích dẫn nguồn tài liệu.
```

Prompt engineering trong RAG khác với prompting thông thường ở chỗ phải **kiểm soát sự tương tác** giữa system instruction, retrieved context, và user query — đây là nơi dễ xảy ra hallucination và prompt injection nhất.

#### 2.1.3 Các vấn đề khi đưa LLM vào production

| Vấn đề | Mô tả | Hệ quả |
|---|---|---|
| **Hallucination** | LLM sinh thông tin sai nhưng nghe hợp lý | Người dùng tin vào thông tin sai |
| **Non-determinism** | Cùng input, output khác nhau giữa các lần gọi | Khó tái lập, khó test |
| **Prompt sensitivity** | Thay đổi nhỏ trong prompt → thay đổi lớn trong output | Prompt regression |
| **Token cost** | Chi phí tỷ lệ thuận với input+output tokens | Budget vượt kiểm soát |
| **Latency** | Thời gian phản hồi phụ thuộc vào context length và model | UX kém |
| **Safety risks** | Prompt injection, PII leakage, harmful content | Rủi ro pháp lý |

---

### 2.2 Retrieval-Augmented Generation (RAG)

#### 2.2.1 Kiến trúc RAG cơ bản

```
User Query → Query Processing → Retrieval → Context Assembly → LLM Generation → Response
```

**Các bước chi tiết:**

1. **Query Processing**: Tiền xử lý câu hỏi (sửa lỗi chính tả, mở rộng query, query rewriting)
2. **Embedding**: Chuyển query thành vector representation
3. **Retrieval**: Tìm top-k đoạn tài liệu gần nhất trong vector database
4. **Reranking** (tùy chọn): Sắp xếp lại kết quả retrieval bằng cross-encoder
5. **Context Assembly**: Ghép các đoạn tài liệu vào prompt template
6. **LLM Generation**: LLM sinh câu trả lời dựa trên context
7. **Post-processing**: Trích xuất citation, format output

#### 2.2.2 Chunking — chia tài liệu

Chunking là **bước quan trọng nhất** trong pipeline RAG, quyết định chất lượng retrieval. Các chiến lược phổ biến:

| Chiến lược | Cách hoạt động | Ưu điểm | Nhược điểm |
|---|---|---|---|
| **Fixed-size** | Chia theo số token cố định (256, 512, 1024) | Đơn giản, dự đoán được | Có thể cắt giữa câu/ý |
| **Recursive** | Chia theo separator (paragraph → sentence → character) | Tôn trọng cấu trúc văn bản | Chunk size không đồng đều |
| **Semantic** | Chia dựa trên sự thay đổi chủ đề (embedding similarity) | Chunk coherent nhất | Tốn computation |
| **Sentence-based** | Mỗi chunk là N câu liên tiếp | Đơn vị ngữ nghĩa tự nhiên | Chunk nhỏ, cần top-k lớn |
| **Document-structure** | Chia theo heading, section, Điều/Khoản | Giữ cấu trúc pháp lý | Cần parser riêng |

**Overlap**: Mỗi chunk chồng lấn một phần với chunk liền kề (thường 10-20%) để tránh mất thông tin ở ranh giới.

#### 2.2.3 Embedding Models

| Model | Chiều | Đa ngôn ngữ | Tiếng Việt | Kích thước |
|---|---|---|---|---|
| `multilingual-e5-large` | 1024 | ✅ | Khá | 560M |
| `bge-m3` | 1024 | ✅ | Tốt | 568M |
| `text-embedding-3-small` (OpenAI) | 1536 | ✅ | Khá | API |
| `text-embedding-3-large` (OpenAI) | 3072 | ✅ | Tốt | API |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | ✅ | Trung bình | 118M |

#### 2.2.4 Retrieval Strategies

| Chiến lược | Cách hoạt động | Ưu điểm | Nhược điểm |
|---|---|---|---|
| **Dense retrieval** | Cosine similarity trên embedding vectors | Nắm bắt ngữ nghĩa | Tốn memory, có thể miss keyword match |
| **Sparse retrieval (BM25)** | Term frequency + inverse document frequency | Nhanh, chính xác với keyword | Không hiểu ngữ nghĩa |
| **Hybrid** | Kết hợp dense + BM25 bằng RRF (Reciprocal Rank Fusion) | Tốt nhất cả hai | Phức tạp hơn, cần tuning |
| **Reranking** | Cross-encoder chấm điểm lại top-k | Cải thiện precision đáng kể | Tăng latency |

#### 2.2.5 Vector Database

| Vector DB | Loại | Ưu điểm | Phù hợp |
|---|---|---|---|
| **Qdrant** | Standalone server | Production-ready, filtering, versioning | Production-like demo |
| **FAISS** | Library | Nhanh, nhẹ, dễ dùng | Prototype, thí nghiệm |
| **Chroma** | Embedded | Đơn giản nhất | Prototype nhỏ |
| **Weaviate** | Standalone server | GraphQL API, multi-modal | Enterprise |
| **Milvus** | Distributed | Scale lớn, distributed | Large-scale |

---

### 2.3 MLOps → LLMOps: Sự tiến hóa

#### 2.3.1 MLOps là gì?

MLOps (Machine Learning Operations) là tập hợp thực hành để tự động hóa và chuẩn hóa workflow ML: từ data preparation, model training, evaluation, deployment đến monitoring.

Các nguyên tắc cốt lõi:
- **Reproducibility**: Có thể tái tạo kết quả
- **Automation**: Tự động hóa pipeline
- **Continuous X**: CI/CD/CT (Continuous Training)
- **Monitoring**: Phát hiện model drift, data drift
- **Version control**: Data, model, code đều được version hóa

#### 2.3.2 LLMOps mở rộng MLOps như thế nào?

LLMOps giữ nguyên tinh thần MLOps nhưng **thêm các thành phần mới**:

```
MLOps components:
  ✅ Data versioning
  ✅ Model registry
  ✅ Experiment tracking
  ✅ CI/CD pipeline
  ✅ Monitoring & alerting
  ✅ A/B testing

LLMOps additions:
  🆕 Prompt management & versioning
  🆕 LLM-as-a-Judge evaluation
  🆕 Token cost monitoring & optimization
  🆕 Hallucination detection
  🆕 Guardrails (prompt injection, PII)
  🆕 Retrieval quality monitoring (for RAG)
  🆕 Context window management
  🆕 Model routing & fallback
  🆕 Semantic caching
  🆕 Non-deterministic output handling

RAGOps additions:
  🆕 Data ingestion pipeline management
  🆕 Chunking strategy management
  🆕 Vector index versioning
  🆕 Data freshness monitoring
  🆕 Retrieval-generation correlation analysis
```

#### 2.3.3 LLMOps Lifecycle

![Hình 2.1. Vòng đời LLMOps cho hệ thống RAG](figures/fig_2_1_llmops_lifecycle.png)

---

### 2.4 Evaluation cho LLM/RAG

#### 2.4.1 Tại sao evaluation cho LLM khó?

- **Output phi cấu trúc**: Câu trả lời bằng ngôn ngữ tự nhiên, không có "đáp án đúng duy nhất"
- **Non-deterministic**: Cùng input có thể cho output khác nhau
- **Chất lượng đa chiều**: Cần đánh giá correctness, relevance, faithfulness, completeness, safety cùng lúc
- **Ground truth hiếm**: Không phải lúc nào cũng có đáp án chuẩn để so sánh
- **Scale**: Không thể đánh giá thủ công hàng nghìn câu hỏi

#### 2.4.2 Các phương pháp evaluation

| Phương pháp | Mô tả | Ưu điểm | Nhược điểm |
|---|---|---|---|
| **Code-based metrics** | BLEU, ROUGE, exact match, F1 | Nhanh, deterministic | Không nắm bắt ngữ nghĩa |
| **LLM-as-a-Judge** | Dùng LLM đánh giá output của LLM khác | Gần với đánh giá con người | Tốn chi phí, có bias |
| **Semantic similarity** | Cosine similarity giữa answer và ground truth embeddings | Linh hoạt hơn exact match | Không phân biệt sai vs khác cách diễn đạt |
| **Human evaluation** | Người đánh giá trực tiếp | Chính xác nhất | Tốn thời gian, không scale |
| **Composite frameworks** | RAGAS, DeepEval — kết hợp nhiều metric | Toàn diện | Cần thiết lập phức tạp |

#### 2.4.3 RAGAS Framework

RAGAS (Retrieval-Augmented Generation Assessment) cung cấp bộ metric chuẩn cho RAG:

| Metric | Đo cái gì | Cần gì |
|---|---|---|
| **Faithfulness** | Câu trả lời có trung thành với context không? | question, context, answer |
| **Answer Relevancy** | Câu trả lời có liên quan đến câu hỏi không? | question, answer |
| **Context Precision** | Các chunk liên quan có được xếp hạng cao không? | question, context, ground_truth |
| **Context Recall** | Context có chứa đủ thông tin để trả lời không? | context, ground_truth |

#### 2.4.4 DeepEval Framework

DeepEval mở rộng thêm các metric:

| Metric | Đo cái gì |
|---|---|
| **Hallucination** | Mức độ thông tin bịa đặt ngoài context |
| **Groundedness** | Mỗi claim trong answer có được support bởi context không? |
| **Bias** | Câu trả lời có thiên vị không? |
| **Toxicity** | Câu trả lời có nội dung độc hại không? |
| **Answer Correctness** | Câu trả lời có đúng so với ground truth không? |

---

### 2.5 Observability cho LLM

#### 2.5.1 Định nghĩa

Observability cho LLM là khả năng **hiểu trạng thái nội bộ** của hệ thống thông qua các tín hiệu bên ngoài: logs, traces, metrics. Khác với monitoring (chỉ theo dõi metric biết trước), observability cho phép **khám phá lỗi chưa biết**.

#### 2.5.2 Ba trụ cột

| Trụ cột | Trong LLM/RAG |
|---|---|
| **Logs** | Prompt, context, response, model version, token count cho mỗi request |
| **Traces** | Phân tách latency theo từng stage: retrieval, reranking, generation |
| **Metrics** | Aggregated: throughput, latency p50/p95/p99, cost, error rate |

#### 2.5.3 Các công cụ hiện có

| Tool | Loại | Đặc điểm |
|---|---|---|
| **Langfuse** | Open-source/SaaS, self-host tùy cấu hình | Tracing, prompt management, evaluation, cost tracking; self-host v3 cần thêm ClickHouse, Redis/Valkey, S3/Blob store |
| **LangSmith** | SaaS (LangChain) | Tích hợp chặt với LangChain, playground |
| **OpenTelemetry** | Standard | Protocol chuẩn, tích hợp được nhiều backend |
| **Arize Phoenix** | Open-source | Embedding analysis, LLM tracing |
| **Weights & Biases** | SaaS | Experiment tracking, model comparison |

---

## PHẦN III — KIẾN TRÚC HỆ THỐNG CHI TIẾT

### 3.1 Tổng quan kiến trúc

Kiến trúc full-scope gồm **9 module liên kết thành một vòng đời LLMOps/RAGOps hoàn chỉnh**. Thay vì xem một số phần là mở rộng sau này, toàn bộ các năng lực chính đều nằm trong scope khóa luận và được triển khai theo từng pha để kiểm soát rủi ro:

- **Data/RAGOps:** ingest, clean, chunk, embed, index, versioning và freshness.
- **Retrieval Experiment:** dense/sparse/hybrid retrieval, reranking, chunking ablation và benchmark.
- **RAG Runtime:** API hỏi đáp, citation, refusal, streaming và structured response.
- **PromptOps:** prompt registry, versioning, diff, offline comparison và simulated A/B.
- **Model Gateway:** multi-provider routing, fallback, budget, rate limit và policy theo độ khó.
- **Evaluation Engine:** automatic metrics, LLM-as-a-Judge, human review sampling và error taxonomy.
- **CI/CD Quality Gate:** regression test cho prompt/model/data/code trước khi deploy.
- **Observability/Cost:** trace, token/cost, latency, retrieval hit rate, hallucination và drift/freshness.
- **Feedback Loop:** user feedback, error clustering, improvement queue và continuous evaluation.

![Hình 3.1. Kiến trúc tổng thể LLMOps/RAGOps full-scope 9 module](figures/fig_3_1_llmops_ragops_full_architecture.png)

Các mục 3.2-3.10 dưới đây mô tả chi tiết 9 module. Thứ tự triển khai nên đi từ dữ liệu và retrieval đến runtime, evaluation, quality gate, observability, model gateway và feedback loop; nhưng tiêu chí hoàn tất là hệ thống đủ module, đủ thực nghiệm và đủ số liệu để bảo vệ.

---

### 3.2 Module 1 — DataOps / RAGOps Layer

#### Mục đích
Quản lý toàn bộ vòng đời dữ liệu: từ tài liệu gốc → cleaning → chunking → embedding → vector index, với version hóa và kiểm soát chất lượng.

#### Quy trình chi tiết

![Hình 3.2. Quy trình DataOps/RAGOps cho tài liệu tiếng Việt](figures/fig_3_2_data_ragops_pipeline.png)

#### Metrics data quality

| Metric | Cách đo | Ngưỡng chấp nhận |
|---|---|---|
| Duplicate ratio | Số chunk trùng / tổng chunk | < 5% |
| OCR noise score | Regex pattern matching (ký tự lạ, encoding lỗi) | < 2% characters |
| Missing metadata rate | Chunk thiếu source/title/date | < 10% |
| Avg chunk length | Trung bình token per chunk | 200-800 tokens |
| Chunk length std | Độ lệch chuẩn | Tùy chiến lược |
| PII detected count | Số PII entries phát hiện | 0 sau masking |
| Language detection | % chunk đúng ngôn ngữ (Vietnamese) | > 98% |

---

### 3.3 Module 2 — Retrieval Experiment Layer

#### Mục đích
Cho phép thực nghiệm và so sánh nhiều cấu hình retrieval khác nhau một cách có hệ thống, reproducible.

#### Các biến thể cần thí nghiệm

##### Embedding Models

| ID | Model | Chiều | Loại |
|---|---|---|---|
| E1 | `multilingual-e5-large` | 1024 | Open-source |
| E2 | `bge-m3` | 1024 | Open-source |
| E3 | `text-embedding-3-small` | 1536 | OpenAI API |
| E4 | `text-embedding-3-large` | 3072 | OpenAI API |
| E5 | Vietnamese-specific model (nếu có) | varies | Domain-specific |

##### Chunking Configurations

| ID | Chunk size | Overlap | Strategy |
|---|---|---|---|
| C1 | 256 tokens | 0% | Fixed-size |
| C2 | 512 tokens | 0% | Fixed-size |
| C3 | 1024 tokens | 0% | Fixed-size |
| C4 | 512 tokens | 10% | Fixed-size |
| C5 | 512 tokens | 20% | Fixed-size |
| C6 | Dynamic | 0% | Recursive |
| C7 | Dynamic | 10% | Semantic |
| C8 | Dynamic | 0% | Document-structure |

##### Retrieval Strategies

| ID | Retriever | Reranker | Top-k |
|---|---|---|---|
| R1 | Dense only | Không | 5 |
| R2 | BM25 only | Không | 5 |
| R3 | Hybrid (RRF) | Không | 5 |
| R4 | Hybrid (RRF) | Có (cross-encoder) | 5 |
| R5 | Hybrid (RRF) | Có | 3 |
| R6 | Hybrid (RRF) | Có | 10 |
| R7 | Dense only | Có | 5 |

#### Experiment Configuration File

```yaml
# experiment_config.yaml
experiment:
  name: "retrieval_ablation_v1"
  dataset_version: "v1.2"
  
  embedding_models:
    - id: E1
      name: multilingual-e5-large
      dimension: 1024
    - id: E2
      name: bge-m3
      dimension: 1024
      
  chunking:
    - id: C2
      strategy: fixed
      chunk_size: 512
      overlap: 0
    - id: C4
      strategy: fixed
      chunk_size: 512
      overlap: 0.1
      
  retrieval:
    - id: R3
      type: hybrid
      dense_weight: 0.7
      sparse_weight: 0.3
      reranker: false
      top_k: 5
    - id: R4
      type: hybrid
      dense_weight: 0.7
      sparse_weight: 0.3
      reranker: true
      reranker_model: cross-encoder/ms-marco-MiniLM-L-12-v2
      top_k: 5
      
  metrics:
    - recall_at_k
    - precision_at_k
    - mrr
    - ndcg
    - context_precision
    - context_recall
    - faithfulness
    - answer_relevance
    - latency
    - cost_per_request
```

#### Retrieval Metrics chi tiết

| Metric | Công thức ý nghĩa | Đo cái gì |
|---|---|---|
| **Recall@k** | (Số doc liên quan trong top-k) / (Tổng doc liên quan) | Khả năng tìm đủ tài liệu |
| **Precision@k** | (Số doc liên quan trong top-k) / k | Tỷ lệ tài liệu hữu ích |
| **MRR** | 1 / (vị trí doc liên quan đầu tiên) | Tài liệu đúng có ở đầu không |
| **nDCG** | Discounted cumulative gain, normalized | Chất lượng ranking tổng thể |
| **Context Precision** | RAGAS metric | Top chunks có liên quan hơn bottom chunks không |
| **Context Recall** | RAGAS metric | Context có chứa đủ info để trả lời không |

---

### 3.4 Module 3 — RAG Runtime + Model Gateway

#### 3.4.1 RAG Runtime

Pipeline xử lý mỗi request:

![Hình 3.3. Luồng xử lý RAG runtime từ câu hỏi đến câu trả lời có citation](figures/fig_3_3_rag_runtime_flow.png)

#### 3.4.2 Model Gateway

Model Gateway quản lý việc gọi nhiều LLM providers và chọn model phù hợp:

![Hình 3.4. Cơ chế Model Gateway và routing theo độ phức tạp truy vấn](figures/fig_3_4_model_gateway_routing.png)

```python
# Pseudocode cho Model Gateway
class ModelGateway:
    models = {
        "tier_1_cheap": {
            "provider": "openai",
            "model": "gpt-5-mini",
            "cost_policy": "low_latency_low_cost",
            "max_latency_target": 3000  # ms
        },
        "tier_2_balanced": {
            "provider": "openai",
            "model": "gpt-5.4-mini",
            "cost_policy": "balanced_quality_cost",
            "max_latency_target": 5000
        },
        "tier_3_powerful": {
            "provider": "openai_or_anthropic",
            "model": "gpt-5.5_or_claude-sonnet-4-6",
            "cost_policy": "judge_or_complex_reasoning_only",
            "max_latency_target": 10000
        }
    }
    
    def route(self, query, context):
        complexity = self.classify_complexity(query, context)
        if complexity == "simple":
            return "tier_1_cheap"
        elif complexity == "moderate":
            return "tier_2_balanced"
        else:
            return "tier_3_powerful"
    
    def fallback(self, current_tier, response):
        if response.confidence < 0.6:
            return self.next_tier(current_tier)
        return None
```

**Routing criteria:**

| Tiêu chí | Simple → Cheap model | Complex → Powerful model |
|---|---|---|
| Query length | < 20 tokens | > 50 tokens |
| Query type | Factoid, yes/no | Reasoning, multi-hop |
| Context needed | 1-2 chunks | 5+ chunks |
| Domain | FAQ, basic info | Legal analysis, policy comparison |
| Keywords | "là gì", "ở đâu", "bao nhiêu" | "so sánh", "phân tích", "giải thích tại sao" |

**Fallback strategy:**
1. Gọi model tier 1
2. Nếu confidence thấp (<0.6) hoặc hallucination detected → escalate lên tier 2
3. Nếu vẫn thất bại → escalate lên tier 3
4. Log mọi escalation để phân tích pattern

---

### 3.5 Module 4 — PromptOps

#### Mục đích
Quản lý prompt như một **artifact quan trọng** — có version, test, offline comparison/simulated A/B testing và khả năng block deploy khi regression — thay vì sửa prompt ad-hoc.

#### Prompt Registry Schema

```json
{
  "prompt_id": "qa_main",
  "version": "v3.2",
  "created_at": "2026-06-01T10:00:00Z",
  "created_by": "researcher_a",
  "status": "active",  // active | staging | archived | deprecated
  "template": "...",
  "variables": ["context", "question"],
  "description": "Prompt chính cho QA với instruction từ chối",
  "tags": ["production", "qa", "refusal"],
  "eval_results": {
    "faithfulness": 0.89,
    "answer_relevance": 0.85,
    "hallucination_rate": 0.03,
    "token_usage_avg": 1250,
    "latency_avg_ms": 3200,
    "test_set_version": "test_v2.1"
  },
  "parent_version": "v3.1",
  "changelog": "Thêm instruction từ chối khi context không đủ"
}
```

#### 4-6 Prompt Variants để thực nghiệm

##### P0 — Baseline (đơn giản nhất)
```
Dựa vào thông tin sau đây, hãy trả lời câu hỏi.

Thông tin:
{context}

Câu hỏi: {question}
Trả lời:
```

##### P1 — Context-grounded (bắt buộc bám context)
```
Bạn là trợ lý hỏi đáp tài liệu. Bạn CHỈ ĐƯỢC trả lời dựa trên thông tin 
trong phần "Tài liệu tham khảo" bên dưới. KHÔNG ĐƯỢC sử dụng kiến thức 
ngoài tài liệu.

Tài liệu tham khảo:
{context}

Câu hỏi của người dùng: {question}

Hãy trả lời chính xác dựa trên tài liệu. Nếu tài liệu không chứa đủ 
thông tin, hãy nói rõ.
```

##### P2 — Citation required (bắt buộc trích dẫn)
```
Bạn là trợ lý hỏi đáp tài liệu. Trả lời câu hỏi dựa trên tài liệu 
được cung cấp.

Quy tắc:
1. CHỈ trả lời dựa trên tài liệu.
2. MỖI ý trong câu trả lời PHẢI kèm trích dẫn nguồn [Nguồn: tên tài liệu].
3. Nếu không có thông tin, nói rõ "Không tìm thấy trong tài liệu".

Tài liệu:
{context}

Câu hỏi: {question}
Trả lời (kèm trích dẫn):
```

##### P3 — Refusal instruction (biết từ chối)
```
Bạn là trợ lý hỏi đáp chính xác. Nhiệm vụ của bạn là trả lời câu hỏi 
CHỈ DỰA TRÊN tài liệu được cung cấp.

Quy tắc quan trọng:
- Nếu tài liệu CHỨA thông tin liên quan → trả lời chính xác, kèm trích dẫn
- Nếu tài liệu KHÔNG CHỨA thông tin → trả lời: "Xin lỗi, tôi không tìm 
  thấy thông tin này trong tài liệu hiện có."
- TUYỆT ĐỐI KHÔNG bịa đặt hoặc suy đoán thông tin ngoài tài liệu

Tài liệu tham khảo:
{context}

Câu hỏi: {question}
```

##### P4 — Chain-of-Verification (CoVe) (kiểm chứng nội bộ)
```
Bạn là trợ lý hỏi đáp tài liệu. Thực hiện theo 3 bước:

Bước 1 - Soạn câu trả lời dựa trên tài liệu:
[Soạn bản nháp câu trả lời]

Bước 2 - Kiểm tra từng claim:
Với mỗi claim trong câu trả lời, kiểm tra:
- Claim này có trong tài liệu không? [CÓ/KHÔNG]
- Nếu CÓ, trích dẫn đoạn tài liệu tương ứng
- Nếu KHÔNG, loại bỏ claim này

Bước 3 - Câu trả lời cuối cùng:
[Chỉ xuất phần này cho người dùng]

Tài liệu:
{context}

Câu hỏi: {question}

Thực hiện 3 bước trên và CHỈ xuất kết quả của Bước 3:
```

##### P5 — Token-optimized (tối ưu chi phí)
```
Context: {context}
Q: {question}
A (concise, cite sources):
```

#### Offline Prompt Comparison / Simulated A/B Framework

```yaml
offline_prompt_comparison:
  name: "p3_vs_p4_comparison"
  variants:
    - id: "control"
      prompt_version: "p3"
    - id: "treatment"
      prompt_version: "p4"
  test_set: "data/test_sets/golden_v1.json"
  sample_size: 100
  metrics:
    primary: "faithfulness"
    secondary:
      - "answer_relevance"
      - "hallucination_rate"
      - "token_usage"
      - "latency"
  decision:
    promote_if: "primary improves and no critical metric regresses"
    block_if: "faithfulness_drop > 0.03 or hallucination_rate increases"
```

---

### 3.6 Module 5 — Evaluation Engine (4 tầng)

#### Tổng quan kiến trúc evaluation

![Hình 3.5. Evaluation Engine 4 tầng cho hệ thống RAG](figures/fig_3_5_evaluation_layers.png)

#### Tầng 1 — Retrieval Evaluation

**Mục đích**: Đánh giá retriever có lấy được đúng tài liệu không.

| Metric | Công thức | Ý nghĩa | Target |
|---|---|---|---|
| **Recall@5** | relevant_retrieved / total_relevant | Tìm được bao nhiêu % tài liệu đúng | ≥ 0.85 |
| **Precision@5** | relevant_retrieved / k | Bao nhiêu % kết quả trả về là đúng | ≥ 0.60 |
| **MRR** | 1/rank_of_first_relevant | Tài liệu đúng đầu tiên ở vị trí nào | ≥ 0.70 |
| **nDCG@5** | DCG/IDCG | Ranking tổng thể có tốt không | ≥ 0.75 |
| **Hit Rate** | queries_with_at_least_1_relevant / total | Bao nhiêu query tìm được ít nhất 1 doc đúng | ≥ 0.85 |

**Cách tạo ground truth cho retrieval:**
1. Với mỗi câu hỏi trong test set, annotate **tài liệu/chunk nào chứa câu trả lời**
2. Đánh dấu chunk ID hoặc document ID
3. So sánh retrieved chunks vs annotated chunks

#### Tầng 2 — Context Evaluation

**Mục đích**: Đánh giá context (tập các chunks được chọn) có đủ tốt để trả lời không.

| Metric | Nguồn | Ý nghĩa | Target |
|---|---|---|---|
| **Context Precision** | RAGAS | Chunks liên quan có được xếp trước không | ≥ 0.75 |
| **Context Recall** | RAGAS | Context có chứa đủ thông tin từ ground truth không | ≥ 0.80 |
| **Context Relevance** | Custom | % chunks thực sự liên quan đến câu hỏi | ≥ 0.70 |
| **Context Utilization** | Custom | LLM sử dụng bao nhiêu % context trong câu trả lời | tracking |

#### Tầng 3 — Generation Evaluation

**Mục đích**: Đánh giá chất lượng câu trả lời do LLM sinh ra.

| Metric | Tool | Ý nghĩa | Target |
|---|---|---|---|
| **Faithfulness** | RAGAS | Câu trả lời có trung thành với context không | ≥ 0.85 |
| **Groundedness** | DeepEval | Mỗi claim có được support bởi context không | ≥ 0.85 |
| **Answer Relevance** | RAGAS | Câu trả lời có liên quan đến câu hỏi không | ≥ 0.80 |
| **Answer Correctness** | DeepEval | So với ground truth, câu trả lời đúng không | ≥ 0.75 |
| **Hallucination Rate** | DeepEval | % câu trả lời chứa thông tin ngoài context | ≤ 5% |
| **Citation Accuracy** | Custom | % trích dẫn đúng và có thể verify | ≥ 0.85 |
| **Refusal Accuracy** | Custom | Khi context không đủ, hệ thống có từ chối đúng không | ≥ 0.90 |

**LLM-as-a-Judge implementation:**

```python
judge_prompt = """
Bạn là giám khảo đánh giá chất lượng hệ thống hỏi đáp.

Cho:
- Câu hỏi: {question}
- Context (tài liệu truy xuất): {context}
- Câu trả lời của hệ thống: {answer}
- Đáp án chuẩn: {ground_truth}

Đánh giá theo thang 1-5:
1. Faithfulness: Câu trả lời có bám sát context không?
2. Relevance: Câu trả lời có liên quan đến câu hỏi không?
3. Completeness: Câu trả lời có đầy đủ không?
4. Citation quality: Trích dẫn có chính xác không?

Trả lời dạng JSON:
{{"faithfulness": X, "relevance": X, "completeness": X, 
  "citation_quality": X, "reasoning": "..."}}
"""
```

#### Tầng 4 — Production Evaluation

**Mục đích**: Đánh giá các metric vận hành thực tế.

| Metric | Cách đo | Target |
|---|---|---|
| **Avg Latency** | Trung bình thời gian phản hồi | ≤ 4s |
| **p50 Latency** | Percentile 50 | ≤ 3s |
| **p95 Latency** | Percentile 95 | ≤ 6s |
| **p99 Latency** | Percentile 99 | ≤ 10s |
| **Token/request (input)** | Trung bình input tokens | tracking |
| **Token/request (output)** | Trung bình output tokens | tracking |
| **Cost/request** | Estimated cost per request (USD) | ≤ $0.005 |
| **Throughput** | Requests per second | ≥ 5 RPS |
| **Error rate** | % request lỗi | ≤ 1% |
| **Regression rate** | % test cases pass/fail so với version trước | 0% regression |

---

### 3.7 Module 6 — CI/CD Quality Gate

#### Mục đích
Tự động chạy evaluation pipeline mỗi khi có thay đổi, và **chặn deploy nếu chất lượng không đạt ngưỡng**.

#### Triggers — khi nào quality gate chạy?

| Loại thay đổi | Trigger | Ảnh hưởng |
|---|---|---|
| Sửa prompt template | Prompt version thay đổi | Generation quality |
| Đổi embedding model | Re-embed toàn bộ | Retrieval quality |
| Đổi chunking strategy | Re-chunk + re-embed | Retrieval + generation |
| Đổi retriever/reranker | Config thay đổi | Retrieval quality |
| Đổi LLM | Model version thay đổi | Generation quality + cost |
| Cập nhật tài liệu | Data version thay đổi | Retrieval + generation |
| Thay đổi code logic | Code commit | Mọi thứ |

![Hình 3.6. Quy trình CI/CD Quality Gate cho thay đổi prompt/model/data](figures/fig_3_6_quality_gate_pipeline.png)

#### Quality Gate Configuration

```yaml
# quality_gate.yaml
version: "1.0"

gate:
  name: "rag_production_gate"
  description: "Quality gate cho RAG system trước khi deploy"
  
  # Bộ test set chuẩn
  test_set: "data/test_set_v2.1.json"
  test_set_size: 200  # số câu hỏi
  
  # Ngưỡng chất lượng
  thresholds:
    # Tầng 1: Retrieval
    retrieval:
      recall_at_5: 
        min: 0.85
        severity: "critical"  # block deploy nếu vi phạm
      mrr:
        min: 0.70
        severity: "warning"
      hit_rate:
        min: 0.85
        severity: "critical"
    
    # Tầng 2: Context  
    context:
      context_precision:
        min: 0.75
        severity: "warning"
      context_recall:
        min: 0.80
        severity: "critical"
    
    # Tầng 3: Generation
    generation:
      faithfulness:
        min: 0.85
        severity: "critical"
      answer_relevance:
        min: 0.80
        severity: "critical"
      hallucination_rate:
        max: 0.05
        severity: "critical"
      citation_accuracy:
        min: 0.85
        severity: "warning"
      refusal_accuracy:
        min: 0.90
        severity: "warning"
    
    # Tầng 4: Production
    operations:
      p95_latency_seconds:
        max: 6.0
        severity: "critical"
      cost_per_request_usd:
        max: 0.005
        severity: "warning"
      error_rate:
        max: 0.01
        severity: "critical"
    
    # Regression
    regression:
      max_quality_drop: 0.03  # không cho phép giảm >3% so với version trước
      severity: "critical"
  
  # Quyết định
  decision:
    deploy_if: "all critical thresholds pass"
    warn_if: "any warning threshold violated"
    block_if: "any critical threshold violated"
    rollback_if: "production metrics drop below thresholds within 24h"
    action_if_failed: "block deploy and keep previous prompt/model/data version active"
```

#### GitHub Actions Workflow

```yaml
# .github/workflows/quality_gate.yml
name: RAG Quality Gate

on:
  push:
    paths:
      - 'prompts/**'
      - 'config/**'
      - 'data/**'
      - 'src/**'
  pull_request:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run evaluation pipeline
        run: python scripts/run_evaluation.py --config quality_gate.yaml
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
      
      - name: Check quality gate
        run: python scripts/check_gate.py --results eval_results.json
      
      - name: Compare with previous version
        run: python scripts/regression_check.py --current eval_results.json --previous prev_results.json
      
      - name: Generate report
        run: python scripts/generate_report.py --results eval_results.json --output report.md
      
      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            const report = require('fs').readFileSync('report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              body: report
            });
      
      - name: Deploy (if gate passes)
        if: steps.check_gate.outcome == 'success'
        run: docker compose up -d --build
```

#### Quality Gate Report mẫu

```markdown
## 🔍 Quality Gate Report — Version v3.2

### Status: ✅ PASS (Deploy allowed)

| Category | Metric | Value | Threshold | Status |
|---|---|---|---|---|
| Retrieval | Recall@5 | 0.84 | ≥ 0.80 | ✅ |
| Retrieval | MRR | 0.76 | ≥ 0.70 | ✅ |
| Context | Context Recall | 0.82 | ≥ 0.80 | ✅ |
| Generation | Faithfulness | 0.89 | ≥ 0.85 | ✅ |
| Generation | Hallucination Rate | 0.03 | ≤ 0.05 | ✅ |
| Operations | p95 Latency | 5.2s | ≤ 6.0s | ✅ |
| Operations | Cost/request | $0.003 | ≤ $0.005 | ✅ |

### Regression Check
- Previous version: v3.1
- Faithfulness: 0.89 vs 0.87 (+0.02) ✅
- Answer Relevance: 0.85 vs 0.84 (+0.01) ✅
- No regression detected ✅

### Failed test cases: 3/200 (1.5%)
- Q42: Retrieval failure — context không chứa thông tin cần thiết
- Q118: Hallucination — trả lời ngoài context
- Q195: Citation sai — trích dẫn sai tài liệu
```

---

### 3.8 Module 7 — Observability & Monitoring

![Hình 3.7. Mockup dashboard observability cho hệ thống RAG tiếng Việt](figures/fig_3_7_observability_dashboard.png)

#### Log Schema

Mỗi request được log đầy đủ:

```json
{
  "trace_id": "tr_abc123def456",
  "timestamp": "2026-06-02T10:30:15.123Z",
  "session_id": "sess_xyz789",
  
  "input": {
    "query": "Sinh viên cần bao nhiêu tín chỉ để tốt nghiệp?",
    "query_tokens": 15
  },
  
  "retrieval": {
    "embedding_model": "bge-m3",
    "retriever": "hybrid",
    "reranker": "cross-encoder/ms-marco-MiniLM-L-12-v2",
    "top_k": 5,
    "retrieved_chunks": [
      {
        "chunk_id": "chunk_042",
        "document": "quy_che_dao_tao_2024.pdf",
        "page": 12,
        "score": 0.87,
        "text_preview": "Sinh viên phải tích lũy đủ 130 tín chỉ..."
      }
    ],
    "retrieval_latency_ms": 120,
    "hit_rate": true
  },
  
  "generation": {
    "prompt_version": "p3_v3.2",
    "prompt_template_hash": "sha256:abc123",
    "model": "gpt-5.4-mini",
    "model_provider": "openai",
    "temperature": 0.1,
    "input_tokens": 1500,
    "output_tokens": 320,
    "generation_latency_ms": 2800,
    "answer": "Theo Quy chế đào tạo 2024, sinh viên cần tích lũy đủ 130 tín chỉ...",
    "citations": [
      {
        "source": "quy_che_dao_tao_2024.pdf",
        "page": 12,
        "chunk_id": "chunk_042"
      }
    ]
  },
  
  "evaluation": {
    "faithfulness_score": 0.91,
    "groundedness_score": 0.88,
    "answer_relevance_score": 0.85
  },
  
  "operations": {
    "total_latency_ms": 3210,
    "estimated_cost_usd": 0.0031,
    "cache_hit": false,
    "model_tier_used": "tier_1_cheap",
    "fallback_triggered": false,
    "guardrails_triggered": false
  },
  
  "feedback": {
    "user_rating": null,
    "user_comment": null,
    "collected_at": null
  },
  
  "metadata": {
    "data_version": "v1.2",
    "index_version": "idx_v1.2_bge-m3",
    "system_version": "v3.2",
    "environment": "production"
  }
}
```

#### Dashboard Panels (full-scope)

| # | Panel | Loại | Ý nghĩa |
|---|---|---|---|
| 1 | **Request Volume** | Time series | Số request theo thời gian (giờ/ngày) |
| 2 | **Latency Distribution** | Histogram + p50/p95/p99 | Phân phối thời gian phản hồi |
| 3 | **Token Usage** | Stacked bar | Input vs output tokens theo thời gian |
| 4 | **Cost Tracker** | Cumulative line | Chi phí tích lũy, cost/request trend |
| 5 | **Faithfulness Trend** | Line chart | Faithfulness score trung bình theo ngày |
| 6 | **Retrieval Hit Rate** | Gauge | % query tìm được tài liệu liên quan |
| 7 | **Hallucination Alerts** | Alert list | Danh sách câu trả lời có hallucination score cao |
| 8 | **Top Failed Queries** | Table | Câu hỏi lỗi nhiều nhất + phân loại lỗi |
| 9 | **Prompt Version Compare** | Bar chart comparison | So sánh metric giữa các prompt versions |
| 10 | **Model Usage Distribution** | Pie chart | % request theo từng model tier |
| 11 | **Cache Hit Rate** | Gauge + trend | Tỷ lệ cache hit theo thời gian |
| 12 | **Data Freshness** | Status indicator | Thời gian từ lần index cập nhật gần nhất |

#### Error Classification

Hệ thống phân loại lỗi tự động để dễ debug:

| Loại lỗi | Cách phát hiện | Hành động |
|---|---|---|
| **Retrieval failure** | Retrieval hit rate = false, context relevance thấp | Kiểm tra query, embedding, index |
| **Context insufficient** | Context recall thấp, answer nói "không đủ thông tin" | Cải thiện chunking, mở rộng top-k |
| **Hallucination** | Faithfulness < 0.5, groundedness thấp | Sửa prompt, thêm guardrails |
| **Prompt regression** | Metric giảm sau khi đổi prompt version | Block deploy, giữ prompt version cũ |
| **Stale data** | Answer dựa trên tài liệu cũ, index freshness > 7 ngày | Re-index |
| **High latency** | p95 > threshold | Kiểm tra model, caching, context length |
| **High cost** | Cost/request > threshold | Model routing, compression, caching |
| **Refusal error** | Từ chối sai (context có thông tin nhưng vẫn từ chối) | Sửa prompt refusal instruction |

---

### 3.9 Module 8 — Cost & Latency Optimization

#### Chiến lược tối ưu ưu tiên

##### 1. Semantic Caching

```python
class SemanticCache:
    """Cache response dựa trên semantic similarity của query."""
    
    def __init__(self, redis_client, embedding_model, threshold=0.92):
        self.redis = redis_client
        self.embedder = embedding_model
        self.threshold = threshold  # cosine similarity threshold
    
    def get(self, query):
        query_embedding = self.embedder.encode(query)
        # Tìm query tương tự trong cache
        cached = self.redis.search_similar(query_embedding, top_k=1)
        if cached and cached.score >= self.threshold:
            return cached.response  # Cache HIT
        return None  # Cache MISS
    
    def set(self, query, response, ttl=3600):
        query_embedding = self.embedder.encode(query)
        self.redis.store(query_embedding, response, ttl=ttl)
```

**Kỳ vọng**: Cache hit rate 15-30% cho FAQ-style queries.

##### 2. Context Compression

Giảm số token trong context bằng cách loại bỏ thông tin không liên quan:

| Kỹ thuật | Cách hoạt động | Giảm token |
|---|---|---|
| **LongLLMLingua** | Dùng small LLM để loại bỏ tokens không quan trọng | 40-60% |
| **Extractive compression** | Chỉ giữ câu chứa keyword liên quan | 30-50% |
| **Summary compression** | Tóm tắt mỗi chunk trước khi ghép vào prompt | 50-70% |

##### 3. Top-k Tuning

| Top-k | Pros | Cons |
|---|---|---|
| k=3 | Ít token, nhanh, rẻ | Có thể miss thông tin |
| k=5 | Cân bằng | Default phổ biến |
| k=10 | Recall cao | Nhiều token, chậm, đắt |

##### 4. Model Routing (đã mô tả ở Module 3)

##### 5. Streaming Response
Trả về response token-by-token thay vì chờ toàn bộ → cải thiện **perceived latency** (thời gian chờ cảm nhận).

##### 6. Batch Embedding
Khi ingest tài liệu mới, batch các chunks lại thay vì embed từng chunk → giảm API calls.

##### 7. Embedding Caching
Cache embedding vector của các queries đã xử lý → không cần re-embed nếu query giống.

##### 8. Adaptive Retrieval
Câu hỏi đơn giản chỉ cần dense search, câu hỏi phức tạp mới cần hybrid + reranker → tiết kiệm compute.

#### Bảng so sánh kỳ vọng

| Cấu hình | Faithfulness | Latency avg | Cost/req | Ghi chú |
|---|---|---|---|---|
| Baseline (no optimization) | 0.85 | 4.2s | $0.004 | Mức cơ bản |
| + Semantic Cache | 0.85 | 2.8s* | $0.003* | *Trung bình bao gồm cache hits |
| + Context Compression | 0.83 | 3.1s | $0.002 | Giảm nhẹ quality |
| + Model Routing | 0.84 | 3.0s | $0.002 | Câu dễ dùng model rẻ |
| + Top-k tuning (5→3) | 0.82 | 3.5s | $0.003 | Giảm context |
| All combined | 0.83 | 2.5s* | $0.0015* | Trade-off tốt nhất |

---

### 3.10 Module 9 — Feedback Loop

#### Mục đích
Thu thập phản hồi từ người dùng và sử dụng để **cải tiến liên tục** hệ thống.

#### Quy trình

![Hình 3.8. Feedback loop từ người dùng đến cải tiến prompt/evaluation](figures/fig_3_8_feedback_loop.png)

#### Feedback Metrics

| Metric | Cách đo | Target |
|---|---|---|
| User satisfaction rate | % thumbs up | ≥ 80% |
| Feedback volume | Số feedback / tuần | tracking |
| Negative feedback pattern | Cluster các feedback tiêu cực | Phân loại lỗi |
| Improvement velocity | Thời gian từ feedback → fix | ≤ 1 tuần |

---

## PHẦN IV — THIẾT KẾ THỰC NGHIỆM

### 4.1 Bộ dữ liệu

#### Test Set Design

Golden set nên được xem là một đóng góp chính của khóa luận, không chỉ là dữ liệu phụ để demo. Với full-scope, mốc chính là **300 câu hỏi có kiểm chứng**, đủ để đánh giá retrieval, generation, refusal, prompt injection, cost/latency và feedback loop.

| Thành phần | Số lượng | Mô tả |
|---|---:|---|
| **Câu hỏi có đáp án** | 200 | Câu hỏi + ground truth answer + relevant chunks + citation mong đợi |
| **Câu hỏi không có đáp án** | 30 | Tài liệu không chứa thông tin, dùng để kiểm tra refusal và over-answering |
| **Câu hỏi adversarial** | 20 | Prompt injection, jailbreak nhẹ, câu hỏi ngoài domain, yêu cầu bỏ qua quy tắc |
| **Câu hỏi multi-hop** | 30 | Cần tổng hợp thông tin từ nhiều chunk/tài liệu |
| **Câu hỏi ambiguous** | 20 | Câu hỏi thiếu ngữ cảnh, kiểm tra khả năng hỏi lại hoặc nêu giả định |

**Tổng full-scope: 300 câu hỏi.** Có thể chạy thêm smoke set 50 câu cho CI nhanh và nightly set 300 câu cho đánh giá đầy đủ.

#### Test Set Schema

```json
{
  "id": "q_001",
  "question": "Sinh viên cần tích lũy bao nhiêu tín chỉ để tốt nghiệp?",
  "ground_truth": "Sinh viên cần tích lũy đủ 130 tín chỉ theo chương trình đào tạo.",
  "relevant_chunks": ["chunk_042", "chunk_043"],
  "relevant_documents": ["quy_che_dao_tao_2024.pdf"],
  "expected_citations": ["Điều 12", "Khoản 2"],
  "category": "factoid",
  "difficulty": "easy",
  "requires_refusal": false,
  "requires_clarification": false,
  "risk_tags": ["graduation", "credits"]
}
```

---

### 4.2 Thiết kế 6 nhóm thực nghiệm full-scope

#### Thực nghiệm 1: Chunking Ablation Study (trả lời RQ1)

**Câu hỏi**: Cách chia tài liệu nào giúp retrieval và generation ổn định nhất trên văn bản tiếng Việt có cấu trúc?

| ID | Chunking | Overlap | Ghi chú |
|---|---|---:|---|
| C1 | Fixed-size 256 tokens | 10% | Baseline ngắn |
| C2 | Fixed-size 512 tokens | 10% | Baseline cân bằng |
| C3 | Fixed-size 768 tokens | 10% | Context dài hơn |
| C4 | Recursive character/text splitter | 10-15% | Tối ưu theo đoạn văn |
| C5 | Document-structure chunking | Theo Điều/Khoản/Mục | Phù hợp quy chế/luật |
| C6 | Semantic chunking | Theo embedding similarity | Kiểm tra khả năng giữ ý |
| C7 | Parent-child chunking | Parent 1.5-2k, child 256-512 | Tăng recall nhưng giữ citation nhỏ |
| C8 | Table-aware chunking | Theo bảng/biểu mẫu | Dành cho tài liệu có bảng |

**Giữ cố định**: embedding BGE-M3, retrieval hybrid RRF/DBSF, top-k = 5, reranker tắt ở vòng đầu, runtime model GPT-5.4 mini/GPT-5 mini, prompt baseline P1.

**Metric**: Recall@5, MRR, nDCG, Context Precision/Recall, Citation Accuracy, Faithfulness, Answer Relevance, latency retrieval.

---

#### Thực nghiệm 2: Retrieval Strategy + Reranking Comparison (trả lời RQ1-RQ2)

**Câu hỏi**: Dense, sparse, hybrid và reranking nên kết hợp thế nào để tối ưu chất lượng RAG tiếng Việt?

| ID | Retrieval | Reranker | Top-k trước rerank | Top-k sau rerank |
|---|---|---|---:|---:|
| R1 | Dense vector | Không | 5 | 5 |
| R2 | BM25/sparse | Không | 5 | 5 |
| R3 | Hybrid RRF | Không | 10 | 5 |
| R4 | Hybrid DBSF | Không | 10 | 5 |
| R5 | Hybrid RRF | bge-reranker-v2-m3 | 20 | 5 |
| R6 | Hybrid RRF | Jina Reranker multilingual | 20 | 5 |
| R7 | Hybrid RRF | ViRanker hoặc reranker tiếng Việt tương đương | 20 | 5 |
| R8 | Parent-child retrieval | bge/Jina/ViRanker | 20 | 5 |

**Metric**: Recall@k, MRR, nDCG, Context Precision/Recall, citation hit rate, latency, cost/request. Qdrant có thể xử lý hybrid bằng dense + sparse vector với RRF/DBSF; nếu muốn BM25 truyền thống có thể thêm OpenSearch/Elasticsearch làm sparse backend để so sánh.

---

#### Thực nghiệm 3: PromptOps + Model/Provider Comparison (trả lời RQ2)

**Câu hỏi**: Prompt và model/provider nào cho chất lượng tốt nhất trong giới hạn chi phí và độ trễ?

**Part A — Prompt comparison (cố định model runtime)**

6 prompt variants:

| ID | Prompt variant | Mục tiêu |
|---|---|---|
| P0 | Naive baseline | Đo chất lượng thấp nhất có thể chấp nhận |
| P1 | Grounded answer | Chỉ trả lời theo context |
| P2 | Citation-first | Bắt buộc nêu nguồn/điều/khoản |
| P3 | Refusal-aware | Từ chối khi thiếu căn cứ |
| P4 | Self-check/CoVe-lite | Tự kiểm tra mâu thuẫn trước khi trả lời |
| P5 | Concise/cost-aware | Giảm token nhưng giữ độ chính xác |

**Part B — Model/provider comparison (cố định prompt tốt nhất)**

| Model/provider | Vai trò | Chi phí tương đối | Ghi chú |
|---|---|---:|---|
| GPT-5 mini | Runtime nhanh/rẻ | Thấp | Baseline cost-aware |
| GPT-5.4 mini | Runtime cân bằng | Trung bình | Lựa chọn mặc định nếu chất lượng vượt GPT-5 mini |
| GPT-5.5 | Judge/eval hoặc complex query | Cao | Không dùng cho mọi request để tránh đội chi phí |
| Claude Sonnet 4.6 | Judge/runtime phụ | Trung bình-Cao | So sánh reasoning và citation |
| Claude Opus 4.8 | Judge mạnh | Cao | Dùng cho sampling/eval khó |
| Gemini 3 Flash Preview hoặc Gemini 2.5 Flash | Runtime phụ | Thấp-Trung bình | Cần ghi rõ stable/preview tại thời điểm chạy |
| Qwen3 / Qwen3-2507 | Open-weight/local/API-compatible | Infra-dependent | Tốt để kiểm tra phương án không phụ thuộc API |
| Llama 4 Scout/Maverick hoặc Gemma 4 | Open-weight/local | Infra-dependent | So sánh định tính nếu đủ GPU |

**Metric**: Faithfulness, Groundedness, Answer Relevance, Hallucination Rate, Citation Accuracy, Refusal Accuracy, Token Usage, Cost, Latency, judge agreement.

---

#### Thực nghiệm 4: Evaluation + CI/CD Quality Gate Effectiveness (trả lời RQ3)

**Câu hỏi**: Quality gate có phát hiện được regression do thay đổi prompt/model/data/retrieval/code không?

**Thiết kế**:

1. Tạo **16 thay đổi giả lập**: 8 thay đổi tốt/trung tính và 8 thay đổi xấu.
2. Chạy smoke set 50 câu trong CI và nightly set 300 câu cho đánh giá đầy đủ.
3. Đo gate decision và phân tích nhầm lẫn.

| Metric | Ý nghĩa |
|---|---|
| True Positive | Gate chặn đúng thay đổi xấu |
| True Negative | Gate cho pass đúng thay đổi tốt |
| False Positive | Gate chặn sai thay đổi tốt |
| False Negative | Gate cho pass thay đổi xấu |
| Gate latency | Thời gian chạy CI |
| Regression localization | Khả năng chỉ ra lỗi do prompt, data, retrieval hay model |

**Ví dụ thay đổi giả lập**:

| # | Thay đổi | Loại | Gate nên |
|---:|---|---|---|
| 1 | Đổi prompt P1 → P3, tăng refusal accuracy | Tốt | PASS |
| 2 | Đổi prompt P1 → P0, mất groundedness | Xấu | BLOCK |
| 3 | Thêm reranker, recall giữ nguyên, faithfulness tăng | Tốt | PASS |
| 4 | Giảm top-k từ 5 → 1 | Xấu | BLOCK |
| 5 | Cập nhật dữ liệu mới và reindex đúng | Tốt | PASS |
| 6 | Xóa 30% tài liệu nguồn | Xấu | BLOCK |
| 7 | Đổi embedding model có cải thiện retrieval | Tốt | PASS |
| 8 | Đổi LLM sang model yếu hơn làm hallucination tăng | Xấu | BLOCK |
| 9 | Thêm context compression, chất lượng giữ | Tốt | PASS |
| 10 | Tăng temperature = 1.0 | Xấu | BLOCK |
| 11 | Thêm provider fallback hoạt động đúng | Tốt | PASS |
| 12 | Routing sai sang model rẻ cho câu hỏi khó | Xấu | BLOCK |
| 13 | Cache semantic giảm latency nhưng không đổi answer | Tốt | PASS |
| 14 | Cache dùng nhầm data_version cũ | Xấu | BLOCK |
| 15 | Prompt injection guardrail chặn đúng | Tốt | PASS |
| 16 | Tắt citation requirement | Xấu | BLOCK |

---

#### Thực nghiệm 5: Observability + Error Classification (trả lời RQ4)

**Câu hỏi**: Hệ thống observability có đủ tín hiệu để debug lỗi RAG và phân loại nguyên nhân gốc không?

**Thiết kế**:

1. Chạy toàn bộ 300 queries qua hệ thống với tracing đầy đủ.
2. Thu thập span retrieval, rerank, generation, judge, cache, gateway, cost và feedback.
3. Phân loại lỗi tự động bằng rule + judge + human sampling:
   - Retrieval failure: hit_rate = false hoặc context recall thấp
   - Context insufficient: retrieved chunks đúng một phần nhưng thiếu điều kiện
   - Hallucination: faithfulness/groundedness dưới ngưỡng
   - Citation error: trả lời đúng nhưng trích dẫn sai/thiếu
   - Refusal error: từ chối sai hoặc trả lời khi không có căn cứ
   - Provider/gateway error: timeout, fallback, rate limit, cost spike
   - Stale data: index_version hoặc source_version lỗi thời

**Metric**: error classification accuracy, precision/recall theo loại lỗi, trace completeness, p95 latency, cost/request, dashboard usefulness qua checklist.

---

#### Thực nghiệm 6: Cost/Latency/Quality Optimization + Feedback Loop (trả lời RQ5)

**Câu hỏi**: Có thể giảm chi phí/độ trễ mà vẫn giữ chất lượng bằng cache, compression, routing và feedback loop không?

| # | Cấu hình | Thay đổi |
|---:|---|---|
| O1 | Baseline | Không tối ưu |
| O2 | + Semantic Cache | Redis/redis-vl cache theo query similarity + data_version |
| O3 | + Context Compression | Rút gọn context trước khi generation |
| O4 | + Top-k tuning | Giảm top-k động theo confidence |
| O5 | + Model routing | Query đơn giản dùng model rẻ, query khó dùng model mạnh |
| O6 | + Provider fallback | Fallback khi timeout/rate limit |
| O7 | Combined optimized | Cache + compression + routing + fallback |
| O8 | Feedback-improved | Cấu hình O7 sau khi sửa lỗi từ feedback/error clustering |

**Metric**: cost/request, total token usage, avg/p95 latency, faithfulness, answer relevance, citation accuracy, cache hit rate, fallback success rate, quality drop so với baseline, số lỗi giảm sau feedback loop.

**Phân tích**: trade-off chart cost vs quality, latency vs quality và Pareto frontier cho các cấu hình.

![Hình 4.1. Biểu đồ trade-off cost-latency-quality cho các cấu hình RAG](figures/fig_4_1_cost_latency_quality_tradeoff.png)

---

## PHẦN V — TECH STACK VÀ TRIỂN KHAI

### 5.1 Tech Stack chi tiết

| Thành phần | Công nghệ | Lý do chọn |
|---|---|---|
| **Language** | Python 3.11+ | Ecosystem AI/ML mạnh nhất |
| **Backend API** | FastAPI | Async, auto docs, type hints, production-ready |
| **RAG Framework** | LlamaIndex + LangChain/LangGraph | LlamaIndex mạnh về data/RAG; LangChain/LangGraph hữu ích cho orchestration và workflow có trạng thái |
| **Model Gateway** | LiteLLM Proxy + provider adapters | Gateway OpenAI-compatible cho nhiều provider, fallback, virtual keys, budget, cost tracking và rate limit |
| **Vector DB** | Qdrant (chính) + FAISS (local ablation) + OpenSearch/Elasticsearch tùy chọn | Qdrant hỗ trợ dense/sparse/hybrid và filtering; FAISS nhẹ cho so sánh; OpenSearch/Elasticsearch tốt cho BM25 truyền thống |
| **Embedding** | BGE-M3 (chính) + multilingual-e5/EmbeddingGemma/Qwen3-Embedding (so sánh) | Đa ngôn ngữ; BGE-M3 có dense/sparse/multi-vector signals; các model mới dùng để kiểm tra độ ổn định tiếng Việt |
| **Reranker** | bge-reranker-v2-m3, Jina Reranker multilingual, ViRanker hoặc Qwen3-Reranker | Reranking là baseline quan trọng cho RAG tiếng Việt và văn bản có cấu trúc |
| **LLM runtime** | GPT-5.4 mini hoặc GPT-5 mini (chính), Gemini 3 Flash Preview/Gemini 2.5 Flash và Qwen3/Gemma 4/Llama 4 để so sánh | Cân bằng quality/cost; có provider phụ để đo routing/fallback và tránh phụ thuộc một API |
| **LLM judge** | GPT-5.5 hoặc Claude Sonnet 4.6/Opus 4.8 | Dùng cho evaluation, sampling khó và kiểm tra judge agreement |
| **Semantic Cache** | Redis/Valkey + redis-vl | Nhanh, hỗ trợ cache theo semantic similarity và data_version |
| **Evaluation** | RAGAS + DeepEval + custom metrics + human review sampling | Kết hợp metric retrieval/generation, LLM-as-a-Judge, threshold gate và kiểm chứng thủ công |
| **Observability** | Langfuse self-host v3 + OpenTelemetry GenAI + Prometheus/Grafana + Arize Phoenix tùy chọn | Langfuse cho trace/prompt/eval; OTel chuẩn hóa span GenAI; Grafana cho infra; Phoenix hữu ích cho RAG analysis |
| **Experiment Tracking** | MLflow + DVC metrics | Open-source, compare experiments, lưu artifact/metric theo version |
| **CI/CD** | GitHub Actions | Tích hợp tốt, free cho public repos |
| **Containerization** | Docker + Docker Compose; K3s/Kubernetes local tùy chọn | Compose là baseline bắt buộc; K3s dùng để minh họa triển khai nâng cao nếu cần |
| **Dashboard** | Grafana + Prometheus | Industry-standard, customizable |
| **Data Versioning** | DVC + MinIO/S3; LakeFS tùy chọn | DVC nhẹ và tích hợp Git; object store phục vụ artifact/data snapshot; LakeFS hữu ích nếu muốn branch dữ liệu |
| **Database** | PostgreSQL + ClickHouse | PostgreSQL cho metadata/prompt/config; ClickHouse cho trace/observability throughput cao |
| **Workflow Orchestration** | Prefect hoặc Dagster | Lập lịch ingest, reindex, eval nightly, feedback improvement loop |
| **Security/Guardrails** | OWASP LLM Top 10 checklist, PII detector, prompt injection tests, allowlist tools | Phù hợp rủi ro RAG: prompt injection, data leakage, insecure output, excessive agency |
| **Frontend** | Next.js (App Router) + Tailwind CSS v4 + Motion + GSAP/ScrollTrigger + Lenis + shadcn/ui, gọi FastAPI qua `/qa/query` | Đổi từ Streamlit/Gradio (2026-07-12, theo yêu cầu trực tiếp user) — cần showcase animation cuộn trang, giao diện đẹp cho bảo vệ khóa luận, không chỉ form input/output; xem `docs/system/modules/10_frontend_showcase.md` |

### 5.2 Project Structure

```
llmops-rag-platform/
├── docker-compose.yml
├── Dockerfile
├── .github/
│   └── workflows/
│       └── quality_gate.yml
│
├── config/
│   ├── quality_gate.yaml
│   ├── experiment_config.yaml
│   └── model_gateway.yaml
│
├── data/
│   ├── raw/                    # Tài liệu gốc
│   ├── processed/              # Tài liệu đã xử lý
│   ├── chunks/                 # Chunks đã tạo
│   ├── test_sets/              # Bộ test câu hỏi
│   └── data.dvc                # DVC tracking
│
├── src/
│   ├── dataops/                # Module 1: DataOps/RAGOps
│   │   ├── parser.py
│   │   ├── validator.py
│   │   ├── cleaner.py
│   │   ├── chunker.py
│   │   ├── dedup.py
│   │   ├── pii_detector.py
│   │   └── versioning.py
│   │
│   ├── retrieval/              # Module 2: Retrieval Experiment
│   │   ├── embedder.py
│   │   ├── indexer.py
│   │   ├── retriever.py
│   │   ├── reranker.py
│   │   └── experiment.py
│   │
│   ├── rag/                    # Module 3: RAG Runtime
│   │   ├── orchestrator.py
│   │   ├── model_gateway.py
│   │   ├── cache.py
│   │   ├── compressor.py
│   │   └── guardrails.py
│   │
│   ├── promptops/              # Module 4: PromptOps
│   │   ├── registry.py
│   │   ├── versioning.py
│   │   ├── ab_testing.py
│   │   └── templates/
│   │       ├── p0_baseline.txt
│   │       ├── p1_grounded.txt
│   │       ├── p2_citation.txt
│   │       ├── p3_refusal.txt
│   │       ├── p4_cove.txt
│   │       └── p5_optimized.txt
│   │
│   ├── evaluation/             # Module 5: Evaluation Engine
│   │   ├── retrieval_eval.py
│   │   ├── context_eval.py
│   │   ├── generation_eval.py
│   │   ├── production_eval.py
│   │   ├── llm_judge.py
│   │   └── report.py
│   │
│   ├── quality_gate/           # Module 6: CI/CD Quality Gate
│   │   ├── gate.py
│   │   ├── regression.py
│   │   └── decision.py
│   │
│   ├── observability/          # Module 7: Observability
│   │   ├── tracer.py
│   │   ├── logger.py
│   │   ├── metrics.py
│   │   ├── error_classifier.py
│   │   └── dashboard.py
│   │
│   ├── optimization/           # Module 8: Cost/Latency
│   │   ├── semantic_cache.py
│   │   ├── compressor.py
│   │   ├── router.py
│   │   └── budget.py
│   │
│   ├── feedback/               # Module 9: Feedback Loop
│   │   ├── collector.py
│   │   ├── analyzer.py
│   │   └── augmentor.py
│   │
│   └── api/                    # FastAPI endpoints
│       ├── main.py
│       ├── routes/
│       │   ├── qa.py
│       │   ├── admin.py
│       │   ├── eval.py
│       │   └── feedback.py
│       └── middleware/
│           ├── tracing.py
│           └── auth.py
│
├── scripts/
│   ├── run_evaluation.py
│   ├── check_gate.py
│   ├── regression_check.py
│   ├── generate_report.py
│   ├── run_experiment.py
│   └── ingest_data.py
│
├── frontend/                   # Next.js showcase/QA-demo/dashboard web app
│   ├── app/
│   │   ├── page.tsx             # landing/showcase (kiến trúc, 8 phase, số liệu thật)
│   │   ├── demo/page.tsx        # QA demo thật, gọi /qa/query
│   │   └── dashboard/page.tsx   # trực quan hoá kết quả thực nghiệm (Phase 4/6/8)
│   ├── components/
│   └── lib/                     # API client gọi FastAPI backend
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── notebooks/
│   ├── eda.ipynb
│   ├── experiment_analysis.ipynb
│   └── results_visualization.ipynb
│
├── docs/
│   ├── architecture.md
│   ├── api_docs.md
│   └── setup.md
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

### 5.3 Docker Compose full-scope

Docker Compose nên được xem là **khung triển khai production-like**, không phải toàn bộ file copy-paste cuối cùng. Khi cài thật, nên lấy Docker Compose chính thức của Langfuse v3 làm base cho cụm `langfuse-web`, `langfuse-worker`, `clickhouse`, `minio`, `redis/valkey`, sau đó thêm RAG API, Qdrant, LiteLLM, Prometheus, Grafana, MLflow và frontend.

```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_HOST=qdrant
      - REDIS_HOST=valkey
      - POSTGRES_HOST=postgres
      - LITELLM_BASE_URL=http://litellm:4000
      - LANGFUSE_HOST=http://langfuse-web:3000
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
    depends_on:
      - qdrant
      - valkey
      - postgres
      - litellm
      - langfuse-web

  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "4000:4000"
    volumes:
      - ./config/litellm.yaml:/app/config.yaml
    command: ["--config", "/app/config.yaml"]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DATABASE_URL=postgresql://admin:${POSTGRES_PASSWORD}@postgres:5432/llmops
    depends_on:
      - postgres

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  valkey:
    image: valkey/valkey:8-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:17
    environment:
      - POSTGRES_DB=llmops
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data

  clickhouse:
    image: clickhouse/clickhouse-server:latest
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - clickhouse_data:/var/lib/clickhouse

  minio:
    image: minio/minio:latest
    ports:
      - "9001:9001"
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

  langfuse-web:
    image: langfuse/langfuse:3
    ports:
      - "3000:3000"
    depends_on:
      - postgres
      - clickhouse
      - valkey
      - minio

  langfuse-worker:
    image: langfuse/langfuse-worker:3
    depends_on:
      - postgres
      - clickhouse
      - valkey
      - minio

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana

  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    ports:
      - "5000:5000"
    command: mlflow server --host 0.0.0.0

  frontend:
    build:
      context: ./frontend        # Next.js — xem docs/system/modules/10_frontend_showcase.md
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
    depends_on:
      - api

volumes:
  qdrant_data:
  pg_data:
  clickhouse_data:
  minio_data:
  grafana_data:
```

> **Ghi chú Langfuse v3:** Không dùng cấu hình cũ `langfuse/langfuse:latest + Postgres` như một service đơn lẻ. Langfuse v3 cần web container, worker container, Postgres, ClickHouse, Redis/Valkey và S3/Blob store như MinIO. Các biến môi trường chi tiết nên lấy từ tài liệu self-host chính thức để tránh sai version.

---

## PHẦN VI — DÀN Ý BÁO CÁO KHÓA LUẬN

### Chương 1 — Giới thiệu (10-15 trang)
1.1. Đặt vấn đề
1.2. Bối cảnh: LLM và RAG trong doanh nghiệp
1.3. Vấn đề khi đưa LLM/RAG vào production
1.4. LLMOps là gì và tại sao cần thiết
1.5. Mục tiêu nghiên cứu
1.6. Câu hỏi nghiên cứu (RQ1-RQ5)
1.7. Phạm vi và giới hạn
1.8. Đóng góp của đề tài
1.9. Cấu trúc khóa luận

### Chương 2 — Cơ sở lý thuyết và các công trình liên quan (20-25 trang)
2.1. Large Language Models
  2.1.1. Kiến trúc Transformer
  2.1.2. Prompting và In-Context Learning
  2.1.3. Các hạn chế khi production
2.2. Retrieval-Augmented Generation
  2.2.1. Kiến trúc RAG
  2.2.2. Chunking strategies
  2.2.3. Embedding models
  2.2.4. Vector databases
  2.2.5. Retrieval strategies (dense, sparse, hybrid)
  2.2.6. Reranking
2.3. MLOps và LLMOps
  2.3.1. MLOps lifecycle
  2.3.2. LLMOps — sự mở rộng
  2.3.3. RAGOps — quản lý data lifecycle
  2.3.4. So sánh MLOps vs LLMOps
2.4. Evaluation cho LLM/RAG
  2.4.1. Thách thức đánh giá LLM
  2.4.2. RAGAS framework
  2.4.3. DeepEval framework
  2.4.4. LLM-as-a-Judge
  2.4.5. Human evaluation
2.5. Observability và Monitoring
  2.5.1. Ba trụ cột observability
  2.5.2. Các công cụ hiện có
2.6. Các công trình liên quan
  2.6.1. Hệ thống RAG tiếng Việt hiện có
  2.6.2. LLMOps platforms
  2.6.3. RAG evaluation studies
2.7. Tổng kết chương — khoảng trống nghiên cứu

### Chương 3 — Phân tích và thiết kế hệ thống (25-30 trang)
3.1. Yêu cầu hệ thống
  3.1.1. Yêu cầu chức năng
  3.1.2. Yêu cầu phi chức năng
3.2. Kiến trúc tổng thể full-scope 9 module
3.3. Module 1: DataOps/RAGOps Layer
3.4. Module 2: Retrieval Experiment Layer
3.5. Module 3: RAG Runtime + Model Gateway
3.6. Module 4: PromptOps
3.7. Module 5: Evaluation Engine
3.8. Module 6: CI/CD Quality Gate
3.9. Module 7: Observability + Cost/Latency Monitoring
3.10. Module 8: Optimization + Provider Routing
3.11. Module 9: Feedback Loop + Continuous Improvement
3.12. Thiết kế cơ sở dữ liệu
3.13. Thiết kế API
3.14. Tech stack và lý do lựa chọn

### Chương 4 — Cài đặt hệ thống (20-25 trang)
4.1. Thiết lập môi trường phát triển
4.2. Cài đặt DataOps pipeline
4.3. Cài đặt Retrieval engine
4.4. Cài đặt RAG orchestrator
4.5. Cài đặt PromptOps
4.6. Cài đặt Evaluation Engine
4.7. Cài đặt CI/CD Quality Gate
4.8. Cài đặt Observability Dashboard
4.9. Cài đặt Cost/Latency Monitoring
4.10. Cài đặt Model Gateway, routing và fallback
4.11. Cài đặt Feedback Loop và human review queue
4.12. Docker hóa và triển khai full-scope
4.13. Frontend demo

### Chương 5 — Thực nghiệm và đánh giá (20-25 trang)
5.1. Tổng quan thiết kế thực nghiệm
5.2. Bộ dữ liệu và test set
5.3. Thực nghiệm 1: Chunking Ablation Study
  5.3.1. Thiết lập
  5.3.2. Kết quả
  5.3.3. Phân tích
5.4. Thực nghiệm 2: Retrieval Strategy + Reranking Comparison
  5.4.1. Thiết lập
  5.4.2. Kết quả
  5.4.3. Phân tích
5.5. Thực nghiệm 3: PromptOps + Model/Provider Comparison
  5.5.1. Thiết lập prompt/model/provider
  5.5.2. Kết quả
  5.5.3. Phân tích
5.6. Thực nghiệm 4: Evaluation + CI/CD Quality Gate Effectiveness
  5.6.1. Thiết lập 16 thay đổi giả lập
  5.6.2. Kết quả gate decisions
  5.6.3. Phân tích
5.7. Thực nghiệm 5: Observability + Error Classification
  5.7.1. Thiết lập tracing và dashboard
  5.7.2. Kết quả phân loại lỗi
  5.7.3. Phân tích root cause
5.8. Thực nghiệm 6: Cost/Latency/Quality Optimization + Feedback Loop
  5.8.1. Thiết lập tối ưu
  5.8.2. Trade-off analysis
  5.8.3. Tác động của feedback loop
5.9. Tổng hợp kết quả — cấu hình tối ưu
5.10. Phân tích lỗi (Error Analysis)
5.11. Thảo luận và trả lời Research Questions

### Chương 6 — Kết luận và hướng phát triển (5-8 trang)
6.1. Tóm tắt kết quả đạt được
6.2. Đóng góp chính
6.3. Hạn chế
6.4. Hướng phát triển sau khi hoàn tất full-scope
  6.4.1. Fine-tuning embedding cho tiếng Việt
  6.4.2. Benchmark multi-domain và dữ liệu người dùng thật
  6.4.3. Kubernetes/cloud deployment có HA, autoscaling và disaster recovery
  6.4.4. Guardrails nâng cao và red-teaming tự động
  6.4.5. Enterprise security: SSO, RBAC, audit log, data governance
  6.4.6. Multi-turn conversation dài hạn với memory có kiểm soát
  6.4.7. Multi-modal RAG cho hình ảnh, bảng biểu và tài liệu scan phức tạp
  6.4.8. Multi-agent/agentic RAG nâng cao với tool calling và workflow phức tạp

---

## PHẦN VII — KẾ HOẠCH THỰC HIỆN

### Timeline gợi ý full-scope (24 tuần)

| Tuần | Công việc | Deliverable |
|---|---|---|
| 1-2 | Nghiên cứu tài liệu, khảo sát tools | Chương 2 (bản nháp) |
| 3-4 | Thu thập dữ liệu, thiết kế schema golden set, xây DataOps pipeline | Module 1 hoàn thành, dữ liệu sạch, 300 câu hỏi draft |
| 5-6 | Xây chunking, embedding, dense/sparse/hybrid retrieval | Module 2 hoàn thành, index versioned |
| 7-8 | Xây RAG Runtime, citation, refusal, streaming, guardrails | Module 3 hoàn thành, demo QA cơ bản |
| 9-10 | Xây PromptOps, prompt registry, diff, offline comparison | Module 4 hoàn thành |
| 11-12 | Xây Model Gateway với LiteLLM, routing, fallback, budget | Module 8/gateway hoàn thành |
| 13-14 | Xây Evaluation Engine, RAGAS/DeepEval/custom metrics, judge agreement | Module 5 hoàn thành |
| 15-16 | Xây CI/CD Quality Gate, smoke set 50 câu, nightly set 300 câu | Module 6 hoàn thành |
| 17-18 | Xây Observability, Langfuse v3, OTel traces, Prometheus/Grafana dashboard | Module 7 hoàn thành |
| 19-20 | Xây feedback loop, error clustering, human review queue, improvement workflow | Module 9 hoàn thành |
| 21-22 | Chạy 6 nhóm thực nghiệm, thu thập kết quả, phân tích lỗi | Chương 5 bản nháp, bảng/biểu đồ kết quả |
| 23 | Hoàn thiện báo cáo, kiến trúc, cài đặt, discussion | Chương 3, 4, 5 hoàn thiện |
| 24 | Review, chỉnh sửa, chuẩn bị bảo vệ, đóng gói demo | Báo cáo hoàn chỉnh + demo full-scope |

---

## PHẦN VIII — DELIVERABLES TỔNG KẾT

### Sản phẩm kỹ thuật
- [ ] Web/API hỏi đáp tài liệu tiếng Việt
- [ ] DataOps pipeline (ingest → clean → chunk → embed → index)
- [ ] Retrieval experiment layer với dense/sparse/hybrid retrieval và reranking
- [ ] RAG runtime có citation, refusal, streaming và guardrails
- [ ] Prompt registry với 6+ prompt variants, prompt diff và offline comparison
- [ ] Model gateway với LiteLLM/provider adapters, fallback, budget và routing policy
- [ ] Evaluation engine 4 tầng
- [ ] CI/CD quality gate (GitHub Actions)
- [ ] Observability dashboard 12+ panel (latency, cost, retrieval, hallucination/error labels, data freshness, provider fallback)
- [ ] Cost optimization pipeline (cache, compression, dynamic top-k, model routing)
- [ ] Feedback loop với user feedback, human review queue và error clustering
- [ ] Docker Compose full-scope deployment
- [ ] Bộ test set 300 câu hỏi tiếng Việt có ground truth, relevant chunks và expected citations

### Báo cáo định lượng
- [ ] Bảng so sánh 8 cấu hình chunking
- [ ] Bảng so sánh 8 cấu hình retrieval/reranking
- [ ] Bảng so sánh 6+ prompt variants
- [ ] Bảng so sánh 6-8 model/runtime/judge/provider options
- [ ] Quality gate effectiveness report
- [ ] Error classification accuracy report
- [ ] Cost/latency optimization report
- [ ] Model routing/fallback effectiveness report
- [ ] Feedback loop improvement report
- [ ] Trade-off analysis charts

### Tài liệu
- [ ] Báo cáo khóa luận (6 chương, ~120-150 trang)
- [ ] README.md hướng dẫn chạy hệ thống
- [ ] API documentation
- [ ] Architecture decision records

---

## PHẦN IX — NGUỒN THAM KHẢO CẬP NHẬT NÊN TRÍCH DẪN

- OpenAI API Docs — Latest model guide: https://developers.openai.com/api/docs/guides/latest-model
- OpenAI API Docs — GPT-5.4 mini model page: https://developers.openai.com/api/docs/models/gpt-5.4-mini
- OpenAI API Docs — GPT-5 mini model page: https://developers.openai.com/api/docs/models/gpt-5-mini
- Anthropic Claude Docs — Models overview: https://platform.claude.com/docs/en/about-claude/models/overview
- Google AI for Developers — Gemini models and model version patterns: https://ai.google.dev/gemini-api/docs/models
- Meta AI — Llama 4 release: https://ai.meta.com/blog/llama-4-multimodal-intelligence/
- Qwen — Qwen3 release: https://qwenlm.github.io/blog/qwen3/
- Google Blog — Gemma 4 release: https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/
- Langfuse Docs — Langfuse v2 to v3 self-host migration: https://langfuse.com/self-hosting/upgrade/upgrade-guides/upgrade-v2-to-v3
- LiteLLM Docs — Proxy Server / LLM Gateway: https://docs.litellm.ai/
- Qdrant Docs — Hybrid queries: https://qdrant.tech/documentation/search/hybrid-queries/
- OpenTelemetry Docs — GenAI semantic conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/
- RAGAS Docs — Available metrics: https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/
- Arize Phoenix Docs — LLM tracing and evaluation: https://arize.com/docs/phoenix/
- McKinsey — The State of AI 2025: https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai
- OWASP — Top 10 for LLM Applications 2025: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- DeepEval Docs — LLM evaluation metrics: https://deepeval.com/docs/metrics-introduction
- BGE-M3 model card: https://huggingface.co/BAAI/bge-m3
- CSConDa Vietnamese customer support benchmark: https://arxiv.org/abs/2507.22542
- ViRanker Vietnamese reranking paper: https://arxiv.org/abs/2509.09131
- VLegal-Bench: https://vlegalbench.cmcai.vn/
- MIRAGE-Bench multilingual RAG evaluation: https://mirage-bench.github.io/

> [!IMPORTANT]
> Đề tài này có tính **nghiên cứu định lượng** và định hướng production-like full-scope. Điểm khác biệt lớn nhất so với các đề tài chatbot thông thường là **không chỉ xây hệ thống hỏi đáp, mà còn xây quy trình đánh giá, giám sát, kiểm thử, định tuyến model, tối ưu chi phí và cải tiến có kiểm soát** — đúng tinh thần LLMOps/RAGOps hiện nay.
