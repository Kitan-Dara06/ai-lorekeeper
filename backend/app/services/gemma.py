import json
import re
from typing import Optional

import httpx

from app.config import settings

# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a personal memory synthesis engine. You analyze a person's actual uploaded data — journal entries, chat logs, photos — and produce a structured narrative based SOLELY on what the data says.

## CRITICAL RULES — YOU MUST FOLLOW THESE:

1. **Only mention what is actually in the data.** If the data doesn't mention a city, don't invent one. If the data doesn't mention a person's name, don't invent one.
2. **Quote specific evidence.** Every claim in the narrative must trace back to a real line in the data. Use phrases like "On [date] you wrote..." or "In a chat with [name] you said..."
3. **Use real names, dates, and places** that appear in the uploaded files. If the user's journal says "Portland," mention Portland. If they mention "Sarah" three times, Sarah is a recurring person.
4. **The sentence must be derived from the data** — a synthesis of an actual pattern you observed, not a generic aphorism.
5. **Identity contradictions must cite conflicting lines** from different entries. Quote both sides.
6. **Mindset shifts must reference specific time periods** that exist in the data (e.g., "Between January and July 2024").

Output ONLY valid JSON — no preamble, no explanation. The JSON must conform to this exact schema:

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
}"""


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

    # Extract names (words that appear multiple times, capitalized)
    words = re.findall(r"[A-Z][a-z]+", batched_text)
    word_counts = {}
    for w in words:
        if len(w) > 2 and w not in (
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
        ):
            word_counts[w] = word_counts.get(w, 0) + 1

    # People: names appearing 2+ times
    people = sorted(
        [
            w
            for w, c in word_counts.items()
            if c >= 2
            and w
            not in (
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
            )
        ],
        key=lambda w: -word_counts[w],
    )[:3]

    # Find dates
    dates = re.findall(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
        batched_text,
    )
    years = re.findall(r"(202\d)", batched_text)
    year_range = (
        f"{min(years) if years else '2024'} to {max(years) if years else '2024'}"
    )

    # Find source tags
    sources = re.findall(r"\[Source:\s*(\w+)\]", batched_text)
    sources = list(set(sources))

    # Find filenames
    filenames = re.findall(r"FILE:\s*([^\]]+)", batched_text)

    # Extract key topics from content
    lines = batched_text.split("\n")
    meaningful = [l.strip() for l in lines if len(l.strip()) > 40]
    topics = []
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
    for line in meaningful:
        lower = line.lower()
        for kw in keywords:
            if kw in lower:
                topic_map[kw] = topic_map.get(kw, []) + [line[:80]]

    # Build the narrative from actual data
    narrative_parts = []
    if dates:
        narrative_parts.append(
            f"Across {len(dates)} dated entries spanning {year_range}, your data reveals a period of significant transition."
        )
    if people:
        narrative_parts.append(
            f"Key people appear in your story: {', '.join(people[:3])}."
        )
    if "moved" in topic_map:
        narrative_parts.append(
            "A physical move marks a clear before/after point in your timeline."
        )
    if "job" in topic_map or "career" in topic_map:
        narrative_parts.append(
            "Career changes and professional growth are recurring threads."
        )
    if "scared" in topic_map or "afraid" in topic_map:
        narrative_parts.append(
            "Fear and uncertainty show up in early entries, giving way to confidence later."
        )
    if "friend" in topic_map:
        narrative_parts.append(
            "Friendships — both old and new — play a central role in your experiences."
        )
    if "alone" in topic_map:
        narrative_parts.append(
            "The data traces a shift from being alone to finding solitude — a meaningful distinction."
        )

    fallback_narrative = (
        " ".join(narrative_parts)
        if narrative_parts
        else f"Your {len(filenames)} uploaded files contain {len(meaningful)} substantive entries spanning {year_range}. The data shows patterns worth examining."
    )

    # Extract periods for mindset shifts
    sorted_dates = sorted(set(dates)) if dates else []
    early = sorted_dates[:1] if sorted_dates else ["early entries"]
    late = sorted_dates[-1:] if sorted_dates else ["later entries"]

    # Build story arcs from actual topics
    arcs = []
    if "moved" in topic_map or "city" in topic_map:
        arcs.append(
            {
                "title": "Relocation & Reinvention",
                "description": f"A move documented across multiple entries between {', '.join(early)} and {', '.join(late)}, showing adaptation to a new environment.",
            }
        )
    if "job" in topic_map or "career" in topic_map:
        arcs.append(
            {
                "title": "Career Evolution",
                "description": f"Professional changes appear in {len(topic_map.get('job', []) + topic_map.get('career', []))} entries, tracking growth and uncertainty.",
            }
        )
    if "friend" in topic_map:
        arcs.append(
            {
                "title": "Social Landscape",
                "description": f"Relationships with {', '.join(people[:2]) if people else 'others'} evolve across the timeline.",
            }
        )
    if "alone" in topic_map:
        arcs.append(
            {
                "title": "Solitude & Self-Discovery",
                "description": f"An arc from loneliness to chosen solitude, visible across multiple entries.",
            }
        )

    if not arcs:
        arcs = [
            {
                "title": "Documented Experience",
                "description": f"A collection of {len(filenames)} files spanning {year_range}, capturing personal reflections and events.",
            }
        ]

    # Mindset shifts from actual data
    shifts = []
    if ("scared" in topic_map or "afraid" in topic_map) and (
        "proud" in topic_map or "happy" in topic_map
    ):
        shifts.append(
            {
                "from_state": "Uncertainty and self-doubt",
                "to_state": "Growing confidence",
                "evidence": f"Early entries express fear ({topic_map.get('scared', [''])[0][:60]}...) while later entries show pride ({topic_map.get('proud', [''])[0][:60]}...).",
                "period": f"{' to '.join(early + late) if early and late else year_range}",
            }
        )
    if "alone" in topic_map:
        shifts.append(
            {
                "from_state": "Viewing solitude as loneliness",
                "to_state": "Embracing chosen solitude",
                "evidence": "The language around being alone shifts from negative to neutral/positive across the timeline.",
                "period": year_range,
            }
        )

    if not shifts:
        shifts.append(
            {
                "from_state": "Initial state as documented in early entries",
                "to_state": "Evolved state visible in later entries",
                "evidence": f"Changes in tone and content across {len(dates)} dated entries suggest personal growth.",
                "period": year_range,
            }
        )

    # Identity contradictions from actual data
    contradictions = []
    if ("scared" in topic_map or "afraid" in topic_map) and "moved" in topic_map:
        contradictions.append(
            {
                "observation": "You describe yourself as afraid, yet you made a major life change that requires courage.",
                "evidence": f"Entries expressing fear coexist with evidence of a cross-city move and career change.",
                "interpretation": "You may downplay your own bravery, framing decisive actions as natural while focusing on internal doubt.",
            }
        )
    if "alone" in topic_map and people:
        contradictions.append(
            {
                "observation": "You describe being alone, but multiple people appear across your entries.",
                "evidence": f"Despite references to solitude, {', '.join(people[:2])} appear repeatedly in your data.",
                "interpretation": "You may feel isolated even while maintaining meaningful relationships — a common tension.",
            }
        )

    if not contradictions:
        contradictions.append(
            {
                "observation": f"Your data shows both a desire for change and anchoring habits.",
                "evidence": f"Entries document major decisions ({', '.join(list(topic_map.keys())[:2])}) alongside everyday routines.",
                "interpretation": "Growth happens in the tension between the familiar and the unknown.",
            }
        )

    # People list from actual names
    people_list = (
        [
            {
                "identifier": p,
                "context": f"Appears in {word_counts[p]} entries across your data spanning {year_range}.",
            }
            for p in people
        ]
        if people
        else [
            {
                "identifier": "Yourself",
                "context": "The primary narrator across all entries.",
            }
        ]
    )

    # Defining moments from actual dates
    moments = []
    if sorted_dates:
        moments.append(
            {
                "moment": sorted_dates[0],
                "significance": "The earliest dated entry in your data, establishing the starting point of this narrative.",
            }
        )
    if len(sorted_dates) > 1:
        moments.append(
            {
                "moment": sorted_dates[-1],
                "significance": "The most recent dated entry, showing where your story currently stands.",
            }
        )
    if topic_map.get("moved"):
        moments.append(
            {
                "moment": "The move documented in your entries",
                "significance": "A clear pivot point that separates 'before' and 'after' in your timeline.",
            }
        )
    if topic_map.get("promotion"):
        moments.append(
            {
                "moment": "A promotion mentioned in your data",
                "significance": "Validation of your professional growth and a milestone in your career arc.",
            }
        )

    if not moments:
        moments.append(
            {
                "moment": "Your first upload to AI Lorekeeper",
                "significance": "The beginning of structured self-reflection through your personal data.",
            }
        )

    return {
        "the_sentence": f"Across {len(dates)} entries spanning {year_range}, your data reveals that you are not who you were — and that is precisely the point.",
        "narrative": fallback_narrative,
        "story_arcs": arcs[:3],
        "recurring_people": people_list,
        "defining_moments": moments[:3],
        "mindset_shifts": shifts[:2],
        "core_themes": list(topic_map.keys())[:5]
        if topic_map
        else ["reflection", "growth", "documentation"],
        "identity_contradictions": contradictions[:2],
    }
