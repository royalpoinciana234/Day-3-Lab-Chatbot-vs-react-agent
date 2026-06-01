# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Văn Phúc
- **Student ID**: 2A202600539
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

- **Modules Implemented**: `src/tools/doctor_tools.py`, `src/tools/registry.py`, `src/tools/seed_data.py`, `src/tools/__init__.py`
- **Code Highlights**: Thiết kế và triển khai 4 tools: `classify_specialty`, `search_doctors`, `get_availability`, `book_appointment`. Seed data: 10 chuyên khoa, 21 bác sĩ với các trạng thái đa dạng (có lịch / hết slot / chưa công bố lịch / timeout). `registry.py` quản lý tool lookup cho agent.
- **Documentation**: Mỗi tool có `args_schema` tách biệt khỏi mô tả tự nhiên. `book_appointment` được mô tả rõ "KHÔNG THỂ HOÀN TÁC — chỉ gọi sau xác nhận" để định hướng hành vi agent. Tool description là hợp đồng với LLM.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: `get_availability` cho BS99 ném `TimeoutError` — agent không xử lý được, crash thay vì tiếp tục với bác sĩ khác.
- **Log Source**: `logs/*.log` — `AGENT_ERROR: TOOL_TIMEOUT` tại bước gọi `get_availability(doctor_id="BS99")`.
- **Diagnosis**: `_execute_tool` không có `except` riêng cho `TimeoutError`, lỗi bubble up và terminate agent loop.
- **Solution**: Wrap tool call trong `try/except Exception` — lỗi timeout trả về Observation mô tả lỗi thay vì crash. Agent đọc Observation, tự chuyển sang bác sĩ khác trong bước tiếp theo.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Tool description chất lượng cao ảnh hưởng trực tiếp đến chất lượng Thought — LLM chọn đúng tool và truyền đúng tham số khi schema rõ ràng. Chatbot không có tool nên không cần lo điều này.
2. **Reliability**: Agent kém hơn Chatbot khi tool spec mơ hồ: LLM sinh sai tham số → PARSE_ERROR → loop hỏng. Chatbot không có điểm thất bại này.
3. **Observation**: Observation từ tool phải đủ thông tin để LLM quyết định bước kế — nếu trả về quá ít data (chỉ `true/false`), agent không biết phải làm gì tiếp. Seed data thiết kế cờ `has_schedule`, `urgent`, `no_published_schedule` để Observation phong phú hơn.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thay seed in-memory bằng Postgres + API lịch khám thật; thêm tool `cancel_appointment` với soft-delete.
- **Safety**: Thêm tool `check_emergency` — nếu triệu chứng cờ `urgent=true`, agent ưu tiên cảnh báo cấp cứu trước khi tìm bác sĩ.
- **Performance**: Tool `search_doctors` hiện scan toàn bộ seed — index theo chuyên khoa để scale lên hàng nghìn bác sĩ.
