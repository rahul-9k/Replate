# app/agents/ngo_fetcher.py

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.graph.state import AgentState


DATA_PATH = Path("data/ngos.json")


def _validate_ngo(ngo: Dict[str, Any]) -> bool:
    """
    Basic validation to ensure NGO has minimum required fields.
    """
    required_fields = ["id", "name", "address", "lat", "lng"]

    for field in required_fields:
        if field not in ngo:
            return False

    return True


def _load_ngos() -> List[Dict[str, Any]]:
    """
    Load NGOs from JSON file.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError("NGO data file not found at data/ngos.json")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("NGO data must be a list")

    return data


def ngo_fetcher_agent(state: AgentState) -> AgentState:
    """
    Load NGO data and attach to state.

    Future:
    - filter by distance
    - filter by operating hours
    """
    updated_state: AgentState = dict(state)

    try:
        ngos_raw = _load_ngos()

        valid_ngos = []
        skipped = []

        for ngo in ngos_raw:
            if not isinstance(ngo, dict):
                skipped.append("Invalid NGO entry (not dict)")
                continue

            if not _validate_ngo(ngo):
                skipped.append(f"Invalid NGO missing fields: {ngo.get('id', 'unknown')}")
                continue

            valid_ngos.append(ngo)

        if not valid_ngos:
            raise ValueError("No valid NGOs available after filtering")

        updated_state["available_ngos"] = valid_ngos
        updated_state["status"] = "ngos_loaded"

        metadata = dict(updated_state.get("metadata", {}))
        metadata["ngos_loaded_at"] = datetime.now(timezone.utc).isoformat()
        metadata["total_ngos"] = len(valid_ngos)
        if skipped:
            metadata["ngo_warnings"] = skipped
        updated_state["metadata"] = metadata

        return updated_state

    except Exception as exc:
        updated_state["status"] = "failed"
        errors = list(updated_state.get("errors", []))
        errors.append(str(exc))
        updated_state["errors"] = errors
        return updated_state
    