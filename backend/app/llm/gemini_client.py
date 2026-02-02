from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

def get_client(api_key: str = None):
    """Get a Gemini client with the given API key, or from environment if not provided."""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("No API key provided and GEMINI_API_KEY not set in environment")
    return genai.Client(api_key=key)

# Default client for backwards compatibility (uses env variable)
# Only use this for local development; production should use get_client() with user's key
client = None
try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
except:
    pass  # Will fail if no key; functions should use get_client() instead