def process_search_request(user_text: str) -> str:
    if not user_text.strip():
        return "Please provide a job search query."
    return f"Received your search request: {user_text}"