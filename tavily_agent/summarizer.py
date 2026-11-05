"""LLM summariser with an honest extractive fallback.

Rules:
- No LLM call is made unless LLM_API_KEY is set in the environment.
- LLM_BASE_URL and LLM_MODEL are optional env vars; defaults point
  at an OpenAI-compatible chat-completions endpoint. No provider is
  claimed as tested unless a live run with that provider succeeds.
- Any failure, timeout, or missing key returns the extractive
  summary and the caller must label the briefing 'extractive'.
- The LLM is only asked to summarise the supplied snippets. It is
  never asked to invent dates, sources, or facts, and its output is
  never used to add new developments to the briefing.
"""
from __future__ import annotations

import os

import requests

from .briefing import first_sentence


def extractive_summary(results) -> str:
    sentences = [first_sentence(r.snippet) for r in results[:3]]
    return " ".join(s for s in sentences if s)


def try_llm_summary(results, subject: str) -> tuple[str | None, str]:
    """Return (summary or None, mode). Mode is 'llm' or 'extractive'."""
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key or not results:
        return None, "extractive"
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    context = "\n".join(
        f"- {r.title} ({r.url}): {first_sentence(r.snippet)}" for r in results[:8]
    )
    prompt = (
        f"Summarise only the findings below for a pre-meeting briefing "
        f"about {subject}. Do not invent dates, facts, or sources. "
        f"Keep it to 3 sentences.\n\n{context}"
    )
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=30,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"].strip()
        return (text or None), ("llm" if text else "extractive")
    except Exception:
        return None, "extractive"
