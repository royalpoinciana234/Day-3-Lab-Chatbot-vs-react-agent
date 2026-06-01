# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Hoàng Dương
- **Student ID**: 2A202600849
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

- **Modules Implemented**: `src/telemetry/logger.py`, `src/telemetry/metrics.py`, `scripts/parse_logs.py`, `scripts/run_experiments.py`
- **Code Highlights**: Hệ thống telemetry ghi log JSON-per-line với 3 event type: `LLM_METRIC` (tokens, latency, cost), `AGENT_STEP` (tool call, observation), `AGENT_ERROR` (error-code taxonomy). `parse_logs.py` tổng hợp metrics từ `logs/*.log`. `run_experiments.py` chạy 3 truy vấn × 2 chế độ (Chatbot/Agent) và export kết quả so sánh.
- **Documentation**: Logger inject vào mọi LLM call và tool call — không cần sửa business logic. Metrics thu thập: tokens/task, latency/task, cost/task, token ratio (completion/prompt), error rate theo loại.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Log `AGENT_ERROR: REPEATED_ACTION_LOOP` xuất hiện liên tục với Phi-3 — `search_doctors("Tim mạch")` được gọi 4 lần liên tiếp, không tiến triển sang `get_availability`.
- **Log Source**: `logs/*.log` — chuỗi `AGENT_STEP` liên tiếp với cùng action string, không có bước nào khác xen vào.
- **Diagnosis**: Phi-3 không theo dõi được trạng thái scratchpad — không biết đã gọi `search_doctors` rồi, cứ lặp lại. Metrics cho thấy latency/task lên ~40s (5 bước × ~8s/bước) và cost bị đốt vô ích.
- **Solution**: Loop-guard trong agent: phát hiện action lặp lần thứ 3 → log `REPEATED_ACTION_LOOP` → dừng sớm. Telemetry xác nhận loop-guard cắt từ 5 bước xuống 3 bước, tiết kiệm ~16s và ~40% cost.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Telemetry cho thấy Agent dùng ~9× tokens so với Chatbot — chi phí của việc "suy nghĩ" qua nhiều bước. Phần lớn token là scratchpad (Thought + Observation tích lũy), không phải câu trả lời cuối.
2. **Reliability**: Agent kém hơn Chatbot về độ ổn định trên model yếu — Phi-3 có error rate ~100% (PARSE_ERROR hoặc REPEATED_ACTION_LOOP), Chatbot chạy ổn trên cùng model.
3. **Observation**: Token ratio (completion/prompt) ~0.04–0.23 với Agent: Agent sinh ít text (Action ngắn), nhưng prompt dài dần do scratchpad tích lũy. Cần cắt scratchpad khi hội thoại dài.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Tách telemetry ra service riêng (OpenTelemetry + Jaeger) để trace phân tán khi scale lên multi-agent.
- **Safety**: Thêm cost alert — nếu cost/session vượt ngưỡng, tự động dừng agent và thông báo.
- **Performance**: Đo TTFT (time-to-first-token) riêng biệt thay vì chỉ đo total latency; thêm dashboard realtime thay vì parse log sau.
