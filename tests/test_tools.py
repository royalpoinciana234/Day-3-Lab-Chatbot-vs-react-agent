"""Unit tests for the mock doctor tools (happy + error paths)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.doctor_tools import (
    classify_specialty, search_doctors, get_availability, book_appointment,
)
from src.tools import TOOLS


def test_classify_specialty_cardiology():
    result = classify_specialty(["đau ngực", "khó thở", "hồi hộp tim đập nhanh"])
    assert result["specialty"] == "Tim mạch"
    assert "Hô hấp" in result["alternatives"]


def test_classify_specialty_unclear():
    assert classify_specialty([]) == {"error": "unclear_symptoms"}
    assert classify_specialty(["mệt mệt"]) == {"error": "unclear_symptoms"}


def test_search_doctors_found():
    doctors = search_doctors("Tim mạch")
    ids = [d["doctor_id"] for d in doctors]
    # Trace-critical trio stays first, in order.
    assert ids[:3] == ["BS01", "BS02", "BS03"]
    bs03 = next(d for d in doctors if d["doctor_id"] == "BS03")
    assert bs03["has_schedule"] is False  # BS03 chưa công bố lịch


def test_search_doctors_empty():
    assert search_doctors("Khoa không tồn tại") == []


def test_classify_more_specialties():
    assert classify_specialty(["đau bụng", "tiêu chảy"])["specialty"] == "Tiêu hóa"
    assert classify_specialty(["nổi mẩn", "ngứa"])["specialty"] == "Da liễu"
    assert classify_specialty(["mờ mắt", "nhức mắt"])["specialty"] == "Mắt"


def test_classify_urgent_flag():
    result = classify_specialty(["đau ngực dữ dội", "khó thở"])
    assert result["specialty"] == "Tim mạch"
    assert result["urgent"] is True


def test_search_doctors_diverse_specialties():
    # Dataset now covers many specialties.
    for specialty in ["Hô hấp", "Thần kinh", "Tiêu hóa", "Da liễu", "Nhi", "Mắt"]:
        assert len(search_doctors(specialty)) >= 1


def test_get_availability_with_slot():
    result = get_availability("BS01", ["2026-06-04 chiều"])
    assert result["free_slots"] == ["2026-06-04 14:30"]


def test_get_availability_empty():
    assert get_availability("BS02", ["x"])["free_slots"] == []


def test_get_availability_no_published_schedule():
    result = get_availability("BS03", ["x"])
    assert result["free_slots"] == []
    assert result["reason"] == "no_published_schedule"


def test_get_availability_timeout():
    with pytest.raises(TimeoutError):
        get_availability("BS99", ["x"])


def test_book_appointment_success():
    result = book_appointment("BS01", "2026-06-04 14:30")
    assert result["status"] == "confirmed"
    assert result["booking_id"].startswith("BK")
    # Slot is now taken -> a second booking of the same slot fails.
    again = book_appointment("BS01", "2026-06-04 14:30")
    assert again["status"] == "failed"
    assert again["reason"] == "slot_unavailable"


def test_book_appointment_invalid_slot():
    result = book_appointment("BS02", "khung giờ không có thật")
    assert result["status"] == "failed"
    assert result["reason"] == "slot_unavailable"


def test_registry_contract():
    assert [t["name"] for t in TOOLS] == [
        "classify_specialty", "search_doctors", "get_availability", "book_appointment",
    ]
    for tool in TOOLS:
        assert set(tool) >= {"name", "description", "func", "args_schema"}
        assert callable(tool["func"])
