# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Vũ Đình Phượng
- **Student ID**: 2A202600634
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

- **Modules Implemented**: `tests/test_agent.py`, `tests/test_tools.py`, `tests/test_local.py`, `report/group_report/GROUP_REPORT_C5.md`
- **Code Highlights**: Viết test suite kiểm tra 3 happy-path (đặt lịch thành công, triệu chứng mơ hồ → hỏi lại, đa khoa → hỏi khung giờ) và các failure case (PARSE_ERROR, HALLUCINATED_TOOL, REPEATED_ACTION_LOOP). Đánh giá kết quả Agent vs Chatbot thủ công trên 3 truy vấn chuẩn.
- **Documentation**: Test cases phủ toàn bộ nhánh nghiệp vụ trong flowchart: classify → search → availability → book. Mỗi test assert cả output lẫn số tool call để phát hiện regression khi refactor agent.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: `test_agent.py` fail ngẫu nhiên — agent đôi khi trả Final Answer sau 2 bước, đôi khi cần 4 bước cho cùng input, khiến assert cứng số bước bị vỡ.
- **Log Source**: `logs/*.log` — so sánh 2 run: run 1 `AGENT_STEP` count = 2, run 2 = 4 với cùng query "Đau ngực, khó thở, rảnh chiều T5".
- **Diagnosis**: LLM non-deterministic — temperature > 0 khiến số bước thay đổi giữa các lần chạy. Test assert `step_count == 3` là quá cứng.
- **Solution**: Đổi assertion sang kiểm tra *kết quả* (Final Answer chứa tên bác sĩ + slot hợp lệ) thay vì số bước. Thêm `assert step_count <= max_steps` thay vì bằng cứng.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Qua quá trình viết test, nhận thấy Agent cần test chiến lược khác Chatbot — không thể assert output string cứng vì Thought/Action biến động. Phải test hành vi (tool nào được gọi, thứ tự nào) thay vì text output.
2. **Reliability**: Agent khó test hơn Chatbot vì có nhiều điểm thất bại (parse, tool, loop). Chatbot chỉ có 1 điểm thất bại (LLM call). Trade-off: Agent mạnh hơn nhưng test coverage phức tạp hơn nhiều.
3. **Observation**: Evaluation thủ công trên 3 truy vấn đủ để xác nhận happy-path nhưng chưa đủ thống kê. Cần mở rộng test set để có success rate đáng tin cậy hơn.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Tự động hóa evaluation bằng LLM-as-judge — dùng một LLM khác chấm điểm Final Answer thay vì đánh giá thủ công.
- **Safety**: Thêm regression test chạy tự động trên CI/CD — phát hiện sớm khi thay đổi prompt/tool làm vỡ happy-path.
- **Performance**: Mở rộng test set lên 20–50 truy vấn đa dạng để có success rate thống kê chắc hơn; đo variance giữa các lần chạy.
