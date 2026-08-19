"""Small OpenAI Responses API client implemented with the Python standard library."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


DEFAULT_API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.6-luna"


def extract_response_text(response: dict[str, Any]) -> str:
    """Extract text from a Responses API payload."""

    direct = response.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    pieces: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                pieces.append(content["text"])
    text = "\n".join(pieces).strip()
    if not text:
        raise RuntimeError("The AI provider returned no text.")
    return text


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating a fenced markdown wrapper."""

    cleaned = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The AI response was not valid JSON. Please try again.") from exc
    if not isinstance(value, dict):
        raise RuntimeError("The AI response must be a JSON object.")
    return value


def generate_json(
    *,
    instructions: str,
    prompt: str,
    max_output_tokens: int = 1400,
) -> dict[str, Any]:
    """Call the Responses API and return its JSON object output."""

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OpenAI mode needs OPENAI_API_KEY. Use Offline demo mode or set the key locally."
        )

    request_body = {
        "model": os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        "instructions": instructions,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
    }
    request = urllib.request.Request(
        os.getenv("OPENAI_RESPONSES_URL", DEFAULT_API_URL),
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:
            detail = ""
        message = detail or f"OpenAI request failed with status {exc.code}."
        raise RuntimeError(message) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not reach the AI provider. Check your internet connection.") from exc

    return parse_json_object(extract_response_text(payload))
