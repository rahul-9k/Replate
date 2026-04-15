
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from app.graph.state import AgentState


PERISHABLE_FOODS = {
    "milk",
    "curd",
    "yogurt",
    "paneer",
    "salad",
    "fruit",
    "fruits",
    "vegetables",
    "veg",
    "cooked rice",
    "cooked food",
    "biryani",
    "chapati",
    "roti",
    "thali",
    "rice",
    "dal",
    "meal",
}


HIGH_DEMAND_FOODS = {
    "rice",
    "roti",
    "chapati",
    "dal",
    "lentils",
    "bread",
    "vegetables",
    "fruit",
    "fruits",
    "meal",
    "thali",
    "cooked food",
    "biryani",
}


def _clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min_value, min(max_value, value))


def _normalize_food_name(food_type: str) -> str:
    return str(food_type).strip().lower()


def _compute_spoilage_risk(food_type: str, expiry_hours: int) -> str:
    if expiry_hours <= 1:
        return "high"
    if expiry_hours <= 4:
        return "high" if food_type in PERISHABLE_FOODS else "medium"
    if expiry_hours <= 8:
        return "medium" if food_type in PERISHABLE_FOODS else "low"
    return "low"


def _compute_urgency_score(food_type: str, expiry_hours: int, quantity: int) -> float:
    if expiry_hours <= 1:
        base = 95
    elif expiry_hours <= 3:
        base = 85
    elif expiry_hours <= 6:
        base = 70
    elif expiry_hours <= 12:
        base = 50
    else:
        base = 30

    if food_type in PERISHABLE_FOODS:
        base += 10

    if quantity >= 200:
        base += 5

    return _clamp(base)


def _compute_demand_score(food_type: str, quantity: int) -> float:
    score = 40.0

    if food_type in HIGH_DEMAND_FOODS:
        score += 30

    if food_type in PERISHABLE_FOODS:
        score += 10

    if quantity >= 100:
        score += 10
    if quantity >= 250:
        score += 5

    return _clamp(score)


def prediction_agent(state: AgentState) -> AgentState:
    """
    Estimate spoilage risk, urgency, and demand score from the validated donation.
    """
    updated_state: AgentState = dict(state)

    try:
        donation = updated_state.get("donation")
        if not isinstance(donation, dict):
            raise ValueError("'donation' must exist before prediction")

        food_type = _normalize_food_name(donation.get("food_type", ""))
        quantity = int(donation.get("quantity", 0))
        expiry_hours = int(donation.get("expiry_hours", 0))
        is_veg = bool(donation.get("is_veg", True))

        if not food_type:
            raise ValueError("'food_type' is required for prediction")
        if quantity <= 0:
            raise ValueError("'quantity' must be greater than 0")
        if expiry_hours < 0:
            raise ValueError("'expiry_hours' cannot be negative")

        spoilage_risk = _compute_spoilage_risk(food_type, expiry_hours)
        urgency_score = _compute_urgency_score(food_type, expiry_hours, quantity)
        demand_score = _compute_demand_score(food_type, quantity)

        if not is_veg and food_type in {"paneer", "curd", "yogurt"}:
            demand_score = _clamp(demand_score - 5)

        if spoilage_risk == "high":
            notes = "Prioritize immediate matching and pickup due to spoilage risk."
        elif spoilage_risk == "medium":
            notes = "Handle soon; food is still usable but should not be delayed."
        else:
            notes = "Stable enough for normal redistribution planning."

        updated_state["predictions"] = {
            "spoilage_risk": spoilage_risk,
            "urgency_score": round(urgency_score, 2),
            "demand_score": round(demand_score, 2),
            "notes": notes,
        }
        updated_state["status"] = "predicted"

        metadata = dict(updated_state.get("metadata", {}))
        metadata["predicted_at"] = datetime.now(timezone.utc).isoformat()
        metadata["prediction_model"] = "heuristic_v1"
        updated_state["metadata"] = metadata

        return updated_state

    except Exception as exc:
        updated_state["status"] = "failed"
        errors = list(updated_state.get("errors", []))
        errors.append(str(exc))
        updated_state["errors"] = errors
        return updated_state