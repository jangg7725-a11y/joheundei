(function () {
  "use strict";

  const SPREAD_ORDER = ["today", "week", "month", "year", "worry", "love", "deep"];
  const HOME_MENU = [
    {
      key: "today",
      icon: "🌙",
      subtitle: "하루를 비추는 별빛 한 장",
      featured: true,
      badge: "NEW",
    },
    { key: "week", icon: "⭐", subtitle: "이번 주 흐름 읽기" },
    { key: "month", icon: "🌕", subtitle: "달의 주기로 보는 운" },
    { key: "year", icon: "∞", subtitle: "한 해를 꿰뚫는 한 장" },
    { key: "worry", icon: "💭", subtitle: "답을 찾고 싶을 때" },
    { key: "love", icon: "💕", subtitle: "마음을 읽는 시간" },
  ];
  const FAN_SPREAD_DEG = 196;
  const DEAL_SHUFFLE_MS = 850;
  const DEAL_SPREAD_MS = 1400;

  const els = {
    sajuMain: document.getElementById("saju-main"),
    tarotMain: document.getElementById("tarot-main"),
    maehwaMain: document.getElementById("maehwa-main"),
    tarotSky: document.getElementById("tarot-sky"),
    bottomNav: document.getElementById("bottom-nav"),
    tarotHomeTop: document.getElementById("tarot-home-top-btn"),
    modeBtns: document.querySelectorAll("[data-app-mode]"),
    homePhase: document.getElementById("tarot-home-phase"),
    menuGrid: document.getElementById("tarot-menu-grid"),
    ctaDraw: document.getElementById("tarot-cta-draw"),
    drawSpreadLabel: document.getElementById("tarot-draw-spread-label"),
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

  const METEOR_COUNT = 9;
  const STAR_COUNT = 420;

  /** @type {{ ctx: CanvasRenderingContext2D | null, stars: Array<Record<string, number | boolean>>, rafId: number | null, drift: number, reduceMotion: boolean, width: number, height: number, dpr: number }} */
  const skyAnim = {
    ctx: null,
    stars: [],
    rafId: null,
    drift: 0,
    reduceMotion: false,
    width: 0,
    height: 0,
    dpr: 1,
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

  function buildSkyStars(count) {
    const stars = [];
    for (let i = 0; i < count; i++) {
      const isBright = Math.random() < 0.12;
      stars.push({
        x: Math.random(),
        y: Math.random(),
        size: isBright ? 2 + Math.random() * 2.8 : 0.7 + Math.random() * 1.8,
        phase: Math.random() * Math.PI * 2,
        speed: isBright ? 2.4 + Math.random() * 5.5 : 0.9 + Math.random() * 3.2,
        depth: 0.25 + Math.random() * 0.75,
        gold: Math.random() > 0.68,
        flash: Math.random() > 0.82,
      });
    }
    return stars;
  }

  function resizeTarotSkyCanvas() {
    const canvas = els.tarotSkyCanvas;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth;
    const h = window.innerHeight;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    skyAnim.width = w;
    skyAnim.height = h;
    skyAnim.dpr = dpr;
    const ctx = canvas.getContext("2d");
    if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    skyAnim.ctx = ctx;
  }

  function starBlink(star, t) {
    const waveA = Math.sin(t * star.speed + star.phase);
    const waveB = Math.sin(t * star.speed * 1.7 + star.phase * 2.1);
    let mix = (waveA * 0.55 + waveB * 0.45 + 1) * 0.5;
    if (star.flash) {
      const flashGate = Math.sin(t * star.speed * 3.4 + star.phase * 0.6);
      mix = flashGate > 0.82 ? 1 : mix * 0.35;
    }
    return Math.max(0, Math.min(1, mix));
  }

  function drawSkyStar(ctx, star, t) {
    const blink = starBlink(star, t);
    const minAlpha = star.size > 2.2 ? 0.06 : 0.02;
    const alpha = minAlpha + blink * (star.flash ? 0.98 : 0.92);
    if (alpha < 0.03) return;

    const driftX = skyAnim.drift * star.depth * 18;
    const driftY = skyAnim.drift * star.depth * 12;
    const x = ((star.x * skyAnim.width + driftX) % skyAnim.width + skyAnim.width) % skyAnim.width;
    const y = ((star.y * skyAnim.height + driftY) % skyAnim.height + skyAnim.height) % skyAnim.height;
    const r = star.size * (0.75 + blink * 0.55);
    const glow = star.gold ? `rgba(255, 228, 170, ${alpha})` : `rgba(230, 242, 255, ${alpha})`;

    ctx.save();
    ctx.shadowBlur = r * (star.gold ? 7 : 5);
    ctx.shadowColor = star.gold ? `rgba(255, 210, 130, ${alpha * 0.85})` : `rgba(190, 215, 255, ${alpha * 0.75})`;
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();

    if (blink > 0.45 && r > 1.4) {
      ctx.shadowBlur = 0;
      ctx.strokeStyle = glow;
      ctx.lineWidth = 0.6;
      const flare = r * (1.2 + blink * 2.8);
      ctx.beginPath();
      ctx.moveTo(x - flare, y);
      ctx.lineTo(x + flare, y);
      ctx.moveTo(x, y - flare);
      ctx.lineTo(x, y + flare);
      ctx.stroke();
    }
    ctx.restore();
  }

  function renderTarotSkyFrame(ts) {
    if (!skyAnim.ctx || !els.tarotSky || els.tarotSky.hidden) {
      skyAnim.rafId = null;
      return;
    }
    const t = ts * 0.001;
    skyAnim.drift += skyAnim.reduceMotion ? 0 : 0.012;
    skyAnim.ctx.clearRect(0, 0, skyAnim.width, skyAnim.height);
    skyAnim.stars.forEach((star) => drawSkyStar(skyAnim.ctx, star, t));
    skyAnim.rafId = window.requestAnimationFrame(renderTarotSkyFrame);
  }

  function startTarotSkyAnim() {
    if (skyAnim.rafId != null || !skyAnim.ctx) return;
    if (skyAnim.reduceMotion) {
      renderTarotSkyFrame(performance.now());
      return;
    }
    skyAnim.rafId = window.requestAnimationFrame(renderTarotSkyFrame);
  }

  function stopTarotSkyAnim() {
    if (skyAnim.rafId != null) {
      window.cancelAnimationFrame(skyAnim.rafId);
      skyAnim.rafId = null;
    }
  }

  function initTarotMeteors() {
    if (!els.tarotMeteors) return;
    els.tarotMeteors.innerHTML = "";
    for (let i = 0; i < METEOR_COUNT; i++) {
      const meteor = document.createElement("span");
      meteor.className = "tarot-meteor";
      if (Math.random() > 0.4) meteor.classList.add("tarot-meteor--gold");
      meteor.style.left = `${5 + Math.random() * 78}%`;
      meteor.style.top = `${-10 + Math.random() * 42}%`;
      meteor.style.animationDuration = `${5 + Math.random() * 10}s`;
      meteor.style.animationDelay = `${Math.random() * 12}s`;
      els.tarotMeteors.appendChild(meteor);
    }
  }

  function initTarotSky() {
    if (!els.tarotSky || els.tarotSky.dataset.ready === "1") return;
    stopTarotSkyAnim();
    els.tarotSky.dataset.ready = "1";
  }

  function setTarotSkyVisible(visible) {
    if (!els.tarotSky) return;
    els.tarotSky.hidden = !visible;
    els.tarotSky.setAttribute("aria-hidden", visible ? "false" : "true");
    if (!visible) stopTarotSkyAnim();
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

  function renderNarrativeSections(sections) {
    if (!els.readingText) return;
    if (!sections?.length) {
      renderNarrativeText("");
      return;
    }
    els.readingText.innerHTML = sections
      .map((block) => {
        const typeClass = `tarot-narrative-${block.type || "scene"}`;
        const title = block.title
          ? `<h5 class="tarot-narrative-title ${typeClass}">${escapeHtml(block.title)}</h5>`
          : "";
        const text = String(block.text || "")
          .split("\n")
          .filter(Boolean)
          .map((line) => `<p>${escapeHtml(line)}</p>`)
          .join("");
        return `<section class="tarot-narrative-block ${typeClass}">${title}${text}</section>`;
      })
      .join("");
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
    els.spreadCards.dataset.spread = activeSpread;
    els.spreadCards.dataset.count = String(positions.length);
    els.spreadCards.innerHTML = positions
      .map((pos, idx) => {
        const rev = pos.is_reversed ? " card-reversed" : "";
        const orient = pos.is_reversed ? " · 역방향" : "";
        const summary = pos.scene_summary
          ? `<p class="tarot-spread-card-summary">${escapeHtml(pos.scene_summary)}</p>`
          : "";
        const quarterBreak =
          activeSpread === "year" && idx > 0 && idx % 3 === 0
            ? '<span class="tarot-spread-quarter" aria-hidden="true"></span>'
            : "";
        return `${quarterBreak}<figure class="tarot-spread-card">
          <span class="tarot-spread-card-order">${idx + 1}</span>
          <div class="tarot-spread-card-img">
            <img src="${escapeHtml(pos.image_url)}" alt="${escapeHtml(pos.name)}" class="${rev.trim()}" />
          </div>
          <figcaption>
            <strong>${escapeHtml(pos.position_label)}</strong>
            <span>${escapeHtml(pos.position_role)}</span>
            <em>${escapeHtml(pos.name)}${orient}</em>
            ${summary}
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

  function showHomePhase() {
    if (els.homePhase) els.homePhase.hidden = false;
    if (els.drawPhase) els.drawPhase.hidden = true;
    if (els.resultPhase) els.resultPhase.hidden = true;
  }

  function updateDrawSpreadLabel() {
    if (els.drawSpreadLabel) {
      els.drawSpreadLabel.textContent = spreadLabel();
    }
  }

  function openDrawForSpread(spreadKey) {
    if (spreadKey && meta?.spreads?.[spreadKey]) {
      activeSpread = spreadKey;
      renderSpreadTabs();
    }
    showDrawPhase();
    updateDrawSpreadLabel();
    if (!deckOrder.length && meta) {
      resetDeckSelection();
    } else if (deckOrder.length) {
      updateInstruction();
    }
  }

  function renderHomeMenu() {
    if (!els.menuGrid || !meta) return;
    els.menuGrid.innerHTML = HOME_MENU.map((item) => {
      const info = meta.spreads[item.key];
      if (!info) return "";
      const featured = item.featured ? " tarot-menu-card--featured" : "";
      const badge = item.badge
        ? `<span class="tarot-menu-badge">${escapeHtml(item.badge)}</span>`
        : "";
      return `<button type="button" class="tarot-menu-card${featured}" data-spread="${escapeHtml(item.key)}" role="listitem">
        <span class="tarot-menu-icon" aria-hidden="true">${item.icon}</span>
        <span class="tarot-menu-text">
          <span class="tarot-menu-title-row">
            <span class="tarot-menu-title">${escapeHtml(info.label)}</span>
            ${badge}
          </span>
          <span class="tarot-menu-sub">${escapeHtml(item.subtitle)}</span>
        </span>
      </button>`;
    }).join("");

    els.menuGrid.querySelectorAll("[data-spread]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (pickingLocked || dealing || randomRunning) return;
        openDrawForSpread(btn.dataset.spread);
      });
    });
  }

  function setAppMode(mode) {
    const isTarot = mode === "tarot";
    const isMaehwa = mode === "maehwa";
    if (isTarot) initTarotSky();
    setTarotSkyVisible(isTarot);
    if (els.sajuMain) els.sajuMain.hidden = isTarot || isMaehwa;
    if (els.tarotMain) els.tarotMain.hidden = !isTarot;
    if (els.maehwaMain) els.maehwaMain.hidden = !isMaehwa;
    document.body.classList.toggle("tarot-mode", isTarot);
    document.body.classList.toggle("maehwa-mode", isMaehwa);
    if (els.bottomNav) {
      if (isTarot || isMaehwa) {
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
    if (els.tarotHomeTop) {
      els.tarotHomeTop.hidden = !isTarot;
    }
    els.modeBtns.forEach((btn) => {
      const on = btn.dataset.appMode === mode;
      btn.classList.toggle("active", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    if (isTarot) {
      showHomePhase();
    }
    if (isTarot && !meta) {
      initTarot();
    }
    if (isMaehwa && window.MaehwaApp && typeof window.MaehwaApp.init === "function") {
      window.MaehwaApp.init();
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
        showDrawPhase();
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
    if (els.homePhase) els.homePhase.hidden = true;
    if (els.drawPhase) els.drawPhase.hidden = false;
    if (els.resultPhase) els.resultPhase.hidden = true;
    updateDrawSpreadLabel();
  }

  function showResultPhase() {
    if (els.homePhase) els.homePhase.hidden = true;
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
      if (data.narrative_sections?.length) {
        const displaySections = data.narrative_sections.filter((s) => s.type !== "closing");
        renderNarrativeSections(displaySections);
      } else {
        renderNarrativeText(data.narrative || "");
      }
      if (els.spreadClosingText) {
        els.spreadClosingText.textContent = data.closing || "";
      }
      if (els.spreadClosing) {
        els.spreadClosing.hidden = !(data.closing || "").trim();
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
      renderHomeMenu();
      renderSpreadTabs();
      renderCategoryTabs();
      showHomePhase();
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

  if (els.ctaDraw) {
    els.ctaDraw.addEventListener("click", () => {
      if (pickingLocked || dealing || randomRunning) return;
      openDrawForSpread(activeSpread || "today");
    });
  }

  if (els.tarotHomeTop) {
    els.tarotHomeTop.addEventListener("click", () => {
      if (pickingLocked || dealing || randomRunning) return;
      showHomePhase();
    });
  }

  if (els.shuffle) {
    els.shuffle.addEventListener("click", () => shuffleDeck());
  }
  if (els.randomPick) {
    els.randomPick.addEventListener("click", () => randomPickCards());
  }
  if (els.redraw) {
    els.redraw.addEventListener("click", () => {
      if (pickingLocked || dealing || randomRunning) return;
      showDrawPhase();
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
      showDrawPhase();
      resetDeckSelection();
    });
  }

  window.TarotApp = { setAppMode, initTarot };
})();
