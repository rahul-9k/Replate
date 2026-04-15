
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from app.graph.state import AgentState, Donation


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_int(value: Any, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{field_name}' must be an integer")


def _to_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{field_name}' must be a number")


def _to_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False

    raise ValueError(f"'{field_name}' must be a boolean")


def _normalize_donation(raw: Dict[str, Any]) -> Donation:
    required_fields = [
        "id",
        "source_name",
        "contact_phone",
        "food_type",
        "quantity",
        "is_veg",
        "prepared_at",
        "expiry_hours",
        "pickup_address",
        "pickup_lat",
        "pickup_lng",
        "special_notes",
    ]

    missing = [field for field in required_fields if field not in raw]
    if missing:
        raise ValueError(f"Missing required donation fields: {', '.join(missing)}")

    donation_id = _clean_text(raw.get("id"))
    source_name = _clean_text(raw.get("source_name"))
    contact_phone = _clean_text(raw.get("contact_phone"))
    food_type = _clean_text(raw.get("food_type"))
    prepared_at = _clean_text(raw.get("prepared_at"))
    pickup_address = _clean_text(raw.get("pickup_address"))
    special_notes = _clean_text(raw.get("special_notes"))

    quantity = _to_int(raw.get("quantity"), "quantity")
    expiry_hours = _to_int(raw.get("expiry_hours"), "expiry_hours")
    is_veg = _to_bool(raw.get("is_veg"), "is_veg")
    pickup_lat = _to_float(raw.get("pickup_lat"), "pickup_lat")
    pickup_lng = _to_float(raw.get("pickup_lng"), "pickup_lng")

    if not donation_id:
        raise ValueError("'id' cannot be empty")
    if not source_name:
        raise ValueError("'source_name' cannot be empty")
    if not contact_phone:
        raise ValueError("'contact_phone' cannot be empty")
    if not food_type:
        raise ValueError("'food_type' cannot be empty")
    if not prepared_at:
        raise ValueError("'prepared_at' cannot be empty")
    if not pickup_address:
        raise ValueError("'pickup_address' cannot be empty")
    if quantity <= 0:
        raise ValueError("'quantity' must be greater than 0")
    if expiry_hours < 0:
        raise ValueError("'expiry_hours' cannot be negative")

    return {
        "id": donation_id,
        "source_name": source_name,
        "contact_phone": contact_phone,
        "food_type": food_type.lower(),
        "quantity": quantity,
        "is_veg": is_veg,
        "prepared_at": prepared_at,
        "expiry_hours": expiry_hours,
        "pickup_address": pickup_address,
        "pickup_lat": pickup_lat,
        "pickup_lng": pickup_lng,
        "special_notes": special_notes,
    }


def monitoring_agent(state: AgentState) -> AgentState:
    """
    Validate and normalize the incoming donation payload.

    Expected:
        state["donation"] -> Donation-like dict
    """
    updated_state: AgentState = dict(state)

    try:
        raw_donation = updated_state.get("donation")
        if not isinstance(raw_donation, dict):
            raise ValueError("'donation' must be provided as a dictionary")

        normalized_donation = _normalize_donation(raw_donation)

        updated_state["donation"] = normalized_donation
        updated_state["status"] = "validated"
        updated_state["errors"] = []

        metadata = dict(updated_state.get("metadata", {}))
        metadata["validated_at"] = datetime.now(timezone.utc).isoformat()
        metadata["source"] = "monitoring_agent"
        updated_state["metadata"] = metadata

        return updated_state

    except Exception as exc:
        updated_state["status"] = "failed"
        errors = list(updated_state.get("errors", []))
        errors.append(str(exc))
        updated_state["errors"] = errors
        return updated_state