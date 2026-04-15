# app/agents/action.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.graph.state import AgentState


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_notification_message(state: AgentState) -> str:
    donation = state.get("donation", {})
    match_result = state.get("match_result", {})
    pickup_request = state.get("pickup_request", {})

    food_type = _clean_text(donation.get("food_type"))
    quantity = donation.get("quantity")
    source = _clean_text(donation.get("source_name"))
    pickup_address = _clean_text(donation.get("pickup_address"))

    ngo_name = _clean_text(match_result.get("ngo_name"))

    pickup_time = _clean_text(pickup_request.get("pickup_time"))

    message = (
        f"Food Pickup Request\n"
        f"-------------------\n"
        f"NGO: {ngo_name}\n"
        f"Food: {food_type} ({quantity} servings)\n"
        f"Source: {source}\n"
        f"Pickup Location: {pickup_address}\n"
        f"Pickup Time: {pickup_time}\n"
    )

    return message


def _send_notification(message: str) -> bool:
    """
    Placeholder for real notification system.
    Later replace with:
    - SMS (Twilio)
    - Email (SMTP)
    - WhatsApp API
    """
    # For now, we simulate success
    return True


def action_agent(state: AgentState) -> AgentState:
    """
    Execute the pickup request:
    - Send notification to NGO
    - Update status

    Expects:
        - state['pickup_request']
        - state['match_result']
        - state['donation']
    """
    updated_state: AgentState = dict(state)

    try:
        pickup_request = updated_state.get("pickup_request")
        match_result = updated_state.get("match_result")

        if not isinstance(pickup_request, dict):
            raise ValueError("'pickup_request' must exist before action")
        if not isinstance(match_result, dict):
            raise ValueError("'match_result' must exist before action")

        recommended = match_result.get("recommended", {})
        ngo_name = _clean_text(recommended.get("ngo_name"))

        if not ngo_name:
            raise ValueError("Missing NGO name for notification")

        # Build message
        message = _build_notification_message(updated_state)

        # Send notification
        success = _send_notification(message)

        if not success:
            raise RuntimeError("Failed to send notification")

        # Update pickup request
        pickup_request["status"] = "notification_sent"
        pickup_request["confirmation_notes"] = f"Notification sent to {ngo_name}; waiting for NGO confirmation"

        updated_state["pickup_request"] = pickup_request
        updated_state["status"] = "acted"

        metadata = dict(updated_state.get("metadata", {}))
        metadata["acted_at"] = datetime.now(timezone.utc).isoformat()
        metadata["notification_sent"] = True
        metadata["notification_status"] = "notification_sent"
        updated_state["metadata"] = metadata

        return updated_state

    except Exception as exc:
        updated_state["status"] = "failed"
        errors = list(updated_state.get("errors", []))
        errors.append(str(exc))
        updated_state["errors"] = errors
        return updated_state