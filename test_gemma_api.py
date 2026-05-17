"""Test script: calls Gemma 4 via Google AI API using GEMINI_API_KEY from .env"""

import json
import os
import re
import urllib.error
import urllib.request

# Read key from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
with open(env_path) as f:
    env = f.read()
match = re.search(r'GEMINI_API_KEY\s*=\s*"?([^"\n]+)"?', env)
if not match:
    print("GEMINI_API_KEY not found in .env")
    exit(1)
key = match.group(1).strip()
print(f"Key found: {key[:8]}...{key[-4:]}")

# Test models
models = [
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemma-4-e4b-it",
    "gemma-4",
    "gemini-2.0-flash",
]

for model in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": "say hello in 3 words"}]}],
            "generationConfig": {"maxOutputTokens": 10},
        }
    ).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        print(f"✅ {model}: {text}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:150]
        print(f"❌ {model}: HTTP {e.code} — {body}")
    except Exception as e:
        print(f"❌ {model}: {e}")
