#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force UTF-8 environment
os.environ.update({
    'PYTHONIOENCODING': 'utf-8',
    'LC_ALL': 'C.UTF-8',
    'LANG': 'C.UTF-8',
})

import openai
from dotenv import load_dotenv

load_dotenv()

# Monkey-patch httpx to handle encoding issues
import httpx._models
original_normalize = httpx._models._normalize_header_value

def patched_normalize_header_value(value, encoding=None):
    """Patched version that handles Unicode characters gracefully."""
    if isinstance(value, str):
        # Replace problematic Unicode characters
        value = value.replace('\u2014', '--')  # em dash
        value = value.replace('\u2013', '-')   # en dash
        # Remove any remaining non-ASCII characters
        value = ''.join(c for c in value if ord(c) < 128)
    return original_normalize(value, encoding)

httpx._models._normalize_header_value = patched_normalize_header_value

def test_openai_encoding():
    """Test OpenAI API with minimal ASCII text."""
    import httpx
    
    # Create a custom HTTP client with ASCII-safe headers
    http_client = httpx.Client(
        headers={
            "User-Agent": "python-openai/1.0.0"  # Simple ASCII user agent
        }
    )
    
    client = openai.OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        http_client=http_client
    )
    
    # Test with absolutely minimal ASCII text
    test_texts = [
        "hello world",
        "Order 1234 shipped",
        "tracking: XYZ",
        "type: order"
    ]
    
    for i, text in enumerate(test_texts):
        try:
            print(f"Testing text {i+1}: '{text}'")
            
            # Ensure absolutely ASCII-only
            ascii_text = ''.join(c for c in text if ord(c) < 128)
            print(f"ASCII-only version: '{ascii_text}'")
            
            # Test embedding creation
            response = client.embeddings.create(
                input=ascii_text,
                model="text-embedding-ada-002"
            )
            
            print(f"✓ Success for text {i+1}")
            print(f"  Embedding dimensions: {len(response.data[0].embedding)}")
            
        except Exception as e:
            print(f"✗ Failed for text {i+1}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_openai_encoding()
