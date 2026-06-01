"""
Mock tools for the Doctor-Finder ReAct Agent.

All data is seeded in-memory and deterministic so traces are reproducible
during grading. Each tool returns a dict (success or error branch) and never
raises for expected business errors — except get_availability which simulates
a real TimeoutError for a specific doctor id (to exercise retry/failure handling).
"""
from typing import List, Dict, Any

from src.tools.seed_data import SPECIALTY_RULES, URGENT_KEYWORDS, DOCTORS, SCHEDULES

# Mutable copy of schedules so bookings can take slots without touching seed data.
_SCHEDULES: Dict[str, List[str]] = {k: list(v) for k, v in SCHEDULES.items()}


# --- Tools -----------------------------------------------------------------

def classify_specialty(symptoms: List[str]) -> Dict[str, Any]:
    """Map patient symptoms to a medical specialty (with urgency flag)."""
    if not symptoms or all(not s.strip() for s in symptoms):
        return {"error": "unclear_symptoms"}

    text = " ".join(symptoms).lower()
    for keywords, result in SPECIALTY_RULES:
        if any(kw in text for kw in keywords):
            out = dict(result)
            # Escalate urgency if any severe symptom is present.
            if any(kw in text for kw in URGENT_KEYWORDS):
                out["urgent"] = True
            return out

    # Too vague to map to a known specialty.
    return {"error": "unclear_symptoms"}


def search_doctors(specialty: str) -> List[Dict[str, Any]]:
    """Return doctors for a specialty (empty list if none)."""
    return [dict(d) for d in DOCTORS.get(specialty, [])]


def get_availability(doctor_id: str, time_window: List[str]) -> Dict[str, Any]:
    """Return free slots for a doctor within the patient's time windows."""
    if doctor_id == "BS99":
        # Simulate an unresponsive backend so the agent can exercise retry logic.
        raise TimeoutError(f"get_availability timed out for {doctor_id}")

    if doctor_id not in _SCHEDULES:
        return {"doctor_id": doctor_id, "free_slots": [], "reason": "no_published_schedule"}

    return {"doctor_id": doctor_id, "free_slots": list(_SCHEDULES[doctor_id])}


# Bookings made this process (mock persistence) + an incrementing id counter.
_BOOKINGS: Dict[str, Dict[str, Any]] = {}


def book_appointment(doctor_id: str, slot: str) -> Dict[str, Any]:
    """Book an appointment for a doctor at a slot.

    IRREVERSIBLE action — the agent must only call this after the patient has
    explicitly confirmed. The slot must be one the doctor actually has free.
    """
    free = _SCHEDULES.get(doctor_id, [])
    if slot not in free:
        return {"status": "failed", "reason": "slot_unavailable",
                "doctor_id": doctor_id, "slot": slot}

    booking_id = f"BK{len(_BOOKINGS) + 1:04d}"
    _SCHEDULES[doctor_id] = [s for s in free if s != slot]  # slot now taken
    record = {"status": "confirmed", "booking_id": booking_id,
              "doctor_id": doctor_id, "slot": slot}
    _BOOKINGS[booking_id] = record
    return record
