#!/usr/bin/env python3
"""
Script to list all available models under the Gemini API key
"""

from google import genai
import os
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

print("Fetching available models...\n")

try:
    # List all available models
    models = client.models.list()
    
    # Extract model information
    model_data = []
    for model in models:
        model_data.append([
            model.name.split('/')[-1],  # Extract just the model name
            model.display_name,
            model.description if hasattr(model, 'description') else 'N/A',
        ])
    
    # Display in a formatted table
    headers = ["Model ID", "Display Name", "Description"]
    print(tabulate(model_data, headers=headers, tablefmt="grid"))
    
    print(f"\n✓ Total models available: {len(model_data)}")
    
    # Also print raw model objects for more details
    print("\n" + "="*80)
    print("DETAILED MODEL INFORMATION:")
    print("="*80 + "\n")
    
    for model in models:
        print(f"Model: {model.name}")
        print(f"  Display Name: {model.display_name}")
        if hasattr(model, 'description') and model.description:
            print(f"  Description: {model.description}")
        if hasattr(model, 'input_token_limit'):
            print(f"  Input Token Limit: {model.input_token_limit}")
        if hasattr(model, 'output_token_limit'):
            print(f"  Output Token Limit: {model.output_token_limit}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Supported Methods: {model.supported_generation_methods}")
        print()
        
except Exception as e:
    print(f"✗ Error fetching models: {e}")
    print("\nMake sure your GEMINI_API_KEY is set in the .env file")
