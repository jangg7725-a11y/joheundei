(function () {
  "use strict";

  const SPREAD_ORDER = ["today", "week", "month", "year", "worry", "love", "deep"];

  const els = {
    sajuMain: document.getElementById("saju-main"),
    tarotMain: document.getElementById("tarot-main"),
    bottomNav: document.getElementById("bottom-nav"),
    modeBtns: document.querySelectorAll("[data-app-mode]"),
    spreadTabs: document.getElementById("tarot-spread-tabs"),
    deckDesc: document.getElementById("tarot-deck-desc"),
    instruction: document.getElementById("tarot-instruction"),
    deckArea: document.getElementById("tarot-deck-area"),
    drawPhase: document.getElementById("tarot-draw-phase"),
    resultPhase: document.getElementById("tarot-result-phase"),
    autoDraw: document.getElementById("tarot-auto-draw"),
    redraw: document.getElementById("tarot-redraw"),
    backDraw: document.getElementById("tarot-back-draw"),
    status: document.getElementById("tarot-status"),
    resultNav: document.getElementById("tarot-result-nav"),
    heroBack: document.getElementById("tarot-hero-back"),
    heroFront: document.getElementById("tarot-hero-front"),
    orientation: document.getElementById("tarot-orientation"),
    cardName: document.getElementById("tarot-card-name"),
    cardTags: document.getElementById("tarot-card-tags"),
    cardKeyword: document.getElementById("tarot-card-keyword"),
    catTabs: document.getElementById("tarot-cat-tabs"),
    readingTitle: document.getElementById("tarot-reading-title"),
    readingText: document.getElementById("tarot-reading-text"),
    todayText: document.getElementById("tarot-today-text"),
  };

  if (!els.tarotMain) return;

  /** @type {{ spreads: Record<string, {label:string,count:number}>, reading_categories: string[], back_image_url: string, deck_name: string } | null} */
  let meta = null;

  /** @type {string} */
  let activeSpread = "today";

  /** @type {string} */
  let activeCategory = "종합운";

  /** @type {Array<Record<string, unknown>>} */
  let drawnCards = [];

  /** @type {boolean[]} */
  let flipped = [];

  /** @type {number} */
  let activeCardIdx = 0;

  /** @type {boolean} */
  let autoRunning = false;

  function setStatus(msg, isError) {
    if (!els.status) return;
    els.status.textContent = msg || "";
    els.status.classList.toggle("error", !!isError);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function fetchJson(url) {
    const res = await fetch(url);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data.detail || data.message || res.statusText;
      throw new Error(typeof detail === "string" ? detail : "요청에 실패했습니다.");
    }
    return data;
  }

  function setAppMode(mode) {
    const isTarot = mode === "tarot";
    if (els.sajuMain) els.sajuMain.hidden = isTarot;
    if (els.tarotMain) els.tarotMain.hidden = !isTarot;
    document.body.classList.toggle("tarot-mode", isTarot);
    if (els.bottomNav) {
      if (isTarot) {
        els.bottomNav.dataset.sajuHidden = els.bottomNav.hidden ? "1" : "0";
        els.bottomNav.hidden = true;
        document.body.classList.remove("has-bottom-nav");
      } else {
        const wasVisible = els.bottomNav.dataset.sajuHidden === "0";
        const results = document.getElementById("results");
        const showNav = wasVisible || (results && !results.hidden);
        if (showNav && window.matchMedia("(max-width: 768px)").matches) {
          els.bottomNav.hidden = false;
          document.body.classList.add("has-bottom-nav");
        }
      }
    }
    els.modeBtns.forEach((btn) => {
      const on = btn.dataset.appMode === mode;
      btn.classList.toggle("active", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    if (isTarot && !meta) {
      initTarot();
    }
  }

  function renderSpreadTabs() {
    if (!meta || !els.spreadTabs) return;
    els.spreadTabs.innerHTML = SPREAD_ORDER.map((key) => {
      const info = meta.spreads[key];
      if (!info) return "";
      const active = key === activeSpread ? " active" : "";
      return `<button type="button" class="tab${active}" role="tab" data-spread="${key}" aria-selected="${key === activeSpread}">${escapeHtml(info.label)}</button>`;
    }).join("");

    els.spreadTabs.querySelectorAll("[data-spread]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (btn.dataset.spread === activeSpread || autoRunning) return;
        activeSpread = btn.dataset.spread;
        renderSpreadTabs();
        startDraw();
      });
    });
  }

  function renderCategoryTabs() {
    if (!meta || !els.catTabs) return;
    const cats = meta.reading_categories || [];
    els.catTabs.innerHTML = cats
      .map((cat) => {
        const active = cat === activeCategory ? " active" : "";
        return `<button type="button" class="tab${active}" role="tab" data-category="${escapeHtml(cat)}" aria-selected="${cat === activeCategory}">${escapeHtml(cat)}</button>`;
      })
      .join("");

    els.catTabs.querySelectorAll("[data-category]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const cat = btn.dataset.category;
        if (!cat || cat === activeCategory) return;
        activeCategory = cat;
        renderCategoryTabs();
        refreshReadingForActiveCard();
      });
    });
  }

  function showDrawPhase() {
    if (els.drawPhase) els.drawPhase.hidden = false;
    if (els.resultPhase) els.resultPhase.hidden = true;
  }

  function showResultPhase() {
    if (els.drawPhase) els.drawPhase.hidden = true;
    if (els.resultPhase) els.resultPhase.hidden = false;
  }

  function renderDeckLoading() {
    if (!els.deckArea) return;
    els.deckArea.dataset.count = "0";
    els.deckArea.classList.add("is-loading");
    els.deckArea.innerHTML = '<p class="tarot-deck-loading">카드를 섞는 중…</p>';
    if (els.autoDraw) els.autoDraw.disabled = true;
    if (els.redraw) els.redraw.disabled = true;
  }

  function renderDeck() {
    if (!els.deckArea || !meta) return;
    els.deckArea.classList.remove("is-loading");
    const backUrl = meta.back_image_url || "/static/tarot/back/back.png";
    const pickCount = drawnCards.length;
    const displayCount = pickCount === 1 ? 7 : pickCount;
    const pickedDisplay = els.deckArea.dataset.pickedDisplay;
    els.deckArea.dataset.count = String(displayCount);

    const slots = [];
    for (let i = 0; i < displayCount; i++) {
      if (pickCount === 1) {
        slots.push({ card: drawnCards[0], idx: 0, decoy: false });
      } else {
        slots.push({ card: drawnCards[i], idx: i, decoy: false });
      }
    }

    els.deckArea.innerHTML = slots
      .map((slot, displayIdx) => {
        const { card, idx } = slot;
        const showFlipped = pickCount === 1
          ? flipped[0] && String(displayIdx) === String(pickedDisplay ?? "")
          : flipped[idx];
        const revClass = card.is_reversed ? " card-reversed" : "";
        const flipClass = showFlipped ? " flipped" : "";
        const disabled = autoRunning || (pickCount === 1 && flipped[0] && String(displayIdx) !== String(pickedDisplay ?? "")) ? " is-disabled" : "";
        const label = pickCount > 1 ? `<span class="tarot-card-index">${idx + 1}</span>` : "";
        const frontImg = showFlipped
          ? `<img src="${escapeHtml(card.image_url)}" alt="${escapeHtml(card.name)}" class="${revClass.trim()}" />`
          : "";
        const fanOffset = displayCount > 1 ? ` style="--fan-i:${displayIdx};--fan-n:${displayCount}"` : "";
        return `<button type="button" class="tarot-card-slot${disabled}" data-idx="${idx}" data-display="${displayIdx}"${fanOffset} aria-label="카드${showFlipped ? " (뒤집힘)" : ""}">
          <div class="card-flip${flipClass}">
            <div class="card-face card-face-back">
              <img src="${escapeHtml(backUrl)}" alt="카드 뒷면" />
              ${label}
            </div>
            <div class="card-face card-face-front">${frontImg}</div>
          </div>
        </button>`;
      })
      .join("");

    els.deckArea.querySelectorAll(".tarot-card-slot").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = Number(btn.dataset.idx);
        const displayIdx = btn.dataset.display;
        if (Number.isNaN(idx) || autoRunning) return;
        if (pickCount === 1) {
          if (flipped[0]) return;
          if (els.deckArea) els.deckArea.dataset.pickedDisplay = displayIdx;
        } else if (flipped[idx]) {
          return;
        }
        flipCard(idx, true, displayIdx);
      });
    });

    const allFlipped = flipped.length && flipped.every(Boolean);
    if (els.autoDraw) els.autoDraw.disabled = autoRunning || allFlipped || !drawnCards.length;
    if (els.redraw) els.redraw.disabled = autoRunning || !drawnCards.length;
  }

  function flipCard(idx, goResult, displayIdx) {
    if (!drawnCards[idx] || (drawnCards.length > 1 && flipped[idx])) return;
    if (drawnCards.length === 1 && flipped[0]) return;

    const selector = displayIdx != null
      ? `.tarot-card-slot[data-display="${displayIdx}"] .card-flip`
      : `.tarot-card-slot[data-idx="${idx}"] .card-flip:not(.flipped)`;
    const flipEl = els.deckArea?.querySelector(selector);
    const slotEl = flipEl?.closest(".tarot-card-slot");
    if (flipEl) {
      flipEl.classList.add("is-flipping");
      const frontFace = flipEl.querySelector(".card-face-front");
      const card = drawnCards[idx];
      const revClass = card.is_reversed ? "card-reversed" : "";
      if (frontFace) {
        frontFace.innerHTML = `<img src="${escapeHtml(card.image_url)}" alt="${escapeHtml(card.name)}" class="${revClass}" />`;
      }
      requestAnimationFrame(() => {
        flipEl.classList.add("flipped");
        flipEl.classList.remove("is-flipping");
        if (slotEl) slotEl.setAttribute("aria-label", `카드 ${idx + 1} (뒤집힘)`);
      });
    }
    flipped[idx] = true;

    window.setTimeout(() => {
      if (goResult) {
        activeCardIdx = idx;
        openResult(idx);
      } else {
        renderDeck();
      }
    }, 600);
  }

  async function autoFlipAll() {
    if (autoRunning || !drawnCards.length) return;
    autoRunning = true;
    if (els.autoDraw) els.autoDraw.disabled = true;
    if (els.redraw) els.redraw.disabled = true;
    setStatus("카드를 자동으로 뽑는 중…");

    if (drawnCards.length === 1) {
      const centerDisplay = "3";
      if (els.deckArea) els.deckArea.dataset.pickedDisplay = centerDisplay;
      await new Promise((resolve) => {
        flipCard(0, false, centerDisplay);
        window.setTimeout(resolve, 650);
      });
      autoRunning = false;
      activeCardIdx = 0;
      openResult(0);
      return;
    }

    for (let i = 0; i < drawnCards.length; i++) {
      if (!flipped[i]) {
        await new Promise((resolve) => {
          flipCard(i, false);
          window.setTimeout(resolve, 650);
        });
      }
    }

    autoRunning = false;
    activeCardIdx = 0;
    openResult(0);
  }

  function renderResultNav() {
    if (!els.resultNav) return;
    if (drawnCards.length <= 1) {
      els.resultNav.hidden = true;
      els.resultNav.innerHTML = "";
      return;
    }
    els.resultNav.hidden = false;
    els.resultNav.innerHTML = drawnCards
      .map((card, idx) => {
        const active = idx === activeCardIdx ? " active" : "";
        const rev = card.is_reversed ? " card-reversed" : "";
        return `<button type="button" class="tarot-result-thumb${active}" data-idx="${idx}" aria-label="${escapeHtml(card.name)}">
          <img src="${escapeHtml(card.image_url)}" alt="" class="${rev.trim()}" />
        </button>`;
      })
      .join("");

    els.resultNav.querySelectorAll(".tarot-result-thumb").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = Number(btn.dataset.idx);
        if (Number.isNaN(idx)) return;
        activeCardIdx = idx;
        displayCardResult(drawnCards[idx], false);
        renderResultNav();
      });
    });
  }

  function displayCardResult(card, loadingReading) {
    if (!card) return;
    const backUrl = card.back_image_url || meta?.back_image_url || "/static/tarot/back/back.png";
    if (els.heroBack) els.heroBack.src = backUrl;
    if (els.heroFront) {
      els.heroFront.src = card.image_url;
      els.heroFront.alt = card.name || "";
      els.heroFront.classList.toggle("card-reversed", !!card.is_reversed);
    }
    if (els.orientation) {
      if (card.is_reversed) {
        els.orientation.hidden = false;
        els.orientation.textContent = "역방향 (Reversed)";
      } else {
        els.orientation.hidden = true;
        els.orientation.textContent = "";
      }
    }
    if (els.cardName) els.cardName.textContent = card.name || "";
    const tags = [card.element, card.category_kr].filter(Boolean).join(" · ");
    if (els.cardTags) els.cardTags.textContent = tags;
    if (els.cardKeyword) els.cardKeyword.textContent = card.keyword ? `「${card.keyword}」` : "";
    if (els.readingTitle) els.readingTitle.textContent = activeCategory;
    if (els.readingText) {
      els.readingText.textContent = loadingReading
        ? "해석을 불러오는 중…"
        : card.reading?.content || "";
    }
    if (els.todayText) els.todayText.textContent = card.today_message || "";
  }

  async function refreshReadingForActiveCard() {
    const card = drawnCards[activeCardIdx];
    if (!card) return;
    displayCardResult(card, true);
    setStatus("");
    try {
      const rev = card.is_reversed ? "true" : "false";
      const url = `/api/tarot/reading/${encodeURIComponent(card.card_id)}?category=${encodeURIComponent(activeCategory)}&reversed=${rev}`;
      const data = await fetchJson(url);
      const updated = data.card;
      drawnCards[activeCardIdx] = { ...card, ...updated, reading: updated.reading };
      displayCardResult(drawnCards[activeCardIdx], false);
    } catch (err) {
      setStatus(err.message || "해석을 불러오지 못했습니다.", true);
    }
  }

  function openResult(idx) {
    activeCardIdx = idx;
    showResultPhase();
    renderResultNav();
    displayCardResult(drawnCards[idx], false);
    renderCategoryTabs();
    setStatus("");
  }

  async function startDraw() {
    showDrawPhase();
    renderDeckLoading();
    setStatus("");
    flipped = [];
    drawnCards = [];
    activeCategory = "종합운";
    if (els.deckArea) delete els.deckArea.dataset.pickedDisplay;

    const spreadLabel = meta?.spreads?.[activeSpread]?.label || "타로";
    if (els.instruction) {
      els.instruction.textContent = `${spreadLabel} — 마음을 가다듬고 카드를 선택하거나 자동 뽑기를 눌러 주세요.`;
    }

    try {
      const url = `/api/tarot/draw/${encodeURIComponent(activeSpread)}?category=${encodeURIComponent(activeCategory)}`;
      const data = await fetchJson(url);
      drawnCards = data.cards || [];
      flipped = drawnCards.map(() => false);
      renderDeck();
      if (els.autoDraw) els.autoDraw.disabled = false;
      if (els.redraw) els.redraw.disabled = false;
    } catch (err) {
      if (els.deckArea) {
        els.deckArea.classList.remove("is-loading");
        els.deckArea.innerHTML = "";
      }
      setStatus(err.message || "카드를 뽑지 못했습니다.", true);
    }
  }

  async function initTarot() {
    setStatus("타로 덱을 불러오는 중…");
    try {
      meta = await fetchJson("/api/tarot/spreads");
      if (els.deckDesc) {
        els.deckDesc.textContent = `${meta.deck_name || "오행 타로"} · ${meta.card_count || 60}장`;
      }
      renderSpreadTabs();
      renderCategoryTabs();
      await startDraw();
      setStatus("");
    } catch (err) {
      setStatus(err.message || "타로 정보를 불러오지 못했습니다.", true);
    }
  }

  els.modeBtns.forEach((btn) => {
    btn.addEventListener("click", () => setAppMode(btn.dataset.appMode || "saju"));
  });

  if (els.autoDraw) {
    els.autoDraw.addEventListener("click", () => autoFlipAll());
  }
  if (els.redraw) {
    els.redraw.addEventListener("click", () => {
      if (autoRunning) return;
      startDraw();
    });
  }
  if (els.backDraw) {
    els.backDraw.addEventListener("click", () => {
      showDrawPhase();
      flipped = drawnCards.map(() => false);
      if (els.deckArea) delete els.deckArea.dataset.pickedDisplay;
      renderDeck();
      setStatus("");
    });
  }

  window.TarotApp = { setAppMode, initTarot };
})();
