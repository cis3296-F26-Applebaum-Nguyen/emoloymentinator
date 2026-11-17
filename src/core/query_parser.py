import os
import json
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types

# ---------- Setup: runs once when the file starts ----------

# Find .env.local and load its values into environment variables
load_dotenv(find_dotenv(".env.local", raise_error_if_not_found=True))

# Read the API key from the environment and create the client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

MODEL = "gemma-4-26b-a4b-it"

# Read the prompt from its text file
prompt_path = Path(__file__).parent/"prompts"/"query_parser_prompt.txt"  # the path to the prompt file
print(f"Reading prompt from {prompt_path}")
system_prompt = prompt_path.read_text(encoding="utf-8")             # the whole file as one string

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
            thinking_config=types.ThinkingConfig(thinking_level="minimal"),
        ),
    )

    # The reply is text. Remove extra spaces, then remove code fences if the model added them
    reply = response.text.strip()
    reply = reply.replace("```json", "").replace("```", "").strip()

    # Turn the JSON text into a Python dictionary
    return json.loads(reply)


# ---------- Test it by running this file directly ----------

if __name__ == "__main__":
    result = translate_request(
        "Entry level software developer in New York using python, javascript, react. Backend development. Pays 40000-60000 usd. Remote work is ok."
    )
    print(json.dumps(result, indent=2))  # indent=2 prints it neatly
