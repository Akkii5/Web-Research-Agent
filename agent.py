"""
agent.py — Orchestrates the full research pipeline:
           Search → Scrape → Synthesize → Report
"""

import time
from backend.search import search_web
from backend.scraper import fetch_page_content
from backend.synthesizer import synthesize_report


def run_research_agent(topic: str, num_sources: int = 6) -> dict:
    """
    Main entry point. Runs the full research pipeline and returns a report dict.

    Steps:
      1. Search the web for the topic
      2. Scrape full content from each result URL
      3. Synthesize a structured report using Claude

    Returns:
        {
          "topic":    str,
          "sources":  [ { title, url, snippet, content } ],
          "report":   { title, summary, sections, key_facts, citations, conclusion },
          "duration": float (seconds),
          "error":    str or None,
        }
    """
    start = time.time()

    # ── 1. Search ──────────────────────────────
    print(f"[agent] Searching for: {topic}")
    try:
        search_results = search_web(topic, num_results=num_sources)
    except Exception as e:
        return _error_response(topic, f"Search failed: {e}", start)

    if not search_results:
        return _error_response(topic, "No search results found.", start)

    print(f"[agent] Found {len(search_results)} results")

    # ── 2. Scrape ──────────────────────────────
    sources = []
    for i, result in enumerate(search_results):
        print(f"[agent] Scraping [{i+1}/{len(search_results)}]: {result['url']}")
        content = fetch_page_content(result["url"])
        sources.append({
            "title":   result["title"],
            "url":     result["url"],
            "snippet": result["snippet"],
            "content": content,
        })
        time.sleep(0.3)   # be a polite scraper

    # ── 3. Synthesize ─────────────────────────
    print("[agent] Synthesizing report with Claude…")
    try:
        report = synthesize_report(topic, sources)
    except Exception as e:
        return _error_response(topic, f"Synthesis failed: {e}", start)

    duration = round(time.time() - start, 1)
    print(f"[agent] Done in {duration}s")

    return {
        "topic":    topic,
        "sources":  sources,
        "report":   report,
        "duration": duration,
        "error":    None,
    }


def _error_response(topic: str, message: str, start: float) -> dict:
    return {
        "topic":    topic,
        "sources":  [],
        "report":   None,
        "duration": round(time.time() - start, 1),
        "error":    message,
    }
