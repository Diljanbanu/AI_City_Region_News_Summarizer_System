"""
AI Summary Service (🤖 AI-Powered API)
Uses Google Gemini to produce a structured news summary, with a local NLP fallback.
"""

import json
import logging
import os
import re
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def generate_ai_news_summary(article: Dict[str, Any], gemini_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Summarize a news article with Gemini, falling back to extractive NLP."""
    api_key = (gemini_api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if api_key:
        gemini_result = _summarize_with_gemini(article, api_key)
        if gemini_result:
            return gemini_result
        logger.warning("Gemini unavailable; using local NLP summarizer.")
    return generate_nlp_fallback_summary(article)


def _summarize_with_gemini(article: Dict[str, Any], api_key: str) -> Optional[Dict[str, Any]]:
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        logger.warning("google-genai import failed: %s", exc)
        return None

    headline = article.get("title", "")
    source = article.get("source", "")
    location = article.get("location", "the area")
    content = article.get("full_text") or article.get("summary_preview") or headline

    prompt = f"""You are a news analyst. Summarize this article for residents of "{location}".

Headline: {headline}
Source: {source}
Location: {location}
Article text:
{content}

Return ONLY valid JSON with this schema:
{{
  "concise_summary": "2-3 clear sentences covering the story.",
  "important_points": ["key fact 1", "key fact 2", "key fact 3"],
  "main_event": "The central event or development.",
  "regional_impact": "Impact on people, transport, business, or daily life in {location}.",
  "urgency_level": "High, Medium, or Low",
  "category": "Weather, Infrastructure, Transit, Business, Civic, or General"
}}"""

    try:
        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
        )
        for model_name in GEMINI_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                text = (response.text or "").strip() if response else ""
                parsed = parse_json_response(text) if text else None
                if parsed and parsed.get("concise_summary"):
                    parsed["ai_engine"] = f"Google Gemini ({model_name})"
                    parsed["status"] = "Success"
                    parsed.setdefault("important_points", [])
                    parsed.setdefault("main_event", headline)
                    parsed.setdefault("regional_impact", f"Local developments in {location}.")
                    parsed.setdefault("urgency_level", "Medium")
                    parsed.setdefault("category", "General")
                    return parsed
            except Exception as model_exc:
                logger.warning("Gemini model %s failed: %s", model_name, model_exc)
    except Exception as exc:
        logger.warning("Gemini client failed: %s", exc)
    return None


def generate_nlp_fallback_summary(article: Dict[str, Any]) -> Dict[str, Any]:
    """Extractive summary used when Gemini is not available."""
    headline = article.get("title", "")
    content = article.get("full_text") or article.get("summary_preview") or headline
    location = article.get("location", "the city")
    source = article.get("source", "News Bureau")

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if len(s.strip()) > 15]
    if not sentences:
        sentences = [headline]

    concise = " ".join(sentences[:2]) if sentences else headline
    points = []
    keywords = ("expected", "announced", "project", "alert", "official", "issued", "new", "will", "plan", "residents")
    for sentence in sentences:
        if any(word in sentence.lower() for word in keywords) and sentence not in points:
            points.append(sentence)
    while len(points) < 3:
        extras = [
            f"Reported by {source}.",
            f"Authorities in {location} are tracking the situation.",
            f"Residents of {location} should follow official updates.",
        ]
        points.append(extras[len(points)])
    points = points[:4]

    text_lower = f"{headline} {content}".lower()
    if any(k in text_lower for k in ("rain", "flood", "storm", "weather", "cyclone", "warning", "alert")):
        main_event = f"Weather advisory issued for {location}."
        impact = f"Residents in {location} should stay alert, avoid waterlogged roads, and follow official weather bulletins."
        urgency, category = "High", "Weather"
    elif any(k in text_lower for k in ("metro", "train", "bus", "transport", "route", "transit", "highway")):
        main_event = f"Public transport update announced in {location}."
        impact = f"Daily commutes and traffic in {location} may change as the new transit plans take effect."
        urgency, category = "Medium", "Transit"
    elif any(k in text_lower for k in ("infrastructure", "project", "bridge", "flyover", "smart city", "park")):
        main_event = f"Infrastructure development announced for {location}."
        impact = f"Civic facilities and local investment in {location} are expected to improve."
        urgency, category = "Medium", "Infrastructure"
    else:
        main_event = f"Local development reported in {location} by {source}."
        impact = f"This update is relevant to residents and businesses in {location}."
        urgency, category = "Low", "General"

    return {
        "concise_summary": concise,
        "important_points": points,
        "main_event": main_event,
        "regional_impact": impact,
        "urgency_level": urgency,
        "category": category,
        "ai_engine": "Local NLP Summarizer",
        "status": "Success",
    }


def parse_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
    try:
        cleaned = re.sub(r"```json\s*", "", raw_text)
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(cleaned)
    except Exception as exc:
        logger.warning("Failed to parse Gemini JSON: %s", exc)
        return None
