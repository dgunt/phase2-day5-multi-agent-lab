# Lab 20 - Multi-Agent Research System

## 1. Giới thiệu
Học viên: Vũ Đức Minh
Mã học viên: 2A202600459

Repo này là bài lab xây dựng hệ thống nghiên cứu bằng
multi-agent.

Hệ thống gồm các agent chính:

- **Supervisor Agent**: điều phối workflow và chọn agent tiếp theo.
- **Researcher Agent**: tìm mock source và tạo research notes.
- **Analyst Agent**: phân tích research notes.
- **Writer Agent**: viết final answer.
- **Critic Agent**: kiểm tra nhẹ final answer, dùng cho hướng mở rộng.

Ngoài multi-agent workflow, repo còn có single-agent baseline để so
sánh theo latency, estimated cost, token usage, quality score và
traceability.

## 2. Mục tiêu bài lab

Bài lab tập trung vào các mục tiêu sau:

- Thiết kế role rõ ràng cho nhiều agent.
- Xây dựng shared state để các agent handoff thông tin.
- Thêm guardrails như max iterations, timeout, retry, fallback và
  validation.
- Trace được luồng chạy của hệ thống.
- Benchmark single-agent baseline với multi-agent workflow.

## 3. Kiến trúc tổng quan

Luồng xử lý chính:

1. User gửi research query.
2. Supervisor chọn route đầu tiên.
3. Researcher tạo `research_notes` và lấy `sources`.
4. Analyst tạo `analysis_notes`.
5. Writer tạo `final_answer`.
6. Workflow ghi trace và phục vụ benchmark.

Route thành công mặc định:

```text
researcher
  -> analyst
  -> writer
  -> done
```

## 4. Các module chính

### Agents

Thư mục `src/multi_agent_research_lab/agents` chứa:

- `supervisor.py`: chọn route tiếp theo.
- `researcher.py`: tạo research notes từ query và source snippets.
- `analyst.py`: phân tích research notes.
- `writer.py`: viết final answer.
- `critic.py`: kiểm tra nhẹ final answer.

### Core

Thư mục `src/multi_agent_research_lab/core` chứa:

- `schemas.py`: Pydantic schemas.
- `state.py`: shared state của workflow.
- `config.py`: cấu hình hệ thống.
- `errors.py`: custom errors.

### Services

Thư mục `src/multi_agent_research_lab/services` chứa:

- `llm_client.py`: gọi OpenAI API.
- `search_client.py`: mock search source cho lab.

### Workflow

File `src/multi_agent_research_lab/graph/workflow.py` chứa logic
orchestration.

Hiện tại workflow dùng explicit Python orchestration theo hướng
graph-like. Hệ thống chưa dùng LangGraph thật, nhưng logic đã bám theo
mô hình graph routing.

### Evaluation

Thư mục `src/multi_agent_research_lab/evaluation` chứa:

- `benchmark.py`: chạy benchmark và tính metrics.
- `report.py`: render benchmark report.

Script `scripts/run_benchmark.py` dùng để sinh benchmark report.

## 5. Các phần đã hoàn thành

### LLM Client

Đã implement LLM client thật với OpenAI.

Tính năng đã có:

- Đọc API key từ `.env`.
- Gọi OpenAI Chat Completions API.
- Có timeout.
- Có retry với exponential backoff.
- Trả về content, input tokens và output tokens.

### Search Client

Đã implement local mock search.

Search client trả về danh sách `SourceDocument`, giúp Researcher có
source snippets để tạo research notes.

Lý do dùng mock search:

- Không cần Tavily, Bing hoặc SerpAPI key.
- Dễ chạy local.
- Phù hợp phạm vi lab.
- Vẫn chứng minh được luồng `sources -> research_notes`.

### Multi-Agent Workflow

Workflow đã chạy được route:

```text
researcher
  -> analyst
  -> writer
  -> done
```

Mỗi agent ghi trace event vào `ResearchState.trace`.

Trace hiện có:

- Workflow start.
- Supervisor route decisions.
- Researcher run.
- Analyst run.
- Writer run.
- Workflow completion.

### Benchmark

Benchmark đã so sánh:

- Single-agent baseline.
- Multi-agent workflow.

Metrics gồm:

- Latency.
- Estimated cost.
- Quality score heuristic.
- Input tokens.
- Output tokens.
- Error count.
- Route history.
- Trace events.

Output benchmark:

- `reports/benchmark_report.md`
- `reports/benchmark_results.json`

## 6. Cài đặt môi trường

### Tạo virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Hoặc dùng `.venv`:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### Cài dependencies

```powershell
pip install -e ".[dev]"
```

Nếu thiếu package OpenAI:

```powershell
pip install openai
```

## 7. Cấu hình biến môi trường

Tạo file `.env` từ `.env.example`.

Windows PowerShell:

```powershell
copy .env.example .env
```

Nội dung `.env` cần có:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=60
LLM_INPUT_COST_PER_1K=0.00015
LLM_OUTPUT_COST_PER_1K=0.00060
```

Lưu ý:

- Không commit `.env`.
- Không hard-code API key trong source code.
- Đảm bảo `.env` nằm ở root project.

## 8. Chạy test

Do Windows PowerShell không có sẵn `make`, dùng lệnh sau:

```powershell
python -m pytest
```

Kết quả kỳ vọng:

```text
7 passed
```

## 9. Chạy single-agent baseline

Để tránh dòng lệnh quá dài trong PowerShell, có thể dùng biến query:

```powershell
$q = "Research GraphRAG state-of-the-art"
python -m multi_agent_research_lab.cli baseline --query $q
```

Baseline dùng một LLM call để xử lý toàn bộ task.

Output gồm:

- Final answer.
- Latency.
- Input tokens.
- Output tokens.
- Cost estimate nếu có.

## 10. Chạy multi-agent workflow

Dùng biến query để command dễ đọc:

```powershell
$q = "Research GraphRAG state-of-the-art"
python -m multi_agent_research_lab.cli multi-agent --query $q
```

Kết quả kỳ vọng:

- Route: `researcher -> analyst -> writer -> done`.
- Iterations: `4`.
- Errors: `0`.
- Có final answer.
- Có trace events.
- Có sources.
- Có research notes và analysis notes.

## 11. Chạy benchmark

```powershell
python scripts\run_benchmark.py
```

Benchmark chạy 3 queries:

1. Research GraphRAG state-of-the-art and write a 500-word summary.
2. Compare single-agent and multi-agent systems for research tasks.
3. Explain common failure modes of multi-agent orchestration and how to
   fix them.

Sau khi chạy xong, hệ thống sinh ra:

- `reports/benchmark_report.md`
- `reports/benchmark_results.json`

## 12. Tóm tắt kết quả benchmark

Kết quả benchmark cho thấy:

- Single-agent baseline nhanh hơn.
- Single-agent baseline rẻ hơn.
- Multi-agent workflow chậm hơn vì dùng nhiều LLM calls.
- Multi-agent workflow có traceability tốt hơn.
- Multi-agent workflow tạo được intermediate artifacts như
  `research_notes` và `analysis_notes`.
- Multi-agent workflow dễ debug hơn nhờ route history và trace events.

Trade-off chính:

- Single-agent phù hợp với task đơn giản, cần tốc độ và chi phí thấp.
- Multi-agent phù hợp với task phức tạp, cần phân tách vai trò và quan
  sát được luồng xử lý.

## 13. Trace evidence

Trace được lưu trong `ResearchState.trace`.

Một successful run có route:

```text
researcher
  -> analyst
  -> writer
  -> done
```

Screenshot trace đã được lưu tại:

- `docs/images/multi_agent_summary.png`
- `docs/images/full_state_trace.png`

Các screenshot này dùng để chứng minh:

- Workflow chạy đủ các agent.
- Supervisor route đúng.
- Có trace events.
- Không có lỗi trong run.

## 14. Failure modes và cách fix

### Failure Mode 1: Researcher tạo notes quá chung chung

Nguyên nhân:

- Prompt quá rộng.
- Source grounding chưa đủ mạnh.

Cách fix:

- Tích hợp external search thật.
- Yêu cầu Researcher tạo notes dựa trên source snippets.
- Thêm citation coverage check.

### Failure Mode 2: Analyst lặp lại Researcher

Nguyên nhân:

- Role separation chưa đủ rõ.
- Prompt Analyst chưa ép phân tích sâu.

Cách fix:

- Yêu cầu Analyst tập trung vào claim, trade-off, risk và limitation.
- Thêm validation để phát hiện analysis quá giống research notes.

### Failure Mode 3: Writer không tuân thủ format

Nguyên nhân:

- Chưa có output validation sau generation.

Cách fix:

- Validate word count.
- Validate required sections.
- Retry Writer nếu output chưa đạt.

### Failure Mode 4: Multi-agent tăng latency và cost

Nguyên nhân:

- Multi-agent dùng nhiều LLM calls hơn baseline.

Cách fix:

- Dùng model nhỏ hơn cho Researcher hoặc Analyst.
- Cache research notes.
- Early stop khi đủ thông tin.
- Chỉ gọi Critic khi cần.

## 15. Hạn chế hiện tại

Hệ thống hiện tại vẫn còn một số hạn chế:

- Search client đang dùng local mock, chưa phải external search thật.
- Quality score là heuristic-based, chưa phải human evaluation.
- Cost là estimated cost, chưa phải billing thật.
- Workflow chưa dùng LangGraph đầy đủ.
- Benchmark chỉ dùng 3 queries, phù hợp lab-scale.
- Critic Agent chưa được nối vào workflow chính.

## 16. Hướng cải thiện tiếp theo

Các hướng có thể phát triển thêm:

- Tích hợp Tavily, Bing, SerpAPI hoặc internal document search.
- Thay mock search bằng external search thật.
- Thêm LangGraph workflow.
- Thêm LangSmith hoặc Langfuse tracing.
- Nối Critic Agent vào workflow chính.
- Thêm LLM-as-judge hoặc multi-judge evaluation.
- Thêm citation coverage scoring.
- Thêm output validation cho final answer.
- Mở rộng benchmark dataset.

## 17. Deliverables

Các deliverables chính của bài lab:

- GitHub repo cá nhân.
- Screenshot trace.
- `reports/benchmark_report.md`.
- `reports/benchmark_results.json`.
- Failure mode analysis trong benchmark report.
- Design document tại `docs/design_template.md`.

## 18. Ghi chú chạy trên Windows

Một số lệnh trong README gốc dùng cú pháp Linux hoặc macOS.

Trên Windows PowerShell:

- Không dùng `make test` nếu chưa cài GNU Make.
- Dùng `python -m pytest` thay cho `make test`.
- Không dùng dấu `\` để xuống dòng command.
- Nếu cần xuống dòng trong PowerShell, dùng dấu backtick.
- Cách dễ nhất là dùng biến `$q` cho query dài.

Ví dụ:

```powershell
$q = "Research GraphRAG state-of-the-art"
python -m multi_agent_research_lab.cli multi-agent --query $q
```

## 19. Trạng thái hiện tại

Trạng thái sau khi hoàn thành lab:

- LLM client: hoàn thành.
- Search client mock: hoàn thành.
- Supervisor routing: hoàn thành.
- Researcher Agent: hoàn thành.
- Analyst Agent: hoàn thành.
- Writer Agent: hoàn thành.
- Critic Agent: hoàn thành ở mức lightweight check.
- Workflow: hoàn thành ở mức explicit graph-like orchestration.
- Trace: hoàn thành ở mức local trace.
- Benchmark report: hoàn thành.
- Design document: hoàn thành.
- Unit tests: pass.
