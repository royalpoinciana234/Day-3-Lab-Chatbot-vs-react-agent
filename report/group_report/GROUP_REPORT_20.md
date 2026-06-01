# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: 20
- **Team Members**:   
Nguyễn Quang Hoà - 2A202600986  
Tiền Anh Kiệt - 2A202600961  
Nguyễn Văn Phúc - 2A202600539  
Nguyễn Hoàng Dương - 2A202600849  
Vũ Đình Phượng - 2A202600634  

- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

Hệ thống là một **ReAct Agent tìm bác sĩ** (Doctor-Finder): nhận triệu chứng + khung
giờ rảnh của bệnh nhân → phân loại chuyên khoa → tìm bác sĩ → kiểm tra lịch trống →
gợi ý và đặt lịch *sau khi bệnh nhân xác nhận*. So sánh trực tiếp với Chatbot baseline
(1 lần gọi LLM, không tool).

- **Success Rate (Agent)**: 3/3 truy vấn cho ra hành động đúng & grounded (happy-path
  đặt lịch, triệu chứng mơ hồ → hỏi lại, thiếu khung giờ → hỏi tiếp).
- **Key Outcome**: Trên truy vấn multi-step, **Chatbot chỉ đưa lời khuyên chung chung
  (0/3 hành động cụ thể)**, trong khi **Agent gọi đúng tool, lấy lịch thật và đề xuất
  slot cụ thể**. Agent thắng tuyệt đối ở các tác vụ cần *hành động*; Chatbot nhanh hơn
  và rẻ hơn ở câu hỏi tư vấn đơn thuần.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

Vòng lặp `Thought → Action → Observation` cài trong `src/agent/agent.py`:

```
User input → [LLM sinh Thought + Action] → parse regex
   ├─ Final Answer?  → trả lời, dừng
   └─ Action: tool(args) → _execute_tool → nối Observation vào prompt → lặp
Guardrails: max_steps · loop-guard (action lặp 3 lần) · không tự đặt lịch khi chưa xác nhận
```

Đặc điểm quan trọng:
- Mỗi `Observation` từ tool được **nối lại vào scratchpad** — agent không tự bịa dữ liệu.
- Scratchpad giữ qua các lượt chat (`reset=False`) nên xác nhận đặt lịch dùng đúng `doctor_id`/`slot` đã quan sát được.
- Sơ đồ luồng đầy đủ: `report/group_report/doctor-finder-react-flowchart.md`

### 2.2 Tool Definitions (Inventory)

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `classify_specialty` | `symptoms: list[str]` | Map triệu chứng → chuyên khoa; trả `urgent=True` nếu triệu chứng nặng; lỗi `unclear_symptoms` nếu mơ hồ |
| `search_doctors` | `specialty: str` | Danh sách bác sĩ theo chuyên khoa; cờ `has_schedule` cho biết có lịch không |
| `get_availability` | `doctor_id: str, time_window: list[str]` | Slot trống trong khung giờ bệnh nhân; `no_published_schedule` nếu chưa có lịch; mô phỏng `TimeoutError` (BS99) |
| `book_appointment` | `doctor_id: str, slot: str` | **Đặt lịch (irreversible)** — CHỈ gọi sau khi bệnh nhân xác nhận; chống double-book |

Dữ liệu seed: **10 chuyên khoa, 21 bác sĩ** (`src/tools/seed_data.py`), gồm bác sĩ có lịch / hết slot / chưa công bố lịch.

> **Tool description là hợp đồng với LLM.** `args_schema` tách biệt khỏi mô tả tự nhiên; `book_appointment` ghi rõ "KHÔNG THỂ HOÀN TÁC" để định hướng guardrail.

### 2.3 LLM Providers Used

- **Primary**: Google `gemini-3.1-flash-lite` (SDK mới `google-genai`).
- **Secondary**: OpenAI `gpt-4o` (đổi qua `.env` `DEFAULT_PROVIDER`, không sửa code).
- **Local (đối chứng failure analysis)**: Phi-3-mini-4k (GGUF, llama-cpp, CPU).

---

## 3. Telemetry & Performance Dashboard

Số liệu thật từ `scripts/run_experiments.py --provider google` (Gemini flash-lite), 3 truy vấn × 2 chế độ:

| Chỉ số | Chatbot baseline | ReAct Agent |
| :--- | :--- | :--- |
| LLM requests / task | 1 | 2–4 (theo số bước) |
| Tokens / task (TB) | ~316 | ~2.766 |
| Latency / task (TB) | ~2.1 s | ~5.8 s |
| Cost / task (TB) | ~$0.000054 | ~$0.000163 |
| Hành động cụ thể | ❌ chỉ tư vấn | ✅ tìm bác sĩ + slot + đặt lịch |

- **Per-call latency (Gemini)**: P50 ~1.0 s, P99 ~3.3 s.
- **Tổng cost bộ test**: ~$0.000651 (3 agent runs + 3 chatbot runs).
- **Token ratio (completion/prompt)**: 0.04–0.23 — agent sinh Action ngắn gọn, ít "chatter".

Metrics thu tự động trong `logs/*.log` (JSON-per-line): `LLM_METRIC`, `AGENT_STEP`, `AGENT_ERROR`. Phân tích bằng `scripts/parse_logs.py`.

**Đánh đổi:** Agent tốn ~9× tokens và ~3× latency, đổi lại khả năng *hành động grounded*. Chatbot rẻ/nhanh hơn cho câu hỏi tư vấn đơn thuần.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study 1: Local model copy nguyên cú pháp schema → PARSE_ERROR

- **Provider**: Phi-3-mini (local CPU).
- **Input**: "Tôi đau ngực, khó thở".
- **Trace lỗi**:
  ```
  Action: classify_specialty(symptoms: list[str] — "đau ngực, khó thở")
  AGENT_ERROR: PARSE_ERROR — invalid syntax
  ```
- **Lặp lại**: 5 lần liên tiếp → `MAX_STEPS_EXCEEDED`.
- **Root Cause**: System prompt v1 hiển thị tool dạng `name(arg: type)` → model nhỏ bắt chước, viết luôn `arg: type` thay vì `arg=value`.
- **Fix (v2)**: Ẩn kiểu dữ liệu, thêm block ví dụ **ĐÚNG/SAI** cú pháp `key=value` + 1 worked example.
- **Kết quả**: Loại bỏ hoàn toàn lớp lỗi này.

### Case Study 2: Local model lặp action không tiến triển → REPEATED_ACTION_LOOP

- **Provider**: Phi-3-mini (sau khi fix Case 1).
- **Observation (lỗi)**: Phi-3 gọi `search_doctors("Tim mạch")` 4 lần liên tiếp, không chuyển sang `get_availability` → hết `max_steps` (~40 giây lãng phí).
- **Root Cause**: Model nhỏ không track được state đã làm gì; không suy luận được bước kế tiếp.
- **Fix (v2)**: **Loop-guard** — phát hiện action lặp lần thứ 3 → dừng sớm, log `REPEATED_ACTION_LOOP`.

### Case Study 3: Regex cắt nhầm ")" trong chuỗi slot → PARSE_ERROR

- **Provider**: Gemini.
- **Input**: Bệnh nhân xác nhận đặt lịch; agent sinh `book_appointment(doctor_id="BS01", slot="14:30 (04/06/2026)")`.
- **Root Cause**: Regex non-greedy `(.*?)\)` dừng ở `)` ĐẦU TIÊN (bên trong chuỗi) → cắt cụt → unterminated string.
- **Fix**: Regex greedy `(.*)` + bỏ DOTALL (bám 1 dòng, match `)` cuối). Thêm `except Exception` trong `_execute_tool` để lỗi tham số trả về Observation thay vì crash.

*Tổng số lỗi ghi nhận trong log*: PARSE_ERROR (40), MAX_STEPS_EXCEEDED (15), HALLUCINATED_TOOL (11), REPEATED_ACTION_LOOP (10).

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2 (Phi-3 local)

| | Prompt v1 | Prompt v2 |
| :--- | :--- | :--- |
| Format Action | `arg: type — value` (sai) | `arg=value` (đúng) |
| PARSE_ERROR rate | **100%** | 0% (format hợp lệ) |
| Diff chính | Hiển thị tool với `arg: type` | Ẩn type, thêm ví dụ ĐÚNG/SAI + worked example; loop-guard |

### Experiment 2: Chatbot vs Agent (Gemini flash-lite, dữ liệu thật)

| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| "Đau ngực, khó thở, rảnh chiều T5" | Khuyên đi khám tim mạch (chung) | Tìm BS. Lan + slot 14:30 T5 + hỏi đặt lịch | **Agent** |
| "Mệt mệt trong người" (mơ hồ) | Liệt kê nguyên nhân chung | Nhận diện mơ hồ → hỏi thêm triệu chứng | **Agent** |
| "Đau đầu, chóng mặt, mất ngủ" | Khuyên chung không định hướng | Phân loại Thần kinh + hỏi khung giờ | **Agent** |
| Chi phí & tốc độ | ~$0.00005, ~2.1s | ~$0.00016, ~5.8s | **Chatbot** |

### Experiment 3: Provider comparison (Gemini vs Phi-3 local)

| | Gemini 3.1-flash-lite | Phi-3-mini (CPU) |
| :--- | :--- | :--- |
| Hoàn thành trace | ✅ 4–5 bước | ❌ lỗi format / lặp |
| Latency / bước | ~1 s | ~5–13 s |
| Tuân thủ ReAct format | Ổn định | Dễ vỡ |
| Cost | ~$0.0002/run | $0 (offline) |

---

## 6. Production Readiness Review

- **Security**:
  - Tham số tool parse bằng `ast.literal_eval` — không dùng `eval` tùy ý, chặn code injection.
  - `book_appointment` là irreversible → **bắt buộc human confirmation** trước khi gọi.
  - Slot validate trước khi book — chặn double-booking.

- **Guardrails**:
  - `max_steps` chặn vòng lặp vô hạn (tránh đốt tiền API).
  - Loop-guard dừng khi action lặp 3 lần.
  - Lỗi tool trả về Observation (không crash agent); `TimeoutError` phân loại & xử lý.
  - Agent không bịa dữ liệu — mọi slot/bác sĩ đến từ Observation thật.

- **Scaling (đề xuất)**:
  - Thay seed in-memory bằng DB thật (Postgres) + API lịch khám bệnh viện.
  - Dùng function-calling gốc của provider (JSON schema) thay regex → parser bền hơn với mọi model.
  - Chuyển sang LangGraph/multi-agent cho nhánh phức tạp (đa bệnh viện, đặt lịch tái khám).
  - Thêm RAG cho kiến thức y khoa (triệu chứng → chuyên khoa → bệnh thường gặp).
  - Tóm tắt/cắt scratchpad khi hội thoại dài để kiểm soát token cost.

---

## Phụ lục: Cách tái lập số liệu

```bash
# Cài dependencies
pip install -r requirements.txt

# Sao chép và điền API key
cp .env.example .env

# Chạy thực nghiệm (sinh log)
python scripts/run_experiments.py --provider google

# Phân tích log
python scripts/parse_logs.py

# Demo UI (chat + trace + telemetry)
streamlit run app.py

# CLI multi-turn
python main.py --chat
```

## Câu hỏi còn mở / hạn chế

- **TTFT** (time-to-first-token) chưa đo riêng — hiện có total latency.
- Giá `gemini-3.1-flash-lite` là ước lượng theo tier flash-lite — cần xác nhận chính thức.
- Success rate đánh giá trên 3 truy vấn; nên mở rộng test set để thống kê chắc hơn.

---
