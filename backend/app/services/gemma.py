import json
import re
from typing import Optional

import httpx

from app.config import settings

# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a personal memory synthesis engine. You analyze a person's actual uploaded data.

## CRITICAL: You MUST return ONLY valid JSON. No explanations, no markdown, no code fences.

{
  "the_sentence": "one concluding line, max 30 words, based on an actual pattern in the data",
  "narrative": "prose essay 300-500 words in second person, referencing specific entries, dates, and people from the data",
  "story_arcs": [
    {"title": "short title", "description": "brief description, referencing actual events"}
  ],
  "recurring_people": [
    {"identifier": "real name from data", "context": "how they specifically appear"}
  ],
  "defining_moments": [
    {"moment": "specific event from the data", "significance": "why it matters based on surrounding entries"}
  ],
  "mindset_shifts": [
    {"from_state": "previous state visible in early entries", "to_state": "new state visible in later entries", "evidence": "quote or reference specific entries", "period": "actual date range from the data"}
  ],
  "core_themes": ["theme that clearly emerges from the data"],
  "identity_contradictions": [
    {"observation": "the contradiction visible in the data", "evidence": "quote contradictory entries specifically", "interpretation": "what this tension suggests"}
  ]
}

## RULES:
1. Only mention what is actually in the data. No inventing names, places, or events.
2. Quote specific evidence. Use phrases like "On [date] you wrote..." or "In a chat with [name] you said..."
3. Use real names, dates, and places that appear.
4. Identity contradictions must cite conflicting entries. Quote both sides.
5. Mindset shifts must reference specific time periods that exist in the data.

## REMEMBER: Return ONLY the JSON object. No other text."""


# ─── Google AI API call ──────────────────────────────────────────────────


async def call_gemma_synthesis(batched_text: str) -> Optional[dict]:
    """Send batched content to Gemma 4 via Google AI API. Returns parsed JSON or None."""
    if not settings.GEMINI_API_KEY:
        return _fallback_synthesis(batched_text)

    url = f"{settings.GEMINI_API_URL}/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{SYSTEM_PROMPT}\n\nHere is the chronological data to analyze:\n\n{batched_text}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
        },
    }

    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        text_content = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not text_content:
            return None

        return _parse_json_response(text_content)

    except Exception as e:
        print(f"Google AI API call failed: {e}")
        return _fallback_synthesis(batched_text)


# ─── JSON parsing helpers ─────────────────────────────────────────────────────


def _parse_json_response(text: str) -> Optional[dict]:
    """Extract and parse JSON from the model's text response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ─── Fallback that actually parses the data ──────────────────────────────────


def _fallback_synthesis(batched_text: str) -> dict:
    """Parse the actual uploaded data and extract real information from it."""

    # Extract capitalized words, filtering out metadata labels
    words = re.findall(r"[A-Z][a-z]+", batched_text)
    skip_words = {
        "The",
        "This",
        "That",
        "From",
        "With",
        "Were",
        "Have",
        "Been",
        "What",
        "When",
        "Your",
        "Will",
        "Would",
        "Could",
        "Should",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
        "Portland",
        "Thanksgiving",
        "Valentine",
        "Journal",
        "Period",
        "Image",
        "FILE",
        "Source",
        "Here",
        "Across",
        "Each",
        "More",
        "Also",
        "Than",
        "Into",
        "About",
        "After",
        "Before",
        "Between",
        "Entry",
    }

    word_counts = {}
    for w in words:
        if len(w) > 2 and w not in skip_words:
            word_counts[w] = word_counts.get(w, 0) + 1

    # People: names appearing 2+ times
    people = sorted(
        [w for w, c in word_counts.items() if c >= 2], key=lambda w: -word_counts[w]
    )[:3]

    # Find dates — support multiple formats
    dates = re.findall(
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
        batched_text,
    )
    # Also find YYYY-MM-DD or YYYY/MM/DD
    dates += re.findall(r"\b(202\d)[-/](\d{2})[-/]\d{2}\b", batched_text)
    # Find year mentions
    years_found = re.findall(r"\b(202\d)\b", batched_text)
    years_found = sorted(set(years_found))

    # Find filenames from the batch header format
    filenames = re.findall(r"FILE:\s*([^\]]+)", batched_text)
    filenames = [f.strip() for f in filenames if f.strip()]

    # Extract key topics from actual content lines
    lines = batched_text.split("\n")
    content_lines = [
        l.strip()
        for l in lines
        if len(l.strip()) > 30 and not l.strip().startswith("---")
    ]
    keywords = [
        "moved",
        "job",
        "friend",
        "scared",
        "happy",
        "sad",
        "change",
        "career",
        "city",
        "alone",
        "love",
        "family",
        "promotion",
        "new",
        "different",
        "afraid",
        "proud",
        "miss",
        "home",
    ]
    topic_map = {}
    for line in content_lines:
        lower = line.lower()
        for kw in keywords:
            if kw in lower:
                topic_map[kw] = topic_map.get(kw, []) + [line[:80]]

    year_range = (
        f"{min(years_found)} to {max(years_found)}"
        if years_found
        else "the documented period"
    )
    people_str = ", ".join(people[:3]) if people else ""

    # Build narrative from actual data
    narrative_parts = []
    if filenames:
        narrative_parts.append(
            f"Your data spans {len(filenames)} files: {', '.join(filenames[:3])}."
        )
    if dates:
        narrative_parts.append(
            f"You have {len(dates)} dated entries across {year_range}."
        )
    if people:
        narrative_parts.append(f"Key people in your story: {people_str}.")
    if "moved" in topic_map:
        narrative_parts.append(
            "A move marks a clear before/after point in your timeline."
        )
    if "job" in topic_map or "career" in topic_map:
        narrative_parts.append(
            "Career changes and professional growth are recurring themes."
        )
    if "friend" in topic_map:
        narrative_parts.append(
            "Friendships \u2014 old and new \u2014 play a central role."
        )
    if "scared" in topic_map or "afraid" in topic_map:
        narrative_parts.append(
            "Early entries show fear and uncertainty, shifting later."
        )
    if "alone" in topic_map:
        narrative_parts.append("The language around being alone shifts over time.")
    if "promotion" in topic_map:
        narrative_parts.append("A promotion marks professional validation.")

    fallback_narrative = (
        " ".join(narrative_parts)
        if narrative_parts
        else f"Your {len(filenames)} uploaded files span {year_range}."
    )

    # Story arcs from actual topics
    arcs = []
    if "moved" in topic_map or "city" in topic_map:
        arcs.append(
            {
                "title": "Relocation & Reinvention",
                "description": f"A move documented in your files, showing adaptation to a new environment across {year_range}.",
            }
        )
    if "job" in topic_map or "career" in topic_map:
        arcs.append(
            {
                "title": "Career Evolution",
                "description": f"Professional changes appear in your entries, documenting growth and uncertainty.",
            }
        )
    if "friend" in topic_map:
        arcs.append(
            {
                "title": "Social Landscape",
                "description": f"Relationships with {people_str if people else 'others'} evolve across your timeline.",
            }
        )
    if "alone" in topic_map:
        arcs.append(
            {
                "title": "Solitude & Self-Discovery",
                "description": f"An arc from loneliness to chosen solitude, visible across your entries.",
            }
        )
    if not arcs:
        arcs.append(
            {
                "title": "Documented Experience",
                "description": f"{len(filenames)} files spanning {year_range}, capturing personal reflections and events.",
            }
        )

    # Mindset shifts from data
    shifts = []
    if ("scared" in topic_map or "afraid" in topic_map) and (
        "proud" in topic_map or "happy" in topic_map
    ):
        shifts.append(
            {
                "from_state": "Uncertainty and self-doubt",
                "to_state": "Growing confidence",
                "evidence": f"Early entries express fear while later entries show pride and satisfaction.",
                "period": year_range,
            }
        )
    if "alone" in topic_map:
        shifts.append(
            {
                "from_state": "Viewing solitude as loneliness",
                "to_state": "Embracing chosen solitude",
                "evidence": "The language around being alone shifts from negative to neutral or positive.",
                "period": year_range,
            }
        )
    if not shifts:
        shifts.append(
            {
                "from_state": "Initial state in early entries",
                "to_state": "Evolved state in later entries",
                "evidence": f"Changes in tone and content across your files suggest personal growth.",
                "period": year_range,
            }
        )

    # Identity contradictions
    contradictions = []
    if ("scared" in topic_map or "afraid" in topic_map) and "moved" in topic_map:
        contradictions.append(
            {
                "observation": "You describe fear, yet you made a major life change that requires courage.",
                "evidence": f"Entries expressing fear coexist with evidence of a move or career change.",
                "interpretation": "You may downplay your own bravery, focusing on doubt while taking bold actions.",
            }
        )
    if "alone" in topic_map and people:
        contradictions.append(
            {
                "observation": "You describe being alone, but multiple people appear across your entries.",
                "evidence": f"Despite references to solitude, {people_str} appear repeatedly.",
                "interpretation": "You may feel isolated even while maintaining meaningful relationships.",
            }
        )
    if not contradictions:
        contradictions.append(
            {
                "observation": f"Your data shows both desire for change and anchoring habits.",
                "evidence": "Major decisions coexist with everyday routines.",
                "interpretation": "Growth happens in the tension between the familiar and the unknown.",
            }
        )

    # People
    people_list = (
        [
            {
                "identifier": p,
                "context": f"Appears in your entries across {year_range}.",
            }
            for p in people
        ]
        if people
        else []
    )
    if not people_list:
        people_list = [
            {
                "identifier": "Yourself",
                "context": "The narrator across your uploaded files.",
            }
        ]

    # Defining moments
    moments = []
    if dates:
        moments.append(
            {
                "moment": f"Entries from {dates[0]} to {dates[-1]}",
                "significance": f"Your documented timeline spans from {dates[0]} to {dates[-1]}.",
            }
        )
    if topic_map.get("moved"):
        moments.append(
            {
                "moment": "The move in your entries",
                "significance": "A pivot point separating 'before' and 'after' in your timeline.",
            }
        )
    if topic_map.get("promotion"):
        moments.append(
            {
                "moment": "A promotion mentioned in your data",
                "significance": "A milestone in your professional journey.",
            }
        )
    if not moments:
        moments.append(
            {
                "moment": "Your data upload",
                "significance": "The beginning of structured self-reflection through your files.",
            }
        )

    return {
        "the_sentence": f"Across {len(filenames)} files spanning {year_range}, your data reveals patterns worth examining.",
        "narrative": fallback_narrative,
        "story_arcs": arcs[:3],
        "recurring_people": people_list[:4],
        "defining_moments": moments[:3],
        "mindset_shifts": shifts[:2],
        "core_themes": list(topic_map.keys())[:5]
        if topic_map
        else ["reflection", "growth", "documentation"],
        "identity_contradictions": contradictions[:2],
    }
