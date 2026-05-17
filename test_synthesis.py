"""Test synthesis locally with demo data, bypassing auth."""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Read demo files
demo_dir = os.path.join(os.path.dirname(__file__), "demo-data")
with open(os.path.join(demo_dir, "journal-2024.txt")) as f:
    journal = f.read()
with open(os.path.join(demo_dir, "whatsapp-chats.txt")) as f:
    chats = f.read()
with open(os.path.join(demo_dir, "photo-descriptions.json")) as f:
    photos = f.read()

batched = f"--- FILE: journal-2024.txt ---\n{journal}\n\n--- FILE: whatsapp-chats.txt [Source: WhatsApp]\n{chats}\n\n--- FILE: photos.json [Source: Photos]\n{photos}"

from app.services.gemma import call_gemma_synthesis


async def test():
    print(f"Batched text: {len(batched)} chars")
    print("Calling Gemma 4 via Google AI API...")
    result = await call_gemma_synthesis(batched)
    if result:
        print("\n✅ SUCCESS!")
        print(json.dumps(result, indent=2))
    else:
        print("\n❌ FAILED - returned None")


asyncio.run(test())
