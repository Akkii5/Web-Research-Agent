# 🔍 Web Research Agent

A fully local AI-powered research agent. Give it a topic — it searches the web,
reads the top results, and generates a structured report with citations using Claude.

---

## 📁 Project Structure

```
web-research-agent/
├── app.py                  ← Flask server (run this)
├── agent.py                ← Main pipeline orchestrator
├── requirements.txt        ← Python dependencies
├── .env.example            ← Copy to .env and add your keys
│
├── backend/
│   ├── search.py           ← Web search (DuckDuckGo or SerpAPI)
│   ├── scraper.py          ← Page content fetcher
│   └── synthesizer.py      ← Claude AI report generator
│
├── frontend/
│   ├── templates/
│   │   └── index.html      ← Main UI page
│   └── static/
│       ├── css/style.css   ← Styling
│       └── js/main.js      ← Frontend logic
│
└── reports/                ← (Optional) saved markdown reports
```

---

## 🚀 Setup & Run

### 1. Install Python dependencies

```bash
cd web-research-agent
pip install -r requirements.txt
```

### 2. Set up your API key

```bash
cp .env.example .env
```

Open `.env` and add your **Anthropic API key**:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Get your key at: https://console.anthropic.com/

### 3. (Optional) Add SerpAPI for better search results

The agent works out-of-the-box using free DuckDuckGo search.
For more reliable results, sign up at https://serpapi.com (100 free searches/month)
and add to `.env`:
```
SERPAPI_KEY=your_key_here
```

### 4. Run the server

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 💡 How It Works

```
User enters topic
       ↓
[Search] DuckDuckGo / SerpAPI → top N URLs
       ↓
[Scrape] Fetch & clean text from each URL
       ↓
[Synthesize] Claude reads all content → structured JSON report
       ↓
[Display] Beautiful UI with sections, key facts, citations
       ↓
[Export] Download as Markdown file
```

---

## ⚙️ Configuration

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Claude API key |
| `SERPAPI_KEY` | No | Better search (optional) |
| `FLASK_PORT` | No | Default: `5000` |
| `FLASK_DEBUG` | No | Default: `false` |
