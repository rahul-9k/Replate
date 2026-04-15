
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.graph.state import AgentState
from app.llm.explainer import generate_explanation
from app.llm.comparator import generate_comparison
import math


import math

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine distance in kilometers.
    """
    R = 6371.0

    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
    
def _format_ngo_output(ngo, score, distance_km):
    return {
        "ngo_id": _clean_text(ngo.get("id")),
        "ngo_name": _clean_text(ngo.get("name")),
        "ngo_address": _clean_text(ngo.get("address")),
        "distance_km": round(distance_km, 2),
        "match_score": score
    }


def _distance_score(distance_km: float, service_radius_km: float) -> float:
    """
    Higher score for closer NGOs within service radius.
    Max: 35
    """
    if distance_km < 0 or service_radius_km <= 0:
        return 0.0

    if distance_km > service_radius_km:
        return 0.0

    ratio = distance_km / max(service_radius_km, 0.001)

    if ratio <= 0.10:
        return 35.0
    elif ratio <= 0.25:
        return 30.0
    elif ratio <= 0.50:
        return 24.0
    elif ratio <= 0.75:
        return 16.0
    else:
        return 8.0


def _capacity_score(quantity: int, capacity_left: int) -> float:
    """
    Higher score when the NGO can comfortably handle the donation size.
    Max: 30
    """
    if quantity <= 0 or capacity_left <= 0:
        return 0.0

    if capacity_left >= quantity * 3:
        return 30.0
    elif capacity_left >= quantity * 2:
        return 27.0
    elif capacity_left >= quantity:
        return 24.0
    elif capacity_left >= quantity * 0.75:
        return 18.0
    elif capacity_left >= quantity * 0.5:
        return 10.0
    else:
        return 4.0


def _reliability_score(reliability: float) -> float:
    """
    Expects reliability on a 0.0 to 1.0 scale.
    Max: 20
    """
    if reliability <= 0:
        return 0.0

    if reliability >= 0.95:
        return 20.0
    elif reliability >= 0.9:
        return 18.0
    elif reliability >= 0.8:
        return 15.0
    elif reliability >= 0.7:
        return 12.0
    elif reliability >= 0.6:
        return 8.0
    else:
        return 4.0


def _food_fit_score(food_type: str, food_preferences: List[str]) -> float:
    """
    Rewards exact or partial match with NGO food preferences.
    Max: 10
    """
    prefs = {str(item).strip().lower() for item in food_preferences if str(item).strip()}
    food_type = str(food_type).strip().lower()

    if not prefs or not food_type:
        return 0.0

    if food_type in prefs:
        return 10.0

    for pref in prefs:
        if pref in food_type or food_type in pref:
            return 7.0

    # mild credit for being vegetarian-friendly if the NGO accepts veg
    if "veg" in prefs and any(word in food_type for word in ["rice", "roti", "dal", "paneer", "biryani", "thali"]):
        return 5.0

    return 0.0


def _urgency_bonus(urgency_score: float, distance_km: float, capacity_left: int) -> float:
    """
    Gives extra weight when urgency is high and the NGO is feasible.
    Max: 15
    """
    bonus = 0.0

    if urgency_score >= 90:
        bonus += 8.0
    elif urgency_score >= 75:
        bonus += 6.0
    elif urgency_score >= 60:
        bonus += 4.0
    elif urgency_score >= 40:
        bonus += 2.0

    if distance_km <= 3:
        bonus += 4.0
    elif distance_km <= 7:
        bonus += 2.5
    elif distance_km <= 12:
        bonus += 1.0

    if capacity_left >= 150:
        bonus += 3.0
    elif capacity_left >= 75:
        bonus += 2.0
    elif capacity_left > 0:
        bonus += 1.0

    return min(bonus, 15.0)


def _score_ngo(
    ngo: Dict[str, Any],
    donation: Dict[str, Any],
    food_type: str,
    quantity: int,
    urgency_score: float,
) -> Tuple[float, List[str]]:
    reasons: List[str] = []

    ngo_id = _clean_text(ngo.get("id"))
    ngo_name = _clean_text(ngo.get("name"))
    ngo_address = _clean_text(ngo.get("address"))

    service_radius_km = _to_float(ngo.get("service_radius_km"), default=0.0)
    capacity_per_day = _to_int(ngo.get("capacity_per_day"), default=0)
    current_load = _to_int(ngo.get("current_load"), default=0)
    reliability_score = _to_float(ngo.get("reliability_score"), default=0.0)

    food_preferences = ngo.get("food_preferences", [])
    if not isinstance(food_preferences, list):
        food_preferences = []

    donation_lat = _to_float(donation.get("pickup_lat"), default=0.0)
    donation_lng = _to_float(donation.get("pickup_lng"), default=0.0)
    ngo_lat = _to_float(ngo.get("lat"), default=0.0)
    ngo_lng = _to_float(ngo.get("lng"), default=0.0)

    if donation_lat and donation_lng and ngo_lat and ngo_lng:
        distance_km = calculate_distance_km(
            donation_lat, donation_lng,
            ngo_lat, ngo_lng
        )
    else:
        distance_km = 9999.0

    if service_radius_km > 0 and distance_km > service_radius_km:
        return 0.0, [
            f"NGO: {ngo_name or ngo_id or 'unknown'}",
            f"Outside service radius ({distance_km:.2f} km > {service_radius_km:.2f} km)",
        ]

    capacity_left = max(0, capacity_per_day - current_load)

    score = 0.0
    reasons.append(f"NGO: {ngo_name or ngo_id or 'unknown'}")

    dist_score = _distance_score(distance_km, service_radius_km)
    cap_score = _capacity_score(quantity, capacity_left)
    rel_score = _reliability_score(reliability_score)
    fit_score = _food_fit_score(food_type, food_preferences)
    urgent_bonus = _urgency_bonus(urgency_score, distance_km, capacity_left)

    score += dist_score
    score += cap_score
    score += rel_score
    score += fit_score
    score += urgent_bonus

    if service_radius_km > 0:
        reasons.append(f"Service radius considered: {service_radius_km:.1f} km")
    if distance_km != 9999.0:
        reasons.append(f"Distance: {distance_km:.2f} km")
        reasons.append(f"Distance score: {dist_score:.1f}")
    if capacity_left > 0:
        reasons.append(f"Capacity fit score: {cap_score:.1f}")
    if reliability_score:
        reasons.append(f"Reliability score: {rel_score:.1f}")
    if fit_score > 0:
        reasons.append("Food type matches NGO preference")
    if urgent_bonus > 0:
        reasons.append(f"Urgency bonus applied: {urgent_bonus:.1f}")
    if ngo_address:
        reasons.append(f"Address: {ngo_address}")

    return score, reasons

def matching_agent(state: AgentState) -> AgentState:
    """
    Select the best NGO from state['available_ngos'] using donation + prediction context.

    Expects:
        - state['donation']
        - state['predictions']
        - state['available_ngos']
    Produces:
        - state['match_result']
    """
    updated_state: AgentState = dict(state)

    try:
        donation = updated_state.get("donation")
        predictions = updated_state.get("predictions")
        ngos = updated_state.get("available_ngos", [])

        if not isinstance(donation, dict):
            raise ValueError("'donation' must exist before matching")
        if not isinstance(predictions, dict):
            raise ValueError("'predictions' must exist before matching")
        if not isinstance(ngos, list) or not ngos:
            raise ValueError("'available_ngos' must be a non-empty list before matching")

        food_type = _clean_text(donation.get("food_type")).lower()
        quantity = _to_int(donation.get("quantity"), default=0)
        donation_id = _clean_text(donation.get("id"))
        urgency_score = _to_float(predictions.get("urgency_score"), default=0.0)

        if not food_type:
            raise ValueError("'food_type' is required for matching")
        if quantity <= 0:
            raise ValueError("'quantity' must be greater than 0")
        if not donation_id:
            raise ValueError("'id' is required in donation for matching")

        scored_ngos: List[Dict[str, Any]] = []
        skipped_reasons: List[str] = []

        for ngo in ngos:
            if not isinstance(ngo, dict):
                skipped_reasons.append("Skipped invalid NGO entry: not a dictionary")
                continue

            if not _clean_text(ngo.get("id")) and not _clean_text(ngo.get("name")):
                skipped_reasons.append("Skipped NGO entry with missing id/name")
                continue

            score, reasons = _score_ngo(
                ngo=ngo,
                donation=donation,
                food_type=food_type,
                quantity=quantity,
                urgency_score=urgency_score,
            )

            scored_ngos.append(
                {
                    "ngo": ngo,
                    "score": round(score, 2),
                    "reasons": reasons,
                }
            )

        if not scored_ngos:
            raise ValueError("No valid NGOs available for matching")

        scored_ngos.sort(key=lambda item: item["score"], reverse=True)
        top_ngos = scored_ngos[:3]

        best = top_ngos[0]
        best_ngo = best["ngo"]
        alternatives = top_ngos[1:]

        formatted_top = []
        for item in top_ngos:
            ngo = item["ngo"]
            ngo_lat = _to_float(ngo.get("lat"), 0.0)
            ngo_lng = _to_float(ngo.get("lng"), 0.0)
            donation_lat = _to_float(donation.get("pickup_lat"), 0.0)
            donation_lng = _to_float(donation.get("pickup_lng"), 0.0)

            if donation_lat and donation_lng and ngo_lat and ngo_lng:
                dist = calculate_distance_km(
                    donation_lat, donation_lng,
                    ngo_lat, ngo_lng
                )
            else:
                dist = 0.0

            formatted_top.append(
                _format_ngo_output(ngo, item["score"], dist)
            )

        best_distance = formatted_top[0]["distance_km"] if formatted_top else 0.0
        service_radius_km = _to_float(best_ngo.get("service_radius_km"), default=0.0)
        capacity_per_day = _to_int(best_ngo.get("capacity_per_day"), default=0)
        current_load = _to_int(best_ngo.get("current_load"), default=0)
        capacity_left = max(0, capacity_per_day - current_load)

        ai_reason = generate_explanation(
            donation,
            {
                "ngo_name": _clean_text(best_ngo.get("name")),
                "distance_km": round(best_distance, 2),
                "match_score": best["score"],
            },
            predictions,
        )

        comparison_reason = generate_comparison(donation, formatted_top)

        updated_state["match_result"] = {
            "recommended": formatted_top[0],
            "alternatives": formatted_top[1:],
            "comparison_reason": comparison_reason,
            "ai_reason": ai_reason,
        }
        updated_state["status"] = "matched"

        metadata = dict(updated_state.get("metadata", {}))
        metadata["matched_at"] = datetime.now(timezone.utc).isoformat()
        metadata["match_candidates"] = len(scored_ngos)
        metadata["best_service_radius_km"] = service_radius_km
        metadata["best_capacity_left"] = capacity_left
        if skipped_reasons:
            metadata["matching_warnings"] = skipped_reasons
        updated_state["metadata"] = metadata

        return updated_state

    except Exception as exc:
        updated_state["status"] = "failed"
        errors = list(updated_state.get("errors", []))
        errors.append(str(exc))
        updated_state["errors"] = errors
        return updated_state