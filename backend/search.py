"""
search.py — Handles web search using DuckDuckGo (free) or SerpAPI (optional).
"""

import os
import requests
from bs4 import BeautifulSoup
import time
import re


# ──────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────

def search_web(query: str, num_results: int = 6) -> list[dict]:
    """
    Search the web for `query` and return a list of result dicts:
        { title, url, snippet }

    Tries SerpAPI first (if SERPAPI_KEY is set), then falls back to
    DuckDuckGo HTML scraping.
    """
    serpapi_key = os.getenv("SERPAPI_KEY", "").strip()
    if serpapi_key:
        try:
            return _serpapi_search(query, num_results, serpapi_key)
        except Exception as e:
            print(f"[search] SerpAPI failed ({e}), falling back to DuckDuckGo")

    return _duckduckgo_search(query, num_results)


# ──────────────────────────────────────────────
# SerpAPI backend
# ──────────────────────────────────────────────

def _serpapi_search(query: str, num_results: int, api_key: str) -> list[dict]:
    params = {
        "engine": "google",
        "q": query,
        "num": num_results,
        "api_key": api_key,
    }
    resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("organic_results", [])[:num_results]:
        results.append({
            "title":   item.get("title", ""),
            "url":     item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })
    return results


# ──────────────────────────────────────────────
# DuckDuckGo HTML scraping backend (free, no key)
# ──────────────────────────────────────────────

def _duckduckgo_search(query: str, num_results: int) -> list[dict]:
    """Scrape DuckDuckGo HTML search results (no API key needed)."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    url = "https://html.duckduckgo.com/html/"
    data = {"q": query, "b": "", "kl": "us-en"}

    try:
        resp = requests.post(url, data=data, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[search] DuckDuckGo request failed: {e}")
        return _fallback_results(query)

    soup = BeautifulSoup(resp.text, "lxml")
    results = []

    for result in soup.select(".result.results_links.results_links_deep")[:num_results]:
        title_tag = result.select_one(".result__title a")
        snippet_tag = result.select_one(".result__snippet")

        if not title_tag:
            continue

        raw_url = title_tag.get("href", "")
        # DuckDuckGo wraps URLs — extract the real one
        real_url = _extract_real_url(raw_url)

        results.append({
            "title":   title_tag.get_text(strip=True),
            "url":     real_url,
            "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
        })

    if not results:
        return _fallback_results(query)

    return results


def _extract_real_url(ddg_url: str) -> str:
    """Extract the real URL from DuckDuckGo's redirect wrapper."""
    match = re.search(r"uddg=([^&]+)", ddg_url)
    if match:
        from urllib.parse import unquote
        return unquote(match.group(1))
    return ddg_url


def _fallback_results(query: str) -> list[dict]:
    """Return a minimal fallback so the pipeline never breaks."""
    print("[search] Returning fallback placeholder results.")
    return [
        {
            "title":   f"Search result for: {query}",
            "url":     f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            "snippet": f"Wikipedia article about {query}.",
        }
    ]
