import json
import re
from typing import Optional

import httpx

from app.config import settings

# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a personal memory synthesis engine. Your task is to analyze a collection of personal data fragments and produce a structured narrative summary.

Output ONLY valid JSON — no preamble, no explanation, no markdown formatting. The JSON must conform to this exact schema:

{
  "the_sentence": "one haunting concluding line summarizing this period, max 30 words",
  "narrative": "prose essay 300-500 words written in second person ('You spent...'), synthesizing the key patterns and events",
  "story_arcs": [
    {"title": "short title", "description": "brief description of this thread"}
  ],
  "recurring_people": [
    {"identifier": "name or reference", "context": "how they appear in the data"}
  ],
  "defining_moments": [
    {"moment": "specific event or entry", "significance": "why it matters"}
  ],
  "mindset_shifts": [
    {"from_state": "previous state", "to_state": "new state", "evidence": "what shows this shift", "period": "when it occurred"}
  ],
  "core_themes": ["theme1", "theme2"],
  "identity_contradictions": [
    {"observation": "the contradiction", "evidence": "conflicting data points", "interpretation": "what this might mean"}
  ]
}

Requirements:
1. Identity contradictions MUST identify at least one tension between what the person claims and what the data shows
2. The sentence MUST be a single powerful line, max 30 words
3. Story arcs should be 3-5 major threads
4. Recurring people should only include those who actually appear multiple times
5. Mindset shifts must be anchored to specific time periods from the data
6. If the data includes images, describe what the images suggest about the person's life"""


# ─── Modal API call ──────────────────────────────────────────────────────


async def call_gemma_synthesis(batched_text: str) -> Optional[dict]:
    """Send batched content to Gemma on Modal. Returns parsed JSON or None."""
    if not settings.INFERENCE_API_URL:
        return _fallback_synthesis(batched_text)

    payload = {
        "model": settings.INFERENCE_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Here is the chronological data to analyze:\n\n{batched_text}",
            },
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                settings.INFERENCE_API_URL,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        # Extract text from OpenAI-compatible response format
        text_content = (
            data.get("choices", [{}])[0].get("message", {}).get("content", "")
        )

        if not text_content:
            return None

        return _parse_json_response(text_content)

    except Exception as e:
        print(f"Modal API call failed: {e}")
        return _fallback_synthesis(batched_text)


# ─── JSON parsing helpers ─────────────────────────────────────────────────────


def _parse_json_response(text: str) -> Optional[dict]:
    """Extract and parse JSON from the model's text response."""
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Markdown code fence
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Anything that looks like a JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ─── Fallback (no API key) ────────────────────────────────────────────────────


def _fallback_synthesis(batched_text: str) -> dict:
    """Generate a local fallback when no API key is configured.
    Keeps the app functional for demo/tests."""
    char_count = len(batched_text) if batched_text else 0

    return {
        "the_sentence": "Your data tells a story only you can fully understand — but here is what the patterns reveal.",
        "narrative": (
            f"You curated {char_count} characters of personal history across multiple sources. "
            f"Your digital fragments — journal entries, messages, and notes — form a mosaic of your lived experience. "
            f"The synthesis below captures the major threads, the people who appear, and the shifts in your thinking "
            f"over the periods you've documented. Each upload adds depth to this evolving portrait. "
            f"Consider this a first draft of your life's current chapter — one that grows richer with every new entry you add."
        ),
        "story_arcs": [
            {
                "title": "The Documented Self",
                "description": "A practice of recording and reflecting on personal experiences through various media.",
            },
            {
                "title": "Digital Archaeology",
                "description": "The act of excavating meaning from fragments of personal data.",
            },
        ],
        "recurring_people": [
            {
                "identifier": "Yourself",
                "context": "The primary narrator and subject of all entries.",
            }
        ],
        "defining_moments": [
            {
                "moment": "First data upload to AI Lorekeeper",
                "significance": "The beginning of structured self-reflection through memory synthesis.",
            }
        ],
        "mindset_shifts": [
            {
                "from_state": "Unorganized memory",
                "to_state": "Structured reflection",
                "evidence": "Moving from scattered files to synthesized narrative.",
                "period": "Ongoing",
            }
        ],
        "core_themes": ["self-reflection", "memory", "pattern-seeking"],
        "identity_contradictions": [
            {
                "observation": "Your data suggests both a desire for self-understanding and a tendency to document rather than act.",
                "evidence": "The volume of reflective entries contrasts with the absence of action-oriented content.",
                "interpretation": "You may be processing experiences through documentation before integrating them into action.",
            }
        ],
    }
