# Flowchart — Doctor-Finder ReAct Agent

Luồng xử lý của agent theo kịch bản (đính kèm cùng trace cho Deliverable cuối ngày).

## 1. Vòng lặp ReAct tổng quát (generic loop + guardrail)

```mermaid
flowchart TD
    START([User input: triệu chứng + khung giờ rảnh]) --> INIT[Khởi tạo prompt + system prompt<br/>step = 0, max_steps = 5]
    INIT --> GEN[LLM.generate Thought + Action]
    GEN --> PARSE{Parse được<br/>Action / Final Answer?}

    PARSE -->|Parse lỗi| ERR_PARSE[log AGENT_ERROR: PARSE_ERROR]
    ERR_PARSE --> RETRY{step < max_steps?}

    PARSE -->|Final Answer| GUARD{Có hành động<br/>irreversible?<br/>vd đặt lịch}
    PARSE -->|Action| TOOLCHK{Tool tồn tại<br/>trong registry?}

    TOOLCHK -->|Không| ERR_HALL[log AGENT_ERROR: HALLUCINATED_TOOL<br/>Observation = Tool not found]
    TOOLCHK -->|Có| EXEC[_execute_tool: gọi func, parse args]
    ERR_HALL --> APPEND
    EXEC --> APPEND[Append Observation vào prompt<br/>log AGENT_STEP]
    APPEND --> RETRY

    RETRY -->|Còn step| INC[step += 1] --> GEN
    RETRY -->|Hết step| ERR_MAX[log AGENT_ERROR: MAX_STEPS_EXCEEDED] --> FAIL([Trả lỗi timeout])

    GUARD -->|Có| CONFIRM[KHÔNG tự thực thi<br/>Gợi ý + yêu cầu human confirmation]
    GUARD -->|Không| ANSWER([Final Answer cho user])
    CONFIRM --> ANSWER
```

## 2. Luồng quyết định nghiệp vụ (đúng trace mẫu)

```mermaid
flowchart TD
    A([Bắt đầu]) --> B[classify_specialty<br/>symptoms]
    B --> C{Kết quả?}
    C -->|error: unclear_symptoms| C1([Hỏi lại bệnh nhân<br/>làm rõ triệu chứng])
    C -->|specialty = Tim mạch| D[search_doctors<br/>specialty]

    D --> E{Có bác sĩ?}
    E -->|empty list| E1([Báo: chưa có bác sĩ khoa này])
    E -->|BS01, BS02 có lịch · BS03 chưa| F[Tách 2 nhánh]

    F --> G[Nhánh A: bác sĩ CÓ lịch<br/>get_availability cho BS01, BS02<br/>trong khung user rảnh]
    F --> H[Nhánh B: bác sĩ CHƯA có lịch<br/>BS03 từ kết quả search<br/>không gọi thêm tool]

    G --> G1[BS01 → 14:30 T5 ✓<br/>BS02 → rỗng ✗]
    H --> H1[BS03 → gợi ý chờ<br/>phòng khám xếp lịch]

    G1 --> STOP{Điều kiện dừng:<br/>≥1 bác sĩ khớp giờ<br/>AND đã xử lý nhánh chưa-có-lịch?}
    H1 --> STOP
    STOP -->|Đủ evidence| FINAL([Final Answer:<br/>BS. Lan 14:30 T5 +<br/>gợi ý BS. Mai chờ xếp lịch +<br/>cảnh báo cấp cứu nếu nặng])
    STOP -->|Chưa đủ| D
```

## Điểm grounding & an toàn (bám rubric)
- **Thứ tự tool đúng:** classify → search → availability (không gọi sai thứ tự).
- **Không bịa dữ liệu:** mọi slot đều từ Observation.
- **Guardrail:** agent KHÔNG tự đặt lịch — booking irreversible, cần human confirmation.
- **Điều kiện dừng rõ ràng:** đủ evidence (≥1 bác sĩ khớp giờ + xử lý xong nhánh chưa-có-lịch) → dừng, không gọi thừa tool.
