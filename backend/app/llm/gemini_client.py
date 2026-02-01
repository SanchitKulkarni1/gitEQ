from google import genai
import os

# Just initialize the client here
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])