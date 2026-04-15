from typing import Dict


def build_prompt(donation: Dict, match_result: Dict, predictions: Dict) -> str:
    return f"""
You are an AI system explaining a food redistribution decision.

Donation Details:
- Food Type: {donation.get("food_type")}
- Quantity: {donation.get("quantity")}
- Expiry (hours): {donation.get("expiry_hours")}
- Location: {donation.get("pickup_address")}

Selected NGO:
- Name: {match_result.get("ngo_name")}
- Distance: {match_result.get("distance_km")} km

System Scores:
- Match Score: {match_result.get("match_score")}
- Urgency Score: {predictions.get("urgency_score")}
- Spoilage Risk: {predictions.get("spoilage_risk")}

Explain clearly in 2–3 sentences WHY this NGO was chosen.
Make it sound natural, human-like, and professional.
Avoid mentioning raw score numbers unless needed.
"""


from app.llm.groq_client import generate_response


def generate_explanation(donation, match_result, predictions) -> str:
    prompt = build_prompt(donation, match_result, predictions)
    return generate_response(prompt)