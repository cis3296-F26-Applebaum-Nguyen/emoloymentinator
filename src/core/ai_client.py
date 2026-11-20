"""
Communicates with the AI API.
Sends prompts, receives responses, and handles API errors.
"""
import os
import time
from google import genai
from google.genai import errors


def ask_ai(prompt: str, client=None) -> str:
    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        client = genai.Client(api_key=api_key)

    for attempt in range(2):
        time.sleep(6 if attempt == 0 else 12)

        try:
            response = client.models.generate_content(
                model="gemma-4-26b-a4b-it",
                contents=prompt,
            )
        except errors.APIError as error:
            if error.code != 429 or attempt == 1:
                raise
            continue

        if not response.text:
            raise ValueError("AI returned an empty response")

        return response.text