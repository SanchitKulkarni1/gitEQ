from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Just initialize the client here
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])