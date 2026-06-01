"""
Tool registry — the contract shared between the tools layer (M1) and the
ReAct agent (M2). Each entry: {name, description, func, args_schema}.

The agent reads `description` + `args_schema` to build its system prompt and
calls `func(**kwargs)` to execute a tool.
"""
from src.tools import doctor_tools

TOOLS = [
    {
        "name": "classify_specialty",
        "description": "Map triệu chứng bệnh nhân sang chuyên khoa cần khám.",
        "func": doctor_tools.classify_specialty,
        "args_schema": {"symptoms": "list[str] — danh sách triệu chứng"},
    },
    {
        "name": "search_doctors",
        "description": "Tìm danh sách bác sĩ theo chuyên khoa.",
        "func": doctor_tools.search_doctors,
        "args_schema": {"specialty": "str — tên chuyên khoa"},
    },
    {
        "name": "get_availability",
        "description": "Lấy slot trống của 1 bác sĩ trong các khung giờ bệnh nhân rảnh.",
        "func": doctor_tools.get_availability,
        "args_schema": {
            "doctor_id": "str — mã bác sĩ",
            "time_window": "list[str] — các khung giờ bệnh nhân rảnh",
        },
    },
    {
        "name": "book_appointment",
        "description": ("Đặt lịch khám (HÀNH ĐỘNG KHÔNG THỂ HOÀN TÁC). "
                        "CHỈ gọi sau khi bệnh nhân đã xác nhận đồng ý đặt lịch."),
        "func": doctor_tools.book_appointment,
        "args_schema": {
            "doctor_id": "str — mã bác sĩ",
            "slot": "str — khung giờ cụ thể lấy từ free_slots",
        },
    },
]
