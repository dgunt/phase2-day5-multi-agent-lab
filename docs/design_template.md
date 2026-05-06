# Design

## Problem

Hệ thống được thiết kế để xử lý các câu hỏi nghiên cứu và tạo ra câu trả lời cuối cùng rõ ràng thông qua workflow multi-agent.

Ví dụ task:

> Research GraphRAG state-of-the-art and write a 500-word summary.

Hệ thống không chỉ trả về câu trả lời cuối cùng, mà còn cần thể hiện được các kết quả trung gian:

- Research notes từ Researcher Agent
- Analysis notes từ Analyst Agent
- Final answer từ Writer Agent
- Route history và trace events từ Supervisor/workflow

Mục tiêu là so sánh cách tiếp cận multi-agent với single-agent baseline theo các tiêu chí: chất lượng, độ trễ, chi phí ước tính và khả năng quan sát.

## Why multi-agent?

Single-agent baseline nhanh hơn vì chỉ dùng một lần gọi LLM. Tuy nhiên, cách này có một số hạn chế:

- Research, analysis và writing bị trộn chung trong một prompt.
- Quá trình suy luận khó quan sát.
- Khó debug khi câu trả lời yếu hoặc thiếu ý.
- Không tạo ra các artifact trung gian như research notes hoặc analysis notes.
- Không phù hợp bằng multi-agent khi task phức tạp và cần chia nhỏ vai trò.

Multi-agent workflow chia task thành các vai trò rõ ràng:

- Researcher thu thập và tổ chức research notes.
- Analyst phân tích claim, rủi ro, trade-off và điểm yếu bằng chứng.
- Writer viết câu trả lời cuối cùng.
- Supervisor điều phối workflow và tránh vòng lặp vô hạn.

Cách này giúp hệ thống dễ quan sát, dễ debug và có phân tách trách nhiệm rõ ràng hơn. Đổi lại, latency và cost tăng lên vì cần nhiều lần gọi LLM hơn. Đúng rồi, muốn rõ ràng hơn thì phải trả tiền bằng thời gian và token, rất đúng tinh thần cuộc sống.

## Agent Roles

| Agent | Trách nhiệm | Input | Output | Failure Mode |
|---|---|---|---|---|
| Supervisor | Chọn route tiếp theo và quyết định khi nào dừng | `ResearchState` hiện tại | Route mới trong `route_history` | Chọn sai route, dừng quá sớm, lặp vô hạn |
| Researcher | Tạo research notes có cấu trúc | User query | `research_notes` | Notes chung chung, thiếu bằng chứng, claim chưa chắc chắn |
| Analyst | Phân tích research notes | Query + `research_notes` | `analysis_notes` | Lặp lại ý của Researcher, phân tích yếu, thiếu limitation |
| Writer | Viết câu trả lời cuối cùng | Query + research/analysis notes | `final_answer` | Bỏ qua cấu trúc, độ dài, limitation hoặc yêu cầu người dùng |

## Shared State

Workflow sử dụng `ResearchState` làm nguồn dữ liệu chung được truyền qua các agent.

| Field | Mục đích |
|---|---|
| `request` | Lưu `ResearchQuery` gốc của người dùng |
| `iteration` | Đếm số bước routing |
| `route_history` | Ghi lại các route mà Supervisor đã chọn |
| `sources` | Lưu tài liệu/source nếu tích hợp search sau này |
| `research_notes` | Lưu output của Researcher |
| `analysis_notes` | Lưu output của Analyst |
| `final_answer` | Lưu output cuối cùng của Writer |
| `agent_results` | Dự phòng cho output có cấu trúc của từng agent |
| `trace` | Lưu latency, token usage, status và workflow events |
| `errors` | Lưu lỗi hoặc fallback message |

Ghi chú về implementation hiện tại:

- Researcher hiện đang dùng LLM để tạo research notes.
- Chưa tích hợp external search.
- Vì vậy, `sources` hiện có thể vẫn rỗng.

## Routing Policy

Supervisor sử dụng rule-based routing policy đơn giản.

| Điều kiện | Route tiếp theo |
|---|---|
| Chưa có `research_notes` | `researcher` |
| Chưa có `analysis_notes` | `analyst` |
| Chưa có `final_answer` | `writer` |
| Đã có đủ output cần thiết | `done` |
| Đạt max iterations | `done` và ghi lỗi |

Route sequence bình thường khi chạy thành công:

| Step | Route |
|---:|---|
| 1 | `researcher` |
| 2 | `analyst` |
| 3 | `writer` |
| 4 | `done` |

Expected route history:

`researcher -> analyst -> writer -> done`

Routing policy này đơn giản, deterministic và dễ debug. Nó phù hợp với bài lab vì mục tiêu chính là thể hiện role separation, shared state, tracing và benchmarking.

## Guardrails

| Guardrail | Implementation hiện tại |
|---|---|
| Max iterations | `max_iterations = 8` |
| Timeout | Cấu hình qua `LLM_TIMEOUT_SECONDS`, mặc định 60 giây |
| Retry | LLM client retry tối đa 3 lần với exponential backoff |
| Fallback | Agent ghi lỗi vào `state.errors`; một số agent có fallback message |
| Validation | Pydantic validate `ResearchQuery` và `BenchmarkMetrics` |

Các hướng validation có thể cải thiện sau:

- Validate số từ của final answer
- Validate các section bắt buộc
- Validate citation hoặc source coverage
- Retry Writer nếu output chưa đạt yêu cầu

## Benchmark Plan

Benchmark so sánh hai cách chạy:

1. Single-agent baseline
2. Multi-agent workflow

### Benchmark Queries

| # | Query |
|---:|---|
| 1 | Research GraphRAG state-of-the-art and write a 500-word summary |
| 2 | Compare single-agent and multi-agent systems for research tasks |
| 3 | Explain common failure modes of multi-agent orchestration and how to fix them |

### Metrics

| Metric | Mô tả |
|---|---|
| Latency | Tổng thời gian chạy tính bằng giây |
| Estimated cost | Chi phí ước tính từ input/output tokens |
| Quality score | Điểm heuristic dựa trên độ đầy đủ, cấu trúc, traceability và error count |
| Input tokens | Tổng số input tokens |
| Output tokens | Tổng số output tokens |
| Error count | Số lỗi được ghi trong state |
| Trace events | Số trace events được ghi lại |
| Route history | Chuỗi route do Supervisor chọn |

### Expected Outcome

| Approach | Điểm mạnh kỳ vọng | Điểm yếu kỳ vọng |
|---|---|---|
| Single-agent | Nhanh hơn, rẻ hơn | Ít observable hơn, phân tách vai trò yếu hơn |
| Multi-agent | Trace tốt hơn, cấu trúc rõ hơn | Chậm hơn, tốn chi phí hơn |

Observed benchmark pattern:

- Baseline nhanh hơn.
- Multi-agent chậm hơn khoảng 2-3 lần.
- Estimated cost của multi-agent cao hơn khoảng 3-4 lần.
- Multi-agent có traceability tốt hơn nhờ intermediate notes và route history.

## Current Limitations

- Chưa tích hợp external search.
- `sources` có thể vẫn rỗng.
- Quality score hiện là heuristic-based, chưa phải đánh giá từ người thật hoặc LLM-as-judge.
- Cost được ước tính từ token pricing cấu hình, chưa phải billing thật.
- Benchmark chỉ dùng 3 queries, nên kết quả phù hợp cho lab-scale, chưa đủ mạnh để kết luận thống kê.

## Future Improvements

- Tích hợp Tavily, Bing, SerpAPI hoặc internal document search.
- Populate `sources` bằng tài liệu retrieve thật.
- Thêm citation coverage check.
- Thêm Critic Agent để phát hiện hallucination.
- Thêm LLM-as-judge hoặc multi-judge evaluation.
- Thêm output validation cho word count và các section bắt buộc.
- Thay explicit Python workflow bằng LangGraph đầy đủ nếu cần triển khai production.