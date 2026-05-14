(function () {
  const form = document.getElementById("saju-form");
  const statusEl = document.getElementById("status");
  const results = document.getElementById("results");
  const resultsSub = document.getElementById("results-sub");
  const leapBlock = document.getElementById("leap-block");
  const calendarInput = document.getElementById("calendar");
  const lunarLeapCheck = document.getElementById("lunar_leap");

  const PILLAR_KEYS = ["year", "month", "day", "hour"];
  const LABELS = {
    year: "年柱 · 년주",
    month: "月柱 · 월주",
    day: "日柱 · 일주",
    hour: "時柱 · 시주",
  };

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

  let latestReport = null;
  let lastSajuBody = null;
  /** @type {"daewoon"|"sewoon"|"wolwoon"|"ilwoon"} */
  let tab3Subtab = "daewoon";

  const defaultYear = new Date().getFullYear();
  document.getElementById("year").value = defaultYear;
  document.getElementById("month").value = 1;
  document.getElementById("day").value = 1;

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

  function renderOhaengChart(counts) {
    const wrap = el("div", "ohaeng-chart");
    const order = ["목", "화", "토", "금", "수"];
    const total = order.reduce((s, k) => s + (counts[k] || 0), 0) || 1;
    const maxV = Math.max(...order.map((k) => counts[k] || 0), 1);
    order.forEach((k) => {
      const v = counts[k] || 0;
      const pct = Math.round((100 * v) / total);
      const wbar = Math.round((100 * v) / maxV);
      const row = el("div", "ohaeng-row");
      row.innerHTML = `<span>${k}</span><div class="bar-bg"><div class="bar-fill" style="width:${wbar}%"></div></div><span class="pct">${v} (${pct}%)</span>`;
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
      </div>`;
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
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "dhw-segment";
      btn.style.width = `${pct}%`;
      btn.style.background = daewoonSegmentGradient(score);
      btn.title = `${c.ganzhi} · ${c.start_age}–${c.end_age}세 · ${c.start_year}–${c.end_year}년`;
      btn.innerHTML = `<span class="dhw-segment-inner han-inline">${escapeHtml(c.ganzhi)}</span>`;
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
      (typeof r.narrative?.bullets === "string"
        ? r.narrative.bullets.split("\n").find((x) => x.trim())
        : "") ||
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

  function renderTab0(r) {
    const root = panels[0];
    root.innerHTML = "";
    const pillars = r.pillars;

    const sec1 = el("div", "panel-section");
    sec1.appendChild(el("h3", null, "사주 원국 四柱"));
    sec1.appendChild(el("p", "panel-note", `${r.solar.label} · ${r.lunar.label}`));

    const chart = el("div", "chart-pillars");
    PILLAR_KEYS.forEach((k) => {
      const p = pillars[k];
      const cell = el("div", "pillar-cell");
      cell.innerHTML = `
        <div class="label-kr">${LABELS[k]}</div>
        <div class="gan-han">${p.gan}</div>
        <div class="gan-kr">${p.gan_kr || ""}</div>
        <div class="zhi-han">${p.zhi}</div>
        <div class="zhi-kr-nayin">${p.zhi_kr || ""}${p.nayin ? " · " + p.nayin : ""}</div>`;
      chart.appendChild(cell);
    });
    sec1.appendChild(chart);
    root.appendChild(sec1);

    const sec2 = el("div", "panel-section");
    sec2.appendChild(el("h3", null, "천간 · 지지 · 十神 · 十二運"));
    const tw = el("div", "table-wrap");
    const tb = document.createElement("table");
    tb.className = "data-table";
    tb.innerHTML =
      "<thead><tr><th>주柱</th><th>천간干</th><th>지지支</th><th>십신十神</th><th>십이運星</th><th>運星 의미</th></tr></thead><tbody></tbody>";
    const body = tb.querySelector("tbody");
    PILLAR_KEYS.forEach((k) => {
      const p = pillars[k];
      const sip = r.sipsin_stems[k];
      const sb = r.sibiunsung[k] || {};
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${LABELS[k]}</td>
        <td><span class="han-inline">${p.gan}</span> ${sip.gan_kr || ""}</td>
        <td><span class="han-inline">${p.zhi}</span> ${sb.zhi_kr || ""}</td>
        <td>${sip.sipsin || ""}${sip.yukchin && sip.yukchin.length ? `<br><small>(${sip.yukchin.join(", ")})</small>` : ""}</td>
        <td>${sb.stage || ""}</td>
        <td>${sb.meaning || ""}</td>`;
      body.appendChild(tr);
    });
    tw.appendChild(tb);
    sec2.appendChild(tw);

    const jj = el("div", "panel-section");
    jj.appendChild(el("h3", null, "지장간 支藏干 · 십신"));
    r.jijanggan &&
      Object.entries(r.jijanggan).forEach(([k, block]) => {
        const hid = block.hidden.map((h) => `${h.gan}(${h.element})`).join(", ");
        const sp = r.sipsin_hidden[k] || [];
        const spTxt = sp
          .map((x) =>
            `${x.gan}:${x.sipsin}${x.yukchin && x.yukchin.length ? "(" + x.yukchin.join("/") + ")" : ""}`
          )
          .join(" · ");
        jj.appendChild(el("p", "panel-note", `${LABELS[k]} 지지 ${block.zhi} → ${hid} / ${spTxt}`));
      });
    sec2.appendChild(jj);
    root.appendChild(sec2);

    const sec3 = el("div", "panel-section");
    sec3.appendChild(el("h3", null, "오행 五行 분포 (지장간 포함)"));
    sec3.appendChild(renderOhaengRadar(r));
    sec3.appendChild(renderOhaengChart(r.ohaeng.counts));
    root.appendChild(sec3);

    const sec4 = el("div", "panel-section");
    sec4.appendChild(el("h3", null, "요약"));
    sec4.appendChild(el("pre", "pre-plain", r.narrative.bullets));
    root.appendChild(sec4);
  }

  function renderTab1(r) {
    const root = panels[1];
    root.innerHTML = "";
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

  function renderTab2(r) {
    const root = panels[2];
    root.innerHTML = "";
    const ys = r.yongsin;
    const sec = el("div", "panel-section");
    sec.appendChild(el("h3", null, "신강·신약 身强身弱"));
    const j = ys["일간_강약"] || "";
    const score = ys["강약_점수"];
    sec.appendChild(el("p", "panel-note", `판단: ${j}${score != null ? ` (점수 ${score})` : ""}`));
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

    detail.innerHTML = `
      <div class="sewoon-detail-rich">
        <div class="${shellCls}">
          <div class="sewoon-detail-head sew-head-rich">
            <span class="sewoon-detail-year">${yi}년</span>
            <span class="han-inline sewoon-detail-gz sew-gz-large">${escapeHtml(row["간지"] || "")}</span>
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
    r.daewoon.cycles.forEach((c) => {
      const gzDisp = c.표시_간지 || (c.ganzhi && String(c.ganzhi).trim().length >= 2 ? c.ganzhi : "〈대운 시작 전〉");
      const item = el("div", "timeline-item");
      item.innerHTML = `<div class="gz">${escapeHtml(gzDisp)}</div><div class="age">${c.start_age}–${c.end_age}세</div><div class="age">${c.start_year}–${c.end_year}</div>`;
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
    const cat = r["분석_카테고리"];
    if (!cat) {
      root.appendChild(el("p", "panel-note", "분석 카테고리 데이터가 없습니다."));
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
    activateTab(0);
    updateResultsChrome();
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

    if (lunarLeapCheck) lunarLeapCheck.checked = leapOn;

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

  function renderGhPillarCard(sn) {
    const kr = { year: "년주", month: "월주", day: "일주", hour: "시주" };
    const zh = sn.주 || {};
    const rows = ["year", "month", "day", "hour"]
      .map((k) => {
        const p = zh[k] || {};
        return `<div class="gh-pillar-cell"><span class="gh-pk">${kr[k]}</span><span class="han-inline gh-pgz">${escapeHtml(p.간지 || "")}</span></div>`;
      })
      .join("");
    return `
      <div class="gh-chart-card">
        <h4 class="gh-chart-name">${escapeHtml(sn.표시_이름 || "")}</h4>
        <p class="gh-chart-ec han-inline">${escapeHtml(sn.eight_char_string || "")}</p>
        <p class="gh-chart-date">${escapeHtml(sn.양력 || "")} · ${escapeHtml(sn.음력 || "")}</p>
        <div class="gh-pillar-grid">${rows}</div>
      </div>`;
  }

  function renderGoonghapResult(pack) {
    const mount = document.getElementById("goonghap-result");
    if (!mount) return;
    const sc = pack["종합_점수"] || {};
    const pct = sc["하트_게이지_퍼센트"] ?? 0;
    const side = pack["원국_나란히"] || {};
    const ilji = pack["기본_일지"] || {};
    const ohx = pack["오행_궁합"] || {};
    const ig = pack["일간_궁합"] || {};
    const cg = pack["천간합"] || {};
    const ysx = pack["용신_궁합"] || {};

    const scoreRows = [
      ["인연 강도", sc["인연_강도"]],
      ["갈등 가능성", sc["갈등_가능성"]],
      ["경제적 궁합", sc["경제적_궁합"]],
      ["성격 궁합", sc["성격_궁합"]],
      ["전체 궁합", sc["전체_궁합"]],
    ]
      .map(([lab, o]) => {
        if (!o) return "";
        return `<div class="gh-score-row"><span>${escapeHtml(lab)}</span><span class="gh-stars">${escapeHtml(o.문자 || "")}</span></div>`;
      })
      .join("");

    mount.hidden = false;
    mount.innerHTML = `
      <div class="gh-heart-section">
        <div class="gh-heart-visual" aria-hidden="true">
          <span class="gh-heart-icon">♥</span>
          <div class="gh-heart-track"><div class="gh-heart-fill" style="width:${pct}%"></div></div>
          <span class="gh-heart-pct">${pct}%</span>
        </div>
        <p class="gh-heart-caption">전체 궁합 하트 게이지 (참고)</p>
      </div>
      <div class="gh-charts-row">
        ${renderGhPillarCard(side.A || {})}
        ${renderGhPillarCard(side.B || {})}
      </div>
      <div class="gh-scores-block">${scoreRows}</div>
      <div class="gh-detail-block">
        <h4>기본 궁합 (일지)</h4>
        <p>${escapeHtml(ilji.커플_유형 || "")} — ${escapeHtml((ilji.관계_표기 || []).join(", ") || "—")}</p>
        <p class="panel-note">${escapeHtml(ilji.해설 || "")}</p>
        <h4>오행 궁합</h4>
        <ul class="meta-list">${(ohx.요약_문장 || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
        <h4>일간 궁합</h4>
        <p>${escapeHtml(ig.유형 || "")}: ${escapeHtml(ig.해설 || "")}</p>
        <h4>천간합</h4>
        <p>${cg.성립 ? `${escapeHtml(cg.표기 || "")} · ${escapeHtml(cg.해설 || "")}` : "일간 천간합 해당 없음"}</p>
        <h4>용신 궁합</h4>
        <p>A 기준: ${escapeHtml(ysx["A가_느끼는_상대"]?.등급 || "")} — ${escapeHtml(ysx["A가_느끼는_상대"]?.해설 || "")}</p>
        <p>B 기준: ${escapeHtml(ysx["B가_느끼는_상대"]?.등급 || "")} — ${escapeHtml(ysx["B가_느끼는_상대"]?.해설 || "")}</p>
      </div>
      <blockquote class="gh-summary-quote">${escapeHtml(pack["총평"] || "")}</blockquote>
      <p class="panel-note gh-disclaimer">${escapeHtml(pack["참고"] || "")}</p>
    `;
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
      const body = {
        person_a: readGhNative("a"),
        person_b: readGhNative("b"),
        name_a: (document.getElementById("gh-name-a").value || "").trim(),
        name_b: (document.getElementById("gh-name-b").value || "").trim(),
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
