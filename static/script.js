(function () {
  const form = document.getElementById("saju-form");
  const statusEl = document.getElementById("status");
  const results = document.getElementById("results");
  const resultsSub = document.getElementById("results-sub");
  const leapBlock = document.getElementById("leap-block");
  const calendarInput = document.getElementById("calendar");
  const lunarLeapCheck = document.getElementById("lunar_leap");

  const PILLAR_KEYS = ["year", "month", "day", "hour"];
  /** 원국 카드: 시→일→월→년 (좌→우). */
  const PILLAR_KEYS_WONGUK_ORDER = ["hour", "day", "month", "year"];
  /** 표·지장간 등 세로 나열: 년→월→일→시 (위→아래). */
  const PILLAR_KEYS_COL_ORDER = ["year", "month", "day", "hour"];
  const LABELS = {
    year: "年柱 · 년주",
    month: "月柱 · 월주",
    day: "日柱 · 일주",
    hour: "時柱 · 시주",
  };

  /* ── 오행 색상 코딩 ── */
  const STEM_OH = {
    甲:"목",乙:"목",丙:"화",丁:"화",戊:"토",己:"토",庚:"금",辛:"금",壬:"수",癸:"수"
  };
  const BRANCH_OH = {
    子:"수",丑:"토",寅:"목",卯:"목",辰:"토",巳:"화",午:"화",未:"토",申:"금",酉:"금",戌:"토",亥:"수"
  };
  function ohClass(char) {
    const e = STEM_OH[char] || BRANCH_OH[char] || "";
    return e ? "oh-" + e : "";
  }
  /* 한자 텍스트 노드에 오행 색 span 씌우기 */
  function coloredHan(char) {
    const cls = ohClass(char);
    return cls ? `<span class="han-inline ${cls}">${escapeHtml(char)}</span>`
               : `<span class="han-inline">${escapeHtml(char)}</span>`;
  }

  /* ── 십신 + 용신 연계 CSS 클래스 ── */
  function sipYongClass(sipsinName, yong) {
    if (!yong || !sipsinName) return "sip-neutral";
    const yongE  = yong["용신_오행"] || "";
    const heeArr = yong["희신"] || [];
    const giArr  = yong["기신"] || [];
    const sipElem = (sipsinName.match(/목|화|토|금|수/) || [""])[0]; // crude check
    // 십신명에서 오행을 바로 추출하기보다 sipsin_stems 에 stem_element 포함 여부 확인
    if (!sipElem) return "sip-neutral";
    if (sipElem === yongE) return "sip-yong";
    if (heeArr.includes(sipElem)) return "sip-hee";
    if (giArr.includes(sipElem)) return "sip-gi";
    return "sip-neutral";
  }

  const SK = "⭐ 핵심 한줄 요약";
  const EV = "📌 근거";
  const WR = "⚠️ 주의사항";
  const AD = "✅ 조언";

  const CHONG = [
    ["子", "午"],
    ["丑", "未"],
    ["寅", "申"],
    ["卯", "酉"],
    ["辰", "戌"],
    ["巳", "亥"],
  ];
  const LIU_PO = [
    ["子", "酉"],
    ["午", "卯"],
    ["巳", "申"],
    ["寅", "亥"],
    ["辰", "丑"],
    ["戌", "未"],
  ];
  const LIU_HAI = [
    ["子", "未"],
    ["丑", "午"],
    ["寅", "巳"],
    ["卯", "辰"],
    ["申", "亥"],
    ["酉", "戌"],
  ];
  /** 六合 (지지 쌍) */
  const LIU_HE = [
    ["子", "丑"],
    ["寅", "亥"],
    ["卯", "戌"],
    ["辰", "酉"],
    ["巳", "申"],
    ["午", "未"],
  ];

  function pairKey(a, b) {
    return [a, b].sort().join("");
  }

  function makePairSet(pairs) {
    const s = new Set();
    pairs.forEach(([a, b]) => s.add(pairKey(a, b)));
    return s;
  }

  const CHONG_SET = makePairSet(CHONG);
  const PO_SET = makePairSet(LIU_PO);
  const HAI_SET = makePairSet(LIU_HAI);
  const HE_SET = makePairSet(LIU_HE);

  const STEM_ELEM = {
    甲: "목",
    乙: "목",
    丙: "화",
    丁: "화",
    戊: "토",
    己: "토",
    庚: "금",
    辛: "금",
    壬: "수",
    癸: "수",
  };
  const BR_ELEM = {
    子: "수",
    丑: "토",
    寅: "목",
    卯: "목",
    辰: "토",
    巳: "화",
    午: "화",
    未: "토",
    申: "금",
    酉: "금",
    戌: "토",
    亥: "수",
  };

  function relationBetween(z1, z2) {
    const k = pairKey(z1, z2);
    if (CHONG_SET.has(k)) return "chong";
    if (PO_SET.has(k)) return "po";
    if (HAI_SET.has(k)) return "hai";
    if (HE_SET.has(k)) return "he";
    return null;
  }

  function daewoonToneScore(yong, gz) {
    if (!yong || !gz || gz.length < 2) return 0;
    const yElem = yong["용신_오행"] || "";
    const hui = new Set(yong["희신"] || []);
    const gi = new Set(yong["기신"] || []);
    let score = 0;
    const ge = STEM_ELEM[gz[0]];
    const ze = BR_ELEM[gz[1]];
    [ge, ze].forEach((e) => {
      if (!e) return;
      if (e === yElem || hui.has(e)) score += 1;
      if (gi.has(e)) score -= 1;
    });
    return score;
  }

  function daewoonSegmentGradient(score) {
    if (score >= 2) return "linear-gradient(180deg, rgba(72,160,110,0.95), rgba(38,92,68,0.92))";
    if (score >= 1) return "linear-gradient(180deg, rgba(84,130,118,0.9), rgba(36,52,46,0.9))";
    if (score <= -2) return "linear-gradient(180deg, rgba(200,72,85,0.95), rgba(88,28,38,0.92))";
    if (score <= -1) return "linear-gradient(180deg, rgba(160,96,72,0.9), rgba(58,38,32,0.88))";
    return "linear-gradient(180deg, rgba(76,98,128,0.9), rgba(36,48,62,0.9))";
  }

  function sewoonBranchStress(nativeZhis, pillarStr) {
    if (!pillarStr || pillarStr.length < 2) return null;
    const sz = pillarStr[1];
    let chong = false;
    let pohai = false;
    for (const nz of nativeZhis) {
      const k = pairKey(sz, nz);
      if (CHONG_SET.has(k)) chong = true;
      if (PO_SET.has(k) || HAI_SET.has(k)) pohai = true;
    }
    if (chong) return "chong";
    if (pohai) return "poha";
    return null;
  }

  function el(tag, cls, html) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }

  /** /api/saju 영문 키 우선, 기존 한글 키 폴백 */
  function resolveSewoonDeep(r) {
    const kr = r["세운_심층"];
    if (kr && Array.isArray(kr["연도별"])) return kr;
    if (Array.isArray(r.sewoon)) {
      const cy = r.meta?.sewoon_center_applied ?? new Date().getFullYear();
      return {
        기준연도: cy,
        범위: kr?.범위 ?? {},
        연도별: r.sewoon,
      };
    }
    return kr || null;
  }

  function resolveWolwoonPack(r) {
    const full = r["월운표"];
    if (full && Array.isArray(full["월별"])) return full;
    if (Array.isArray(r.wolwoon)) {
      const y = r.meta?.wolwoon_center_applied ?? new Date().getFullYear();
      return {
        세운연도: y,
        월별: r.wolwoon,
        절월_안내: full?.절월_안내 || "",
        특별주의: full?.특별주의 || { "🔴경고": [], "✅기회": [], "⚠️공망": [] },
        출력_표텍스트: full?.출력_표텍스트,
      };
    }
    return full || null;
  }

  function resolveIlwoon(r) {
    return r.ilwoon ?? r["일운"] ?? null;
  }

  function resolveTimeline(r) {
    return r.timeline ?? r["통합_타임라인"] ?? null;
  }

  function syncCalendarUI() {
    const lunar = calendarInput.value === "lunar";
    leapBlock.classList.toggle("active", lunar);
    if (!lunar && lunarLeapCheck) lunarLeapCheck.checked = false;
  }

  document.querySelectorAll(".seg-calendar .seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".seg-calendar .seg-btn").forEach((b) => {
        b.classList.toggle("active", b === btn);
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      calendarInput.value = btn.dataset.calendar || "solar";
      syncCalendarUI();
    });
  });

  document.querySelectorAll(".seg-gender .seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".seg-gender .seg-btn").forEach((b) => {
        b.classList.toggle("active", b === btn);
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      document.getElementById("gender").value = btn.dataset.gender || "male";
    });
  });

  document.querySelectorAll(".seg-leap .seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".seg-leap .seg-btn").forEach((b) => {
        b.classList.toggle("active", b === btn);
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      document.getElementById("lunar_leap_val").value = btn.dataset.leap || "0";
      if (lunarLeapCheck) lunarLeapCheck.checked = btn.dataset.leap === "1";
    });
  });

  syncCalendarUI();

  /* ── 사주 프로필 저장 (localStorage) ───────────────────────── */
  const PROFILE_STORAGE_KEY = "joheundei_saju_profiles_v1";
  const profileTabsEl = document.getElementById("profile-tabs");
  const profileAddBtn = document.getElementById("profile-add-btn");
  const profileSaveBtn = document.getElementById("profile-save-btn");
  const profileDelBtn = document.getElementById("profile-del-btn");

  function newProfileId() {
    return "p_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 8);
  }

  function defaultProfileData() {
    const y = new Date().getFullYear();
    return {
      user_name: "",
      calendar: "solar",
      year: y,
      month: 1,
      day: 1,
      hour: 12,
      minute: 0,
      gender: "male",
      lunar_leap: false,
      sewoon_year: "",
      partner_day_pillar: "",
      ya_jasi: false,
    };
  }

  function readFormProfileData() {
    const fd = new FormData(form);
    const calendar = calendarInput.value;
    const lunarLeapSeg = document.querySelector(".seg-leap .seg-btn.active");
    const leapOn = calendar === "lunar" && lunarLeapSeg && lunarLeapSeg.dataset.leap === "1";
    const yaJasiEl = document.getElementById("ya_jasi");
    return {
      user_name: (document.getElementById("user_name").value || "").trim(),
      calendar,
      year: Number(fd.get("year")) || defaultProfileData().year,
      month: Number(fd.get("month")) || 1,
      day: Number(fd.get("day")) || 1,
      hour: Number(fd.get("hour")) ?? 12,
      minute: Number(fd.get("minute")) ?? 0,
      gender: document.getElementById("gender").value || "male",
      lunar_leap: leapOn,
      sewoon_year: (fd.get("sewoon_year") || "").toString().trim(),
      partner_day_pillar: (fd.get("partner_day_pillar") || "").toString().trim(),
      ya_jasi: !!(yaJasiEl && yaJasiEl.checked),
    };
  }

  function applyFormProfileData(data) {
    if (!data) return;
    const d = { ...defaultProfileData(), ...data };
    document.getElementById("user_name").value = d.user_name || "";
    document.getElementById("year").value = d.year;
    document.getElementById("month").value = d.month;
    document.getElementById("day").value = d.day;
    document.getElementById("hour").value = d.hour;
    document.getElementById("minute").value = d.minute;
    document.getElementById("sewoon_year").value = d.sewoon_year || "";
    document.getElementById("partner_day_pillar").value = d.partner_day_pillar || "";
    const yaJasiEl = document.getElementById("ya_jasi");
    if (yaJasiEl) yaJasiEl.checked = !!d.ya_jasi;

    const cal = d.calendar === "lunar" ? "lunar" : "solar";
    calendarInput.value = cal;
    document.querySelectorAll(".seg-calendar .seg-btn").forEach((b) => {
      const on = (b.dataset.calendar || "solar") === cal;
      b.classList.toggle("active", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });

    const g = d.gender === "female" ? "female" : "male";
    document.getElementById("gender").value = g;
    document.querySelectorAll(".seg-gender .seg-btn").forEach((b) => {
      const on = (b.dataset.gender || "male") === g;
      b.classList.toggle("active", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });

    const leap = d.lunar_leap ? "1" : "0";
    document.getElementById("lunar_leap_val").value = leap;
    document.querySelectorAll(".seg-leap .seg-btn").forEach((b) => {
      const on = (b.dataset.leap || "0") === leap;
      b.classList.toggle("active", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    if (lunarLeapCheck) lunarLeapCheck.checked = leap === "1";
    syncCalendarUI();
  }

  function loadProfileStore() {
    try {
      const raw = localStorage.getItem(PROFILE_STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.profiles) || !parsed.profiles.length) return null;
      return parsed;
    } catch {
      return null;
    }
  }

  function saveProfileStore(store) {
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(store));
  }

  let profileStore = loadProfileStore();
  if (!profileStore) {
    profileStore = {
      activeId: newProfileId(),
      profiles: [
        {
          id: newProfileId(),
          label: "본인",
          data: defaultProfileData(),
        },
      ],
    };
    profileStore.activeId = profileStore.profiles[0].id;
    saveProfileStore(profileStore);
  }

  function getActiveProfile() {
    return profileStore.profiles.find((p) => p.id === profileStore.activeId) || profileStore.profiles[0];
  }

  function profileTabLabel(p) {
    const name = (p.data && p.data.user_name) || p.label || "프로필";
    return name.length > 12 ? name.slice(0, 11) + "…" : name;
  }

  function renderProfileTabs() {
    if (!profileTabsEl) return;
    profileTabsEl.innerHTML = "";
    profileStore.profiles.forEach((p) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "profile-tab" + (p.id === profileStore.activeId ? " active" : "");
      btn.setAttribute("role", "tab");
      btn.setAttribute("aria-selected", p.id === profileStore.activeId ? "true" : "false");
      btn.dataset.profileId = p.id;
      btn.textContent = profileTabLabel(p);
      btn.title = (p.data && p.data.user_name) || p.label || "";
      btn.addEventListener("click", () => switchProfile(p.id));
      profileTabsEl.appendChild(btn);
    });
    if (profileDelBtn) {
      profileDelBtn.disabled = profileStore.profiles.length <= 1;
    }
  }

  function persistActiveProfileFromForm() {
    const p = getActiveProfile();
    if (!p) return;
    p.data = readFormProfileData();
    const nm = (p.data.user_name || "").trim();
    if (nm) p.label = nm;
    saveProfileStore(profileStore);
    renderProfileTabs();
  }

  function switchProfile(id) {
    if (id === profileStore.activeId) return;
    persistActiveProfileFromForm();
    profileStore.activeId = id;
    saveProfileStore(profileStore);
    const p = getActiveProfile();
    applyFormProfileData(p.data);
    renderProfileTabs();
    statusEl.textContent = `「${profileTabLabel(p)}」 프로필로 전환했습니다.`;
    statusEl.classList.remove("error");
  }

  function addProfile() {
    persistActiveProfileFromForm();
    const n = profileStore.profiles.length + 1;
    const p = {
      id: newProfileId(),
      label: `프로필 ${n}`,
      data: defaultProfileData(),
    };
    profileStore.profiles.push(p);
    profileStore.activeId = p.id;
    saveProfileStore(profileStore);
    applyFormProfileData(p.data);
    renderProfileTabs();
    statusEl.textContent = `새 프로필 「${p.label}」을(를) 추가했습니다.`;
    statusEl.classList.remove("error");
    document.getElementById("user_name").focus();
  }

  function deleteActiveProfile() {
    if (profileStore.profiles.length <= 1) {
      statusEl.textContent = "마지막 프로필은 삭제할 수 없습니다.";
      statusEl.classList.add("error");
      return;
    }
    const cur = getActiveProfile();
    const name = profileTabLabel(cur);
    if (!window.confirm(`「${name}」 프로필을 삭제할까요?`)) return;
    profileStore.profiles = profileStore.profiles.filter((p) => p.id !== profileStore.activeId);
    profileStore.activeId = profileStore.profiles[0].id;
    saveProfileStore(profileStore);
    applyFormProfileData(getActiveProfile().data);
    renderProfileTabs();
    statusEl.textContent = `「${name}」 프로필을 삭제했습니다.`;
    statusEl.classList.remove("error");
  }

  if (profileAddBtn) profileAddBtn.addEventListener("click", addProfile);
  if (profileSaveBtn) {
    profileSaveBtn.addEventListener("click", () => {
      persistActiveProfileFromForm();
      statusEl.textContent = `「${profileTabLabel(getActiveProfile())}」 저장 완료`;
      statusEl.classList.remove("error");
    });
  }
  if (profileDelBtn) profileDelBtn.addEventListener("click", deleteActiveProfile);

  applyFormProfileData(getActiveProfile().data);
  renderProfileTabs();

  let latestReport = null;
  let lastSajuBody = null;
  /** @type {"daewoon"|"sewoon"|"wolwoon"|"ilwoon"} */
  let tab3Subtab = "daewoon";

  const panels = [0, 1, 2, 3, 4, 5].map((i) => document.getElementById(`panel-${i}`));
  const tabBtns = [0, 1, 2, 3, 4, 5].map((i) => document.getElementById(`tab-${i}`));

  let activeTabIdx = 0;

  function activateTab(idx) {
    activeTabIdx = idx;
    tabBtns.forEach((b, i) => {
      const on = i === idx;
      b.classList.toggle("active", on);
      b.setAttribute("aria-selected", on ? "true" : "false");
    });
    panels.forEach((p, i) => {
      if (!p) return;
      const on = i === idx;
      p.hidden = !on;
      p.classList.toggle("active", on);
    });
    document.querySelectorAll(".bottom-nav-btn").forEach((b, i) => {
      const on = i === idx;
      b.classList.toggle("active", on);
      b.setAttribute("aria-current", on ? "page" : "false");
    });
    if (window.SajuAi && latestReport) {
      window.SajuAi.onTabVisible(idx, latestReport);
    }
  }

  tabBtns.forEach((btn, i) => {
    btn.addEventListener("click", () => activateTab(i));
  });

  document.querySelectorAll(".bottom-nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const t = btn.getAttribute("data-tab");
      const idx = t != null ? Number(t) : NaN;
      if (!Number.isFinite(idx)) return;
      activateTab(idx);
    });
  });

  const tabPanelsEl = document.querySelector(".tab-panels");
  if (tabPanelsEl) {
    let tx = null;
    tabPanelsEl.addEventListener(
      "touchstart",
      (ev) => {
        tx = ev.changedTouches[0].clientX;
      },
      { passive: true }
    );
    tabPanelsEl.addEventListener(
      "touchend",
      (ev) => {
        if (tx == null) return;
        const dx = ev.changedTouches[0].clientX - tx;
        tx = null;
        if (results.hidden || Math.abs(dx) < 55) return;
        if (dx < 0 && activeTabIdx < panels.length - 1) activateTab(activeTabIdx + 1);
        else if (dx > 0 && activeTabIdx > 0) activateTab(activeTabIdx - 1);
      },
      { passive: true }
    );
  }

  window.addEventListener("resize", () => updateResultsChrome());

  function riskClassForRow(row) {
    const g = row.강도 || row["강도"] || "";
    if (g.includes("높음")) return { cls: "row-risk-high", icon: "🔴" };
    if (g.includes("중")) return { cls: "row-risk-mid", icon: "🟠" };
    return { cls: "row-risk-low", icon: "🟡" };
  }

  function renderOhaengChart(ohaeng) {
    const wrap = el("div", "ohaeng-chart");
    const order = ["목", "화", "토", "금", "수"];
    const counts = (ohaeng && ohaeng.counts) || ohaeng || {};
    const surf = ohaeng && ohaeng.counts_surface;
    const hid = ohaeng && ohaeng.counts_hidden;
    const hasSplit =
      surf &&
      hid &&
      typeof surf === "object" &&
      typeof hid === "object" &&
      order.every((k) => typeof (surf[k] ?? 0) === "number" && typeof (hid[k] ?? 0) === "number");

    const total = order.reduce((s, k) => s + (Number(counts[k]) || 0), 0) || 1;
    const maxV = Math.max(...order.map((k) => Number(counts[k]) || 0), 1);

    if (hasSplit) {
      const legend = el("p", "ohaeng-split-legend panel-note");
      legend.innerHTML =
        '<span class="ohaeng-leg-surf" aria-hidden="true">■</span> 표면(천간·지지) ' +
        '<span class="ohaeng-leg-hid" aria-hidden="true">■</span> 지장간 · ' +
        '<span class="ohaeng-leg-sum">숫자는 「표면+지장간=합」·괄호 안은 전체 대비 비율</span>';
      wrap.appendChild(legend);
    }

    order.forEach((k) => {
      const v = Number(counts[k]) || 0;
      const pct = Math.round((100 * v) / total);
      const wOuter = Math.max(0, Math.round((100 * v) / maxV));
      const sVal = hasSplit ? Number(surf[k]) || 0 : v;
      const hVal = hasSplit ? Number(hid[k]) || 0 : 0;

      const row = el("div", "ohaeng-row");
      let barInner = "";
      if (hasSplit && v > 0) {
        const ws = Math.round((100 * sVal) / v);
        const wh = 100 - ws;
        barInner = `<div class="bar-stack" style="width:${wOuter}%">
          <div class="bar-seg-surface" style="width:${ws}%"></div>
          <div class="bar-seg-hidden" style="width:${wh}%"></div>
        </div>`;
      } else {
        barInner = `<div class="bar-fill" style="width:${wOuter}%"></div>`;
      }

      const numTxt = hasSplit
        ? `<span class="ohaeng-num-split">${sVal}+${hVal}</span>=${v} <span class="ohaeng-pct-muted">(${pct}%)</span>`
        : `${v} (${pct}%)`;

      row.innerHTML = `<span class="ohaeng-el">${k}</span><div class="bar-bg">${barInner}</div><span class="pct">${numTxt}</span>`;
      wrap.appendChild(row);
    });
    return wrap;
  }

  function classifyOhaengVertex(elem, counts, yongElem, domWeak) {
    const v = counts[elem] || 0;
    const total = ["목", "화", "토", "금", "수"].reduce((s, k) => s + (counts[k] || 0), 0) || 1;
    const avg = total / 5;
    const strong = domWeak?.strong || [];
    const weak = domWeak?.weak || [];
    if (yongElem && elem === yongElem) return "yong";
    if (strong.includes(elem) && v >= avg + 0.51) return "excess";
    if (weak.includes(elem)) return "lack";
    return "ok";
  }

  function renderOhaengRadar(r) {
    const counts = r.ohaeng?.counts || {};
    const domWeak = r.ohaeng?.dominant_weak || { strong: [], weak: [] };
    const yongElem = r.yongsin?.["용신_오행"] || "";
    const order = ["목", "화", "토", "금", "수"];
    const maxV = Math.max(...order.map((k) => counts[k] || 0), 1);
    const cx = 100;
    const cy = 100;
    const rOuter = 72;
    const rInner = 22;
    const pts = order.map((elem, i) => {
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
      const vn = (counts[elem] || 0) / maxV;
      const rr = rInner + vn * (rOuter - rInner);
      return {
        elem,
        x: cx + rr * Math.cos(ang),
        y: cy + rr * Math.sin(ang),
        ax: cx + rOuter * Math.cos(ang),
        ay: cy + rOuter * Math.sin(ang),
        cls: classifyOhaengVertex(elem, counts, yongElem, domWeak),
      };
    });
    const poly = pts.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(" ");
    const ring = order
      .map((elem, i) => {
        const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
        const x = cx + rOuter * Math.cos(ang);
        const y = cy + rOuter * Math.sin(ang);
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      })
      .join(" ");

    const vertexColors = {
      excess: "#e85d6f",
      lack: "#6ba3ff",
      ok: "#6fcf97",
      yong: "#f0d878",
    };

    let axes = "";
    order.forEach((elem, i) => {
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
      const x2 = cx + rOuter * Math.cos(ang);
      const y2 = cy + rOuter * Math.sin(ang);
      axes += `<line x1="${cx}" y1="${cy}" x2="${x2.toFixed(2)}" y2="${y2.toFixed(2)}" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>`;
    });

    const labels = order
      .map((elem, i) => {
        const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
        const xr = cx + (rOuter + 18) * Math.cos(ang);
        const yr = cy + (rOuter + 18) * Math.sin(ang);
        const p = pts[i];
        const fill = vertexColors[p.cls] || "#ccc";
        const star = p.cls === "yong" ? "★" : "";
        return `<text x="${xr.toFixed(2)}" y="${(yr + 4).toFixed(2)}" text-anchor="middle" fill="${fill}" font-size="11" font-weight="700">${elem}${star}</text>`;
      })
      .join("");

    const wrap = el("div", "ohaeng-radar-wrap");
    wrap.innerHTML = `
      <svg class="ohaeng-radar-svg" viewBox="0 0 200 200" role="img" aria-label="오행 레이더">
        <polygon points="${ring}" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
        ${axes}
        <polygon points="${poly}" fill="rgba(111,207,151,0.18)" stroke="rgba(212,175,55,0.45)" stroke-width="1.6"/>
        ${pts
          .map(
            (p) =>
              `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="4.5" fill="${vertexColors[p.cls]}" stroke="rgba(0,0,0,0.35)" stroke-width="1"/>`
          )
          .join("")}
        ${labels}
      </svg>
      <div class="ohaeng-radar-legend">
        <span style="color:#e85d6f">과다</span>
        <span style="color:#6ba3ff">결핍</span>
        <span style="color:#6fcf97">적정</span>
        <span style="color:#f0d878">용신 ★</span>
      </div>
      <p class="ohaeng-radar-note panel-note">레이더 면적·꼭짓점 거리는 표면+지장간 합계 기준입니다.</p>`;
    return wrap;
  }

  function renderBodySilhouette(r) {
    const domWeak = r.ohaeng?.dominant_weak || { strong: [], weak: [] };
    const strong = new Set(domWeak.strong || []);
    const weak = new Set(domWeak.weak || []);
    const zoneClass = (elem) => {
      if (strong.has(elem)) return "risk";
      if (weak.has(elem)) return "warn";
      return "ok";
    };
    const fill = {
      risk: "rgba(232, 93, 111, 0.55)",
      warn: "rgba(233, 162, 59, 0.45)",
      ok: "rgba(111, 207, 151, 0.35)",
    };
    const panel = el("div", "body-silhouette-panel");
    panel.innerHTML = `
      <h4>오행 균형과 신체 부위 (참고)</h4>
      <p class="panel-note" style="margin:0 0 0.5rem;font-size:0.74rem">과다 오행 구간은 붉게, 부족 구간은 주황으로 표시했습니다. 의학적 진단이 아닙니다.</p>
      <svg class="body-sil-svg" viewBox="0 0 120 220" aria-hidden="true">
        <ellipse cx="60" cy="28" rx="22" ry="26" class="body-zone" data-el="목" fill="${fill[zoneClass("목")]}" stroke="rgba(255,255,255,0.12)"/>
        <path class="body-zone" data-el="금" d="M28 58 Q60 48 92 58 L88 95 Q60 88 32 95 Z" fill="${fill[zoneClass("금")]}" stroke="rgba(255,255,255,0.12)"/>
        <path class="body-zone" data-el="화" d="M38 96 Q60 90 82 96 L78 138 Q60 132 42 138 Z" fill="${fill[zoneClass("화")]}" stroke="rgba(255,255,255,0.12)"/>
        <path class="body-zone" data-el="토" d="M42 140 Q60 134 78 140 L74 168 Q60 164 46 168 Z" fill="${fill[zoneClass("토")]}" stroke="rgba(255,255,255,0.12)"/>
        <path class="body-zone" data-el="수" d="M46 170 Q60 166 74 170 L70 215 Q60 218 50 215 Z" fill="${fill[zoneClass("수")]}" stroke="rgba(255,255,255,0.12)"/>
      </svg>
      <p class="panel-note" style="margin-top:0.45rem;font-size:0.7rem">
        머리·목 근처≈목, 흉부≈화, 복부≈토, 어깨·폐≈금, 하복부·신장≈수 (입문용 매핑)
      </p>`;
    return panel;
  }

  function renderPillarRelationMap(r) {
    const pillars = r.pillars;
    const keys = PILLAR_KEYS;
    const zhis = keys.map((k) => pillars[k].zhi);
    const positions = [
      { x: 14, y: 46 },
      { x: 38, y: 46 },
      { x: 62, y: 46 },
      { x: 86, y: 46 },
    ];
    const pairs = [];
    for (let i = 0; i < keys.length; i += 1) {
      for (let j = i + 1; j < keys.length; j += 1) {
        const rel = relationBetween(zhis[i], zhis[j]);
        if (rel) pairs.push({ i, j, rel });
      }
    }
    const priority = { chong: 0, po: 1, hai: 2, he: 3 };
    pairs.sort((a, b) => priority[a.rel] - priority[b.rel]);

    function pathForRel(rel, x1, y1, x2, y2) {
      const mx = (x1 + x2) / 2;
      const my = (y1 + y2) / 2 - (rel === "he" ? 2 : 10);
      if (rel === "chong") {
        return `<path d="M ${x1} ${y1} L ${x2} ${y2}" fill="none" stroke="#e85d6f" stroke-width="2" marker-end="url(#m-arr)" marker-start="url(#m-arr-rev)" />`;
      }
      if (rel === "po") {
        return `<path d="M ${x1} ${y1} L ${x2} ${y2}" fill="none" stroke="#e9a23b" stroke-width="1.5" stroke-dasharray="5 4" />`;
      }
      if (rel === "hai") {
        const waves = [];
        const steps = 10;
        for (let s = 0; s <= steps; s += 1) {
          const t = s / steps;
          const x = x1 + (x2 - x1) * t;
          const y = y1 + (y2 - y1) * t + Math.sin(t * Math.PI * 3) * 5;
          waves.push(`${s === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`);
        }
        return `<path d="${waves.join(" ")}" fill="none" stroke="#f5e6a6" stroke-width="1.35" />`;
      }
      return `<path d="M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}" fill="none" stroke="#6fcf97" stroke-width="1.7" />`;
    }

    let svgInner = `<defs>
      <marker id="m-arr" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
        <polygon points="0 0, 7 3.5, 0 7" fill="#e85d6f" />
      </marker>
      <marker id="m-arr-rev" markerWidth="7" markerHeight="7" refX="1" refY="3.5" orient="auto">
        <polygon points="7 0, 0 3.5, 7 7" fill="#e85d6f" />
      </marker>
    </defs>`;
    pairs.forEach(({ i, j, rel }) => {
      const p1 = positions[i];
      const p2 = positions[j];
      svgInner += pathForRel(rel, p1.x, p1.y, p2.x, p2.y);
    });

    const wrap = el("div", "pillar-rel-panel");
    wrap.innerHTML = `
      <div class="pillar-rel-head">四柱 지지 관계 (충 ↔ · 파 ‑ ‑ · 해 ～ · 육합 —)</div>
      <div class="pillar-rel-wrap">
        <svg class="pillar-rel-svg" viewBox="0 0 100 78" preserveAspectRatio="none" aria-hidden="true">${svgInner}</svg>
        <div class="pillar-rel-boxes">
          ${keys
            .map((k) => {
              const p = pillars[k];
              return `<div class="pillar-rel-cell">
                <div class="pr-label">${LABELS[k]}</div>
                <div class="pr-gz han-inline">${escapeHtml(p.gan)}${escapeHtml(p.zhi)}</div>
                <div class="pr-zhi">${escapeHtml(p.zhi_kr || "")}</div>
              </div>`;
            })
            .join("")}
        </div>
      </div>
      <div class="pillar-rel-legend">
        <span class="rel-chong">↔ 충</span>
        <span class="rel-po">− − 파</span>
        <span class="rel-hai">～ 해</span>
        <span class="rel-he">— 육합</span>
      </div>`;
    return wrap;
  }

  function renderHorizontalDaewoonTimeline(r, nativeZhis) {
    const cycles = (r.daewoon?.cycles || []).filter((c) => c.ganzhi);
    if (!cycles.length) return null;
    const yong = r.yongsin || {};
    let spanYears = 0;
    cycles.forEach((c) => {
      const sy = Number(c.start_year);
      const ey = Number(c.end_year);
      spanYears += Number.isFinite(sy) && Number.isFinite(ey) ? Math.max(1, ey - sy + 1) : 10;
    });
    const cy = new Date().getFullYear();

    const chart = el("div", "dhw-chart");
    const track = el("div", "dhw-track");
    cycles.forEach((c) => {
      const sy = Number(c.start_year);
      const ey = Number(c.end_year);
      const yrs = Number.isFinite(sy) && Number.isFinite(ey) ? Math.max(1, ey - sy + 1) : 10;
      const pct = (100 * yrs) / spanYears;
      const score = daewoonToneScore(yong, c.ganzhi);
      const isCurDw = Number.isFinite(sy) && Number.isFinite(ey) && cy >= sy && cy <= ey;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "dhw-segment" + (isCurDw ? " dhw-segment--current" : "");
      btn.style.width = `${pct}%`;
      btn.style.background = daewoonSegmentGradient(score);
      btn.title = `${c.ganzhi} · ${c.start_age}–${c.end_age}세 · ${c.start_year}–${c.end_year}년${isCurDw ? " ◀ 현재 대운" : ""}`;
      const ganC = ohClass((c.ganzhi||"")[0]);
      const zhiC = ohClass((c.ganzhi||"")[1]);
      btn.innerHTML = `<span class="dhw-segment-inner"><span class="han-inline ${ganC}">${escapeHtml((c.ganzhi||"")[0]||"")}</span><span class="han-inline ${zhiC}">${escapeHtml((c.ganzhi||"")[1]||"")}</span></span>`;
      track.appendChild(btn);
    });
    chart.appendChild(track);

    const markers = el("div", "dhw-markers");
    (r.sewoon_nearby || []).forEach((item) => {
      const y = Number(item.year);
      const sy = Number(cycles[0].start_year);
      const ey = Number(cycles[cycles.length - 1].end_year);
      if (!Number.isFinite(y) || !Number.isFinite(sy) || !Number.isFinite(ey)) return;
      if (y < sy || y > ey) return;
      const pos = ((y - sy + 0.5) / (ey - sy + 1)) * 100;
      const stress = sewoonBranchStress(nativeZhis, item.pillar);
      const dot = document.createElement("span");
      dot.className = "dhw-dot";
      if (stress === "chong") dot.classList.add("dhw-dot--stress");
      else if (!stress) dot.classList.add("dhw-dot--good");
      dot.style.left = `${pos}%`;
      dot.title = `${y}년 ${item.pillar || ""}`;
      markers.appendChild(dot);
    });

    const syAll = Number(cycles[0].start_year);
    const eyAll = Number(cycles[cycles.length - 1].end_year);
    const nowLeft =
      Number.isFinite(syAll) && Number.isFinite(eyAll) && eyAll > syAll
        ? ((cy - syAll + 0.5) / (eyAll - syAll + 1)) * 100
        : 50;
    const nowEl = el("div", "dhw-now");
    nowEl.style.left = `${Math.min(99, Math.max(1, nowLeft))}%`;
    markers.appendChild(nowEl);
    chart.appendChild(markers);

    const wrap = el("div", "timeline-h");
    wrap.appendChild(chart);
    const note = el("p", "dhw-note");
    note.textContent =
      "굵은 바는 대운(10년 단위), 점은 근방 세운 연도입니다. ▼는 올해 위치입니다. 바 색은 용신·희신·기신과의 오행 궁합을 단순 반영했습니다.";
    wrap.appendChild(note);
    return wrap;
  }

  function formatDotsIso(iso) {
    const m = String(iso || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
    return m ? `${m[1]}.${m[2]}.${m[3]}` : String(iso || "");
  }

  /** 원국_스토리텔링 한 줄 → narrative 폴백 */
  function getStoryQuoteLine(r) {
    const story = r["원국_스토리텔링"];
    const narr = r.narrative;
    if (story && story["사주_한줄_핵심"]) return String(story["사주_한줄_핵심"]).trim();
    if (narr?.main) return String(narr.main).trim();
    if (typeof narr?.bullets === "string") {
      const line = narr.bullets.split("\n").find((x) => x.trim());
      if (line) return line.trim();
    }
    return "";
  }

  function appendStoryCoreCard(parent, r, { prepend = true } = {}) {
    const line = getStoryQuoteLine(r);
    if (!line || !parent) return null;
    const card = el("div", "story-card");
    const p = el("p", "story-main");
    p.textContent = line;
    card.appendChild(p);
    if (prepend && parent.firstChild) parent.insertBefore(card, parent.firstChild);
    else parent.appendChild(card);
    return card;
  }

  function appendStoryListBlock(parent, title, items) {
    if (!Array.isArray(items) || !items.length) return;
    const b = el("div", "story-block");
    b.appendChild(el("h4", "story-block-title", title));
    const ul = document.createElement("ul");
    ul.className = "story-list";
    items.forEach((item) => {
      const li = document.createElement("li");
      if (item && typeof item === "object" && item["직군"]) {
        li.textContent = `${item["직군"]}: ${item["이유"] || ""}`;
      } else {
        li.textContent = String(item ?? "");
      }
      ul.appendChild(li);
    });
    b.appendChild(ul);
    parent.appendChild(b);
  }

  function appendStoryKvBlock(parent, title, obj, keys) {
    if (!obj || typeof obj !== "object") return;
    const b = el("div", "story-block");
    b.appendChild(el("h4", "story-block-title", title));
    keys.forEach(([key, label]) => {
      const val = obj[key];
      if (val == null || val === "") return;
      if (Array.isArray(val)) {
        appendStoryListBlock(b, label, val);
        return;
      }
      const p = el("p", "story-line");
      p.innerHTML = `<strong>${escapeHtml(label)}</strong> ${escapeHtml(String(val))}`;
      b.appendChild(p);
    });
    if (b.querySelector(".story-line, .story-list")) parent.appendChild(b);
  }

  function renderNativeStoryFull(root, story) {
    if (!story || typeof story !== "object") return;
    const sec = el("div", "panel-section story-pack");
    sec.appendChild(el("h3", null, "원국 스토리텔링"));
    if (story["사주_한줄_핵심"]) {
      const card = el("div", "story-card story-card--hero");
      const p = el("p", "story-main");
      p.textContent = story["사주_한줄_핵심"];
      card.appendChild(p);
      sec.appendChild(card);
    }
    appendStoryKvBlock(sec, "성격 · 기질", story["성격_분석"], [
      ["대인관계_스타일", "대인관계"],
      ["스트레스_반응", "스트레스"],
      ["의사결정_방식", "의사결정"],
    ]);
    if (story["성격_분석"]) {
      appendStoryListBlock(sec, "장점", story["성격_분석"]["장점_5"]);
      appendStoryListBlock(sec, "주의할 점", story["성격_분석"]["단점_5"]);
    }
    const life = story["인생_전체_흐름"];
    if (life && typeof life === "object") {
      const b = el("div", "story-block");
      b.appendChild(el("h4", "story-block-title", "인생 흐름"));
      Object.entries(life).forEach(([k, v]) => {
        const p = el("p", "story-line");
        p.innerHTML = `<strong>${escapeHtml(k)}</strong> ${escapeHtml(String(v))}`;
        b.appendChild(p);
      });
      sec.appendChild(b);
    }
    appendStoryKvBlock(sec, "직업 · 적성", story["직업_적성"], [
      ["사업_적합", "사업"],
    ]);
    if (story["직업_적성"]) {
      appendStoryListBlock(sec, "추천 직군 TOP5", story["직업_적성"]["최적_직군_TOP5"]);
      appendStoryListBlock(sec, "피할 직군", story["직업_적성"]["피해야_할_직군"]);
      const modes = story["직업_적성"]["근무형태_판정"];
      if (Array.isArray(modes)) appendStoryListBlock(sec, "근무 형태", modes);
    }
    appendStoryKvBlock(sec, "재물", story["재물_패턴"], [
      ["버는_방식", "버는 방식"],
      ["평생_재물_흐름", "평생 흐름"],
      ["부자_가능성_판정", "부자 가능성"],
    ]);
    if (story["재물_패턴"]) {
      appendStoryListBlock(sec, "새는 패턴", story["재물_패턴"]["새는_패턴"]);
    }
    appendStoryKvBlock(sec, "건강", story["건강_평생"], [
      ["장수_가능성", "장수"],
    ]);
    if (story["건강_평생"]) {
      appendStoryListBlock(sec, "선천 취약 축", story["건강_평생"]["선천_취약_축"]);
      const age = story["건강_평생"]["나이대별_주의"];
      if (age && typeof age === "object") {
        const b = el("div", "story-block");
        b.appendChild(el("h4", "story-block-title", "나이대별 건강"));
        Object.entries(age).forEach(([k, v]) => {
          const p = el("p", "story-line");
          p.innerHTML = `<strong>${escapeHtml(k)}</strong> ${escapeHtml(String(v))}`;
          b.appendChild(p);
        });
        sec.appendChild(b);
      }
      appendStoryListBlock(sec, "건강 유지", story["건강_평생"]["건강_유지_조언"]);
    }
    const special = story["특별_포인트"];
    if (special && typeof special === "object") {
      const b = el("div", "story-block");
      b.appendChild(el("h4", "story-block-title", "특별 포인트"));
      Object.entries(special).forEach(([k, v]) => {
        if (Array.isArray(v)) appendStoryListBlock(b, k, v);
        else if (v) {
          const p = el("p", "story-line");
          p.innerHTML = `<strong>${escapeHtml(k)}</strong> ${escapeHtml(String(v))}`;
          b.appendChild(p);
        }
      });
      sec.appendChild(b);
    }
    if (story["안내"]) {
      sec.appendChild(el("p", "panel-note story-footnote", story["안내"]));
    }
    root.insertBefore(sec, root.firstChild);
  }

  function renderDashboardSummary(r) {
    const mount = document.getElementById("dashboard-summary");
    if (!mount) return;
    const il = resolveIlwoon(r);
    const today = il?.오늘;
    const isoToday = todayISO();
    const dateStr = formatDotsIso(today?.양력문자열 || isoToday);
    const gzToday = today?.간지 || "";

    const cy = r.meta?.sewoon_center_applied ?? new Date().getFullYear();
    const deep = resolveSewoonDeep(r);
    let row = deep?.연도별?.find((x) => x["연도"] === cy);
    if (!row && deep?.연도별?.length) row = deep.연도별[Math.floor(deep.연도별.length / 2)];
    const dom = row?.종합점수_영역별 || {};
    const overallStars =
      dom?.전체?.문자 || (row?.별점 != null ? ratingBarFromNum(row.별점) : ratingBarFromNum(3));

    const domainOrder = [
      ["재물", "💰재물"],
      ["애정", "💑애정"],
      ["직업", "💼직업"],
      ["건강", "🏥건강"],
    ];
    const domainHtml = domainOrder
      .map(([key, label]) => {
        const block = dom[key];
        const stars = block?.문자 || ratingBarFromNum(block?.별점 ?? 3);
        return `<div class="dash-domain"><span class="dash-domain-label">${label}</span><span class="dash-domain-stars">${escapeHtml(stars)}</span></div>`;
      })
      .join("");

    const quote =
      today?.한줄판정 ||
      row?.이해_총평_한마디 ||
      row?.세운_총평_한줄 ||
      getStoryQuoteLine(r) ||
      "무리한 확장보다 검토와 정리에 집중하면 안정적입니다.";

    mount.hidden = false;
    mount.innerHTML = `
      <div class="dash-summary-card">
        <div class="dash-summary-head">
          <h3 class="dash-summary-title">🔮 오늘의 운세 (${escapeHtml(dateStr)} ${escapeHtml(gzToday)})</h3>
          <span class="dash-summary-overall">전체운 ${escapeHtml(overallStars)}</span>
        </div>
        <div class="dash-summary-domains">${domainHtml}</div>
        <p class="dash-summary-quote">💬 ${escapeHtml(String(quote).trim())}</p>
      </div>`;
  }

  function updateResultsChrome() {
    const bottomNav = document.getElementById("bottom-nav");
    const dash = document.getElementById("dashboard-summary");
    const show = !results.hidden;
    const mobile = window.matchMedia("(max-width: 768px)").matches;
    document.body.classList.toggle("has-bottom-nav", show && mobile);
    if (bottomNav) bottomNav.hidden = !show || !mobile;
    if (dash && !show) dash.hidden = true;
  }

  function renderCategoryCompact(title, block) {
    if (!block || typeof block !== "object") return null;
    const box = el("div", "compact-block");
    box.appendChild(el("h4", null, title));
    const sum = block[SK];
    if (sum) {
      const p = el("p", "sum-line", "");
      p.textContent = sum;
      box.appendChild(p);
    }
    const parts = [
      [EV, block[EV]],
      [WR, block[WR]],
      [AD, block[AD]],
    ];
    parts.forEach(([label, arr]) => {
      if (!Array.isArray(arr) || !arr.length) return;
      box.appendChild(el("p", null, label));
      const ul = document.createElement("ul");
      ul.className = "meta-list";
      arr.forEach((line) => {
        const li = document.createElement("li");
        li.textContent = line;
        ul.appendChild(li);
      });
      box.appendChild(ul);
    });
    return box;
  }

  const JJ_PILLAR_ROLE = {
    year: "년지(年支)는 가문·조상·유년기 환경의 속기운을 봅니다. 겉으로 드러나지 않은 가문의 성향이나 초년 분위기가 여기서 읽힙니다.",
    month: "월지(月支)는 부모·형제·성장 환경·사회에 나아가는 방식과 연결됩니다. 직장·학업의 초기 뿌리도 월지 지장간에서 단서를 찾습니다.",
    day: "일지(日支)는 본인의 내면·배우자궁·성인 이후 삶의 핵심 반응 패턴입니다. 천간 일간이 ‘겉’, 일지 지장간이 ‘속’에 가깝습니다.",
    hour: "시지(時支)는 자녀·말년·행동 결과·노후의 흐름을 보조합니다. 천간 시간과 합쳐 ‘무엇을 하며 어떻게 드러내는지’를 짚습니다.",
  };

  const JJ_SLOT_NOTE = {
    정기: "정기(正氣) — 그 지지 안에서 가장 강하게 작용하는 본기(本氣)입니다.",
    중기: "중기(中氣) — 정기를 보조하며 상황에 따라 중간 강도로 드러납니다.",
    여기: "여기(餘氣) — 잔기·이전 계절의 기운이 남은 층으로, 약하지만 트리거되면 발동합니다.",
  };

  function jjYukchinTag(arr) {
    if (!arr || !arr.length) return "";
    return ` <span class="jj-yuk">(${arr.map(escapeHtml).join(" · ")})</span>`;
  }

  function renderJijangganSection(r) {
    const wrap = el("div", "jj-section");
    const dm = r.day_master || "";
    const dmKr = r.day_master_kr || "";
    const intro = el("div", "jj-intro panel-note");
    intro.innerHTML = `
      <p><strong>지장간(支藏干)</strong>은 지지(子·丑·寅…) 안에 숨어 있는 천간입니다.
      명식에서는 <strong>일간 ${escapeHtml(dm)}(${escapeHtml(dmKr)})</strong>을 기준으로,
      각 지장간도 십신·육친으로 분류합니다.</p>
      <ul class="jj-intro-list">
        <li><strong>천간 십신</strong> — 겉으로 드러나는 성향·사회적 역할(표면).</li>
        <li><strong>지장간 십신</strong> — 속마음·잠재력·가족·인연 궁에서 작용하는 기운(내면·잠재).</li>
        <li>같은 지지라도 <strong>정기 → 중기 → 여기</strong> 순으로 힘의 크기가 달라집니다(정기가 가장 큼).</li>
        <li>대운·세운의 천간·지지가 지장간을 충·합·형하면, 숨어 있던 십신이 갑자기 드러나기도 합니다.</li>
      </ul>`;
    wrap.appendChild(intro);

    const list = el("div", "jj-pillar-list");
    PILLAR_KEYS_COL_ORDER.forEach((k) => {
      const block = r.jijanggan && r.jijanggan[k];
      if (!block) return;
      const hidden = block.hidden || [];
      const spRows = r.sipsin_hidden && r.sipsin_hidden[k] ? r.sipsin_hidden[k] : [];
      const stemSip = (r.sipsin_stems && r.sipsin_stems[k]) || {};
      const ganStem = stemSip.gan || (r.pillars && r.pillars[k] && r.pillars[k].gan) || "";
      const card = el("article", "jj-pillar-card");
      const head = el("div", "jj-pillar-head");
      head.innerHTML = `<span class="jj-pillar-label">${LABELS[k]}</span>
        <span class="jj-pillar-zhi han-inline ${ohClass(block.zhi)}">${escapeHtml(block.zhi)}</span>
        <span class="jj-pillar-zhi-kr">${escapeHtml(block.zhi_kr || "")}</span>`;
      card.appendChild(head);

      const surface = el("p", "jj-surface");
      surface.innerHTML = `<span class="jj-surface-lab">천간(표면)</span>
        ${escapeHtml(ganStem)}
        → <strong>${escapeHtml(stemSip.sipsin || "—")}</strong>
        ${jjYukchinTag(stemSip.yukchin)}`;
      card.appendChild(surface);

      const rows = el("div", "jj-hidden-rows");
      hidden.forEach((h, idx) => {
        const sp = spRows[idx] || spRows.find((x) => x.gan === h.gan) || {};
        const row = el("div", "jj-hidden-row");
        const slot = h.slot || "";
        row.innerHTML = `
          <span class="jj-slot">${escapeHtml(slot)}</span>
          <span class="jj-gan han-inline ${ohClass(h.gan)}">${escapeHtml(h.gan)}</span>
          <span class="jj-gan-kr">(${escapeHtml(h.kr || "")}·${escapeHtml(h.element || "")})</span>
          <span class="jj-arrow">→</span>
          <span class="jj-sip"><strong>${escapeHtml(sp.sipsin || "—")}</strong>${jjYukchinTag(sp.yukchin)}</span>
          <span class="jj-slot-note">${escapeHtml(JJ_SLOT_NOTE[slot] || "")}</span>`;
        rows.appendChild(row);
      });
      card.appendChild(rows);

      const role = el("p", "jj-pillar-role");
      role.textContent = JJ_PILLAR_ROLE[k] || "";
      card.appendChild(role);

      list.appendChild(card);
    });
    wrap.appendChild(list);
    return wrap;
  }

  function appendWongukStorySections(panel, story) {
    if (!story || !panel) return;

    if (story["성격_분석"]) {
      const per = story["성격_분석"];
      const perDiv = el("div", "story-section");
      perDiv.innerHTML = `
        <h4 class="story-section-title">💫 성격과 특성</h4>
        <p class="story-text">${escapeHtml(per["대인관계_스타일"] || "")}</p>
        <p class="story-text">⚡ ${escapeHtml(per["스트레스_반응"] || "")}</p>
        <p class="story-text">🎯 ${escapeHtml(per["의사결정_방식"] || "")}</p>
        <div class="story-pros-cons">
          <div class="story-pros">
            <h5>✅ 장점</h5>
            ${(per["장점_5"] || []).map((s) => `<p>${escapeHtml(s)}</p>`).join("")}
          </div>
          <div class="story-cons">
            <h5>⚠️ 단점</h5>
            ${(per["단점_5"] || []).map((s) => `<p>${escapeHtml(s)}</p>`).join("")}
          </div>
        </div>`;
      panel.appendChild(perDiv);
    }

    if (story["인생_전체_흐름"]) {
      const arc = story["인생_전체_흐름"];
      const arcDiv = el("div", "story-section");
      arcDiv.innerHTML = `<h4 class="story-section-title">🌊 인생 흐름</h4>`;
      Object.entries(arc).forEach(([k, v]) => {
        const row = el("div", "life-arc-row");
        row.innerHTML = `
          <span class="arc-label">${escapeHtml(k)}</span>
          <span class="arc-text">${escapeHtml(String(v))}</span>`;
        arcDiv.appendChild(row);
      });
      panel.appendChild(arcDiv);
    }

    if (story["직업_적성"]) {
      const job = story["직업_적성"];
      const jobDiv = el("div", "story-section");
      const top5 = (job["최적_직군_TOP5"] || [])
        .map(
          (j) => `
        <div class="job-item">
          <span class="job-name">${escapeHtml(j["직군"] || "")}</span>
          <span class="job-why">${escapeHtml(j["이유"] || "")}</span>
        </div>`
        )
        .join("");
      const modes = job["근무형태_판정"];
      const modesText = Array.isArray(modes) ? modes.join(" / ") : String(modes || "");
      jobDiv.innerHTML = `
        <h4 class="story-section-title">💼 직업 적성</h4>
        ${top5}
        <p class="story-text">🏢 ${escapeHtml(modesText)}</p>`;
      panel.appendChild(jobDiv);
    }

    if (story["재물_패턴"]) {
      const w = story["재물_패턴"];
      const wDiv = el("div", "story-section");
      wDiv.innerHTML = `
        <h4 class="story-section-title">💰 재물 패턴</h4>
        <p class="story-text">💵 ${escapeHtml(w["버는_방식"] || "")}</p>
        <p class="story-text">💸 새는 패턴: ${escapeHtml((w["새는_패턴"] || []).join(", "))}</p>
        <p class="story-text">📈 ${escapeHtml(w["평생_재물_흐름"] || "")}</p>
        <p class="story-highlight">${escapeHtml(w["부자_가능성_판정"] || "")}</p>`;
      panel.appendChild(wDiv);
    }

    if (story["건강_평생"]) {
      const h = story["건강_평생"];
      const hDiv = el("div", "story-section");
      hDiv.innerHTML = `
        <h4 class="story-section-title">🏥 건강 패턴</h4>
        <p class="story-text">⚠️ 취약 축: ${escapeHtml((h["선천_취약_축"] || []).join(", "))}</p>
        <p class="story-text">💪 ${escapeHtml(h["장수_가능성"] || "")}</p>
        ${(h["건강_유지_조언"] || [])
          .map((a) => `<p class="story-text">✅ ${escapeHtml(a)}</p>`)
          .join("")}`;
      panel.appendChild(hDiv);
    }

    if (story["특별_포인트"]) {
      const sp = story["특별_포인트"];
      const spDiv = el("div", "story-section");
      spDiv.innerHTML = `
        <h4 class="story-section-title">✨ 특별 포인트</h4>
        <p class="story-text">🌟 ${escapeHtml(sp["귀인_복"] || "")}</p>
        <p class="story-text">🔄 ${escapeHtml(sp["고난_역전_가능성"] || "")}</p>
        <p class="story-text">🙏 ${escapeHtml(sp["종교_정신세계_성향"] || "")}</p>`;
      panel.appendChild(spDiv);
    }

    if (story["안내"]) {
      panel.appendChild(el("p", "panel-note story-footnote", story["안내"]));
    }
  }

  function renderTab0(r) {
    const root = panels[0];
    root.innerHTML = "";
    const pillars = r.pillars;

    const story = r["원국_스토리텔링"];
    if (story) {
      const storyPanel = el("div", "panel-section wonguk-story-panel");
      appendStoryCoreCard(storyPanel, r);
      appendWongukStorySections(storyPanel, story);
      root.appendChild(storyPanel);
    }

    const sec1 = el("div", "panel-section");
    sec1.appendChild(el("h3", null, "사주 원국 四柱"));
    sec1.appendChild(el("p", "panel-note", `${r.solar.label} · ${r.lunar.label}`));
    sec1.appendChild(
      el(
        "p",
        "panel-note wonguk-order-hint",
        "四柱 배열: 시주 → 일주 → 월주 → 년주 순(왼쪽이 시주, 오른쪽이 년주)."
      )
    );

    const chart = el("div", "chart-pillars");
    PILLAR_KEYS_WONGUK_ORDER.forEach((k) => {
      const p = pillars[k];
      const sb = (r.sibiunsung && r.sibiunsung[k]) || {};
      const stage = sb.stage || "";
      const stageMeaning = sb.meaning || "";
      const stageClass = ["장생","관대","건록","제왕"].includes(stage) ? "sibi-strong"
                       : ["병","사","묘","절"].includes(stage) ? "sibi-weak"
                       : "sibi-mid";
      const ganOh = ohClass(p.gan);
      const zhiOh = ohClass(p.zhi);
      const cell = el("div", "pillar-cell");
      cell.innerHTML = `
        <div class="label-kr">${LABELS[k]}</div>
        <div class="gan-han han-inline ${ganOh}">${escapeHtml(p.gan)}</div>
        <div class="gan-kr">${escapeHtml(p.gan_kr || "")}</div>
        <div class="zhi-han han-inline ${zhiOh}">${escapeHtml(p.zhi)}</div>
        <div class="zhi-kr">${escapeHtml(p.zhi_kr || "")}</div>
        <div class="pillar-sibi ${stageClass}" title="${escapeHtml(stageMeaning)}">${escapeHtml(stage)}</div>`;
      chart.appendChild(cell);
    });
    sec1.appendChild(chart);

    const sibiGuide = el("div", "sibi-guide-block");
    sibiGuide.appendChild(el("h4", "sibi-guide-heading", "십이운성 · 궁(연·월·일·시)별 이해"));
    sibiGuide.appendChild(
      el(
        "p",
        "panel-note sibi-guide-intro",
        "아래는 일간 기준으로 각 주의 지지에 붙은 운성을, 어느 「궁」에서 볼 때 쓰는지와 함께 풀어 쓴 참고 해석입니다. 파종·세팅에 따라 세부는 달라질 수 있습니다."
      )
    );
    const guideGrid = el("div", "sibi-guide-grid");
    PILLAR_KEYS_COL_ORDER.forEach((k) => {
      const sb = (r.sibiunsung && r.sibiunsung[k]) || {};
      const card = el("div", "sibi-guide-card");
      const head = el("div", "sibi-guide-card-head");
      head.innerHTML = `<span class="sibi-guide-ju">${escapeHtml(sb["주"] || LABELS[k])}</span><span class="sibi-guide-stage han-inline">${escapeHtml(sb.stage || "")}</span>`;
      card.appendChild(head);
      const body = el("p", "sibi-guide-body");
      body.textContent = sb["해설_통합"] || sb["해설통합"] || "";
      card.appendChild(body);
      guideGrid.appendChild(card);
    });
    sibiGuide.appendChild(guideGrid);
    sec1.appendChild(sibiGuide);

    root.appendChild(sec1);

    const sec2 = el("div", "panel-section");
    sec2.appendChild(el("h3", null, "천간 · 지지 · 十神 · 十二運"));
    sec2.appendChild(
      el("p", "panel-note", "아래 표·지장간은 위에서 아래로 년주 → 월주 → 일주 → 시주 순입니다.")
    );
    const tw = el("div", "table-wrap");
    const tb = document.createElement("table");
    tb.className = "data-table";
    tb.innerHTML =
      "<thead><tr><th>주柱</th><th>천간干</th><th>지지支</th><th>십신十神</th><th>십이運星</th><th>運星 의미</th></tr></thead><tbody></tbody>";
    const body = tb.querySelector("tbody");
    const yong = r.yongsin || {};
    PILLAR_KEYS_COL_ORDER.forEach((k) => {
      const p = pillars[k];
      const sip = r.sipsin_stems[k] || {};
      const sb = r.sibiunsung[k] || {};
      const ganOh = ohClass(p.gan);
      const zhiOh = ohClass(p.zhi);
      // 십신 + 용신 연계 색
      const stemElem = (r.pillars && r.pillars[k]) ? (r.pillars[k].stem_element || "") : "";
      const yongE   = yong["용신_오행"] || "";
      const heeArr  = yong["희신"] || [];
      const giArr   = yong["기신"] || [];
      let sipCls = "sip-neutral";
      if (stemElem) {
        if (stemElem === yongE) sipCls = "sip-yong";
        else if (heeArr.includes(stemElem)) sipCls = "sip-hee";
        else if (giArr.includes(stemElem)) sipCls = "sip-gi";
      }
      const sipLabel = sip.sipsin || "";
      const yongTag  = sipCls === "sip-yong" ? " <span class='sip-badge sip-yong'>[용신]</span>"
                     : sipCls === "sip-hee"  ? " <span class='sip-badge sip-hee'>[희신]</span>"
                     : sipCls === "sip-gi"   ? " <span class='sip-badge sip-gi'>[기신]</span>" : "";
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${LABELS[k]}</td>
        <td><span class="han-inline ${ganOh}">${escapeHtml(p.gan)}</span> <small>${escapeHtml(sip.gan_kr || "")}</small></td>
        <td><span class="han-inline ${zhiOh}">${escapeHtml(p.zhi)}</span> <small>${escapeHtml(sb.zhi_kr || "")}</small></td>
        <td class="${sipCls}">${escapeHtml(sipLabel)}${yongTag}${sip.yukchin && sip.yukchin.length ? `<br><small class="muted-small">(${sip.yukchin.map(escapeHtml).join(", ")})</small>` : ""}</td>
        <td>${escapeHtml(sb.stage || "")}</td>
        <td class="muted-small">${escapeHtml(sb.meaning || "")}</td>`;
      body.appendChild(tr);
    });
    tw.appendChild(tb);
    sec2.appendChild(tw);

    sec2.appendChild(el("h3", null, "지장간 支藏干 · 십신"));
    if (r.jijanggan) {
      sec2.appendChild(renderJijangganSection(r));
    }
    root.appendChild(sec2);

    const sec3 = el("div", "panel-section");
    sec3.appendChild(el("h3", null, "오행 五行 분포 · 표면과 지장간 구분"));
    sec3.appendChild(renderOhaengRadar(r));
    sec3.appendChild(renderOhaengChart(r.ohaeng));
    root.appendChild(sec3);
  }

  function renderTab1(r) {
    const root = panels[1];
    root.innerHTML = "";
    const cat = r["분석_카테고리"];
    if (cat) {
      const catSec = el("div", "panel-section");
      catSec.appendChild(el("h3", null, "합·충과 연결된 생활 해석"));
      catSec.appendChild(
        el(
          "p",
          "panel-note",
          "원국 충·파·해·형과 맞물리는 연애·건강·사고·이별 테마를 카테고리 분석으로 정리했습니다."
        )
      );
      const chungCats = [
        ["1_연애_궁합", "연애 · 궁합"],
        ["4_건강", "건강"],
        ["5_사고_관재", "사고 · 관재"],
        ["9_이별_별리", "이별 · 거리"],
      ];
      chungCats.forEach(([key, title]) => {
        const node = renderCategoryCompact(title, cat[key]);
        if (node) catSec.appendChild(node);
      });
      root.appendChild(catSec);
    }
    root.appendChild(renderPillarRelationMap(r));
    const cp = r.chung_pa_hae || {};
    const detail = cp["관계_상세_전체"] || [];

    const sec = el("div", "panel-section");
    sec.appendChild(el("h3", null, "원국 合·沖·破·害·刑"));
    sec.appendChild(
      el(
        "div",
        "risk-legend",
        "<span>🔴 높음</span><span>🟠 중</span><span>🟡 참고</span>"
      )
    );

    const nativeRows = detail.filter((row) => (row["분류"] || "").startsWith("원국"));
    const filtered = nativeRows;

    const tw = el("div", "table-wrap");
    const tb = document.createElement("table");
    tb.className = "data-table";
    tb.innerHTML =
      "<thead><tr><th>위험度</th><th>관係</th><th>글자</th><th>위치</th><th>강도</th><th>해석</th></tr></thead><tbody></tbody>";
    const body = tb.querySelector("tbody");
    filtered.forEach((row) => {
      const { cls, icon } = riskClassForRow(row);
      const tr = document.createElement("tr");
      tr.className = cls;
      tr.innerHTML = `<td class="badge-risk">${icon}</td><td>${row.관계}</td><td class="han-inline">${row.글자}</td><td>${row.위치}</td><td>${row.강도}</td><td>${row.해석}</td>`;
      body.appendChild(tr);
    });
    if (!filtered.length) {
      const tr = document.createElement("tr");
      tr.innerHTML =
        "<td colspan=\"6\">원국에서 드러나는 충·파·해·형·합 관계가 없거나 데이터가 비었습니다.</td>";
      body.appendChild(tr);
    }
    tw.appendChild(tb);
    sec.appendChild(tw);
    root.appendChild(sec);

    const sec2 = el("div", "panel-section");
    sec2.appendChild(el("h3", null, "세운·대운 伏吟·沖 (현재 기준년 포함)"));
    const tw2 = el("div", "table-wrap");
    const tb2 = document.createElement("table");
    tb2.className = "data-table";
    tb2.innerHTML =
      "<thead><tr><th>관係</th><th>글자</th><th>위치</th><th>해석</th></tr></thead><tbody></tbody>";
    const b2 = tb2.querySelector("tbody");
    detail.forEach((row) => {
      const label = row["분류"] || "";
      if (label !== "복음" && !label.includes("세운")) return;
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${row.관계}</td><td class="han-inline">${row.글자}</td><td>${row.위치}</td><td>${row.해석}</td>`;
      b2.appendChild(tr);
    });
    if (!b2.children.length) {
      b2.innerHTML = "<tr><td colspan=\"4\">세운·복음 데이터 없음</td></tr>";
    }
    tw2.appendChild(tb2);
    sec2.appendChild(tw2);
    root.appendChild(sec2);
  }

  function renderStrengthBadge(grade) {
    const g = String(grade || "보통");
    const cls =
      g === "유리" ? "strength-badge strength-good" : g === "주의" ? "strength-badge strength-warn" : "strength-badge";
    return `<span class="${cls}">${escapeHtml(g)}</span>`;
  }

  function renderTab2(r) {
    const root = panels[2];
    root.innerHTML = "";
    const ys = r.yongsin;
    const sec = el("div", "panel-section");
    sec.appendChild(el("h3", null, "신강·신약 身强身弱"));
    const j = ys["일간_강약"] || "";
    const score = ys["강약_점수"];
    const detail = ys["강약_상세"] || {};
    const head = el("div", "strength-head");
    head.innerHTML = `<span class="strength-verdict">${escapeHtml(j || "—")}</span>${
      score != null ? `<span class="strength-score">점수 ${escapeHtml(score)}</span>` : ""
    }${detail["점수_구간"] ? `<span class="strength-band">${escapeHtml(detail["점수_구간"])}</span>` : ""}`;
    sec.appendChild(head);
    if (detail["판단_요약"]) sec.appendChild(el("p", "strength-lead", detail["판단_요약"]));
    if (detail["점수_해설"]) sec.appendChild(el("p", "panel-note strength-score-note", detail["점수_해설"]));
    if (Array.isArray(detail["현상_특징"]) && detail["현상_특징"].length) {
      const box = el("div", "strength-box");
      box.appendChild(el("h4", "strength-subtitle", "이렇게 나타나기 쉽습니다"));
      const ul = el("ul", "strength-list");
      detail["현상_특징"].forEach((line) => ul.appendChild(el("li", null, line)));
      box.appendChild(ul);
      sec.appendChild(box);
    }
    if (Array.isArray(detail["생활_조언"]) && detail["생활_조언"].length) {
      const box2 = el("div", "strength-box strength-box-tip");
      box2.appendChild(el("h4", "strength-subtitle", "생활에서 이렇게 보세요"));
      const ul2 = el("ul", "strength-list");
      detail["생활_조언"].forEach((line) => ul2.appendChild(el("li", null, line)));
      box2.appendChild(ul2);
      sec.appendChild(box2);
    }
    if (detail["세운_읽는_법"]) sec.appendChild(el("p", "panel-note", detail["세운_읽는_법"]));
    const sewStrength = ys["세운_강약_해설"] || [];
    if (sewStrength.length) {
      const sewSec = el("div", "strength-sewoon-block");
      sewSec.appendChild(el("h4", "strength-subtitle", "세운별 강약 해설 (±10년)"));
      sewSec.appendChild(
        el(
          "p",
          "panel-note",
          "원국이 신강·신약인지에 따라, 매년 들어오는 오행이 도움이 되는지·부담인지를 짧게 정리했습니다. 합충·신살과 함께 보세요."
        )
      );
      const tw = el("div", "table-wrap strength-sewoon-table-wrap");
      const table = el("table", "data-table strength-sewoon-table");
      table.innerHTML =
        "<thead><tr><th>연도</th><th>간지</th><th>등급</th><th>한줄 요약</th><th>해설</th></tr></thead>";
      const tb = el("tbody");
      sewStrength.forEach((row) => {
        const tr = el("tr", row["기준년"] ? "strength-row-current" : "");
        tr.innerHTML = `<td>${escapeHtml(row["연도"])}</td><td class="gz">${escapeHtml(
          row["간지"] || ""
        )}</td><td>${renderStrengthBadge(row["종합_등급"])}</td><td>${escapeHtml(row["한줄"] || "")}</td><td class="strength-detail-cell">${escapeHtml(
          row["상세"] || ""
        )}</td>`;
        tb.appendChild(tr);
      });
      table.appendChild(tb);
      tw.appendChild(table);
      sewSec.appendChild(tw);
      sec.appendChild(sewSec);
    }
    root.appendChild(sec);

    const sec2 = el("div", "panel-section");
    sec2.appendChild(el("h3", null, "용신·희신·기신"));
    const lines = ys["출력_문장"];
    if (lines) {
      sec2.appendChild(el("p", "panel-note", lines["용신"] || ""));
      sec2.appendChild(el("p", "panel-note", lines["희신"] || ""));
      sec2.appendChild(el("p", "panel-note", lines["기신"] || ""));
    }
    const han = ys["한신"];
    const gu = ys["구신"];
    if (han && han.length) sec2.appendChild(el("p", "panel-note", `한신 閑神: ${han.join(", ")}`));
    if (gu && gu.length) sec2.appendChild(el("p", "panel-note", `구신 仇神: ${gu.join(", ")}`));
    root.appendChild(sec2);

    const sec3 = el("div", "panel-section");
    sec3.appendChild(el("h3", null, "색·방위·직업 (용신 오행)"));
    const meta = ys["용신_색상_방위_직업"] || {};
    sec3.appendChild(
      el(
        "p",
        "panel-note",
        `색상: ${meta["색상"] || "-"} · 방위: ${meta["방위"] || "-"} · 직업성향: ${meta["직업"] || "-"}`
      )
    );
    root.appendChild(sec3);

    const sec4 = el("div", "panel-section");
    sec4.appendChild(el("h3", null, "근거 요약"));
    (ys.notes || []).forEach((line) => sec4.appendChild(el("p", "panel-note", line)));
    sec4.appendChild(el("p", "panel-note", ys.disclaimer || ""));
    root.appendChild(sec4);
  }

  function escapeHtml(text) {
    const n = document.createElement("div");
    n.textContent = text == null ? "" : String(text);
    return n.innerHTML;
  }

  function todayISO() {
    const d = new Date();
    const p = (x) => String(x).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }

  function compactIso(iso) {
    return String(iso || "").replace(/-/g, "");
  }

  /** 양력 구간 문자열 `YYYY-MM-DD ~ YYYY-MM-DD` 안에 오늘이 포함되는지 */
  function solarRangeContains(isoDay, rangeStr) {
    const m = String(rangeStr).match(/(\d{4})-(\d{2})-(\d{2})\s*~\s*(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return false;
    const lo = `${m[1]}${m[2]}${m[3]}`;
    const hi = `${m[4]}${m[5]}${m[6]}`;
    const t = compactIso(isoDay);
    return t >= lo && t <= hi;
  }

  function ratingBarFromNum(n) {
    const x = Math.max(1, Math.min(5, Number(n) || 3));
    return "★".repeat(x) + "☆".repeat(5 - x);
  }

  function yukchinIconsFromSewRow(row) {
    const bag = new Set();
    const pushPk = (list) => {
      (list || []).forEach((x) => {
        const pk = x.궁;
        if (pk === "year") bag.add("👨‍👩‍👧");
        else if (pk === "month") bag.add("💼");
        else if (pk === "day") bag.add("💰");
        else if (pk === "hour") bag.add("🏥");
      });
    };
    pushPk(row["세운_지지_충"]);
    pushPk(row["세운_지지_파"]);
    pushPk(row["세운_지지_해"]);
    return [...bag].join(" ");
  }

  function sewHasChungPaHae(row) {
    return (
      ((row["세운_지지_충"] || []).length > 0 ||
        (row["세운_지지_파"] || []).length > 0 ||
        (row["세운_지지_해"] || []).length > 0)
    );
  }

  function sewoonLuckRowClass(row) {
    const g = row["운세등급"] || "";
    if (g === "길운") return "sew-row-luck-good";
    if (g === "흉운") return "sew-row-luck-bad";
    return "";
  }

  function wolRelationSummary(nr) {
    if (!nr || typeof nr !== "object") return "—";
    const keys = ["충", "파", "해", "형", "육합"];
    const parts = [];
    keys.forEach((k) => {
      const arr = nr[k];
      if (arr && arr.length) parts.push(`${k}${arr.length}`);
    });
    return parts.length ? parts.join(" · ") : "충파해형합 뚜렷하지 않음";
  }

  function isWolDangerMonth(m) {
    if (!m) return false;
    if (m["길흉판정"] === "대흉우려") return true;
    const f = m["중첩플래그"] || {};
    return !!(f["세운월운_동시충"] || f["세운월운_복음"]);
  }

  function wolOverallStarsFromGrade(m) {
    if (m && typeof m === "object") {
      const sc = m["길흉점수"];
      if (typeof sc === "number" && Number.isFinite(sc)) {
        return Math.max(1, Math.min(5, sc));
      }
    }
    const gw =
      typeof m === "string" ? m : (m && (m["길흉등급_5단계"] || m["길흉등급"])) || "";
    const map5 = { 대길: 5, 길: 4, 평: 3, 흉: 2, 대흉: 1 };
    if (gw && map5[gw] != null) return map5[gw];
    const mapOld = { 길: 5, 보통: 3, 약흉: 2, 흉: 1 };
    return mapOld[gw] ?? 3;
  }

  function wolFlowStars(m) {
    const f = m["중첩플래그"] || {};
    if (m["길흉판정"] === "대흉우려") return 1;
    if (f["삼합완성"]) return 5;
    if (m["길흉판정"] === "약흉") return 2;
    if (m["길흉판정"] === "대길우려") return 5;
    return 4;
  }

  function syncSewoonDetail(rootEl, pack, year) {
    const detail = rootEl.querySelector("#tab3-sewoon-detail");
    if (!detail || !pack) return;
    const yi = Number(year);
    rootEl.querySelectorAll(".sew-year-card").forEach((btn) => {
      btn.classList.toggle("sew-year-card--selected", Number(btn.dataset.year) === yi);
    });
    const row = (pack["연도별"] || []).find((x) => x["연도"] === yi);
    if (!row) {
      detail.innerHTML = `<p class="panel-note">선택 연도 데이터가 없습니다.</p>`;
      return;
    }
    const icons = yukchinIconsFromSewRow(row);
    const dom = row["종합점수_영역별"] || {};
    const domainKeys = [
      ["건강", "🏥 건강"],
      ["재물", "💰 재물"],
      ["직업", "💼 직업"],
      ["애정", "💑 애정"],
      ["전체", "✨ 전체"],
    ];
    const domainHtml = domainKeys
      .map(([key, label]) => {
        const b = dom[key];
        const stars = b?.문자 || ratingBarFromNum(b?.별점 ?? 3);
        return `<div class="sewoon-detail-domain"><strong>${label}</strong><br>${escapeHtml(stars)}</div>`;
      })
      .join("");

    const storyRaw = row["세운_총평_한줄"] || row["이해_총평_한마디"] || "";
    const storyLines = String(storyRaw)
      .split(/\n+/)
      .reduce((acc, line) => {
        line.split(/[。.]/).forEach((s) => {
          const t = s.trim();
          if (t) acc.push(t);
        });
        return acc;
      }, [])
      .slice(0, 3);

    const risky =
      row["운세등급"] === "흉운" ||
      sewHasChungPaHae(row) ||
      (Number(row["별점"]) > 0 && Number(row["별점"]) <= 2);
    const lucky = row["운세등급"] === "길운" || Number(row["별점"]) >= 4;
    let shellCls = "sewoon-detail-card-shell";
    if (risky) shellCls += " sew-detail--risk";
    else if (lucky) shellCls += " sew-detail--luck";

    const ipNote = row["입춘_안내"] ? `<p class="ipchun-notice">${escapeHtml(row["입춘_안내"])}</p>` : "";
    const gz = row["간지"] || "";
    const ganOhDet = ohClass(gz[0]||"");
    const zhiOhDet = ohClass(gz[1]||"");
    detail.innerHTML = `
      <div class="sewoon-detail-rich">
        ${ipNote}
        <div class="${shellCls}">
          <div class="sewoon-detail-head sew-head-rich">
            <span class="sewoon-detail-year">${yi}년</span>
            <span class="sewoon-detail-gz sew-gz-large"><span class="han-inline ${ganOhDet}">${escapeHtml(gz[0]||"")}</span><span class="han-inline ${zhiOhDet}">${escapeHtml(gz[1]||"")}</span></span>
            <span class="badge-risk sew-grade-badge">${escapeHtml(row["운세등급"] || "")}</span>
          </div>
          <div class="sewoon-detail-big-luck" aria-label="별점">${escapeHtml(row["별점_문자"] || ratingBarFromNum(row["별점"]))}</div>
          ${icons ? `<p class="yukchin-icons-line">${icons} <span class="panel-note-inline">충·파·해 발동 시 육친 궁 영향</span></p>` : ""}
          <div class="sewoon-detail-grid-domains">${domainHtml}</div>
          ${storyLines.map((line) => `<p class="sewoon-detail-story">${escapeHtml(line)}</p>`).join("")}
        </div>
        <h4 class="sewoon-tree-heading">세운 상세 트리</h4>
        <div class="pre-plain sewoon-tree"></div>
      </div>`;
    const treeEl = detail.querySelector(".sewoon-tree");
    if (treeEl) treeEl.textContent = row["출력_트리텍스트"] || "";
    rootEl.querySelectorAll("#tab3-sewoon-table tbody tr").forEach((tr) => {
      tr.classList.toggle("sew-row-selected", Number(tr.dataset.year) === yi);
    });
    const selTr = rootEl.querySelector(`#tab3-sewoon-table tbody tr[data-year="${yi}"]`);
    if (selTr && typeof selTr.scrollIntoView === "function") {
      selTr.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }

  function renderTab3WolPane(r, pane) {
    pane.innerHTML = "";
    const pack = resolveWolwoonPack(r);
    if (!pack || !Array.isArray(pack["월별"])) {
      pane.appendChild(el("p", "panel-note", "월운표 데이터가 없습니다."));
      return;
    }
    const applied = r.meta?.wolwoon_center_applied ?? pack["세운연도"];
    const selWrap = el("div", "wol-toolbar");
    selWrap.innerHTML =
      '<label class="wol-year-label">월운 기준 세운연도 <select id="tab3-wol-year-select" class="wol-year-select"></select></label>';
    const sel = selWrap.querySelector("#tab3-wol-year-select");
    const lo = Math.max(1800, applied - 15);
    const hi = Math.min(2100, applied + 15);
    for (let y = lo; y <= hi; y += 1) {
      const opt = document.createElement("option");
      opt.value = String(y);
      opt.textContent = `${y}년`;
      if (y === pack["세운연도"]) opt.selected = true;
      sel.appendChild(opt);
    }
    pane.appendChild(selWrap);

    pane.appendChild(el("p", "panel-note muted-small", pack["절월_안내"] || ""));

    const warnSlots = pack["특별주의"]?.["🔴경고"] || [];
    const dangerMonths = pack["월별"].filter(isWolDangerMonth);
    const strip = el("div", "wol-danger-strip");
    if (!dangerMonths.length && !warnSlots.length) {
      strip.innerHTML =
        '<span class="wol-danger-title">⚠ 위험 구간 요약</span><span class="panel-note-inline">이 연도에는 🔴 동시충·복음 등 극단 패턴이 두드러진 절월이 없습니다.</span>';
    } else {
      const bits = dangerMonths.map((m) => `${m["절월번호"]}월(${escapeHtml(m["월주간지"] || "")})`);
      strip.innerHTML = `<span class="wol-danger-title">⚠ 주의 절월</span><span>${bits.join(" · ") || warnSlots.map((s) => `${s}절월`).join(" · ")}</span>`;
    }
    pane.appendChild(strip);

    const grid = el("div", "wol-month-grid");
    const isoToday = todayISO();
    pack["월별"].forEach((m) => {
      const grade5 = m["길흉등급_5단계"] || "";
      const isTodayMonth = solarRangeContains(isoToday, m["구간_양력"]);
      const worst = grade5 === "대흉" || m["길흉판정"] === "대흉우려";
      let extra = "";
      if (worst) extra += " wol-month-card--worst";
      else if (isWolDangerMonth(m)) extra += " wol-card--danger-soft";
      const card = el("div", `wol-month-card${isTodayMonth ? " wol-month-card--today" : ""}${extra}`);
      const badgeCls = grade5 ? `wol-month-badge wol-month-badge--${grade5}` : "wol-month-badge";
      const quote = m["월별_핵심스토리"] || m["절기명"] || "—";
      card.innerHTML = `
        <div class="wol-month-top">
          <span class="wol-month-slot">${m["절월번호"]}절월</span>
          <span class="han-inline wol-month-gz">${escapeHtml(m["월주간지"] || "")}</span>
        </div>
        <span class="${badgeCls}">${escapeHtml(grade5 || m["길흉판정"] || "—")}</span>
        <p class="wol-month-quote">${escapeHtml(quote)}</p>
        <div class="wol-month-meta-line">${escapeHtml(m["구간_양력"] || "")}</div>`;
      grid.appendChild(card);
    });
    pane.appendChild(grid);

    sel.addEventListener("change", async () => {
      const y = Number(sel.value);
      if (!lastSajuBody || !Number.isFinite(y)) return;
      try {
        const res = await fetch("/api/saju", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...lastSajuBody, wolwoon_center_year: y }),
        });
        const json = await res.json();
        if (!res.ok) {
          let detail = json.message ?? json.detail ?? res.statusText;
          if (typeof detail === "object") detail = JSON.stringify(detail);
          throw new Error(String(detail));
        }
        latestReport["월운표"] = json.result["월운표"];
        if (Array.isArray(json.result.wolwoon)) latestReport.wolwoon = json.result.wolwoon;
        if (json.result.jeongmil) latestReport.jeongmil = json.result.jeongmil;
        latestReport.meta = latestReport.meta || {};
        latestReport.meta.wolwoon_center_applied =
          json.result.meta?.wolwoon_center_applied ?? y;
        renderTab3WolPane(latestReport, pane);
      } catch (err) {
        statusEl.textContent = err.message || String(err);
        statusEl.classList.add("error");
      }
    });
  }

  function renderTab3IlwoonPane(r, pane) {
    pane.innerHTML = "";
    const pack = resolveIlwoon(r);
    if (!pack || !pack["오늘"]) {
      pane.appendChild(el("p", "panel-note", "일운 데이터가 없습니다."));
      return;
    }
    const today = pack["오늘"];
    const isoToday = todayISO();
    pane.appendChild(el("p", "panel-note muted-small", pack["안내"] || ""));

    const hero = el("div", "ilwoon-hero");
    const detHead = today["오늘_일진_상세"];
    const subExtra = detHead?.["오늘의_십신"] ? ` · 십신 ${detHead["오늘의_십신"]}` : "";
    hero.innerHTML = `
      <div class="ilwoon-hero-date">${escapeHtml(today["양력문자열"] || isoToday)} · ${escapeHtml(today["요일한글"] || "")}요일</div>
      <div class="ilwoon-hero-gz han-inline">${escapeHtml(today["간지"] || "")}</div>
      <div class="ilwoon-hero-sub">${escapeHtml(today["간지한글"] || "")} · 길흉등급 ${escapeHtml(today["길흉등급"] || "")} (${escapeHtml(today["표시색한글"] || "")})${escapeHtml(subExtra)}</div>
    `;
    pane.appendChild(hero);

    const quote = el("p", "ilwoon-quote", "");
    quote.textContent = today["한줄판정"] || "";
    pane.appendChild(quote);

    if (detHead) {
      const box = el("div", "ilwoon-detail-box");
      const stems = Array.isArray(detHead["천간_원국_메모"]) ? detHead["천간_원국_메모"].join(" · ") : "";
      box.innerHTML = `
        <h5>오늘 일진 상세</h5>
        <p>${escapeHtml(detHead["내러티브"] || "")}</p>
        ${stems ? `<p class="panel-note-inline" style="margin-top:0.4rem">${escapeHtml(stems)}</p>` : ""}
      `;
      pane.appendChild(box);
    }

    const hours = today["시간대별_운세"];
    if (Array.isArray(hours) && hours.length) {
      const hHour = el("h4", null, "오늘 시간대별 운세 (十二時)");
      hHour.style.marginBottom = "0.35rem";
      hHour.style.fontSize = "0.88rem";
      pane.appendChild(hHour);
      const ul = el("ul", "ilwoon-hour-list");
      hours.forEach((h) => {
        const li = document.createElement("li");
        const gz = escapeHtml(h["시주간지"] || "");
        const sip = escapeHtml(h["시간천간십신"] || "");
        const gh = escapeHtml(h["길흉"] || "");
        li.innerHTML = `<strong>${escapeHtml(h["시지"] || "")}시 (${escapeHtml(h["시간대"] || "")})</strong> [${gh}] ${gz}·${sip} — ${escapeHtml(h["한줄"] || "")}`;
        ul.appendChild(li);
      });
      pane.appendChild(ul);
    }

    const rec = today["오늘_추천행동"];
    if (rec && typeof rec === "object") {
      const luckNums = Array.isArray(rec["행운_숫자"]) ? rec["행운_숫자"].join(", ") : "";
      const grid = el("div", "ilwoon-rec-grid");
      grid.innerHTML = `
        <div class="ilwoon-rec-card">
          <h5>하면 좋은 일</h5>
          <ul>${(rec["하면_좋은_일"] || []).map((x) => `<li>${escapeHtml(String(x))}</li>`).join("")}</ul>
        </div>
        <div class="ilwoon-rec-card">
          <h5>피해야 할 일</h5>
          <ul>${(rec["피해야_할_일"] || []).map((x) => `<li>${escapeHtml(String(x))}</li>`).join("")}</ul>
        </div>
      `;
      pane.appendChild(grid);
      const luckRow = el("p", "panel-note-inline");
      luckRow.innerHTML = `행운 방향·색상·숫자: <strong>${escapeHtml(rec["행운_방향"] || "—")}</strong> · ${escapeHtml(rec["행운_색상"] || "—")} · <strong>${escapeHtml(luckNums || "—")}</strong>`;
      pane.appendChild(luckRow);
    }

    const weekPack = pack["이번주"];
    const weekRow = el("div", "ilwoon-week");
    weekRow.appendChild(el("h4", null, "이번 주 미리보기 (월~일)"));
    const strip = el("div", "ilwoon-week-strip");
    (weekPack?.일자별 || []).forEach((d) => {
      const cell = el("div", "ilwoon-week-cell");
      const isTd = (d["양력문자열"] || "") === isoToday;
      if (isTd) cell.classList.add("ilwoon-week-cell--today");
      if (d["표시색"] === "green") cell.classList.add("ilwoon-week-cell--good");
      else if (d["표시색"] === "red") cell.classList.add("ilwoon-week-cell--bad");
      const prev = d["미리보기"] || {};
      const emo = escapeHtml(prev["이모지등급"] || "");
      const hint = escapeHtml(prev["핵심한마디"] || d["한줄판정"] || "");
      cell.innerHTML = `
        <div class="iw-prev">${emo}</div>
        <div class="iw-dow">${escapeHtml(d["요일한글"] || "")}</div>
        <div class="iw-dom">${d["일"] != null ? escapeHtml(String(d["일"])) : ""}</div>
        <div class="iw-gz han-inline">${escapeHtml(d["간지"] || "")}</div>
        <div class="iw-hint">${hint}</div>
      `;
      cell.title = d["한줄판정"] || "";
      strip.appendChild(cell);
    });
    weekRow.appendChild(strip);
    pane.appendChild(weekRow);

    const mo = pack["이번달"];
    const calWrap = el("div", "ilwoon-cal-section");
    calWrap.appendChild(el("h4", null, `이번 달 일진 달력 (${mo?.연 ?? ""}.${String(mo?.월 ?? "").padStart(2, "0")})`));
    const grid = el("div", "il-cal-grid");
    const wdays = ["월", "화", "수", "목", "금", "토", "일"];
    const head = el("div", "il-cal-row il-cal-head");
    head.innerHTML = wdays.map((w) => `<div>${w}</div>`).join("");
    grid.appendChild(head);
    (mo?.달력 || []).forEach((week) => {
      const row = el("div", "il-cal-row");
      week.forEach((cell) => {
        const div = el("div", "il-cal-cell");
        if (cell["패딩"]) {
          div.classList.add("il-cal-pad");
          div.textContent = cell["일"] != null ? String(cell["일"]) : "";
        } else {
          if (cell["표시색"] === "green") div.classList.add("il-cal-good");
          else if (cell["표시색"] === "red") div.classList.add("il-cal-bad");
          const iso = cell["양력문자열"];
          if (iso === isoToday) div.classList.add("il-cal-today");
          div.title = [cell["한줄판정"], (cell["달력_표시"]?.["길표시"] || []).join(" "), (cell["달력_표시"]?.["흉경고"] || []).join(" ")]
            .filter(Boolean)
            .join(" | ");
          const markers = cell["달력_표시"] || {};
          const badgeStr = [...(markers["길표시"] || []), ...(markers["흉경고"] || [])].join("");
          div.innerHTML = `<div class="il-cal-cell-inner"><span class="il-cal-dom">${cell["일"] ?? ""}</span><span class="il-cal-badges han-inline">${escapeHtml(badgeStr)}</span></div>`;
        }
        row.appendChild(div);
      });
      grid.appendChild(row);
    });
    calWrap.appendChild(grid);
    pane.appendChild(calWrap);
  }

  function renderTab3(r) {
    latestReport = r;
    const root = panels[3];
    root.innerHTML = "";
    const nativeZhis = PILLAR_KEYS.map((k) => r.pillars[k].zhi);

    const wrap = el("div", "tab3-root");
    const tabs = el("div", "tab3-subtabs");
    tabs.innerHTML = `
      <button type="button" class="tab3-subbtn${tab3Subtab === "daewoon" ? " active" : ""}" data-tab3-sub="daewoon">대운</button>
      <button type="button" class="tab3-subbtn${tab3Subtab === "sewoon" ? " active" : ""}" data-tab3-sub="sewoon">세운</button>
      <button type="button" class="tab3-subbtn${tab3Subtab === "wolwoon" ? " active" : ""}" data-tab3-sub="wolwoon">월운</button>
      <button type="button" class="tab3-subbtn${tab3Subtab === "ilwoon" ? " active" : ""}" data-tab3-sub="ilwoon">일운</button>
    `;
    wrap.appendChild(tabs);

    const mkPane = (name, hidden) => {
      const p = el("div", "tab3-pane");
      p.dataset.tab3Pane = name;
      p.hidden = hidden;
      return p;
    };

    const paneDw = mkPane("daewoon", tab3Subtab !== "daewoon");
    const paneSe = mkPane("sewoon", tab3Subtab !== "sewoon");
    const paneWo = mkPane("wolwoon", tab3Subtab !== "wolwoon");
    const paneIl = mkPane("ilwoon", tab3Subtab !== "ilwoon");

    wrap.appendChild(paneDw);
    wrap.appendChild(paneSe);
    wrap.appendChild(paneWo);
    wrap.appendChild(paneIl);
    root.appendChild(wrap);

    tabs.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-tab3-sub]");
      if (!btn) return;
      const sub = btn.getAttribute("data-tab3-sub");
      if (!sub) return;
      tab3Subtab = sub;
      tabs.querySelectorAll("[data-tab3-sub]").forEach((b) => {
        b.classList.toggle("active", b === btn);
      });
      wrap.querySelectorAll(".tab3-pane").forEach((p) => {
        p.hidden = p.dataset.tab3Pane !== tab3Subtab;
      });
    });

    /* 대운 */
    const sec = el("div", "panel-section");
    sec.appendChild(el("h3", null, "大運 타임라인 (10년)"));
    sec.appendChild(
      el(
        "p",
        "panel-note",
        `방향: ${r.daewoon.forward ? "順行" : "逆行"} · ${r.meta?.gender_for_daewoon ?? ""}`
      )
    );
    const hBar = renderHorizontalDaewoonTimeline(r, nativeZhis);
    if (hBar) sec.appendChild(hBar);
    const tl = el("div", "timeline timeline-legacy");
    const currentYear = new Date().getFullYear();
    r.daewoon.cycles.forEach((c) => {
      const gzDisp = c.표시_간지 || (c.ganzhi && String(c.ganzhi).trim().length >= 2 ? c.ganzhi : "〈대운 시작 전〉");
      const isCurrent = Number(c.start_year) <= currentYear && currentYear <= Number(c.end_year);
      const item = el("div", isCurrent ? "timeline-item dw-current" : "timeline-item");
      const ganC = ohClass((gzDisp||"")[0]);
      const zhiC = ohClass((gzDisp||"")[1]);
      item.innerHTML = `<div class="gz">
        <span class="han-inline ${ganC}">${escapeHtml((gzDisp||"")[0]||"")}</span><span class="han-inline ${zhiC}">${escapeHtml((gzDisp||"")[1]||"")}</span>
        ${isCurrent ? '<span class="dw-now-badge">▶ 현재</span>' : ""}
      </div><div class="age">${c.start_age}–${c.end_age}세</div><div class="age">${c.start_year}–${c.end_year}</div>`;
      tl.appendChild(item);
    });
    sec.appendChild(tl);
    paneDw.appendChild(sec);

    const secNear = el("div", "panel-section");
    secNear.appendChild(el("h3", null, "세운 근방 요약 (±10년 · 나린표)"));
    secNear.appendChild(
      el("p", "panel-note", "지충·파·해 등 간단 긴장 표시입니다. 상세는 「세운」 하위 탭을 보세요.")
    );
    const tw = el("div", "table-wrap");
    const tb = document.createElement("table");
    tb.className = "data-table";
    tb.innerHTML =
      "<thead><tr><th>연도</th><th>간柱</th><th>納音</th><th>지지 긴장</th></tr></thead><tbody></tbody>";
    const body = tb.querySelector("tbody");
    r.sewoon_nearby.forEach((y) => {
      const stress = sewoonBranchStress(nativeZhis, y.pillar);
      const tr = document.createElement("tr");
      let note = "—";
      if (stress === "chong") {
        tr.classList.add("sewoon-row-hit-chong");
        note = "沖·충 요동";
      } else if (stress === "poha") {
        tr.classList.add("sewoon-row-hit-poha");
        note = "破·害 긴장";
      }
      tr.innerHTML = `<td>${y.year}</td><td class="han-inline">${y.pillar}</td><td>${y.nayin || ""}</td><td>${note}</td>`;
      body.appendChild(tr);
    });
    tw.appendChild(tb);
    secNear.appendChild(tw);
    paneDw.appendChild(secNear);

    const tpack = resolveTimeline(r);
    if (tpack) {
      const tls = el("div", "panel-section timeline-pack-section");
      tls.appendChild(el("h3", null, "통합 타임라인"));
      if (tpack["출력_요약텍스트"]) {
        const pre = el("pre", "pre-plain");
        pre.textContent = tpack["출력_요약텍스트"];
        tls.appendChild(pre);
      }
      const fy = tpack["향후5년"];
      const fyRows = fy?.연도별;
      if (Array.isArray(fyRows) && fyRows.length) {
        tls.appendChild(el("p", "panel-note", "향후 5년 초점 (연도별 한 줄):"));
        const ul = document.createElement("ul");
        ul.className = "meta-list";
        fyRows.slice(0, 6).forEach((row) => {
          const li = document.createElement("li");
          li.textContent = `${row["연도"]}년 — ${row["한줄요약"] || ""} · 위험도 ${row["위험도_0_100"] ?? "-"}`;
          ul.appendChild(li);
        });
        tls.appendChild(ul);
      }
      paneDw.appendChild(tls);
    }

    /* 세운 심층 */
    const deep = resolveSewoonDeep(r);
    if (!deep || !Array.isArray(deep["연도별"]) || !deep["연도별"].length) {
      paneSe.appendChild(el("p", "panel-note", "세운 심층 데이터가 없습니다."));
    } else {
      const ys = deep["연도별"].map((row) => row["연도"]);
      const yMin = Math.min(...ys);
      const yMax = Math.max(...ys);
      const yBase = deep["기준연도"] ?? ys[Math.floor(ys.length / 2)];

      const secDeep = el("div", "panel-section");
      secDeep.appendChild(el("h3", null, "세운 심층 (기준연도 ±10년 · 21년치)"));
      secDeep.appendChild(
        el(
          "p",
          "panel-note",
          `기준연도 ${deep["기준연도"] ?? ""}년 · 초록=길운, 빨강=흉운, 노란 테두리=충·파·해 발동`
        )
      );

      const sliderRow = el("div", "sewoon-slider-row");
      sliderRow.innerHTML = `
        <label class="sewoon-slider-label">연도 선택 <span id="tab3-sewoon-slider-val">${yBase}</span>년</label>
        <input type="range" id="tab3-sewoon-slider" min="${yMin}" max="${yMax}" value="${yBase}" step="1" />
      `;
      secDeep.appendChild(sliderRow);

      const cardStrip = el("div", "sewoon-cards-strip");
      cardStrip.innerHTML = `<div class="sewoon-cards-label">연도별 카드 (좌우 스와이프)</div>`;
      const scroller = el("div", "sewoon-cards-scroller");
      deep["연도별"].forEach((rowY) => {
        const y = rowY["연도"];
        const risky =
          rowY["운세등급"] === "흉운" ||
          sewHasChungPaHae(rowY) ||
          (Number(rowY["별점"]) > 0 && Number(rowY["별점"]) <= 2);
        const lucky = rowY["운세등급"] === "길운" || Number(rowY["별점"]) >= 4;
        let cls = "sew-year-card";
        if (risky) cls += " sew-year-card--risky";
        if (lucky) cls += " sew-year-card--lucky";
        const btn = el("button", cls);
        btn.type = "button";
        btn.dataset.year = String(y);
        const mini = String(rowY["세운_총평_한줄"] || "").slice(0, 80);
        btn.innerHTML = `
          <div class="sew-year-card-top">${y}년</div>
          <div class="sew-year-card-gz han-inline">${escapeHtml(rowY["간지"] || "")}</div>
          <div class="sew-year-card-luck">${escapeHtml(rowY["별점_문자"] || ratingBarFromNum(rowY["별점"]))}</div>
          <div class="sew-year-card-mini">${escapeHtml(mini)}</div>`;
        btn.addEventListener("click", () => {
          const sl = sliderRow.querySelector("#tab3-sewoon-slider");
          if (sl) {
            sl.value = String(y);
            sl.dispatchEvent(new Event("input"));
          }
        });
        scroller.appendChild(btn);
      });
      cardStrip.appendChild(scroller);
      secDeep.appendChild(cardStrip);

      const detailMount = el("div", "sewoon-detail card-like");
      detailMount.id = "tab3-sewoon-detail";
      secDeep.appendChild(detailMount);

      const scrollWrap = el("div", "sewoon-table-scroll table-wrap");
      const tb2 = document.createElement("table");
      tb2.className = "data-table sewoon-deep-table";
      tb2.id = "tab3-sewoon-table";
      tb2.innerHTML =
        '<thead><tr><th>연도</th><th>간지</th><th>운세</th><th>충파해</th><th>육친 영향</th></tr></thead><tbody></tbody>';
      const tbBody = tb2.querySelector("tbody");
      deep["연도별"].forEach((row) => {
        const tr = document.createElement("tr");
        tr.dataset.year = String(row["연도"]);
        const luckCls = sewoonLuckRowClass(row);
        if (luckCls) tr.classList.add(luckCls);
        if (sewHasChungPaHae(row)) tr.classList.add("sew-row-cph");
        const hasCph = sewHasChungPaHae(row);
        const cphNote = hasCph
          ? `충${(row["세운_지지_충"] || []).length} 파${(row["세운_지지_파"] || []).length} 해${(row["세운_지지_해"] || []).length}`
          : "—";
        const icons = yukchinIconsFromSewRow(row);
        tr.innerHTML = `<td>${row["연도"]}</td><td class="han-inline">${row["간지"] || ""}</td><td>${row["운세등급"] || ""}</td><td>${cphNote}</td><td class="yukchin-icons">${icons || "—"}</td>`;
        tbBody.appendChild(tr);
      });
      scrollWrap.appendChild(tb2);
      secDeep.appendChild(scrollWrap);
      paneSe.appendChild(secDeep);

      const slider = sliderRow.querySelector("#tab3-sewoon-slider");
      const sliderVal = sliderRow.querySelector("#tab3-sewoon-slider-val");
      slider.addEventListener("input", () => {
        sliderVal.textContent = slider.value;
        syncSewoonDetail(wrap, deep, slider.value);
      });
      syncSewoonDetail(wrap, deep, yBase);
    }

    renderTab3WolPane(r, paneWo);
    renderTab3IlwoonPane(r, paneIl);
  }

  function renderTab4(r) {
    const root = panels[4];
    root.innerHTML = "";
    const story = r["원국_스토리텔링"];
    if (story) renderNativeStoryFull(root, story);

    const cat = r["분석_카테고리"];
    if (!cat) {
      if (!story) root.appendChild(el("p", "panel-note", "분석 데이터가 없습니다."));
      return;
    }

    const groups = [
      ["연애 · 桃花·宮合", ["1_연애_궁합"]],
      ["職業 · 財帛", ["2_직업_사회운", "3_재물운"]],
      ["健康 · 事故·官災", ["4_건강", "5_사고_관재"]],
      ["橫財 · 損財", ["6_횡재운", "7_손재운"]],
      ["離別 · 喪服·憂患", ["9_이별_별리", "8_상복_우환"]],
    ];

    groups.forEach(([title, keys]) => {
      const sec = el("div", "panel-section");
      sec.appendChild(el("h3", null, title));
      keys.forEach((k) => {
        const block = cat[k];
        const subTitle =
          {
            "1_연애_궁합": "연애/궁합",
            "2_직업_사회운": "직업/사회",
            "3_재물운": "재물",
            "4_건강": "건강",
            "5_사고_관재": "사고/관재",
            "6_횡재운": "횡재",
            "7_손재운": "손재",
            "8_상복_우환": "상복/우환",
            "9_이별_별리": "이별/별리",
          }[k] || k;
        const node = renderCategoryCompact(subTitle, block);
        if (node) sec.appendChild(node);
        if (k === "4_건강") sec.appendChild(renderBodySilhouette(r));
      });
      root.appendChild(sec);
    });

    const flow = cat["10_전체_운세_흐름"];
    if (flow) {
      const sec = el("div", "panel-section");
      sec.appendChild(el("h3", null, "運勢 흐름 (대운·세운)"));
      const node = renderCategoryCompact("전체", flow);
      if (node) sec.appendChild(node);
      root.appendChild(sec);
    }
  }

  function renderTab5(r) {
    const root = panels[5];
    root.innerHTML = "";
    const sinsal = r.sinsal || {};
    const rows = sinsal["신살_목록"] || [];

    const good = rows.filter((x) => x.길흉 === "길");
    const bad = rows.filter((x) => x.길흉 !== "길");

    const mkTable = (title, list, rowCls) => {
      const box = el("div", "panel-section");
      box.appendChild(el("h3", null, title));
      const tw = el("div", "table-wrap");
      const tb = document.createElement("table");
      tb.className = "data-table";
      tb.innerHTML =
        "<thead><tr><th>神煞</th><th>글자</th><th>위치</th><th>의미</th></tr></thead><tbody></tbody>";
      const body = tb.querySelector("tbody");
      list.forEach((row) => {
        const tr = document.createElement("tr");
        if (rowCls) tr.className = rowCls;
        tr.innerHTML = `<td>${row.신살}</td><td class="han-inline">${row.글자}</td><td>${row.위치}</td><td>${row.해석}</td>`;
        body.appendChild(tr);
      });
      if (!list.length) {
        body.innerHTML = "<tr><td colspan=\"4\">해당 없음</td></tr>";
      }
      tw.appendChild(tb);
      box.appendChild(tw);
      return box;
    };

    root.appendChild(mkTable(`吉神 (${good.length})`, good, ""));
    root.appendChild(mkTable(`凶煞 (${bad.length})`, bad, ""));

    const keys = Object.keys(sinsal).filter((k) => k !== "신살_목록" && !k.startsWith("_"));
    const extra = el("div", "panel-section");
    extra.appendChild(el("h3", null, "요약 한 줄"));
    keys.forEach((name) => {
      const arr = sinsal[name];
      if (!Array.isArray(arr) || !arr.length || typeof arr[0] === "object") return;
      extra.appendChild(el("p", "panel-note", `${name}: ${arr.join(" · ")}`));
    });
    root.appendChild(extra);
  }

  function renderReport(data) {
    const r = data.result;
    latestReport = r;
    tab3Subtab = "daewoon";
    const name = (document.getElementById("user_name").value || "").trim();
    resultsSub.textContent = name
      ? `${name} 님 · 일간 ${r.day_master}(${r.day_master_kr}) · ${r.eight_char_string || ""}`
      : `일간 ${r.day_master}(${r.day_master_kr}) · ${r.eight_char_string || ""}`;

    renderDashboardSummary(r);
    renderTab0(r);
    renderTab1(r);
    renderTab2(r);
    renderTab3(r);
    renderTab4(r);
    renderTab5(r);
    const finish = () => {
      activateTab(0);
      updateResultsChrome();
    };
    if (window.SajuAi && typeof window.SajuAi.afterReport === "function") {
      const p = window.SajuAi.afterReport(r);
      if (p && typeof p.then === "function") p.then(finish);
      else finish();
    } else {
      finish();
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    statusEl.textContent = "계산 중…";
    statusEl.classList.remove("error");
    results.hidden = true;
    updateResultsChrome();

    const fd = new FormData(form);
    const calendar = calendarInput.value;
    const lunarLeapSeg = document.querySelector(".seg-leap .seg-btn.active");
    const leapOn = calendar === "lunar" && lunarLeapSeg && lunarLeapSeg.dataset.leap === "1";

    const body = {
      calendar,
      year: Number(fd.get("year")),
      month: Number(fd.get("month")),
      day: Number(fd.get("day")),
      hour: Number(fd.get("hour")),
      minute: Number(fd.get("minute")),
      gender: fd.get("gender"),
      lunar_leap: leapOn,
    };
    const sewVal = fd.get("sewoon_year");
    if (sewVal) body.sewoon_center_year = Number(sewVal);
    const partner = (fd.get("partner_day_pillar") || "").toString().trim();
    if (partner) body.partner_day_pillar = partner;
    const yaJasiEl = document.getElementById("ya_jasi");
    if (yaJasiEl && yaJasiEl.checked) body.ya_jasi = true;

    if (lunarLeapCheck) lunarLeapCheck.checked = leapOn;
    persistActiveProfileFromForm();

    try {
      const res = await fetch("/api/saju", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (!res.ok) {
        let detail = json.message ?? json.detail ?? res.statusText;
        if (Array.isArray(detail)) {
          detail = detail.map((x) => x.msg || JSON.stringify(x)).join("; ");
        } else if (detail && typeof detail === "object") {
          detail = JSON.stringify(detail);
        }
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      lastSajuBody = body;
      renderReport(json);
      results.hidden = false;
      statusEl.textContent = "완료";
      results.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      statusEl.textContent = err.message || String(err);
      statusEl.classList.add("error");
    }
  });

  function readGhNative(which) {
    return {
      calendar: document.getElementById(`gh-${which}-calendar`).value,
      year: Number(document.getElementById(`gh-${which}-year`).value),
      month: Number(document.getElementById(`gh-${which}-month`).value),
      day: Number(document.getElementById(`gh-${which}-day`).value),
      hour: Number(document.getElementById(`gh-${which}-hour`).value),
      minute: Number(document.getElementById(`gh-${which}-minute`).value),
      gender: document.getElementById(`gh-${which}-gender`).value,
      lunar_leap: document.getElementById(`gh-${which}-leap`).checked,
    };
  }

  /* ── 궁합 원국 카드 ─────────────────────────────────────── */
  function renderGhPillarCard(sn) {
    const KR = { year: "年", month: "月", day: "日", hour: "時" };
    const zh = sn.주 || {};
    const ganRow = ["year","month","day","hour"].map(k => {
      const p = zh[k] || {};
      return `<td class="gh-cell-gz han-inline">${escapeHtml(p.간||"")}</td>`;
    }).join("");
    const zhiRow = ["year","month","day","hour"].map(k => {
      const p = zh[k] || {};
      return `<td class="gh-cell-gz han-inline">${escapeHtml(p.지||"")}</td>`;
    }).join("");
    const hdrRow = ["year","month","day","hour"].map(k =>
      `<th>${KR[k]}</th>`
    ).join("");
    return `
      <div class="gh-chart-card">
        <h4 class="gh-chart-name">${escapeHtml(sn.표시_이름||"")}</h4>
        <p class="gh-chart-ec han-inline">${escapeHtml(sn.eight_char_string||"")}</p>
        <p class="gh-chart-date">${escapeHtml(sn.양력||"")} · ${escapeHtml(sn.음력||"")}</p>
        <table class="gh-pillar-table">
          <thead><tr>${hdrRow}</tr></thead>
          <tbody>
            <tr>${ganRow}</tr>
            <tr>${zhiRow}</tr>
          </tbody>
        </table>
        <p class="gh-chart-dm">일간 <strong class="han-inline">${escapeHtml(sn.일간||"")}</strong>
          (${escapeHtml(sn.일간_한글||"")} · ${escapeHtml(sn.일간_오행||"")})</p>
      </div>`;
  }

  /* ── 게이지 바 ───────────────────────────────────────────── */
  function ghGaugeBar(pct, colorClass) {
    return `<div class="gh-gauge-track"><div class="gh-gauge-fill ${colorClass||""}" style="width:${pct}%"></div></div>`;
  }

  /* ── 월별 궁합 달력 ─────────────────────────────────────── */
  function renderGhMonthGrid(monthlyArr, labelA, labelB) {
    if (!monthlyArr || !monthlyArr.length) return "";
    const cells = monthlyArr.map(m => {
      const emoji = m.이모지 || "⚪";
      const gz = escapeHtml(m.월주간지 || `${m.절월}월`);
      const cls = emoji==="💚" ? "gh-mon-good" : emoji==="🔴" ? "gh-mon-bad" : "gh-mon-norm";
      return `<div class="gh-mon-cell ${cls}" title="${escapeHtml(m.핵심한마디||"")}">
        <span class="gh-mon-gz">${gz}</span>
        <span class="gh-mon-emoji">${emoji}</span>
        <span class="gh-mon-num">${m.절월}절</span>
      </div>`;
    }).join("");
    return `<div class="gh-month-grid">${cells}</div>`;
  }

  /* ── 전체 궁합 결과 렌더 ─────────────────────────────────── */
  function renderGoonghapResult(pack) {
    const mount = document.getElementById("goonghap-result");
    if (!mount) return;

    const sc   = pack["종합_점수"]    || {};
    const side = pack["원국_나란히"]  || {};
    const snA  = side.A || {};
    const snB  = side.B || {};
    const la   = escapeHtml(snA.표시_이름 || "A");
    const lb   = escapeHtml(snB.표시_이름 || "B");

    const ilji = pack["기본_일지"]        || {};
    const allZ = pack["전체_지지_대조"]   || {};
    const ohx  = pack["오행_궁합"]        || {};
    const ig   = pack["일간_궁합"]        || {};
    const sip  = pack["십신_궁합"]        || {};
    const cg   = pack["천간합"]           || {};
    const ysx  = pack["용신_궁합"]        || {};
    const sewG = pack["세운_궁합"]        || {};
    const cy   = sewG.연도 || new Date().getFullYear();

    const pct        = sc["하트_게이지_퍼센트"] ?? 0;
    const heartEmoji = sc["하트_이모지"]       || "❤️".repeat(Math.round(pct/20));
    const overall    = sc["전체_궁합"]         || {};
    const overallStar= overall.문자 || "";

    /* ── 종합 점수 게이지 행 ── */
    const scoreItems = [
      ["인연 강도",   sc["인연_강도"],   "gh-g-bond"],
      ["갈등 가능성", sc["갈등_가능성"], "gh-g-conf"],
      ["경제 궁합",   sc["경제적_궁합"], "gh-g-econ"],
      ["성격 궁합",   sc["성격_궁합"],   "gh-g-pers"],
      ["전체 궁합",   sc["전체_궁합"],   "gh-g-over"],
    ];
    const scoreHTML = scoreItems.map(([lab, o, cls]) => {
      if (!o) return "";
      const barPct = (o.별점||0) * 20;
      return `<div class="gh-score-row">
        <span class="gh-score-lab">${lab}</span>
        ${ghGaugeBar(barPct, cls)}
        <span class="gh-stars">${escapeHtml(o.문자||"")}</span>
      </div>`;
    }).join("");

    /* ── 세운 A/B ── */
    const sewA = sewG[`${snA.표시_이름||"A"}_세운`] || sewG["A_세운"] || {};
    const sewB = sewG[`${snB.표시_이름||"B"}_세운`] || sewG["B_세운"] || {};

    /* ── 월별 궁합 ── */
    const monthlyHTML = renderGhMonthGrid(sewG["월별_궁합"], la, lb);

    /* ── 강점/과제 ── */
    const strengths  = pack["강점_3가지"]    || [];
    const challenges = pack["극복과제_3가지"]|| [];
    const advice     = pack["핵심조언"]       || "";
    const marriage   = pack["결혼적합도_뱃지"] || "";

    const strHTML = strengths.map(s =>
      `<li>✅ ${escapeHtml(s)}</li>`).join("");
    const chalHTML = challenges.map(c =>
      `<li>⚠️ ${escapeHtml(c)}</li>`).join("");

    /* ── 용신 궁합 텍스트 ── */
    const ysA = ysx["A가_느끼는_상대"] || {};
    const ysB = ysx["B가_느끼는_상대"] || {};

    /* ── 십신 ── */
    const sipAB = Object.entries(sip)
      .filter(([k]) => k.endsWith("_해설"))
      .map(([, v]) => `<p class="gh-note">${escapeHtml(String(v))}</p>`)
      .join("");

    mount.hidden = false;
    mount.innerHTML = `
<!-- ①  하트 게이지 -->
<div class="gh-heart-section">
  <div class="gh-heart-visual">
    <span class="gh-heart-icon">♥</span>
    <div class="gh-heart-track"><div class="gh-heart-fill" style="width:${pct}%"></div></div>
    <span class="gh-heart-pct">${pct}%</span>
  </div>
  <div class="gh-heart-emoji">${heartEmoji}</div>
  <div class="gh-marriage-badge">${escapeHtml(marriage)}</div>
</div>

<!-- ②  두 사람 원국 나란히 -->
<div class="gh-charts-row">
  ${renderGhPillarCard(snA)}
  <div class="gh-vs-divider">VS</div>
  ${renderGhPillarCard(snB)}
</div>

<!-- ③  종합 점수 게이지 -->
<div class="gh-scores-block">
  <h4>궁합 점수</h4>
  ${scoreHTML}
</div>

<!-- ④  일지 궁합 -->
<div class="gh-detail-block gh-card">
  <h4>💑 일지 궁합</h4>
  <p><strong class="gh-couple-type">${escapeHtml(ilji.커플_유형||"")} ${(ilji.커플_태그||[]).map(t=>`<span class="gh-tag">${escapeHtml(t)}</span>`).join("")}</strong></p>
  <p class="gh-note">${escapeHtml(ilji.스토리||"")}</p>
  <p class="gh-sub">관계: ${escapeHtml((ilji.관계_표기||[]).join(" · ")||"—")}</p>
</div>

<!-- ⑤  8글자 지지 전체 대조 -->
<div class="gh-detail-block gh-card">
  <h4>🔗 전체 지지 대조 (8글자)</h4>
  <p class="gh-note">${escapeHtml(allZ["인연_강도_판정"]||"")}</p>
  <p class="gh-sub">합 ${allZ["합_개수"]||0}개 · 충 ${allZ["충_개수"]||0}개</p>
  ${(allZ["합_목록"]||[]).map(r=>`<p class="gh-sub">💚 합: ${escapeHtml(r.A_궁)} ${escapeHtml(r.A_지)} ↔ ${escapeHtml(r.B_궁)} ${escapeHtml(r.B_지)}</p>`).join("")}
  ${(allZ["충_목록"]||[]).map(r=>`<p class="gh-sub">🔴 충: ${escapeHtml(r.A_궁)} ${escapeHtml(r.A_지)} ↔ ${escapeHtml(r.B_궁)} ${escapeHtml(r.B_지)}</p>`).join("")}
</div>

<!-- ⑥  오행 궁합 -->
<div class="gh-detail-block gh-card">
  <h4>☯ 오행 궁합</h4>
  <div class="gh-ohaeng-dist">
    <p><strong>${la}</strong> ${escapeHtml(ohx[`${snA.표시_이름||"A"}_오행_분포`]||ohx["A_오행_분포"]||"")}</p>
    <p><strong>${lb}</strong> ${escapeHtml(ohx[`${snB.표시_이름||"B"}_오행_분포`]||ohx["B_오행_분포"]||"")}</p>
  </div>
  <p class="gh-note">${escapeHtml(ohx.스토리||"")}</p>
  <p class="gh-sub">오행 보완 점수: ${"★".repeat(ohx["오행_보완_점수"]||0)}${"☆".repeat(5-(ohx["오행_보완_점수"]||0))}</p>
</div>

<!-- ⑦  일간 궁합 -->
<div class="gh-detail-block gh-card">
  <h4>⚡ 일간 궁합 (${escapeHtml(ig.유형||"")})</h4>
  <p class="gh-note">${escapeHtml(ig.연애_해석||ig.해설||"")}</p>
  <p class="gh-note gh-sub">${escapeHtml(ig.결혼_해석||"")}</p>
</div>

<!-- ⑧  십신 궁합 -->
<div class="gh-detail-block gh-card">
  <h4>🔢 십신으로 보는 궁합</h4>
  ${sipAB||`<p class="gh-note">${escapeHtml(Object.values(sip).find(v=>typeof v==="string")||"")}</p>`}
</div>

<!-- ⑨  천간합 -->
<div class="gh-detail-block gh-card">
  <h4>🌟 천간합</h4>
  <p class="gh-note">${cg.성립
    ? `<strong>${escapeHtml(cg.표기||"")}</strong> — ${escapeHtml(cg.해설||"")}`
    : escapeHtml(cg.해설||"일간 천간합 해당 없음")}</p>
</div>

<!-- ⑩  용신 궁합 -->
<div class="gh-detail-block gh-card">
  <h4>🌿 용신 궁합</h4>
  <p class="gh-note"><strong>${la} 기준</strong> ${escapeHtml(ysA.등급_한글||ysA.등급||"")} — ${escapeHtml(ysA.해설||"")}</p>
  <p class="gh-note"><strong>${lb} 기준</strong> ${escapeHtml(ysB.등급_한글||ysB.등급||"")} — ${escapeHtml(ysB.해설||"")}</p>
  <p class="gh-sub">${escapeHtml(ysx["종합_평가"]||"")}</p>
</div>

<!-- ⑪  세운 궁합 -->
<div class="gh-detail-block gh-card gh-sewoon-section">
  <h4>📅 ${cy}년 세운 궁합</h4>
  <div class="gh-sewoon-two">
    <div class="gh-sew-person">
      <p><strong>${la}</strong> ${escapeHtml(sewA.운세등급||"")} ${escapeHtml(sewA.별점||"")}</p>
      <p class="gh-note">${escapeHtml(sewA.세운_총평||"")}</p>
    </div>
    <div class="gh-sew-person">
      <p><strong>${lb}</strong> ${escapeHtml(sewB.운세등급||"")} ${escapeHtml(sewB.별점||"")}</p>
      <p class="gh-note">${escapeHtml(sewB.세운_총평||"")}</p>
    </div>
  </div>
  <p class="gh-note gh-sew-couple">${escapeHtml(sewG["궁합_세운_분석"]||"")}</p>
  <h5>월별 궁합 달력</h5>
  ${monthlyHTML}
  <div class="gh-half-summary">
    <p>📈 ${escapeHtml(sewG["상반기_총평"]||"")}</p>
    <p>📉 ${escapeHtml(sewG["하반기_총평"]||"")}</p>
  </div>
  <div class="gh-issues">
    <p>💍 ${escapeHtml((sewG["올해_주요이슈"]||{})["결혼_동거_가능성"]||"")}</p>
    <p>⚡ ${escapeHtml((sewG["올해_주요이슈"]||{})["갈등_주의"]||"")}</p>
    <p>💚 함께 좋은 달: ${((sewG["올해_주요이슈"]||{})["함께_좋은_달_TOP3"]||[]).join(", ")||"—"}</p>
    <p>🔴 함께 주의 달: ${((sewG["올해_주요이슈"]||{})["함께_주의할_달_TOP3"]||[]).join(", ")||"—"}</p>
  </div>
</div>

<!-- ⑫  총평 카드 -->
<div class="gh-story-card">
  <h4>✨ 종합 총평</h4>
  ${(pack["총평"]||"").split("\n").map(l=>`<p>${escapeHtml(l)}</p>`).join("")}
</div>

<!-- ⑬  강점 / 과제 / 조언 -->
<div class="gh-strengths-block gh-card">
  <div class="gh-str-col">
    <h5>💪 이 커플의 강점</h5>
    <ul class="meta-list">${strHTML||"<li>서로를 향한 노력이 가장 큰 강점입니다.</li>"}</ul>
  </div>
  <div class="gh-str-col">
    <h5>🎯 극복 과제</h5>
    <ul class="meta-list">${chalHTML||"<li>꾸준한 소통이 관계를 지킵니다.</li>"}</ul>
  </div>
</div>
<div class="gh-advice-card">
  <span class="gh-advice-icon">💡</span>
  <p class="gh-advice-text">${escapeHtml(advice)}</p>
</div>

<p class="panel-note gh-disclaimer">${escapeHtml(pack["참고"]||"")}</p>
    `;

    /* 커플 태그 — innerHTML 주입이라 다시 렌더 */
    const typeEl = mount.querySelector(".gh-couple-type");
    if (typeEl) {
      typeEl.innerHTML = escapeHtml(ilji.커플_유형||"") + " " +
        (ilji.커플_태그||[]).map(t=>`<span class="gh-tag">${escapeHtml(t)}</span>`).join("");
    }
  }

  const ghForm = document.getElementById("goonghap-form");
  const ghStatus = document.getElementById("goonghap-status");
  if (ghForm && ghStatus) {
    const gyGh = new Date().getFullYear();
    ["gh-a-year", "gh-b-year"].forEach((id) => {
      const el = document.getElementById(id);
      if (el && !(el.value || "").trim()) el.value = gyGh;
    });
    ghForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      ghStatus.textContent = "궁합 계산 중…";
      ghStatus.classList.remove("error");
      const cyEl = document.getElementById("gh-current-year");
      const cyVal = cyEl && cyEl.value.trim() ? Number(cyEl.value) : undefined;
      const body = {
        person_a: readGhNative("a"),
        person_b: readGhNative("b"),
        name_a: (document.getElementById("gh-name-a").value || "").trim(),
        name_b: (document.getElementById("gh-name-b").value || "").trim(),
        ...(cyVal ? { current_year: cyVal } : {}),
      };
      try {
        const res = await fetch("/api/goonghap", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const json = await res.json();
        if (!res.ok) {
          let detail = json.detail ?? json.message ?? res.statusText;
          if (typeof detail === "object") detail = JSON.stringify(detail);
          throw new Error(String(detail));
        }
        renderGoonghapResult(json.result);
        ghStatus.textContent = "완료";
        const ghMount = document.getElementById("goonghap-result");
        if (ghMount) ghMount.scrollIntoView({ behavior: "smooth", block: "nearest" });
      } catch (err) {
        ghStatus.textContent = err.message || String(err);
        ghStatus.classList.add("error");
      }
    });
  }
})();
