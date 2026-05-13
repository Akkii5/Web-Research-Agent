/* ═══════════════════════════════════════════════
   Research Agent — Frontend Logic
   ═══════════════════════════════════════════════ */

let currentReport = null;  // holds the last successful result

// ── Entry point ────────────────────────────────

async function startResearch() {
  const topic = document.getElementById("topicInput").value.trim();
  if (!topic) {
    shakeInput();
    return;
  }

  const numSources = parseInt(document.getElementById("numSources").value, 10);

  setUIState("loading");
  animateSteps();

  try {
    const res = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, num_sources: numSources }),
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      setUIState("error", data.error || "Unknown server error.");
      return;
    }

    currentReport = data;
    renderReport(data);
    setUIState("report");

  } catch (err) {
    setUIState("error", "Could not reach the server. Is Flask running?");
  }
}

// ── UI State ───────────────────────────────────

function setUIState(state, errorMsg = "") {
  document.getElementById("progressArea").style.display = state === "loading" ? "flex" : "none";
  document.getElementById("reportArea").style.display   = state === "report"  ? "block" : "none";
  document.getElementById("errorArea").style.display    = state === "error"   ? "flex"  : "none";

  const btn = document.getElementById("searchBtn");
  btn.disabled = state === "loading";

  if (state === "error") {
    document.getElementById("errorMessage").textContent = errorMsg;
  }
  if (state === "loading") {
    document.querySelector(".hero").style.paddingBottom = "2rem";
  }
}

function resetUI() {
  setUIState("idle");
  document.getElementById("topicInput").value = "";
  document.getElementById("topicInput").focus();
  document.querySelector(".hero").style.paddingBottom = "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ── Animated progress steps ────────────────────

function animateSteps() {
  const steps = ["step1", "step2", "step3"];
  let i = 0;

  steps.forEach(id => {
    const el = document.getElementById(id);
    el.className = "step";
  });
  document.getElementById("step1").classList.add("active");

  const interval = setInterval(() => {
    if (i < steps.length - 1) {
      document.getElementById(steps[i]).classList.remove("active");
      document.getElementById(steps[i]).classList.add("done");
      i++;
      document.getElementById(steps[i]).classList.add("active");
    } else {
      clearInterval(interval);
    }
  }, 2800);
}

// ── Render report ──────────────────────────────

function renderReport(data) {
  const { topic, report, duration, sources } = data;
  if (!report) return;

  // Meta bar
  document.getElementById("reportMeta").innerHTML = `
    <span class="meta-topic">🔍 ${escHtml(topic)}</span>
    <span class="meta-badge ok">✓ ${sources.length} sources</span>
    <span class="meta-badge">Claude</span>
    <span class="meta-time">⏱ ${duration}s</span>
  `;

  // Build body
  let html = `<h1 class="report-title">${escHtml(report.title || topic)}</h1>`;

  if (report.summary) {
    html += `<p class="report-summary">${formatBody(report.summary)}</p>`;
  }

  (report.sections || []).forEach(sec => {
    html += `
      <div class="report-section">
        <h2 class="section-heading">${escHtml(sec.heading)}</h2>
        <div class="section-body">${formatBody(sec.body)}</div>
      </div>
    `;
  });

  if (report.conclusion) {
    html += `
      <div class="report-conclusion">
        <div class="conclusion-label">Conclusion</div>
        <div class="conclusion-text">${formatBody(report.conclusion)}</div>
      </div>
    `;
  }

  document.getElementById("reportBody").innerHTML = html;

  // Key facts sidebar
  const facts = report.key_facts || [];
  if (facts.length) {
    const ul = document.getElementById("keyFactsList");
    ul.innerHTML = facts.map(f => `<li>${escHtml(f)}</li>`).join("");
    document.getElementById("keyFactsBox").style.display = "block";
  }

  // Citations sidebar
  const citations = report.citations || [];
  if (citations.length) {
    const ol = document.getElementById("citationsList");
    ol.innerHTML = citations.map(c => `
      <li>
        <a href="${escHtml(c.url)}" target="_blank" rel="noopener">
          <span class="cite-num">${c.number}</span>
          <span class="cite-title">${escHtml(c.title || c.url)}</span>
        </a>
      </li>
    `).join("");
    document.getElementById("citationsBox").style.display = "block";
  }
}

// ── Helpers ────────────────────────────────────

function formatBody(text) {
  if (!text) return "";
  // Convert [N] citation markers to styled spans
  let safe = escHtml(text);
  safe = safe.replace(/\[(\d+)\]/g, '<span class="cite" title="See source $1">[$1]</span>');
  // Paragraph breaks
  safe = safe.replace(/\n{2,}/g, "</p><p>").replace(/\n/g, "<br/>");
  return `<p>${safe}</p>`;
}

function escHtml(str) {
  if (typeof str !== "string") return String(str || "");
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function shakeInput() {
  const box = document.getElementById("searchBox");
  box.style.animation = "none";
  box.style.transform = "translateX(8px)";
  setTimeout(() => {
    box.style.transition = "transform 0.3s";
    box.style.transform = "translateX(0)";
  }, 80);
}

function setTopic(btn) {
  document.getElementById("topicInput").value = btn.textContent;
  document.getElementById("topicInput").focus();
}

// ── Keyboard shortcut ──────────────────────────
document.addEventListener("keydown", e => {
  if (e.key === "Enter" && document.activeElement.id === "topicInput") {
    startResearch();
  }
});

// ── Export as Markdown ──────────────────────────
function exportMarkdown() {
  if (!currentReport) return;
  const { topic, report, sources, duration } = currentReport;

  let md = `# ${report.title || topic}\n\n`;
  md += `> **Topic:** ${topic}  \n> **Sources:** ${sources.length}  \n> **Time:** ${duration}s\n\n`;
  md += `---\n\n`;
  md += `## Summary\n\n${report.summary || ""}\n\n`;

  (report.sections || []).forEach(sec => {
    md += `## ${sec.heading}\n\n${sec.body}\n\n`;
  });

  if (report.conclusion) {
    md += `## Conclusion\n\n${report.conclusion}\n\n`;
  }

  if (report.key_facts?.length) {
    md += `## Key Facts\n\n`;
    report.key_facts.forEach(f => { md += `- ${f}\n`; });
    md += "\n";
  }

  if (report.citations?.length) {
    md += `## Sources\n\n`;
    report.citations.forEach(c => { md += `${c.number}. [${c.title}](${c.url})\n`; });
  }

  const blob = new Blob([md], { type: "text/markdown" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `research-${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);
}
