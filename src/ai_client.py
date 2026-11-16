import os
from dotenv import load_dotenv, find_dotenv
from google import genai
from httpx2 import stream

# Walks up from this script's folder until it finds .env.local.
# raise_error_if_not_found makes it fail loudly instead of silently.
env_path = find_dotenv(".env.local", raise_error_if_not_found=True)
load_dotenv(env_path)

gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key)

which_model = "gemma-4-26b-a4b-it"
user_prompt = "Can you summarize the story of Odysseus? Tell me about his journey and adventures, and key plot points."

response = client.models.generate_content_stream(
    model=which_model,
    contents=user_prompt,
)

full_text = ""  # keep the pieces so you have the whole answer at the end
for chunk in response:
    if chunk.text:  # some chunks can be empty, so skip those
        print(chunk.text, end="", flush=True)  # flush=True shows it immediately
        full_text += chunk.text