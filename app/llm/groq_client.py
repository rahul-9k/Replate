import os
from groq import Groq

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_response(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert logistics decision assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"AI error: {str(e)}"