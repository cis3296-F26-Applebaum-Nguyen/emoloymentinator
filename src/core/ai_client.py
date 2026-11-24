"""
Communicates with the AI API.
Sends prompts, receives responses, and handles API errors.
"""
import time

from google import genai
from google.genai import errors


def ask_ai(prompt: str, client=None, api_key: str | None = None,
           model: str = "gemma-4-26b-a4b-it") -> str:
    if client is None:
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        client = genai.Client(api_key=api_key)

    for attempt in range(2):
        time.sleep(6 if attempt == 0 else 12)

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
        except errors.APIError as error:
            retryable = error.code in (429, 503, 504)
            if not retryable or attempt == 1:
                raise
            continue

        if not response.text:
            raise ValueError("AI returned an empty response")

        return response.text