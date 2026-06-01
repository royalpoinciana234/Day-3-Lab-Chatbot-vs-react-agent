"""
Seed dataset for the mock doctor tools — kept separate from tool logic so the
data can grow without bloating doctor_tools.py.

Invariants the agent/tests rely on:
- BS01/BS02/BS03 stay in "Tim mạch" (trace) with BS03 has_schedule=False.
- BS01 free slot "2026-06-04 14:30"; BS02 has schedule but no free slot.
- BS04 ("Hô hấp") free slot "2026-06-06 09:00".
- A doctor with has_schedule=True MUST have a SCHEDULES entry (possibly empty);
  has_schedule=False MUST be absent from SCHEDULES.
- "BS99" is reserved as a sentinel that simulates a backend timeout.
"""

# Symptom-classification rules (ordered: first keyword match wins).
SPECIALTY_RULES = [
    (("đau ngực", "khó thở", "hồi hộp", "tim đập", "đánh trống ngực", "huyết áp"),
     {"specialty": "Tim mạch", "alternatives": ["Hô hấp"], "urgent": False}),
    (("ho", "sổ mũi", "viêm phổi", "đờm", "hụt hơi", "viêm phế quản"),
     {"specialty": "Hô hấp", "alternatives": ["Tai mũi họng"], "urgent": False}),
    (("đau đầu", "chóng mặt", "mất ngủ", "tê tay", "đau nửa đầu", "run tay"),
     {"specialty": "Thần kinh", "alternatives": [], "urgent": False}),
    (("đau bụng", "tiêu chảy", "táo bón", "ợ chua", "buồn nôn", "đầy hơi"),
     {"specialty": "Tiêu hóa", "alternatives": [], "urgent": False}),
    (("nổi mẩn", "ngứa", "mụn", "phát ban", "dị ứng da", "viêm da"),
     {"specialty": "Da liễu", "alternatives": [], "urgent": False}),
    (("đau lưng", "đau khớp", "đau vai", "cứng khớp", "đau gối", "thoái hóa"),
     {"specialty": "Cơ xương khớp", "alternatives": [], "urgent": False}),
    (("tiểu nhiều", "khát nước", "sụt cân", "tuyến giáp", "đường huyết"),
     {"specialty": "Nội tiết", "alternatives": [], "urgent": False}),
    (("ù tai", "nghẹt mũi", "đau tai", "khàn tiếng", "ngứa họng", "viêm họng"),
     {"specialty": "Tai mũi họng", "alternatives": ["Hô hấp"], "urgent": False}),
    (("trẻ sốt", "trẻ ho", "con tôi", "bé bị", "trẻ em", "cháu bị"),
     {"specialty": "Nhi", "alternatives": [], "urgent": False}),
    (("mờ mắt", "đau mắt", "nhức mắt", "đỏ mắt", "chảy nước mắt", "cận thị"),
     {"specialty": "Mắt", "alternatives": [], "urgent": False}),
]

# Severe symptoms that flag a case as urgent regardless of specialty.
URGENT_KEYWORDS = (
    "ngất", "co giật", "khó thở dữ dội", "đau ngực dữ dội",
    "mất ý thức", "chảy máu nhiều", "liệt", "nói khó",
)

# Doctors per specialty. has_schedule=False => no published schedule.
DOCTORS = {
    "Tim mạch": [
        {"doctor_id": "BS01", "name": "BS. Lan", "has_schedule": True},
        {"doctor_id": "BS02", "name": "BS. Hùng", "has_schedule": True},
        {"doctor_id": "BS03", "name": "BS. Mai", "has_schedule": False},
        {"doctor_id": "BS05", "name": "BS. Sơn", "has_schedule": True},
    ],
    "Hô hấp": [
        {"doctor_id": "BS04", "name": "BS. Phúc", "has_schedule": True},
        {"doctor_id": "BS06", "name": "BS. Hoa", "has_schedule": True},
        {"doctor_id": "BS07", "name": "BS. Đạt", "has_schedule": False},
    ],
    "Thần kinh": [
        {"doctor_id": "BS08", "name": "BS. Linh", "has_schedule": True},
        {"doctor_id": "BS09", "name": "BS. Tâm", "has_schedule": True},
    ],
    "Tiêu hóa": [
        {"doctor_id": "BS10", "name": "BS. Nam", "has_schedule": True},
        {"doctor_id": "BS11", "name": "BS. Quân", "has_schedule": False},
    ],
    "Da liễu": [
        {"doctor_id": "BS12", "name": "BS. Hà", "has_schedule": True},
        {"doctor_id": "BS13", "name": "BS. Vy", "has_schedule": True},
    ],
    "Cơ xương khớp": [
        {"doctor_id": "BS14", "name": "BS. Bình", "has_schedule": True},
        {"doctor_id": "BS15", "name": "BS. Trang", "has_schedule": False},
    ],
    "Nội tiết": [
        {"doctor_id": "BS16", "name": "BS. Khoa", "has_schedule": True},
    ],
    "Tai mũi họng": [
        {"doctor_id": "BS17", "name": "BS. Yến", "has_schedule": True},
        {"doctor_id": "BS18", "name": "BS. Dũng", "has_schedule": True},
    ],
    "Nhi": [
        {"doctor_id": "BS19", "name": "BS. Thảo", "has_schedule": True},
        {"doctor_id": "BS20", "name": "BS. Long", "has_schedule": True},
    ],
    "Mắt": [
        {"doctor_id": "BS21", "name": "BS. Châu", "has_schedule": True},
    ],
}

# Free slots per scheduled doctor (empty list = has schedule but fully booked).
SCHEDULES = {
    "BS01": ["2026-06-04 14:30"],
    "BS02": [],
    "BS04": ["2026-06-06 09:00"],
    "BS05": ["2026-06-04 15:00", "2026-06-05 09:30"],
    "BS06": ["2026-06-04 08:00"],
    "BS08": ["2026-06-05 10:00", "2026-06-06 14:00"],
    "BS09": [],
    "BS10": ["2026-06-04 16:00"],
    "BS12": ["2026-06-06 10:30", "2026-06-06 15:00"],
    "BS13": ["2026-06-05 13:00"],
    "BS14": ["2026-06-07 09:00"],
    "BS16": ["2026-06-04 11:00"],
    "BS17": ["2026-06-05 08:30"],
    "BS18": [],
    "BS19": ["2026-06-04 14:00", "2026-06-06 10:00"],
    "BS20": ["2026-06-07 15:30"],
    "BS21": ["2026-06-05 16:00"],
}
