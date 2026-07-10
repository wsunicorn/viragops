# Project Charter

## Tên project

**LLMOps/RAGOps Platform for Vietnamese Document Question Answering**

Tên ngắn: **LLMOps Vietnamese RAG Platform**

## Mục tiêu

Xây dựng một nền tảng RAG tiếng Việt có quy trình LLMOps/RAGOps đầy đủ, phục vụ hỏi đáp tài liệu domain "Quy chế đào tạo đại học + FAQ sinh viên". Hệ thống phải cho phép triển khai, đánh giá, giám sát và cải tiến một cách có kiểm soát thay vì chỉ tạo chatbot demo.

## Vấn đề cần giải quyết

Các hệ thống RAG demo thường gặp các vấn đề:

- không biết retrieval có lấy đúng tài liệu không;
- không đo được hallucination;
- không có version prompt/model/data;
- không có test trước deploy;
- không biết chi phí và độ trễ tăng vì lý do gì;
- không có vòng lặp biến feedback thành cải tiến;
- không truy vết được câu trả lời được tạo bởi version nào.

Project này giải quyết bằng cách xây dựng 9 module LLMOps/RAGOps đầy đủ.

## Stakeholder

| Stakeholder | Nhu cầu |
|---|---|
| Sinh viên thực hiện khóa luận | Có hệ thống đủ sâu để bảo vệ, có kết quả định lượng |
| Giảng viên hướng dẫn | Thấy rõ tính nghiên cứu, kiến trúc và thực nghiệm |
| Người dùng demo | Hỏi đáp tài liệu tiếng Việt có trích dẫn nguồn |
| Người vận hành hệ thống | Theo dõi lỗi, chi phí, độ trễ, chất lượng |
| Người đánh giá khóa luận | Có evidence: metric, bảng so sánh, dashboard, report |

## Phạm vi chính

Trong scope:

- RAG hỏi đáp tài liệu tiếng Việt;
- DataOps/RAGOps pipeline;
- retrieval experiment layer;
- RAG runtime API;
- PromptOps;
- Model Gateway;
- Evaluation Engine;
- CI/CD Quality Gate;
- Observability/Cost Monitoring;
- Optimization/Routing;
- Feedback Loop;
- golden set 300 câu hỏi;
- 6 nhóm thực nghiệm;
- Docker Compose deployment.

Ngoài scope:

- full fine-tuning foundation model;
- huấn luyện LLM từ đầu;
- HA production thật với SLA doanh nghiệp;
- mobile app native;
- enterprise SSO/RBAC hoàn chỉnh;
- cam kết traffic người dùng thật.

## Domain đã chốt

Domain là **Quy chế đào tạo đại học + Sổ tay/FAQ sinh viên của Trường Đại học Công nghiệp TP.HCM (IUH)**.

Nguồn dữ liệu cụ thể (website, văn bản, ánh xạ category) được liệt kê trong [experiments/data_sources_iuh.md](experiments/data_sources_iuh.md). Nguồn nền chính: cổng Cẩm nang người học (camnang.iuh.edu.vn), Phòng Đào tạo (pdt.iuh.edu.vn), Phòng Công tác chính trị & Hỗ trợ SV (ctsv.iuh.edu.vn), Phòng Khảo thí & ĐBCL (tqa.iuh.edu.vn).

Lý do chọn:

- nhiều câu hỏi thực tế, người thực hiện quen domain nên dễ kiểm chứng ground truth;
- tài liệu có cấu trúc Điều/Khoản/Mục và bản HTML sạch (camnang) → citation rõ, giảm phụ thuộc OCR;
- cần trích dẫn chính xác;
- dễ tạo golden set;
- phù hợp kiểm tra hallucination, refusal và citation accuracy.

Domain phụ (tùy chọn, ~50-100 câu) để chứng minh tổng quát hóa: một bộ luật giới hạn (ví dụ Bộ luật Lao động 2019). Chỉ thêm sau khi domain IUH đã vững.

## Định nghĩa thành công

Project được xem là thành công khi đạt các điều kiện:

- hệ thống ingest được tài liệu và tạo index version;
- API hỏi đáp trả lời có citation;
- có prompt registry và model config version;
- có golden set 300 câu;
- chạy được 6 nhóm thực nghiệm;
- quality gate chặn được regression giả lập;
- dashboard hiển thị request, latency, cost, retrieval hit rate, hallucination/error labels;
- feedback loop tạo được issue/improvement backlog;
- báo cáo có bảng số liệu định lượng và phân tích lỗi.

## Nguyên tắc thiết kế

- Ưu tiên đo lường hơn cảm tính.
- Mọi artifact quan trọng phải có version.
- Mọi thay đổi có rủi ro phải qua evaluation.
- Không phụ thuộc cứng vào một provider/model.
- Không trả lời khi không có căn cứ trong tài liệu.
- Trace phải đủ để debug câu trả lời sai.
- Chi phí và latency là metric hạng nhất, không phải phần phụ.

