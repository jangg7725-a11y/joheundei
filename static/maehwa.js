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
    manse: document.getElementById("maehwa-panel-manse"),
  };

  let lastData = null;
  let activeTab = "flow";

  function esc(s) {
    if (s == null) return "";
    const d = document.createElement("div");
    d.textContent = String(s);
    return d.innerHTML;
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

  function renderSynth(d) {
    const gf = d.gua_flow;
    els.synth.innerHTML = `
      <div class="maehwa-summary-box">
        <p>${esc(d.synthesis)}</p>
        <div class="maehwa-sum-flow">
          <div class="maehwa-sum-box">
            <div style="color:#8a6a30;font-size:0.65rem">평생 수</div>
            <div style="font-size:1.4rem;color:#e8c86a;font-weight:700">${d.suri.basic_num}</div>
            <div>${esc(d.suri.name)}</div>
          </div>
          <div class="maehwa-sum-arr">→</div>
          <div class="maehwa-sum-box">
            <div style="color:#8a6a30;font-size:0.65rem">본괘</div>
            <div style="font-size:1rem;color:#f0e8c8">${esc(gf.ben.name)}</div>
          </div>
          <div class="maehwa-sum-arr">→</div>
          <div class="maehwa-sum-box">
            <div style="color:#8a6a30;font-size:0.65rem">동효</div>
            <div style="font-size:1rem;color:#c9a84c">${gf.dong.index}효</div>
          </div>
          <div class="maehwa-sum-arr">→</div>
          <div class="maehwa-sum-box">
            <div style="color:#8a6a30;font-size:0.65rem">之卦</div>
            <div style="font-size:1rem;color:#f0e8c8">${esc(gf.zhi.name)}</div>
          </div>
        </div>
      </div>
      <p class="maehwa-dt-note" style="margin-top:1rem">
        ${esc(d.user_name)}님 · ${d.calendar_input === "lunar" ? "음력" : "양력"} 입력 ·
        체용 ${esc(gf.ben.ti_yong?.label)}
      </p>
    `;
  }

  function renderManse(d) {
    const m = d.manseryeok || {};
    const tabs = (m.placeholder_tabs || [])
      .map((t) => `<span>${esc(t)}</span>`)
      .join("");
    els.manse.innerHTML = `
      <div class="maehwa-manse">
        <h3>${esc(m.label || "만세력")}</h3>
        <p>${esc(m.message)}</p>
        <div class="maehwa-manse-tags">${tabs}</div>
        <p class="maehwa-dt-note" style="margin-top:1.25rem">
          사주 원국·절기·월령·일진·시진과 연동되어 한 화면에서 보실 수 있도록 준비 중입니다.
        </p>
      </div>
    `;
  }

  function renderAll(d) {
    lastData = d;
    renderFlow(d);
    renderSuri(d);
    renderSynth(d);
    renderManse(d);
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
          `${m.title || "매화역수"} — ${m.subtitle}. 위 「출생 정보 입력」을 채운 뒤 「매화역수 계산」을 누르시면 본괘·동효·변괘와 평생 9수를 함께 읽습니다.`;
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
