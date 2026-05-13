"""
app.py — Flask web server. Serves the UI and exposes the /api/research endpoint.
"""

import os
import json
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from dotenv import load_dotenv
from agent import run_research_agent

# Load .env variables
load_dotenv()

app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")
app.config["JSON_SORT_KEYS"] = False


# ── Routes ───────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/research", methods=["POST"])
def research():
    """
    POST body: { "topic": "...", "num_sources": 6 }
    Returns:   { topic, sources, report, duration, error }
    """
    body = request.get_json(silent=True) or {}
    topic = (body.get("topic") or "").strip()
    num_sources = min(int(body.get("num_sources", 6)), 10)  # cap at 10

    if not topic:
        return jsonify({"error": "Please provide a research topic."}), 400

    if not os.getenv("GROQ_API_KEY"):
        return jsonify({"error": "GROQ_API_KEY is not set. Please check your .env file."}), 500

    result = run_research_agent(topic, num_sources=num_sources)
    return jsonify(result)


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "groq_key_set":    bool(os.getenv("GROQ_API_KEY")),
        "serpapi_key_set": bool(os.getenv("SERPAPI_KEY")),
    })


# ── Run ──────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"\n🔍  Web Research Agent running at  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
