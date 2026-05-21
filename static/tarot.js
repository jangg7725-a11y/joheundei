(function () {
  "use strict";

  const SPREAD_ORDER = ["today", "week", "month", "year", "worry", "love", "deep"];
  const FAN_SPREAD_DEG = 196;
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
    instruction: document.getElementById("tarot-instruction"),
    deckArea: document.getElementById("tarot-deck-area"),
    drawPhase: document.getElementById("tarot-draw-phase"),
    resultPhase: document.getElementById("tarot-result-phase"),
    redraw: document.getElementById("tarot-redraw"),
    shuffle: document.getElementById("tarot-shuffle"),
    randomPick: document.getElementById("tarot-random-pick"),
    viewReading: document.getElementById("tarot-view-reading"),
    backDraw: document.getElementById("tarot-back-draw"),
    status: document.getElementById("tarot-status"),
    spreadHead: document.getElementById("tarot-result-spread-head"),
    spreadTitle: document.getElementById("tarot-result-spread-title"),
    spreadCards: document.getElementById("tarot-spread-cards"),
    singleResult: document.getElementById("tarot-single-result"),
    spreadClosing: document.getElementById("tarot-spread-closing"),
    spreadClosingText: document.getElementById("tarot-spread-closing-text"),
    today: document.getElementById("tarot-today"),
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
  let pickingLocked = false;

  /** @type {boolean} */
  let dealing = false;

  /** @type {boolean} */
  let randomRunning = false;

  const RANDOM_PICK_DELAY_MS = 520;

  const STAR_LAYERS = {
    far: { count: 180, size: 1, spread: 2800, opacity: [0.3, 0.62] },
    mid: { count: 110, size: 1.6, spread: 2800, opacity: [0.45, 0.82] },
    near: { count: 55, size: 2.2, spread: 2800, opacity: [0.6, 1] },
  };

  function delay(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  function waitForDeckReady() {
    return new Promise((resolve) => {
      const check = () => {
        if (!dealing) {
          resolve();
          return;
        }
        window.setTimeout(check, 80);
      };
      check();
    });
  }

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
      const twinkleCount = 48;
      els.tarotTwinkles.innerHTML = "";
      for (let i = 0; i < twinkleCount; i++) {
        const star = document.createElement("span");
        star.className = "tarot-twinkle";
        const size = 1.5 + Math.random() * 3.2;
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        star.style.animationDuration = `${1.6 + Math.random() * 3.2}s`;
        star.style.animationDelay = `${Math.random() * 6}s`;
        if (Math.random() > 0.55) star.classList.add("tarot-twinkle--gold");
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

  function isMultiSpread() {
    return needCount() > 1;
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

  async function fetchSpreadReading() {
    const res = await fetch("/api/tarot/spread-reading", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        spread: activeSpread,
        category: activeCategory,
        cards: selectedCards.map((c) => ({
          card_id: c.card_id,
          is_reversed: !!c.is_reversed,
        })),
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data.detail || data.message || res.statusText;
      throw new Error(typeof detail === "string" ? detail : "스프레드 해석을 불러오지 못했습니다.");
    }
    return data;
  }

  function renderNarrativeText(text) {
    if (!els.readingText) return;
    const value = String(text || "").trim();
    if (!value) {
      els.readingText.innerHTML = "";
      return;
    }
    els.readingText.innerHTML = value
      .split("\n\n")
      .map((para) => `<p>${escapeHtml(para)}</p>`)
      .join("");
  }

  function setResultLayout(isMulti) {
    if (els.spreadHead) els.spreadHead.hidden = !isMulti;
    if (els.spreadCards) els.spreadCards.hidden = !isMulti;
    if (els.singleResult) els.singleResult.hidden = isMulti;
    if (els.spreadClosing) els.spreadClosing.hidden = !isMulti;
    if (els.today) els.today.hidden = isMulti;
  }

  function renderSpreadCards(positions) {
    if (!els.spreadCards || !positions?.length) return;
    els.spreadCards.innerHTML = positions
      .map((pos, idx) => {
        const rev = pos.is_reversed ? " card-reversed" : "";
        const orient = pos.is_reversed ? " · 역방향" : "";
        return `<figure class="tarot-spread-card">
          <span class="tarot-spread-card-order">${idx + 1}</span>
          <div class="tarot-spread-card-img">
            <img src="${escapeHtml(pos.image_url)}" alt="${escapeHtml(pos.name)}" class="${rev.trim()}" />
          </div>
          <figcaption>
            <strong>${escapeHtml(pos.position_label)}</strong>
            <span>${escapeHtml(pos.position_role)}</span>
            <em>${escapeHtml(pos.name)}${orient}</em>
          </figcaption>
        </figure>`;
      })
      .join("");
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
      els.instruction.textContent = `${label} — 선택 완료. 「해석 보기」를 눌러 주세요.`;
      return;
    }
    els.instruction.textContent = `${label} — 60장 중 ${need}장을 직접 골라 주세요 (${picked}/${need})`;
  }

  function syncCardInteractivity() {
    if (!els.deckArea) return;
    const selectionDone = selectedCards.length >= needCount();
    els.deckArea.querySelectorAll(".tarot-card-slot").forEach((btn) => {
      const cardId = btn.dataset.cardId;
      const isPicked = cardId ? pickedIds.has(cardId) : false;
      const shouldDisable = pickingLocked || dealing || randomRunning || (selectionDone && !isPicked);
      btn.classList.toggle("is-disabled", shouldDisable);
    });
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
        if (btn.dataset.spread === activeSpread || pickingLocked || dealing || randomRunning) return;
        activeSpread = btn.dataset.spread;
        renderSpreadTabs();
        updateInstruction();
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
        if (isMultiSpread() && !els.resultPhase?.hidden) {
          refreshSpreadReading(true);
        } else {
          refreshReadingForActiveCard();
        }
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
    if (els.redraw) els.redraw.disabled = true;
    if (els.shuffle) els.shuffle.disabled = true;
    if (els.randomPick) els.randomPick.disabled = true;
  }

  function renderFanDeck() {
    if (!els.deckArea || !meta || !deckOrder.length) return;
    const selectionDone = selectedCards.length >= needCount();
    const isInitialDeal = selectedCards.length === 0;
    dealing = isInitialDeal;
    els.deckArea.className = `tarot-deck-area tarot-deck-fan${isInitialDeal ? " is-dealing" : ""}`;
    els.deckArea.dataset.pickCount = String(needCount());
    const backUrl = meta.back_image_url || "/static/tarot/back/back.png";
    const total = deckOrder.length;

    els.deckArea.innerHTML = deckOrder
      .map((card, i) => {
        const id = card.id;
        const revealed = revealedById.get(id);
        const isPicked = pickedIds.has(id);
        const flipClass = revealed ? " flipped" : "";
        const pickedClass = isPicked ? " is-picked" : "";
        const doneClass = isPicked && selectionDone ? " is-complete" : "";
        const disabled = selectionDone && !isPicked ? " is-disabled" : "";
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

    if (isInitialDeal) {
      window.setTimeout(() => {
        if (!els.deckArea) return;
        els.deckArea.classList.remove("is-dealing");
        els.deckArea.classList.add("is-spreading");
        window.setTimeout(() => {
          if (els.deckArea) els.deckArea.classList.remove("is-spreading");
          dealing = false;
          syncCardInteractivity();
          updateDrawButtons(selectedCards.length >= needCount());
          updateInstruction();
        }, DEAL_SPREAD_MS);
      }, DEAL_SHUFFLE_MS);
    } else {
      dealing = false;
      els.deckArea.classList.remove("is-dealing", "is-spreading");
      syncCardInteractivity();
      updateDrawButtons(selectionDone);
    }
  }

  function updateDrawButtons(selectionDone) {
    const locked = pickingLocked || dealing || randomRunning || !deckOrder.length;
    if (els.shuffle) els.shuffle.disabled = locked;
    if (els.randomPick) els.randomPick.disabled = locked || selectionDone;
    if (els.redraw) els.redraw.disabled = locked;
    if (els.viewReading) {
      els.viewReading.disabled = locked || !selectionDone;
      els.viewReading.hidden = selectedCards.length === 0;
    }
  }

  function clearSelection() {
    selectedCards = [];
    pickedIds.clear();
    revealedById.clear();
  }

  function shuffleDeck() {
    if (pickingLocked || dealing || randomRunning || !deckOrder.length) return;
    clearSelection();
    deckOrder = shuffle(deckOrder);
    setStatus("");
    renderFanDeck();
  }

  async function randomPickCards() {
    if (randomRunning || pickingLocked || dealing || !deckOrder.length) return;
    if (selectedCards.length >= needCount()) return;

    const need = needCount();
    randomRunning = true;
    pickingLocked = true;
    setStatus("");
    updateDrawButtons(false);

    try {
      clearSelection();
      renderFanDeck();
      await waitForDeckReady();

      const picks = shuffle(deckOrder.map((c) => c.id)).slice(0, need);

      for (let i = 0; i < picks.length; i++) {
        if (els.instruction) {
          els.instruction.textContent = `${spreadLabel()} — 무작위로 ${need}장 뽑는 중… (${i + 1}/${need})`;
        }

        const cardId = picks[i];
        const url = `/api/tarot/reveal/${encodeURIComponent(cardId)}?category=${encodeURIComponent(activeCategory)}`;
        const data = await fetchJson(url);
        const card = data.card;
        pickedIds.add(cardId);
        revealedById.set(cardId, card);
        selectedCards.push(card);

        if (!els.deckArea?.querySelector(`.tarot-card-slot[data-card-id="${cardId}"]`)) {
          renderFanDeck();
          await waitForDeckReady();
        }

        animateFlip(cardId, card);
        await delay(RANDOM_PICK_DELAY_MS);
      }

      renderFanDeck();
    } catch (err) {
      setStatus(err.message || "카드를 무작위로 뽑지 못했습니다.", true);
      renderFanDeck();
    } finally {
      randomRunning = false;
      pickingLocked = false;
      syncCardInteractivity();
      updateDrawButtons(selectedCards.length >= needCount());
      updateInstruction();
    }
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
      pickingLocked ||
      dealing ||
      randomRunning ||
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
      renderFanDeck();
    } catch (err) {
      setStatus(err.message || "카드를 열지 못했습니다.", true);
    } finally {
      pickingLocked = false;
      syncCardInteractivity();
      updateDrawButtons(selectedCards.length >= needCount());
      updateInstruction();
    }
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
    if (loadingReading) {
      renderNarrativeText("해석을 불러오는 중…");
    } else {
      renderNarrativeText(card.reading?.content || "");
    }
    if (els.todayText) els.todayText.textContent = card.today_message || "";
  }

  async function refreshSpreadReading(showLoading) {
    if (!isMultiSpread() || !selectedCards.length) return;
    if (els.readingTitle) els.readingTitle.textContent = activeCategory;
    if (showLoading) renderNarrativeText("해석을 불러오는 중…");
    setStatus("");
    try {
      const data = await fetchSpreadReading();
      if (els.spreadTitle) els.spreadTitle.textContent = data.spread_label || spreadLabel();
      renderSpreadCards(data.positions || []);
      renderNarrativeText(data.narrative || "");
      if (els.spreadClosingText) {
        els.spreadClosingText.textContent = data.closing || "";
      }
    } catch (err) {
      setStatus(err.message || "스프레드 해석을 불러오지 못했습니다.", true);
    }
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

  async function openResult() {
    showResultPhase();
    renderCategoryTabs();
    setStatus("");

    if (isMultiSpread()) {
      setResultLayout(true);
      if (els.spreadTitle) els.spreadTitle.textContent = spreadLabel();
      await refreshSpreadReading(true);
      return;
    }

    setResultLayout(false);
    activeCardIdx = 0;
    displayCardResult(selectedCards[0], false);
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

  if (els.shuffle) {
    els.shuffle.addEventListener("click", () => shuffleDeck());
  }
  if (els.randomPick) {
    els.randomPick.addEventListener("click", () => randomPickCards());
  }
  if (els.redraw) {
    els.redraw.addEventListener("click", () => {
      if (pickingLocked || dealing || randomRunning) return;
      resetDeckSelection();
    });
  }
  if (els.viewReading) {
    els.viewReading.addEventListener("click", () => {
      if (selectedCards.length < needCount() || pickingLocked || dealing || randomRunning) return;
      openResult();
    });
  }
  if (els.backDraw) {
    els.backDraw.addEventListener("click", () => {
      resetDeckSelection();
    });
  }

  window.TarotApp = { setAppMode, initTarot };
})();
