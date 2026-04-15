# app/graph/state.py

from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict


# -----------------------------
# Core Entities
# -----------------------------

class Donation(TypedDict):
    id: str
    source_name: str
    contact_phone: str

    food_type: str
    quantity: int
    is_veg: bool

    prepared_at: str
    expiry_hours: int

    pickup_address: str
    pickup_lat: float
    pickup_lng: float

    special_notes: str


class NGO(TypedDict, total=False):
    id: str
    name: str

    address: str
    lat: float
    lng: float

    service_radius_km: float

    capacity_per_day: int
    current_load: int

    food_preferences: List[str]

    operating_hours: Dict[str, str]

    contact_phone: str

    reliability_score: float


class MatchResult(TypedDict, total=False):
    donation_id: str
    ngo_id: str

    ngo_name: str
    ngo_address: str

    distance_km: float
    estimated_time_min: int

    match_score: float
    decision_reason: str

    created_at: str


class PickupRequest(TypedDict, total=False):
    match_id: str

    status: Literal["pending", "accepted", "rejected", "completed"]

    assigned_to: str
    pickup_time: str

    confirmation_notes: str


# -----------------------------
# Agent State (Shared)
# -----------------------------

class AgentState(TypedDict, total=False):
    # Core input
    donation: Donation

    # Data fetched
    available_ngos: List[NGO]

    # Intermediate intelligence
    predictions: Dict[str, Any]

    # Decision
    match_result: MatchResult

    # Execution
    pickup_request: PickupRequest

    # System tracking
    status: Literal[
        "received",
        "validated",
        "ngos_loaded",
        "predicted",
        "matched",
        "planned",
        "acted",
        "failed",
    ]

    errors: List[str]

    metadata: Dict[str, Any]