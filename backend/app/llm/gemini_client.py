from google import genai
from google.genai import types
import os

# Initialize the client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Generate content with configuration
response = client.models.generate_content(
    model="gemini-1.5-pro",
    config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.9,
        max_output_tokens=2048,
    )
)
