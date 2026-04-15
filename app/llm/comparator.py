from app.llm.groq_client import generate_response

def build_comparison_prompt(donation, ngos):
    text = f"""
You are an intelligent decision system for food redistribution.

Your task is to:
1. Select the BEST NGO (already Option 1)
2. Explain WHY it is best
3. Compare it with other options and explain their drawbacks

IMPORTANT RULES:
- Focus on meaningful factors: distance, capacity, urgency, reliability
- IGNORE tiny differences (e.g., 1–2 km difference is not important)
- Be practical and realistic
- Keep it structured and concise

Donation:
- Food: {donation.get("food_type")}
- Quantity: {donation.get("quantity")}
- Expiry: {donation.get("expiry_hours")} hours

NGO Options:
"""

    for i, ngo in enumerate(ngos, start=1):
        text += f"""
Option {i}:
- Name: {ngo['ngo_name']}
- Distance: {ngo['distance_km']} km
- Score: {ngo['match_score']}
"""

    text += """
Output format EXACTLY like this:

Recommended NGO: <name>

Reason:
<2-3 sentence explanation>

Alternatives:
• <NGO 2> — <drawback>
• <NGO 3> — <drawback>

Do NOT mention option numbers.
Do NOT over-explain.
Do NOT talk about tiny differences.
"""

    return text


def generate_comparison(donation, ngos):
    prompt = build_comparison_prompt(donation, ngos)
    return generate_response(prompt)