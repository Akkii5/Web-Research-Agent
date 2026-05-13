"""
synthesizer.py — Uses the Groq API (llama-3.3-70b) to turn raw scraped data
                 into a structured research report with citations.
"""

import os
import json
import re
import requests


GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def synthesize_report(topic: str, sources: list[dict]) -> dict:
    """
    Given a topic and a list of source dicts:
        { title, url, snippet, content }

    Returns a report dict:
        {
          "title":      str,
          "summary":    str,          # 2-3 sentence executive summary
          "sections":   [             # list of report sections
              { "heading": str, "body": str }
          ],
          "key_facts":  [str, ...],   # bullet-point takeaways
          "citations":  [             # numbered citation list
              { "number": int, "title": str, "url": str }
          ],
          "conclusion": str,
        }
    """
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Please add it to your .env file.")

    source_context = _format_sources(sources)

    system_prompt = """You are an expert research analyst. Your job is to read web sources 
and produce a clear, well-structured research report. Be factual, cite sources by number 
(e.g. [1], [2]), and do not hallucinate. If the sources are thin, say so honestly.

IMPORTANT: You must respond ONLY with a valid JSON object — no markdown fences, no extra text.
The JSON must match this exact schema:
{
  "title": "string — descriptive report title",
  "summary": "string — 2-3 sentence executive summary",
  "sections": [
    { "heading": "string", "body": "string with inline [N] citations" }
  ],
  "key_facts": ["string", "string", ...],
  "citations": [
    { "number": 1, "title": "string", "url": "string" }
  ],
  "conclusion": "string — final synthesis paragraph"
}
Produce 3–5 sections. key_facts should have 4–7 items. Do not include any text outside the JSON."""

    user_message = f"""Research Topic: {topic}

--- SOURCES ---
{source_context}

Write a comprehensive research report about "{topic}" using only the sources above.
Reference sources inline as [1], [2], etc. matching the source numbers above."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens":  2500,
        "temperature": 0.3,
    }

    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()

    raw = resp.json()["choices"][0]["message"]["content"].strip()
    return _parse_json_response(raw, topic, sources)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _format_sources(sources: list[dict]) -> str:
    lines = []
    for i, s in enumerate(sources, 1):
        content_preview = (s.get("content") or s.get("snippet") or "")[:1500]
        lines.append(
            f"[{i}] Title: {s['title']}\n"
            f"    URL: {s['url']}\n"
            f"    Content:\n{content_preview}\n"
        )
    return "\n".join(lines)


def _parse_json_response(raw: str, topic: str, sources: list[dict]) -> dict:
    """Try to parse the JSON; fall back to a minimal report on failure."""
    # Strip accidental markdown fences
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        report = json.loads(clean)
        # Ensure citations always include all sources
        if not report.get("citations"):
            report["citations"] = [
                {"number": i + 1, "title": s["title"], "url": s["url"]}
                for i, s in enumerate(sources)
            ]
        return report
    except json.JSONDecodeError as e:
        print(f"[synthesizer] JSON parse error: {e}\nRaw response:\n{raw[:500]}")
        # Return a minimal valid report
        return {
            "title": f"Research Report: {topic}",
            "summary": "The report could not be fully structured. See the raw content below.",
            "sections": [{"heading": "Raw Output", "body": raw}],
            "key_facts": ["Report generation encountered a formatting issue."],
            "citations": [
                {"number": i + 1, "title": s["title"], "url": s["url"]}
                for i, s in enumerate(sources)
            ],
            "conclusion": "Please retry or refine the topic.",
        }
