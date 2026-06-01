# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Tiền Anh Kiệt
- **Student ID**: 2A202600961
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

- **Modules Implemented**: `src/agent/agent.py`
- **Code Highlights**: Triển khai vòng lặp ReAct (`Thought → Action → Observation`): parse regex để tách Action/Final Answer, gọi `_execute_tool`, nối Observation vào scratchpad, giữ scratchpad qua các lượt hội thoại để xác nhận đặt lịch dùng đúng `doctor_id`/`slot` đã quan sát.
- **Documentation**: Agent nhận input → LLM sinh Thought + Action → parse → nếu Final Answer thì dừng, nếu Action thì gọi tool → nối Observation → lặp. Guardrails: `max_steps`, loop-guard (action lặp 3 lần), không tự đặt lịch trước khi user xác nhận.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Parser cắt nhầm dấu `)` trong chuỗi tham số — `book_appointment(doctor_id="BS01", slot="14:30 (04/06/2026)")` bị cắt cụt tại `)` đầu tiên bên trong chuỗi → `unterminated string`.
- **Log Source**: `logs/*.log` — `AGENT_ERROR: PARSE_ERROR` với action string bị truncate.
- **Diagnosis**: Regex non-greedy `(.*?)\)` dừng ở ký tự `)` đầu tiên gặp được, không phân biệt `)` trong chuỗi hay `)` đóng của Action.
- **Solution**: Đổi sang greedy + bỏ `DOTALL` (bám 1 dòng, match `)` cuối cùng). Thêm `except Exception` trong `_execute_tool` để lỗi parse tham số trả về Observation thay vì crash agent.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Block `Thought` buộc LLM phải "lập luận trung gian" trước khi hành động — tương tự chain-of-thought. Chatbot bỏ qua bước này, trả lời ngay nên dễ hallucinate hành động.
2. **Reliability**: Agent thất bại khi model yếu (Phi-3): không theo dõi được trạng thái, lặp action vô hạn. Chatbot ổn định hơn trên model nhỏ vì chỉ cần 1 lần generate.
3. **Observation**: Observation là cơ chế grounding — mọi slot/bác sĩ trong Final Answer đều đến từ Observation thật, không phải từ tham số huấn luyện của LLM. Nếu không có Observation, Agent sẽ bịa dữ liệu như Chatbot.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thay regex parser bằng function-calling gốc của provider (JSON schema) để parser bền hơn và không phụ thuộc format text.
- **Safety**: Tóm tắt/cắt scratchpad khi hội thoại dài để kiểm soát token và tránh context overflow.
- **Performance**: Chuyển sang LangGraph cho nhánh multi-agent phức tạp; thêm RAG để agent tra cứu kiến thức y khoa thay vì dựa hoàn toàn vào LLM.
