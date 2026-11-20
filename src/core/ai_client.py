"""
Communicates with the AI API.
Sends prompts, receives responses, and handles API errors.
"""
import os
from google import genai


def ask_ai(prompt: str, client=None) -> str:
    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemma-4-26b-a4b-it",
        contents=prompt,
    )

    if not response.text:
        raise ValueError("AI returned an empty response")

    return response.text