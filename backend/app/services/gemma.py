import json
import logging
import re
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ─── No-yapping system prompt with one-shot example ──────────────────────────

SYSTEM_PROMPT = """CRITICAL: Do not explain your thought process. Do not describe these instructions. Do not use conversational filler. Return ONLY the requested JSON output and absolutely nothing else.

Extract a personal narrative synthesis from the user's data. Follow the exact format below.

Example:
Input: Started a new job in March. Felt anxious. By June, made friends at work. Felt happy.
Output: {"the_sentence": "From anxiety to belonging in three months.", "narrative": "You started a new job in March feeling anxious. By June you had made friends and felt happy.", "story_arcs": [{"title": "Workplace Integration", "description": "From nervous newcomer to social team member over three months."}], "recurring_people": [], "defining_moments": [{"moment": "First day at new job in March", "significance": "Marked the beginning of a major life transition."}], "mindset_shifts": [{"from_state": "Anxious about new environment", "to_state": "Comfortable and happy at work", "evidence": "March entry expressed anxiety; June entry expressed happiness.", "period": "March to June"}], "core_themes": ["growth", "adaptation"], "identity_contradictions": []}

Now produce the same format for the data below. Rules:
1. Only use actual data. No invented names, places, or events.
2. Quote specific evidence. Use actual dates and names from the data.
3. Identity contradictions must cite conflicting entries.
4. Mindset shifts must reference real time periods from the data."""


# ─── Google AI API call ──────────────────────────────────────────────────


async def call_gemma_synthesis(batched_text: str) -> Optional[dict]:
    """Send batched content to Gemma 4 via Google AI API. Returns parsed JSON or None."""
    if not settings.GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY configured — using fallback synthesis")
        return _fallback_synthesis(batched_text)

    logger.info(
        f"Sending {len(batched_text)} chars to {settings.GEMINI_MODEL} via Google AI API"
    )
    model = settings.GEMINI_MODEL
    url = f"{settings.GEMINI_API_URL}/{model}:generateContent?key={settings.GEMINI_API_KEY}"

    user_msg = (
        f"{SYSTEM_PROMPT}\n\nUser data:\n{batched_text}\n\nReturn ONLY valid JSON."
    )

    payload = {
        "contents": [{"parts": [{"text": user_msg}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096},
    }

    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Full API response: {str(data)[:300]}")
            if not data.get("candidates"):
                logger.warning(f"No candidates in response")
                return None

        text_content = ""
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if part.get("text", "").strip():
                text_content = part["text"]
                break

        if not text_content:
            logger.warning("Gemma 4 returned empty response")
            return None

        logger.info(
            f"Gemma 4 raw response ({len(text_content)} chars): {text_content[:200]}..."
        )
        parsed = _parse_json_response(text_content)
        if parsed:
            logger.info("JSON parsed successfully")
        else:
            logger.warning(
                f"Failed to parse JSON from response, first 500 chars: {text_content[:500]}"
            )
        return parsed

    except Exception as e:
        logger.error(f"Google AI API call failed: {e}")
        return _fallback_synthesis(batched_text)


# ─── JSON parsing helpers ─────────────────────────────────────────────────────


def _parse_json_response(text: str) -> Optional[dict]:
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


# ─── Fallback ─────────────────────────────────────────────────────────────────


def _fallback_synthesis(batched_text: str) -> dict:
    logger.info("Generating fallback synthesis from parsed data")
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
    people = sorted(
        [w for w, c in word_counts.items() if c >= 2], key=lambda w: -word_counts[w]
    )[:3]
    dates = re.findall(
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
        batched_text,
    )
    years_found = sorted(set(re.findall(r"\b(202\d)\b", batched_text)))
    filenames = [
        f.strip() for f in re.findall(r"FILE:\s*([^\]]+)", batched_text) if f.strip()
    ]
    year_range = (
        f"{min(years_found)} to {max(years_found)}"
        if years_found
        else "the documented period"
    )
    people_str = ", ".join(people[:3]) if people else ""
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
    for cond, msg in [
        ("moved", "A move marks a clear before/after point in your timeline."),
        (
            ("job", "career"),
            "Career changes and professional growth are recurring themes.",
        ),
        ("friend", "Friendships play a central role."),
        (
            ("scared", "afraid"),
            "Early entries show fear and uncertainty, shifting later.",
        ),
        ("alone", "The language around being alone shifts over time."),
        ("promotion", "A promotion marks professional validation."),
    ]:
        if isinstance(cond, tuple):
            if any(k in topic_map for k in cond):
                narrative_parts.append(msg)
        elif cond in topic_map:
            narrative_parts.append(msg)

    arcs = []
    for test, title, desc in [
        (
            ("moved", "city"),
            "Relocation & Reinvention",
            f"A move documented in your files, showing adaptation across {year_range}.",
        ),
        (
            ("job", "career"),
            "Career Evolution",
            "Professional changes appear in your entries.",
        ),
        (
            "friend",
            "Social Landscape",
            f"Relationships with {people_str if people else 'others'} evolve across your timeline.",
        ),
        (
            "alone",
            "Solitude & Self-Discovery",
            "An arc from loneliness to chosen solitude.",
        ),
    ]:
        hits = [test] if isinstance(test, str) else test
        if any(k in topic_map for k in hits):
            arcs.append({"title": title, "description": desc})
    if not arcs:
        arcs.append(
            {
                "title": "Documented Experience",
                "description": f"{len(filenames)} files spanning {year_range}.",
            }
        )

    shifts = []
    if ("scared" in topic_map or "afraid" in topic_map) and (
        "proud" in topic_map or "happy" in topic_map
    ):
        shifts.append(
            {
                "from_state": "Uncertainty and self-doubt",
                "to_state": "Growing confidence",
                "evidence": "Early entries express fear while later entries show pride.",
                "period": year_range,
            }
        )
    if "alone" in topic_map:
        shifts.append(
            {
                "from_state": "Viewing solitude as loneliness",
                "to_state": "Embracing chosen solitude",
                "evidence": "The language around being alone shifts from negative to neutral.",
                "period": year_range,
            }
        )
    if not shifts:
        shifts.append(
            {
                "from_state": "Initial state in early entries",
                "to_state": "Evolved state in later entries",
                "evidence": "Changes in tone suggest personal growth.",
                "period": year_range,
            }
        )

    contradictions = []
    if ("scared" in topic_map or "afraid" in topic_map) and "moved" in topic_map:
        contradictions.append(
            {
                "observation": "You describe fear, yet you made a major life change.",
                "evidence": "Entries expressing fear coexist with evidence of a move.",
                "interpretation": "You may downplay your own bravery.",
            }
        )
    if "alone" in topic_map and people:
        contradictions.append(
            {
                "observation": "You describe being alone, but multiple people appear.",
                "evidence": f"Despite references to solitude, {people_str} appear repeatedly.",
                "interpretation": "You may feel isolated while maintaining relationships.",
            }
        )
    if not contradictions:
        contradictions.append(
            {
                "observation": "Your data shows both desire for change and anchoring habits.",
                "evidence": "Major decisions coexist with everyday routines.",
                "interpretation": "Growth happens in tension between familiar and unknown.",
            }
        )

    return {
        "the_sentence": f"Across {len(filenames)} files spanning {year_range}, your data reveals patterns worth examining.",
        "narrative": " ".join(narrative_parts)
        if narrative_parts
        else f"Your {len(filenames)} uploaded files span {year_range}.",
        "story_arcs": arcs[:3],
        "recurring_people": [
            {
                "identifier": p,
                "context": f"Appears in your entries across {year_range}.",
            }
            for p in people
        ]
        if people
        else [
            {
                "identifier": "Yourself",
                "context": "The narrator across your uploaded files.",
            }
        ],
        "defining_moments": [
            {
                "moment": f"Entries from {dates[0]} to {dates[-1]}",
                "significance": f"Your timeline spans {dates[0]} to {dates[-1]}.",
            }
        ]
        if dates
        else [
            {
                "moment": "Your data upload",
                "significance": "The beginning of structured self-reflection.",
            }
        ],
        "mindset_shifts": shifts[:2],
        "core_themes": list(topic_map.keys())[:5]
        if topic_map
        else ["reflection", "growth", "documentation"],
        "identity_contradictions": contradictions[:2],
    }
