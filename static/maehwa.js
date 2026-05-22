(function () {
  "use strict";

  const els = {
    main: document.getElementById("maehwa-main"),
    intro: document.getElementById("maehwa-intro-text"),
    calcBtn: document.getElementById("maehwa-calc-btn"),
    status: document.getElementById("maehwa-status"),
    result: document.getElementById("maehwa-result"),
    rtabs: document.querySelectorAll("[data-mh-tab]"),
    panels: document.querySelectorAll("[data-mh-panel]"),
    flow: document.getElementById("maehwa-panel-flow"),
    suri: document.getElementById("maehwa-panel-suri"),
    synth: document.getElementById("maehwa-panel-synth"),
    daily: document.getElementById("maehwa-panel-daily"),
    monthly: document.getElementById("maehwa-panel-monthly"),
  };

  let lastData = null;
  let activeTab = "flow";
  let fortuneDaily = null;
  let fortuneMonthly = null;
  let queryDate = null;
  let queryMonth = null;

  function esc(s) {
    if (s == null) return "";
    const d = document.createElement("div");
    d.textContent = String(s);
    return d.innerHTML;
  }

  function fmtStory(s) {
    return esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  }

  function collectPayload() {
    const calendar = document.getElementById("calendar")?.value || "solar";
    const leapSeg = document.querySelector(".seg-leap .seg-btn.active");
    const lunarLeap =
      calendar === "lunar" && leapSeg && leapSeg.dataset.leap === "1";
    const hourUnknown = document.getElementById("hour_unknown")?.checked;
    let hour = Number(document.getElementById("hour")?.value);
    let minute = Number(document.getElementById("minute")?.value);
    if (hourUnknown || Number.isNaN(hour)) {
      hour = 12;
      minute = 0;
    }
    if (Number.isNaN(minute)) minute = 0;

    return {
      user_name: (document.getElementById("user_name")?.value || "").trim(),
      calendar,
      year: Number(document.getElementById("year")?.value),
      month: Number(document.getElementById("month")?.value),
      day: Number(document.getElementById("day")?.value),
      hour,
      minute,
      gender: document.getElementById("gender")?.value || "male",
      lunar_leap: lunarLeap,
    };
  }

  function setStatus(msg, isError) {
    if (!els.status) return;
    els.status.textContent = msg || "";
    els.status.classList.toggle("error", !!isError);
  }

  function setTab(tab) {
    activeTab = tab;
    els.rtabs.forEach((btn) => {
      const on = btn.dataset.mhTab === tab;
      btn.classList.toggle("on", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    els.panels.forEach((p) => {
      p.classList.toggle("show", p.dataset.mhPanel === tab);
    });
  }

  function renderYao(lines) {
    const ordered = [...(lines || [])].sort((a, b) => b.index - a.index);
    return ordered
      .map((row) => {
        const cls = row.yang ? "yang" : "yin";
        const mov = row.moving ? " moving" : "";
        const inner = row.yang
          ? ""
          : "<span></span><span></span>";
        return `<div class="maehwa-yao-row">
          <span class="maehwa-yao-idx">${row.index}</span>
          <div class="maehwa-yao-bar ${cls}${mov}">${inner}</div>
        </div>`;
      })
      .join("");
  }

  function renderTrigramCard(t, roleClass) {
    if (!t) return "";
    return `<div class="maehwa-cv maehwa-cv--${roleClass}">
      <div class="maehwa-cv-role">${esc(t.role)} · ${esc(t.nat)}</div>
      <div class="maehwa-cv-sym">${esc(t.sym)}</div>
      <div class="maehwa-cv-name">${esc(t.name)} <small>${esc(t.elemK)}</small></div>
      <div class="maehwa-cv-xiang">${esc(t.xiang || t.char)}</div>
    </div>`;
  }

  function renderFlow(d) {
    const gf = d.gua_flow;
    const ben = gf.ben;
    const dong = gf.dong;
    const zhi = gf.zhi;

    els.flow.innerHTML = `
      <div class="maehwa-blk maehwa-blk--ben">
        <div class="maehwa-blk-label">본괘 · 本卦</div>
        <div class="maehwa-hex-head">
          <div class="maehwa-hex-syms">${esc(ben.upper?.sym)}${esc(ben.lower?.sym)}</div>
          <div>
            <div class="maehwa-hex-name">${esc(ben.name)}</div>
            <div class="maehwa-hex-hanja">${esc(ben.hanja)} · ${esc(ben.key)}</div>
          </div>
        </div>
        <div class="maehwa-yao" aria-label="육효">${renderYao(ben.lines)}</div>
        <div class="maehwa-cv-grid">
          ${renderTrigramCard(ben.upper, "yong")}
          <div style="text-align:center;color:#5a4a2a;font-size:1.1rem">↔</div>
          ${renderTrigramCard(ben.lower, "che")}
        </div>
        <div class="maehwa-verdict">
          <strong>${esc(ben.ti_yong?.label)}</strong> — ${esc(ben.ti_yong?.desc)}
        </div>
        <p class="maehwa-hex-desc">${esc(ben.desc)}</p>
      </div>

      <div class="maehwa-flow-arrow">↓ 동효 ${dong.index} · 動爻</div>

      <div class="maehwa-blk maehwa-blk--dong">
        <div class="maehwa-blk-label">동효 · 動爻</div>
        <span class="maehwa-dong-badge">${esc(dong.name)} · ${esc(dong.pos)}</span>
        <p class="maehwa-hex-desc">${esc(dong.desc)}</p>
        <div class="maehwa-timing">⏳ ${esc(dong.timing)}</div>
      </div>

      <div class="maehwa-flow-arrow">↓ 변괘</div>

      <div class="maehwa-blk maehwa-blk--zhi">
        <div class="maehwa-blk-label">之卦 · 變卦</div>
        <div class="maehwa-hex-head">
          <div class="maehwa-hex-syms">${esc(zhi.upper?.sym)}${esc(zhi.lower?.sym)}</div>
          <div>
            <div class="maehwa-hex-name">${esc(zhi.name)}</div>
            <div class="maehwa-hex-hanja">${esc(zhi.hanja)} · ${esc(zhi.key)}</div>
          </div>
        </div>
        <div class="maehwa-cv-grid">
          ${renderTrigramCard(zhi.upper, "yong")}
          <div style="text-align:center;color:#5a4a2a;font-size:1.1rem">→</div>
          ${renderTrigramCard(zhi.lower, "che")}
        </div>
        <div class="maehwa-verdict">
          <strong>${esc(zhi.ti_yong?.label)}</strong> — ${esc(zhi.ti_yong?.desc)}
        </div>
        <p class="maehwa-hex-desc">${esc(zhi.desc)}</p>
      </div>

      <p class="maehwa-dt-note">${esc(d.method_note)}<br>
      양력 ${esc(d.datetime?.solar?.label)} · 음력 ${esc(d.datetime?.lunar?.label)}</p>
    `;
  }

  function renderSuri(d) {
    const s = d.suri;
    const aspects = (s.aspects || [])
      .map(
        (a) => `<div class="maehwa-aspect">
          <div class="maehwa-aspect-label">${esc(a.icon || "")} ${esc(a.label)}</div>
          <div class="maehwa-aspect-text">${esc(a.text)}</div>
        </div>`
      )
      .join("");

    const rows = (s.year_table || [])
      .map((yr) => {
        const cls = yr.is_current ? ' class="now"' : "";
        return `<tr${cls}>
          <td>${yr.year}</td>
          <td>${yr.age}세</td>
          <td><strong>${yr.suri}수</strong></td>
          <td>${esc(yr.kw)}</td>
        </tr>`;
      })
      .join("");

    const tags = (s.tags || []).map((t) => `<span>${esc(t)}</span>`).join("");

    els.suri.innerHTML = `
      <div class="maehwa-suri-hero">
        <div class="maehwa-suri-num">${s.basic_num}</div>
        <div class="maehwa-suri-name">${esc(s.name)}</div>
        <div class="maehwa-suri-kw">${esc(s.kw)}</div>
        <div class="maehwa-suri-char">${esc(s.char)}</div>
        ${tags ? `<div class="maehwa-manse-tags" style="margin-top:0.75rem">${tags}</div>` : ""}
      </div>
      <div class="maehwa-blk maehwa-blk--ben">
        <div class="maehwa-blk-label">9방면 · 九面</div>
        ${aspects || "<p class=\"maehwa-hex-desc\">상세 해설 준비 중입니다.</p>"}
      </div>
      <div class="maehwa-blk maehwa-blk--ben" style="margin-top:0.5rem">
        <div class="maehwa-blk-label">연도별 수 · 年運</div>
        <table class="maehwa-year-table">
          <thead><tr><th>연도</th><th>나이</th><th>수</th><th>키워드</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
        <p class="maehwa-dt-note">올해(${new Date().getFullYear()}) 흐름: <strong>${s.current_year_suri}수</strong></p>
      </div>
    `;
  }

  function shiftDate(y, m, d, deltaDays) {
    const dt = new Date(y, m - 1, d);
    dt.setDate(dt.getDate() + deltaDays);
    return { y: dt.getFullYear(), m: dt.getMonth() + 1, d: dt.getDate() };
  }

  function shiftMonth(y, m, delta) {
    const dt = new Date(y, m - 1 + delta, 1);
    return { y: dt.getFullYear(), m: dt.getMonth() + 1 };
  }

  function todayYmd() {
    const t = new Date();
    return { y: t.getFullYear(), m: t.getMonth() + 1, d: t.getDate() };
  }

  async function fetchFortune(period, qy, qm, qd) {
    const body = { ...collectPayload(), period, query_year: qy, query_month: qm, query_day: qd || 1 };
    const res = await fetch("/api/maehwa/fortune", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || res.statusText || "조회 실패");
    return data.fortune;
  }

  function renderGuaMini(gua, label) {
    if (!gua) return "";
    const b = gua.ben;
    const z = gua.zhi;
    return `<div class="maehwa-fortune-gua-mini">
      <span class="maehwa-blk-label" style="margin-bottom:0.35rem">${esc(label)}</span><br>
      ${esc(b.name)} → ${gua.dong.index}효 → ${esc(z.name)} · ${esc(b.ti_yong?.label || "")}
    </div>`;
  }

  function buildCalendarHtml(days, qy, qm, selectedDay) {
    const weekHd = ["일", "월", "화", "수", "목", "금", "토"];
    const firstWd = new Date(qy, qm - 1, 1).getDay();
    let cells = "";
    for (let i = 0; i < firstWd; i++) {
      cells += '<div class="maehwa-cal-cell maehwa-cal-pad"></div>';
    }
    (days || []).forEach((cell) => {
      const cls = [
        "maehwa-cal-cell",
        cell.is_today ? "is-today" : "",
        selectedDay === cell.solar_day ? "is-selected" : "",
      ]
        .filter(Boolean)
        .join(" ");
      cells += `<button type="button" class="${cls}" data-day="${cell.solar_day}" aria-label="${cell.solar_day}일 ${cell.suri}수">
        <span class="d">${cell.solar_day}</span>
        <span class="s">${cell.suri}</span>
      </button>`;
    });
    return `
      <div class="maehwa-blk maehwa-blk--ben maehwa-cal-wrap">
        <div class="maehwa-blk-label">일별 일운 · 달력</div>
        <div class="maehwa-fortune-nav maehwa-fortune-nav--cal" data-fortune-nav="cal-month">
          <button type="button" class="btn" data-cal-delta="-1">◀ 전달</button>
          <span class="maehwa-fortune-date">${qy}년 ${qm}월</span>
          <button type="button" class="btn" data-cal-this="1">이번 달</button>
          <button type="button" class="btn" data-cal-delta="1">다음 달 ▶</button>
        </div>
        <div class="maehwa-cal-grid maehwa-cal-grid--head">
          ${weekHd.map((w) => `<div class="maehwa-cal-hd">${w}</div>`).join("")}
        </div>
        <div class="maehwa-cal-grid">${cells}</div>
        <p class="maehwa-dt-note" style="margin-top:0.65rem">날짜를 누르면 그날의 일운으로 위 내용이 바뀝니다.</p>
      </div>`;
  }

  function bindDailyPanelEvents() {
    if (!els.daily) return;
    els.daily.querySelectorAll('[data-fortune-nav="daily"] button').forEach((btn) => {
      btn.addEventListener("click", onDailyNav);
    });
    els.daily.querySelectorAll('[data-fortune-nav="cal-month"] button').forEach((btn) => {
      btn.addEventListener("click", onDailyCalMonthNav);
    });
    els.daily.querySelectorAll(".maehwa-cal-cell[data-day]").forEach((btn) => {
      btn.addEventListener("click", onCalendarDayClick);
    });
  }

  function renderDailyPanel(f, calendarDays) {
    if (!f || !els.daily) return;
    const n = f.narrative || {};
    const ds = f.day_suri || {};
    const ms = f.month_suri || {};
    const q = f.solar || {};
    queryDate = { y: q.year, m: q.month, d: q.day };
    queryMonth = { y: q.year, m: q.month };
    const days =
      calendarDays ||
      (fortuneMonthly?.solar?.year === q.year &&
      fortuneMonthly?.solar?.month === q.month
        ? fortuneMonthly.calendar_days
        : []);
    const calHtml = days.length
      ? buildCalendarHtml(days, q.year, q.month, q.day)
      : "";

    els.daily.innerHTML = `
      <div class="maehwa-fortune-nav" data-fortune-nav="daily">
        <button type="button" class="btn" data-delta="-1">◀ 하루 전</button>
        <button type="button" class="btn" data-today="1">오늘</button>
        <span class="maehwa-fortune-date" id="mh-daily-date">${esc(f.solar?.label || "")}</span>
        <button type="button" class="btn" data-delta="1">하루 후 ▶</button>
      </div>
      ${f.is_today ? '<p class="maehwa-dt-note" style="text-align:center;margin-bottom:0.75rem">📍 오늘의 운세</p>' : ""}
      <div class="maehwa-fortune-hero">
        <div class="mh-num">${ds.num}</div>
        <div class="mh-name">${esc(ds.name)}</div>
        <div class="mh-kw">${esc(ds.kw)}</div>
        <p class="maehwa-dt-note" style="margin-top:0.65rem">이달 ${ms.num}수 · ${esc(ms.name)}</p>
      </div>
      <p class="maehwa-fortune-story"><strong>${fmtStory(n.headline || "")}</strong><br><br>${fmtStory(n.body || "")}</p>
      ${ds.aspect ? `<div class="maehwa-blk maehwa-blk--ben"><div class="maehwa-blk-label">오늘 종합</div><p class="maehwa-hex-desc">${esc(ds.aspect)}</p></div>` : ""}
      ${renderGuaMini(f.gua_flow, "이날의 괘 (時局)")}
      ${calHtml}
      <p class="maehwa-dt-note">음력 ${esc(f.lunar?.label || "")} · 평생 기본수와 세운·월운을 겹친 일운수입니다.</p>
    `;
    bindDailyPanelEvents();
  }

  async function ensureMonthCalendar(y, m) {
    if (
      fortuneMonthly?.solar?.year === y &&
      fortuneMonthly?.solar?.month === m &&
      fortuneMonthly.calendar_days?.length
    ) {
      return fortuneMonthly.calendar_days;
    }
    fortuneMonthly = await fetchFortune("month", y, m, 1);
    return fortuneMonthly.calendar_days || [];
  }

  async function onDailyNav(ev) {
    const btn = ev.currentTarget;
    if (!queryDate) return;
    const { y, m, d } = queryDate;
    if (btn.dataset.today) {
      Object.assign(queryDate, todayYmd());
    } else {
      const delta = Number(btn.dataset.delta) || 0;
      Object.assign(queryDate, shiftDate(y, m, d, delta));
    }
    setStatus("일운을 불러오는 중…");
    try {
      const [dayFortune, calDays] = await Promise.all([
        fetchFortune("day", queryDate.y, queryDate.m, queryDate.d),
        ensureMonthCalendar(queryDate.y, queryDate.m),
      ]);
      fortuneDaily = dayFortune;
      renderDailyPanel(fortuneDaily, calDays);
      setStatus("");
    } catch (e) {
      setStatus(e.message, true);
    }
  }

  async function onDailyCalMonthNav(ev) {
    const btn = ev.currentTarget;
    if (!queryMonth) return;
    if (btn.dataset.calThis) {
      const t = todayYmd();
      queryMonth.y = t.y;
      queryMonth.m = t.m;
    } else {
      const delta = Number(btn.dataset.calDelta) || 0;
      Object.assign(queryMonth, shiftMonth(queryMonth.y, queryMonth.m, delta));
    }
    setStatus("달력을 불러오는 중…");
    try {
      const calDays = await ensureMonthCalendar(queryMonth.y, queryMonth.m);
      if (fortuneDaily) {
        renderDailyPanel(fortuneDaily, calDays);
      }
      setStatus("");
    } catch (e) {
      setStatus(e.message, true);
    }
  }

  function renderMonthlyPanel(f) {
    if (!f || !els.monthly) return;
    const n = f.narrative || {};
    const ms = f.month_suri || {};
    const qy = f.solar?.year;
    const qm = f.solar?.month;

    els.monthly.innerHTML = `
      <div class="maehwa-fortune-nav" data-fortune-nav="month">
        <button type="button" class="btn" data-delta="-1">◀ 전달</button>
        <button type="button" class="btn" data-this-month="1">이번 달</button>
        <span class="maehwa-fortune-date">${qy}년 ${qm}월</span>
        <button type="button" class="btn" data-delta="1">다음 달 ▶</button>
      </div>
      ${f.is_current_month ? '<p class="maehwa-dt-note" style="text-align:center;margin-bottom:0.75rem">📍 이번 달 운세</p>' : ""}
      <div class="maehwa-fortune-hero">
        <div class="mh-num">${ms.num}</div>
        <div class="mh-name">${esc(ms.name)}</div>
        <div class="mh-kw">${esc(ms.kw)}</div>
        <p class="maehwa-dt-note" style="margin-top:0.65rem">올해 ${f.year_suri}수와 겹친 월운</p>
      </div>
      <p class="maehwa-fortune-story"><strong>${fmtStory(n.headline || "")}</strong><br><br>${fmtStory(n.body || "")}</p>
      ${ms.aspect ? `<div class="maehwa-blk maehwa-blk--ben"><div class="maehwa-blk-label">이달 종합</div><p class="maehwa-hex-desc">${esc(ms.aspect)}</p></div>` : ""}
      ${renderGuaMini(f.gua_flow, "이달 개관 괘 (음력 월초)")}
      <p class="maehwa-dt-note" style="margin-top:0.75rem">한 달 전체의 흐름입니다. 날짜별 일운은 「일별 운세」 탭 달력에서 확인하세요.</p>
    `;
    queryMonth = { y: qy, m: qm };
    els.monthly.querySelectorAll("[data-fortune-nav] button").forEach((btn) => {
      btn.addEventListener("click", onMonthNav);
    });
  }

  async function onMonthNav(ev) {
    const btn = ev.currentTarget;
    if (!queryMonth) return;
    if (btn.dataset.thisMonth) {
      const t = todayYmd();
      queryMonth.y = t.y;
      queryMonth.m = t.m;
    } else {
      const delta = Number(btn.dataset.delta) || 0;
      Object.assign(queryMonth, shiftMonth(queryMonth.y, queryMonth.m, delta));
    }
    setStatus("월운을 불러오는 중…");
    try {
      fortuneMonthly = await fetchFortune("month", queryMonth.y, queryMonth.m, 1);
      renderMonthlyPanel(fortuneMonthly);
      setStatus("");
    } catch (e) {
      setStatus(e.message, true);
    }
  }

  async function onCalendarDayClick(ev) {
    const day = Number(ev.currentTarget.dataset.day);
    if (!queryMonth || !day) return;
    queryDate = { y: queryMonth.y, m: queryMonth.m, d: day };
    setStatus("일운을 불러오는 중…");
    try {
      fortuneDaily = await fetchFortune("day", queryDate.y, queryDate.m, queryDate.d);
      const calDays =
        fortuneMonthly?.calendar_days ||
        (await ensureMonthCalendar(queryMonth.y, queryMonth.m));
      renderDailyPanel(fortuneDaily, calDays);
      setStatus("");
    } catch (e) {
      setStatus(e.message, true);
    }
  }

  function renderSynth(d) {
    const gf = d.gua_flow;
    const st = d.synthesis_story || {};
    const sections = (st.sections || [])
      .map(
        (sec) => `<article class="maehwa-story-ch">
          <h3 class="maehwa-story-ch-title"><span class="maehwa-story-ch-icon" aria-hidden="true">${esc(sec.icon || "")}</span> ${esc(sec.title)}</h3>
          <p class="maehwa-story-ch-text">${fmtStory(sec.text)}</p>
        </article>`
      )
      .join("");

    els.synth.innerHTML = `
      <div class="maehwa-story-hero">
        <p class="maehwa-story-headline">${fmtStory(st.headline || d.synthesis)}</p>
        <p class="maehwa-story-opening">${fmtStory(st.opening || "")}</p>
      </div>
      <div class="maehwa-sum-flow maehwa-sum-flow--story">
        <div class="maehwa-sum-box">
          <div class="maehwa-sum-lbl">평생 수</div>
          <div class="maehwa-sum-val">${d.suri.basic_num}</div>
          <div class="maehwa-sum-sub">${esc(d.suri.name)}</div>
        </div>
        <div class="maehwa-sum-arr">→</div>
        <div class="maehwa-sum-box">
          <div class="maehwa-sum-lbl">본괘</div>
          <div class="maehwa-sum-val maehwa-sum-val--sm">${esc(gf.ben.name)}</div>
        </div>
        <div class="maehwa-sum-arr">→</div>
        <div class="maehwa-sum-box">
          <div class="maehwa-sum-lbl">동효</div>
          <div class="maehwa-sum-val maehwa-sum-val--sm">${gf.dong.index}효</div>
        </div>
        <div class="maehwa-sum-arr">→</div>
        <div class="maehwa-sum-box">
          <div class="maehwa-sum-lbl">之卦</div>
          <div class="maehwa-sum-val maehwa-sum-val--sm">${esc(gf.zhi.name)}</div>
        </div>
      </div>
      <div class="maehwa-story-body">${sections}</div>
      <div class="maehwa-story-closing">
        <h3 class="maehwa-story-ch-title">마무리 · 한 줄기로 읽기</h3>
        <p class="maehwa-story-ch-text">${fmtStory(st.closing || "")}</p>
      </div>
      <p class="maehwa-dt-note maehwa-story-meta">
        ${esc(d.user_name)}님 · ${d.calendar_input === "lunar" ? "음력" : "양력"} ·
        본괘 ${esc(gf.ben.ti_yong?.label)} · 之卦 ${esc(gf.zhi.ti_yong?.label)} ·
        올해 ${new Date().getFullYear()}년 ${d.suri.current_year_suri}수
      </p>
    `;
  }

  function renderAll(d) {
    lastData = d;
    const ft = d.fortune || {};
    fortuneDaily = ft.daily || null;
    fortuneMonthly = ft.monthly || null;
    if (fortuneDaily?.solar) {
      queryDate = {
        y: fortuneDaily.solar.year,
        m: fortuneDaily.solar.month,
        d: fortuneDaily.solar.day,
      };
    }
    if (fortuneMonthly?.solar) {
      queryMonth = { y: fortuneMonthly.solar.year, m: fortuneMonthly.solar.month };
    }
    renderFlow(d);
    renderSuri(d);
    renderSynth(d);
    renderDailyPanel(fortuneDaily, fortuneMonthly?.calendar_days);
    renderMonthlyPanel(fortuneMonthly);
    if (els.result) els.result.classList.add("show");
    setTab(activeTab);
  }

  async function calc() {
    const body = collectPayload();
    if (!body.year || !body.month || !body.day) {
      setStatus("출생 정보를 먼저 입력해 주세요.", true);
      return;
    }
    setStatus("매화역수·수리를 계산하는 중…");
    if (els.calcBtn) els.calcBtn.disabled = true;
    try {
      const res = await fetch("/api/maehwa/reading", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || res.statusText || "계산 실패");
      }
      renderAll(data);
      setStatus("");
      if (els.main) {
        els.main.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } catch (e) {
      setStatus(e.message || "오류가 발생했습니다.", true);
    } finally {
      if (els.calcBtn) els.calcBtn.disabled = false;
    }
  }

  async function loadMeta() {
    try {
      const res = await fetch("/api/maehwa/meta");
      if (!res.ok) return;
      const m = await res.json();
      if (els.intro && m.subtitle) {
        els.intro.textContent =
          `${m.title || "매화역수"} — ${m.subtitle}. 위 「출생 정보 입력」을 채운 뒤 「매화역수 계산」을 누르시면 본괘·평생 수리·통합 요약과 함께 일별·월별 운세를 확인할 수 있습니다.`;
      }
    } catch (_) {
      /* ignore */
    }
  }

  function bind() {
    els.rtabs.forEach((btn) => {
      btn.addEventListener("click", () => setTab(btn.dataset.mhTab || "flow"));
    });
    if (els.calcBtn) {
      els.calcBtn.addEventListener("click", calc);
    }
  }

  function init() {
    if (!els.main) return;
    bind();
    loadMeta();
  }

  window.MaehwaApp = { init, calc, renderAll, collectPayload };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
