# app/agents/planning.py

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from app.graph.state import AgentState


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _estimate_travel_minutes(distance_km: float) -> int:
    """
    Estimate travel time based on city conditions.
    """
    if distance_km <= 0:
        return 10

    minutes = (distance_km / 20.0) * 60.0  # avg 20 km/h
    minutes += 10  # buffer
    return max(10, round(minutes))


from datetime import datetime, timezone, timedelta

def _compute_pickup_time(expiry_hours: int, travel_minutes: int) -> str:
    """
    Decide a practical pickup time based on travel time and expiry.
    """
    now = datetime.now(timezone.utc)

    # Start pickup after a realistic dispatch buffer
    dispatch_buffer_minutes = 15
    estimated_pickup = now + timedelta(minutes=dispatch_buffer_minutes + travel_minutes)

    # Keep it safely before expiry
    latest_safe_time = now + timedelta(hours=expiry_hours) - timedelta(minutes=20)

    if estimated_pickup > latest_safe_time:
        estimated_pickup = latest_safe_time

    return estimated_pickup.isoformat()


def planning_agent(state: AgentState) -> AgentState:
    """
    Convert match_result into a pickup_request plan.

    Expects:
        - state['donation']
        - state['match_result']
    Produces:
        - state['pickup_request']
    """
    updated_state: AgentState = dict(state)

    try:
        donation = updated_state.get("donation")
        match_result = updated_state.get("match_result")

        if not isinstance(donation, dict):
            raise ValueError("'donation' must exist before planning")
        if not isinstance(match_result, dict):
            raise ValueError("'match_result' must exist before planning")

        donation_id = _clean_text(donation.get("id"))
        recommended = match_result.get("recommended", {})

        ngo_id = _clean_text(recommended.get("ngo_id"))

        expiry_hours = int(donation.get("expiry_hours", 0))
        distance_km = _to_float(recommended.get("distance_km"), default=0.0)

        if not donation_id:
            raise ValueError("'donation.id' is required")
        if not ngo_id:
            raise ValueError("'match_result.ngo_id' is required")
        if expiry_hours < 0:
            raise ValueError("'expiry_hours' cannot be negative")

        # Estimate travel time
        travel_minutes = _estimate_travel_minutes(distance_km)
        pickup_time = _compute_pickup_time(expiry_hours, travel_minutes)

        # Create pickup request
        updated_state["pickup_request"] = {
            "match_id": f"{donation_id}_{ngo_id}",
            "status": "pending",
            "assigned_to": "",  # future: volunteer assignment
            "pickup_time": pickup_time,
            "confirmation_notes": "",
        }

        updated_state["status"] = "planned"

        metadata = dict(updated_state.get("metadata", {}))
        metadata["planned_at"] = datetime.now(timezone.utc).isoformat()
        metadata["estimated_travel_minutes"] = travel_minutes
        metadata["pickup_time"] = pickup_time
        updated_state["metadata"] = metadata

        return updated_state

    except Exception as exc:
        updated_state["status"] = "failed"
        errors = list(updated_state.get("errors", []))
        errors.append(str(exc))
        updated_state["errors"] = errors
        return updated_state