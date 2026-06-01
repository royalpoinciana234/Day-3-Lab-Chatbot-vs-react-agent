# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Quang Hoà
- **Student ID**: 2A202600986
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

- **Modules Implemented**: `app.py`, `main.py`, `src/core/chatbot.py`
- **Code Highlights**: Triển khai Chatbot baseline — nhận input người dùng, gọi LLM một lần duy nhất và trả về câu trả lời. Không dùng tool, không có vòng lặp ReAct.
- **Documentation**: `chatbot.py` đóng vai trò baseline đối chứng: mỗi lượt hội thoại chỉ tạo ra 1 LLM request, không có scratchpad, không có Observation. Kết quả được so sánh trực tiếp với Agent trong `scripts/run_experiments.py`.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Chatbot trả lời chung chung, không thực hiện được hành động cụ thể (tìm bác sĩ, đặt lịch) trên các truy vấn multi-step.
- **Log Source**: `logs/*.log` — so sánh `LLM_METRIC` giữa Chatbot và Agent cho cùng input.
- **Diagnosis**: Chatbot không có cơ chế gọi tool, toàn bộ "hành động" chỉ là văn bản tư vấn sinh bởi LLM. Với câu hỏi "Đau ngực, khó thở, rảnh chiều T5", Chatbot chỉ khuyên đi khám tim mạch — không tìm được bác sĩ hay slot cụ thể.
- **Solution**: Đây là giới hạn thiết kế có chủ ý của Chatbot baseline — dùng để làm nổi bật ưu điểm của ReAct Agent, không phải lỗi cần sửa.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Chatbot không có bước `Thought` — LLM trả lời ngay dựa trên tham số huấn luyện. Agent có `Thought` để phân tích tình huống trước khi chọn tool, giúp tránh hành động bừa.
2. **Reliability**: Agent kém hơn Chatbot ở câu hỏi tư vấn đơn thuần (chi phí ~3× token, latency ~3×). Với câu hỏi không cần dữ liệu thật, Chatbot nhanh và rẻ hơn.
3. **Observation**: Chatbot không có Observation — không thể cập nhật trạng thái sau mỗi bước. Agent dùng Observation từ tool để quyết định bước tiếp theo, tránh hallucination về slot/bác sĩ.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thêm streaming response để giảm perceived latency khi Agent cần nhiều bước.
- **Safety**: Chatbot baseline nên có guardrail nhận diện câu hỏi y tế khẩn cấp và cảnh báo người dùng gọi cấp cứu.
- **Performance**: Cache kết quả `classify_specialty` cho các triệu chứng phổ biến để giảm LLM call lặp lại.
