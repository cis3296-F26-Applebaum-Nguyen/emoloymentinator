"""
Uses AI to convert natural-language job requests
into structured search parameters.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types

from core.validation import validate_parsed_request, parse_json_reply
from core.models import request_from_dict

# ---------- Setup: runs once when the file starts ----------

# Find .env.local and load its values into environment variables
load_dotenv(find_dotenv(".env.local", raise_error_if_not_found=True))

# Read the API key from the environment and create the client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

MODEL = "gemma-4-26b-a4b-it"

# Read the prompt from its text file
prompt_path = Path(__file__).parent / "prompts" / "query_parser_prompt.txt"
system_prompt = prompt_path.read_text(encoding="utf-8")  # the whole file as one string


# ---------- The function that does the translating ----------
def translate_request(user_text):
    # Wrap the user's text in the tags that the prompt tells the model to look for
    message = "<user_request>\n" + user_text + "\n</user_request>"

    # Send the request to Gemma and wait for the full reply
    response = client.models.generate_content(
        model=MODEL,
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL),
        ),
    )

    return parse_json_reply(response.text)


class SearchParseError(Exception):
    """The text couldn't become a search. The message is safe to show the user."""

def parse_search_request(user_text):
    """Plain English in, SearchRequest out. Raises SearchParseError on failure."""
    try:
        raw = translate_request(user_text)        # step 1: ask the AI
        clean = validate_parsed_request(raw)      # step 2: check the answer
    except ValueError:
        # Covers an empty AI reply, broken JSON, and a failed validation
        raise SearchParseError("I couldn't understand that search. Try including a job title.")

    # The AI decided this wasn't about jobs, so pass its reason along
    if not clean["is_job_search"]:
        raise SearchParseError(clean["error"])

    return request_from_dict(clean)               # step 3: dataclasses

# ---------- Test it by running this file directly ----------

if __name__ == "__main__":
    # # Step 1: the AI turns plain English into a dictionary
    # raw = translate_request(
    #     "Entry level software developer in New York using python, javascript, react. "
    #     "Backend development. Pays 40000-60000 usd. Remote work is ok."
    # )
    
    # # raw = translate_request(
    # #     "part time data analyst jobs this week"
    # # )
    
    # # raw = translate_request(
    # #     "what's the weather in Miami?"
    # # )
    
    # # raw = translate_request( //This one errors out
    # #     "find me a job"
    # # )

    # # Step 2: validation checks it (raises ValueError if something is wrong)
    # clean = validate_parsed_request(raw)

    # # Step 3: dataclasses hold it in a form the rest of the program can use
    # if clean["is_job_search"]:
    #     request = request_from_dict(clean)
    #     print(request)               # dataclasses print their fields automatically
    # else:
    #     print(clean["error"])        # the AI said it wasn't a job search
    
    try:
        request = parse_search_request(
            "Entry level software developer in New York using python, javascript, react. "
            "Backend development. Pays 40000-60000 usd. Remote work is ok."
        )
        print(request)
    except SearchParseError as e:
        print(f"Error: {e}")
