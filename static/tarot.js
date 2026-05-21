(function () {
  "use strict";

  const SPREAD_ORDER = ["today", "week", "month", "year", "worry", "love", "deep"];
  const FAN_SPREAD_DEG = 178;
  const DEAL_SHUFFLE_MS = 850;
  const DEAL_SPREAD_MS = 1400;

  const els = {
    sajuMain: document.getElementById("saju-main"),
    tarotMain: document.getElementById("tarot-main"),
    tarotSky: document.getElementById("tarot-sky"),
    tarotTwinkles: document.getElementById("tarot-sky-twinkles"),
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

  /** @type {{ spreads: Record<string, {label:string,count:number}>, reading_categories: string[], back_image_url: string, deck_name: string, card_count: number } | null} */
  let meta = null;

  /** @type {Array<{ id: string, image_url?: string, name?: string }>} */
  let deckOrder = [];

  /** @type {string} */
  let activeSpread = "today";

  /** @type {string} */
  let activeCategory = "종합운";

  /** @type {Array<Record<string, unknown>>} */
  let selectedCards = [];

  /** @type {Set<string>} */
  const pickedIds = new Set();

  /** @type {Map<string, Record<string, unknown>>} */
  const revealedById = new Map();

  /** @type {number} */
  let activeCardIdx = 0;

  /** @type {boolean} */
  let autoRunning = false;

  /** @type {boolean} */
  let pickingLocked = false;

  /** @type {boolean} */
  let dealing = false;

  const STAR_LAYERS = {
    far: { count: 140, size: 1, spread: 2400, opacity: [0.25, 0.55] },
    mid: { count: 85, size: 1.6, spread: 2400, opacity: [0.4, 0.75] },
    near: { count: 42, size: 2.2, spread: 2400, opacity: [0.55, 0.95] },
  };

  function buildStarShadows(count, spread, size, opacityRange) {
    const parts = [];
    for (let i = 0; i < count; i++) {
      const x = Math.random() * spread;
      const y = Math.random() * spread;
      const alpha = opacityRange[0] + Math.random() * (opacityRange[1] - opacityRange[0]);
      const s = size * (0.7 + Math.random() * 0.6);
      parts.push(`${x}px ${y}px 0 ${s}px rgba(236, 242, 255, ${alpha.toFixed(3)})`);
    }
    return parts.join(", ");
  }

  function initTarotSky() {
    if (!els.tarotSky || els.tarotSky.dataset.ready === "1") return;

    Object.entries(STAR_LAYERS).forEach(([key, cfg]) => {
      const track = els.tarotSky.querySelector(`[data-stars="${key}"]`);
      if (!track) return;
      track.innerHTML = "";
      for (let layer = 0; layer < 2; layer++) {
        const el = document.createElement("div");
        el.className = "tarot-stars-layer";
        el.style.width = `${cfg.size}px`;
        el.style.height = `${cfg.size}px`;
        el.style.boxShadow = buildStarShadows(cfg.count, cfg.spread, cfg.size, cfg.opacity);
        track.appendChild(el);
      }
    });

    if (els.tarotTwinkles) {
      const twinkleCount = 22;
      els.tarotTwinkles.innerHTML = "";
      for (let i = 0; i < twinkleCount; i++) {
        const star = document.createElement("span");
        star.className = "tarot-twinkle";
        const size = 2 + Math.random() * 2.5;
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        star.style.animationDuration = `${2.2 + Math.random() * 3.8}s`;
        star.style.animationDelay = `${Math.random() * 5}s`;
        els.tarotTwinkles.appendChild(star);
      }
    }

    els.tarotSky.dataset.ready = "1";
  }

  function setTarotSkyVisible(visible) {
    if (!els.tarotSky) return;
    els.tarotSky.hidden = !visible;
    els.tarotSky.setAttribute("aria-hidden", visible ? "false" : "true");
  }

  function needCount() {
    return meta?.spreads?.[activeSpread]?.count ?? 1;
  }

  function spreadLabel() {
    return meta?.spreads?.[activeSpread]?.label || "타로";
  }

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

  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function fanAngle(index, total) {
    if (total <= 1) return 0;
    const mid = (total - 1) / 2;
    return ((index - mid) / mid) * (FAN_SPREAD_DEG / 2);
  }

  function updateInstruction() {
    if (!els.instruction) return;
    const need = needCount();
    const picked = selectedCards.length;
    const label = spreadLabel();
    if (picked >= need) {
      els.instruction.textContent = `${label} — 선택 완료. 해석을 확인해 주세요.`;
      return;
    }
    els.instruction.textContent = `${label} — 60장 중 ${need}장을 직접 골라 주세요 (${picked}/${need})`;
  }

  function setAppMode(mode) {
    const isTarot = mode === "tarot";
    if (isTarot) initTarotSky();
    setTarotSkyVisible(isTarot);
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
        if (btn.dataset.spread === activeSpread || autoRunning || pickingLocked || dealing) return;
        activeSpread = btn.dataset.spread;
        renderSpreadTabs();
        resetDeckSelection();
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
    els.deckArea.className = "tarot-deck-area is-loading";
    els.deckArea.innerHTML = '<p class="tarot-deck-loading">60장을 모아 섞는 중…</p>';
    if (els.autoDraw) els.autoDraw.disabled = true;
    if (els.redraw) els.redraw.disabled = true;
  }

  function renderFanDeck() {
    if (!els.deckArea || !meta || !deckOrder.length) return;
    dealing = true;
    els.deckArea.className = "tarot-deck-area tarot-deck-fan is-dealing";
    const backUrl = meta.back_image_url || "/static/tarot/back/back.png";
    const total = deckOrder.length;
    const selectionDone = selectedCards.length >= needCount();

    els.deckArea.innerHTML = deckOrder
      .map((card, i) => {
        const id = card.id;
        const revealed = revealedById.get(id);
        const isPicked = pickedIds.has(id);
        const flipClass = revealed ? " flipped" : "";
        const pickedClass = isPicked ? " is-picked" : "";
        const doneClass = isPicked && selectionDone ? " is-complete" : "";
        const disabled = autoRunning || pickingLocked || dealing || (selectionDone && !isPicked) ? " is-disabled" : "";
        const angle = fanAngle(i, total).toFixed(2);
        const shuffleR = ((i % 13) - 6) * 2.8;
        const revClass = revealed?.is_reversed ? " card-reversed" : "";
        const frontImg = revealed
          ? `<img src="${escapeHtml(revealed.image_url)}" alt="${escapeHtml(revealed.name || "")}" class="${revClass.trim()}" />`
          : "";
        const pickOrder = isPicked ? selectedCards.findIndex((c) => c.card_id === id) + 1 : 0;
        const label = pickOrder > 0 && needCount() > 1 ? `<span class="tarot-card-index">${pickOrder}</span>` : "";
        return `<button type="button" class="tarot-card-slot${pickedClass}${doneClass}${disabled}" data-card-id="${escapeHtml(id)}" style="--fan-i:${i};--fan-angle:${angle}deg;--shuffle-r:${shuffleR.toFixed(2)}deg" aria-label="타로 카드${isPicked ? ` ${pickOrder}번 선택` : ""}">
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
        const cardId = btn.dataset.cardId;
        if (!cardId) return;
        onPickCard(cardId);
      });
    });

    updateInstruction();
    updateDrawButtons(selectionDone);

    if (selectedCards.length === 0) {
      window.setTimeout(() => {
        if (!els.deckArea) return;
        els.deckArea.classList.remove("is-dealing");
        els.deckArea.classList.add("is-spreading");
        window.setTimeout(() => {
          if (els.deckArea) els.deckArea.classList.remove("is-spreading");
          dealing = false;
          updateDrawButtons(selectedCards.length >= needCount());
        }, DEAL_SPREAD_MS);
      }, DEAL_SHUFFLE_MS);
    } else {
      dealing = false;
      els.deckArea.classList.remove("is-dealing");
    }
  }

  function updateDrawButtons(selectionDone) {
    const locked = autoRunning || pickingLocked || dealing || !deckOrder.length;
    if (els.autoDraw) els.autoDraw.disabled = locked || selectionDone;
    if (els.redraw) els.redraw.disabled = locked;
  }

  function animateFlip(cardId, cardData) {
    const slot = els.deckArea?.querySelector(`.tarot-card-slot[data-card-id="${cardId}"]`);
    const flipEl = slot?.querySelector(".card-flip");
    if (!flipEl) return;
    flipEl.classList.add("is-flipping");
    const frontFace = flipEl.querySelector(".card-face-front");
    const revClass = cardData.is_reversed ? "card-reversed" : "";
    if (frontFace) {
      frontFace.innerHTML = `<img src="${escapeHtml(cardData.image_url)}" alt="${escapeHtml(cardData.name || "")}" class="${revClass}" />`;
    }
    requestAnimationFrame(() => {
      flipEl.classList.add("flipped");
      flipEl.classList.remove("is-flipping");
      if (slot) slot.classList.add("is-picked");
    });
  }

  async function onPickCard(cardId) {
    if (
      autoRunning ||
      pickingLocked ||
      dealing ||
      pickedIds.has(cardId) ||
      selectedCards.length >= needCount()
    ) {
      return;
    }

    pickingLocked = true;
    setStatus("");

    try {
      const url = `/api/tarot/reveal/${encodeURIComponent(cardId)}?category=${encodeURIComponent(activeCategory)}`;
      const data = await fetchJson(url);
      const card = data.card;
      pickedIds.add(cardId);
      revealedById.set(cardId, card);
      selectedCards.push(card);
      animateFlip(cardId, card);

      await new Promise((resolve) => window.setTimeout(resolve, 620));

      if (selectedCards.length >= needCount()) {
        activeCardIdx = 0;
        openResult(0);
      } else {
        renderFanDeck();
      }
    } catch (err) {
      setStatus(err.message || "카드를 열지 못했습니다.", true);
    } finally {
      pickingLocked = false;
    }
  }

  async function autoPickCards() {
    if (autoRunning || !deckOrder.length) return;
    const need = needCount();
    const remaining = need - selectedCards.length;
    if (remaining <= 0) return;

    autoRunning = true;
    if (els.autoDraw) els.autoDraw.disabled = true;
    if (els.redraw) els.redraw.disabled = true;
    setStatus("마음에 닿는 카드를 자동으로 고르는 중…");

    const pool = deckOrder.map((c) => c.id).filter((id) => !pickedIds.has(id));
    const picks = shuffle(pool).slice(0, remaining);

    for (const cardId of picks) {
      await onPickCard(cardId);
      if (selectedCards.length >= need) break;
      await new Promise((resolve) => window.setTimeout(resolve, 280));
    }

    autoRunning = false;
    setStatus("");
  }

  function renderResultNav() {
    if (!els.resultNav) return;
    if (selectedCards.length <= 1) {
      els.resultNav.hidden = true;
      els.resultNav.innerHTML = "";
      return;
    }
    els.resultNav.hidden = false;
    els.resultNav.innerHTML = selectedCards
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
        displayCardResult(selectedCards[idx], false);
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
    const card = selectedCards[activeCardIdx];
    if (!card) return;
    displayCardResult(card, true);
    setStatus("");
    try {
      const rev = card.is_reversed ? "true" : "false";
      const url = `/api/tarot/reading/${encodeURIComponent(card.card_id)}?category=${encodeURIComponent(activeCategory)}&reversed=${rev}`;
      const data = await fetchJson(url);
      const updated = data.card;
      selectedCards[activeCardIdx] = { ...card, ...updated, reading: updated.reading };
      displayCardResult(selectedCards[activeCardIdx], false);
    } catch (err) {
      setStatus(err.message || "해석을 불러오지 못했습니다.", true);
    }
  }

  function openResult(idx) {
    activeCardIdx = idx;
    showResultPhase();
    renderResultNav();
    displayCardResult(selectedCards[idx], false);
    renderCategoryTabs();
    setStatus("");
  }

  function resetDeckSelection() {
    showDrawPhase();
    setStatus("");
    selectedCards = [];
    pickedIds.clear();
    revealedById.clear();
    activeCategory = "종합운";
    deckOrder = shuffle(deckOrder.length ? deckOrder : []);
    renderFanDeck();
  }

  async function initTarot() {
    renderDeckLoading();
    setStatus("타로 덱을 불러오는 중…");
    try {
      const [spreadMeta, deckData] = await Promise.all([
        fetchJson("/api/tarot/spreads"),
        fetchJson("/data/tarot_cards.json"),
      ]);
      meta = spreadMeta;
      deckOrder = shuffle((deckData.cards || []).map((c) => ({ id: c.id })));
      if (els.deckDesc) {
        els.deckDesc.textContent = `${meta.deck_name || "오행 타로"} · ${meta.card_count || deckOrder.length}장`;
      }
      renderSpreadTabs();
      renderCategoryTabs();
      resetDeckSelection();
      setStatus("");
    } catch (err) {
      if (els.deckArea) {
        els.deckArea.className = "tarot-deck-area is-loading";
        els.deckArea.innerHTML = "";
      }
      setStatus(err.message || "타로 정보를 불러오지 못했습니다.", true);
    }
  }

  els.modeBtns.forEach((btn) => {
    btn.addEventListener("click", () => setAppMode(btn.dataset.appMode || "saju"));
  });

  if (els.autoDraw) {
    els.autoDraw.addEventListener("click", () => autoPickCards());
  }
  if (els.redraw) {
    els.redraw.addEventListener("click", () => {
      if (autoRunning || pickingLocked || dealing) return;
      resetDeckSelection();
    });
  }
  if (els.backDraw) {
    els.backDraw.addEventListener("click", () => {
      resetDeckSelection();
    });
  }

  window.TarotApp = { setAppMode, initTarot };
})();
