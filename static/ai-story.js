/**
 * AI 맞춤 스토리텔링 해설 UI (Claude /api/ai/interpret/stream)
 */
(function () {
  "use strict";

  const TAB_KEYS = ["wonkuk", "hapchung", "yongsin", "daewoon", "jonghap", "sinsal"];
  const LOADING_MSGS = [
    "🔮 사주를 읽고 있습니다...",
    "✨ 당신만의 해설을 작성 중입니다...",
    "📖 거의 다 됐습니다...",
  ];

  let aiEnabled = false;
  let tier = "free";
  const panelState = new Map();

  function escapeHtml(text) {
    const n = document.createElement("div");
    n.textContent = text == null ? "" : String(text);
    return n.innerHTML;
  }

  function formatContent(text) {
    return escapeHtml(text || "").replace(/\n/g, "<br>");
  }

  async function fetchConfig() {
    try {
      const res = await fetch("/api/ai/config");
      const data = await res.json();
      aiEnabled = !!data.enabled;
      return data;
    } catch {
      aiEnabled = false;
      return { enabled: false };
    }
  }

  function getUserName() {
    const el = document.getElementById("user_name");
    return el ? (el.value || "").trim() : "";
  }

  function wrapPanel(panel, tabKey) {
    if (!panel || panel.querySelector(".ai-story-panel")) return;
    const children = [...panel.childNodes];
    panel.innerHTML = "";
    panel.dataset.aiWrapped = "1";

    const aiBlock = document.createElement("section");
    aiBlock.className = "ai-story-panel";
    aiBlock.dataset.tab = tabKey;
    aiBlock.innerHTML = `
      <div class="ai-story-toolbar">
        <span class="ai-story-label">✨ 맞춤 스토리텔링 해설</span>
        <button type="button" class="ai-refresh-btn" title="다시 해설받기">🔄 다시 해설받기</button>
      </div>
      <div class="ai-story-status" aria-live="polite"></div>
      <div class="ai-story-body"></div>
      <div class="ai-story-feedback" hidden>
        <span>이 해설이 도움이 되셨나요?</span>
        <button type="button" class="ai-fb-btn" data-vote="up" title="좋아요">👍</button>
        <button type="button" class="ai-fb-btn" data-vote="down" title="아쉬워요">👎</button>
      </div>`;

    const details = document.createElement("details");
    details.className = "ai-data-collapse";
    const summary = document.createElement("summary");
    summary.className = "ai-data-toggle";
    summary.textContent = "데이터 보기 ▼";
    const inner = document.createElement("div");
    inner.className = "ai-data-inner";
    children.forEach((c) => inner.appendChild(c));
    details.appendChild(summary);
    details.appendChild(inner);

    panel.appendChild(aiBlock);
    panel.appendChild(details);

    const refreshBtn = aiBlock.querySelector(".ai-refresh-btn");
    refreshBtn.addEventListener("click", () => {
      const report = window.__latestSajuReport;
      if (report) loadTab(tabKey, report, { force: true });
    });

    aiBlock.querySelectorAll(".ai-fb-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const vote = btn.dataset.vote;
        try {
          const key = `ai_fb_${tabKey}_${reportCacheKey(window.__latestSajuReport)}`;
          localStorage.setItem(key, vote);
        } catch (_) {
          /* ignore */
        }
        btn.closest(".ai-story-feedback").innerHTML = "<span class=\"ai-fb-thanks\">소중한 의견 감사합니다 🙏</span>";
      });
    });

    panelState.set(tabKey, { block: aiBlock, loaded: false });
  }

  function reportCacheKey(report) {
    if (!report || !report.pillars) return "";
    const p = report.pillars;
    return ["year", "month", "day", "hour"]
      .map((k) => (p[k] && p[k].pillar) || "")
      .join("");
  }

  function renderSections(bodyEl, sections, { typing = false } = {}) {
    bodyEl.innerHTML = "";
    if (!sections || !sections.length) {
      bodyEl.innerHTML = "<p class=\"ai-story-empty\">해설을 불러오지 못했습니다.</p>";
      return;
    }
    sections.forEach((sec, idx) => {
      const card = document.createElement("article");
      card.className = "ai-story-section";
      const title = sec.title || sec.id || `섹션 ${idx + 1}`;
      const content = sec.content || "";
      card.innerHTML = `<h4 class="ai-story-section-title">${escapeHtml(title)}</h4><div class="ai-story-section-body"></div>`;
      bodyEl.appendChild(card);
      const body = card.querySelector(".ai-story-section-body");
      if (typing) {
        typeText(body, content);
      } else {
        body.innerHTML = formatContent(content);
      }
    });
  }

  function typeText(el, text, speed = 12) {
    const raw = String(text || "");
    let i = 0;
    el.textContent = "";
    const timer = setInterval(() => {
      i += 3;
      el.textContent = raw.slice(0, i);
      if (i >= raw.length) {
        clearInterval(timer);
        el.innerHTML = formatContent(raw);
      }
    }, speed);
  }

  function setStatus(block, msg) {
    const st = block.querySelector(".ai-story-status");
    if (st) st.textContent = msg || "";
  }

  async function loadTab(tabKey, report, { force = false } = {}) {
    const st = panelState.get(tabKey);
    if (!st || !st.block) return;
    if (!aiEnabled) {
      setStatus(
        st.block,
        "AI 해설: PowerShell에서 GEMINI_API_KEY(또는 ANTHROPIC_API_KEY) 설정 후 서버를 다시 시작하세요."
      );
      return;
    }
    if (st.loading) return;
    st.loading = true;

    const bodyEl = st.block.querySelector(".ai-story-body");
    const fb = st.block.querySelector(".ai-story-feedback");
    if (fb) fb.hidden = true;
    bodyEl.innerHTML = "";
    setStatus(st.block, LOADING_MSGS[0]);

    let msgIdx = 0;
    const msgTimer = setInterval(() => {
      msgIdx = (msgIdx + 1) % LOADING_MSGS.length;
      setStatus(st.block, LOADING_MSGS[msgIdx]);
    }, 2800);

    const payload = {
      tab: tabKey,
      saju_data: report,
      user_name: getUserName(),
      force_refresh: !!force,
      tier,
    };

    try {
      const res = await fetch("/api/ai/interpret/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Saju-Tier": tier },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || `HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let streamBuf = "";
      let doneSections = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const part of parts) {
          const line = part.split("\n").find((l) => l.startsWith("data: "));
          if (!line) continue;
          let ev;
          try {
            ev = JSON.parse(line.slice(6));
          } catch {
            continue;
          }
          if (ev.type === "status" && ev.message) {
            setStatus(st.block, ev.message);
          } else if (ev.type === "cached" && ev.sections) {
            clearInterval(msgTimer);
            setStatus(st.block, "📂 저장된 맞춤 해설을 불러왔습니다.");
            renderSections(bodyEl, ev.sections, { typing: true });
          } else if (ev.type === "delta" && ev.text) {
            streamBuf += ev.text;
            bodyEl.innerHTML = `<pre class="ai-stream-raw">${escapeHtml(streamBuf)}</pre>`;
          } else if (ev.type === "done" && ev.sections) {
            doneSections = ev.sections;
          } else if (ev.type === "error") {
            throw new Error(ev.message || "해설 생성 실패");
          }
        }
      }

      clearInterval(msgTimer);
      if (doneSections) {
        setStatus(st.block, evFromCacheLabel(streamBuf, doneSections));
        renderSections(bodyEl, doneSections, { typing: false });
        if (fb) fb.hidden = false;
      } else if (streamBuf) {
        try {
          const parsed = JSON.parse(streamBuf);
          if (parsed.sections) {
            renderSections(bodyEl, parsed.sections);
            if (fb) fb.hidden = false;
          }
        } catch {
          bodyEl.innerHTML = `<div class="ai-story-raw">${formatContent(streamBuf)}</div>`;
        }
      }
      st.loaded = true;
    } catch (e) {
      clearInterval(msgTimer);
      setStatus(st.block, "");
      const msg = String(e.message || e);
      const friendly =
        msg.includes("429") || /quota|한도/i.test(msg)
          ? "⏳ Gemini 무료 한도에 잠시 걸렸습니다. 15~30분 후 「🔄 다시 해설받기」를 눌러 보세요. 지금은 「데이터 보기 ▼」 기본 해설을 참고하세요."
          : msg;
      bodyEl.innerHTML = `<p class="ai-story-error">${formatContent(friendly)}</p>`;
    } finally {
      st.loading = false;
    }
  }

  function evFromCacheLabel(_buf, _sections) {
    return "✅ 맞춤 해설이 준비되었습니다.";
  }

  function onTabVisible(tabIndex, report) {
    const tabKey = TAB_KEYS[tabIndex];
    if (!tabKey || !report) return;
    window.__latestSajuReport = report;
    const st = panelState.get(tabKey);
    if (!st) return;
    if (!st.loaded || reportCacheKey(report) !== st.lastKey) {
      st.lastKey = reportCacheKey(report);
      st.loaded = false;
    }
    if (!st.loaded && !st.loading) loadTab(tabKey, report);
  }

  function afterReport(report) {
    window.__latestSajuReport = report;
    TAB_KEYS.forEach((key, i) => {
      const panel = document.getElementById(`panel-${i}`);
      if (panel) wrapPanel(panel, key);
      const st = panelState.get(key);
      if (st) {
        st.loaded = false;
        st.lastKey = "";
      }
    });
    if (report) onTabVisible(0, report);
  }

  window.SajuAi = {
    TAB_KEYS,
    fetchConfig,
    wrapPanel,
    onTabVisible,
    loadTab,
    afterReport,
    setTier(t) {
      tier = t || "free";
    },
    init() {
      return fetchConfig();
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => window.SajuAi.init());
  } else {
    window.SajuAi.init();
  }
})();
