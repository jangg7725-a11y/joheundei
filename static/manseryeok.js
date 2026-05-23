/* ═══════════════════════════════════════════════════════
   manseryeok.js  ·  萬歲曆 프론트엔드 로직
   FastAPI /api/manseryeok/* 엔드포인트 연동
   ═══════════════════════════════════════════════════════ */

'use strict';

const API = {
  all:      '/api/manseryeok/all',
  search:   '/api/manseryeok/search',
  calendar: '/api/manseryeok/calendar',
  taekil:   '/api/manseryeok/taekil',
  compute:  '/api/manseryeok/compute',
  goonghap: '/api/goonghap',
  saju:     '/api/manseryeok/saju-match',
  item:     (id) => `/api/manseryeok/item/${id}`,
  category: (cat) => `/api/manseryeok/category/${encodeURIComponent(cat)}`,
};

const MS_PROFILE_KEY = 'ms_manseryeok_profile_v1';

/* ── 상태 ────────────────────────────────────────────── */
let _allData   = [];
let _curModal  = null;
let _sajuProfile = null;

/* ── 카테고리 색상 맵 ────────────────────────────────── */
const CAT_CLASS = {
  '역법':'cat-역법','명리':'cat-명리','혼인':'cat-혼인',
  '풍수':'cat-풍수','길흉':'cat-길흉','제례':'cat-제례','기타':'cat-기타'
};
const DIFF_LABEL = { beginner:'입문', intermediate:'중급', advanced:'고급' };
const DIFF_CLASS = { beginner:'diff-beginner', intermediate:'diff-intermediate', advanced:'diff-advanced' };

const MS_GENERIC_BEGINNER = new Set([
  '사주팔자의 기초 이론입니다. 천간·지지·오행의 관계를 이해하면 내 사주를 스스로 분석할 수 있습니다.',
  '포켓박스 사주팔자의 기초 이론입니다. 천간·지지·오행의 관계를 이해하면 내 사주를 스스로 분석할 수 있습니다.',
]);

function msTitle(item) {
  return item.display_title || item.sub_category || item.chapter || '만세력 항목';
}

function msCardDesc(item) {
  if (item.display_card_desc) return item.display_card_desc;
  const beg = (item.beginner_explanation || '').trim();
  if (MS_GENERIC_BEGINNER.has(beg)) return '';
  if (beg) return beg;
  return item.modern_interpretation || item.korean_translation || '';
}

function msModalBeginner(item) {
  const b = item.display_beginner ?? item.beginner_explanation ?? '';
  return MS_GENERIC_BEGINNER.has((b || '').trim()) ? '' : b;
}

function msBodyPrimary(item) {
  return item.display_body_primary
    || [item.korean_translation, item.modern_interpretation].filter(Boolean).join('\n\n');
}

function msOriginal(item) {
  return item.display_original || item.original_text || '';
}

/* ══════════════════════════════════════════════════════
   초기화
══════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  await loadAllData();
  initTabs();
  initSajuPanel();
  initCalendarTab();
  initTaekilTab();
  if (typeof initMsGoonghapTab === 'function') initMsGoonghapTab();
});

async function loadAllData() {
  try {
    const res  = await fetch(API.all);
    const json = await res.json();
    _allData = json.data || [];
  } catch (e) {
    console.error('만세력 데이터 로드 실패:', e);
    _allData = [];
  }
}

/* ══════════════════════════════════════════════════════
   탭 전환
══════════════════════════════════════════════════════ */
function initTabs() {
  const tabs   = document.querySelectorAll('.ms-tab');
  const panels = document.querySelectorAll('.ms-tab-panel');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected','false'); });
      panels.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      tab.setAttribute('aria-selected','true');
      const target = document.getElementById(`tab-${tab.dataset.tab}`);
      if (target) target.classList.add('active');
    });
  });
}

/* ══════════════════════════════════════════════════════
   사주 입력 · 단독 플레이
══════════════════════════════════════════════════════ */
function initSajuPanel() {
  const form = document.getElementById('msSajuForm');
  if (!form) return;

  bindMsSeg('.ms-seg [data-ms-calendar]', 'data-ms-calendar', (v) => {
    document.getElementById('msCalendar').value = v;
    const leapWrap = document.getElementById('msLeapWrap');
    if (leapWrap) leapWrap.classList.toggle('fallback-hidden', v !== 'lunar');
  });
  bindMsSeg('.ms-seg [data-ms-gender]', 'data-ms-gender', (v) => {
    document.getElementById('msGender').value = v;
  });
  bindMsSeg('.ms-seg [data-ms-leap]', 'data-ms-leap', (v) => {
    document.getElementById('msLunarLeap').value = v;
  });

  const hourUnk = document.getElementById('msHourUnknownBtn');
  if (hourUnk) {
    hourUnk.addEventListener('click', () => {
      const on = hourUnk.getAttribute('aria-pressed') !== 'true';
      hourUnk.setAttribute('aria-pressed', on ? 'true' : 'false');
      document.getElementById('msHour').disabled = on;
      document.getElementById('msMinute').disabled = on;
    });
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    runManseryeokCompute();
  });

  try {
    const saved = localStorage.getItem(MS_PROFILE_KEY);
    if (saved) {
      const p = JSON.parse(saved);
      restoreSajuForm(p.form);
      if (p.profile) applySajuProfile(p.profile, { silent: true });
    }
  } catch (_) { /* ignore */ }
}

function bindMsSeg(selector, dataAttr, onPick) {
  document.querySelectorAll(selector).forEach((btn) => {
    btn.addEventListener('click', () => {
      const group = btn.parentElement;
      group.querySelectorAll('.ms-seg-btn').forEach((b) => {
        b.classList.remove('active');
        b.setAttribute('aria-pressed', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-pressed', 'true');
      onPick(btn.getAttribute(dataAttr));
    });
  });
}

function collectSajuFormBody() {
  const calendar = document.getElementById('msCalendar').value;
  const hourUnk = document.getElementById('msHourUnknownBtn')?.getAttribute('aria-pressed') === 'true';
  const body = {
    calendar,
    year: Number(document.getElementById('msYear').value),
    month: Number(document.getElementById('msMonth').value),
    day: Number(document.getElementById('msDay').value),
    hour: hourUnk ? 12 : Number(document.getElementById('msHour').value),
    minute: hourUnk ? 0 : Number(document.getElementById('msMinute').value),
    gender: document.getElementById('msGender').value,
    lunar_leap: calendar === 'lunar' && document.getElementById('msLunarLeap').value === '1',
    user_name: (document.getElementById('msUserName').value || '').trim(),
  };
  if (hourUnk) body.hour_unknown = true;
  return body;
}

function restoreSajuForm(form) {
  if (!form) return;
  document.getElementById('msUserName').value = form.user_name || '';
  document.getElementById('msYear').value = form.year;
  document.getElementById('msMonth').value = form.month;
  document.getElementById('msDay').value = form.day;
  document.getElementById('msHour').value = form.hour ?? 12;
  document.getElementById('msMinute').value = form.minute ?? 0;
  setMsSegValue('[data-ms-calendar]', 'data-ms-calendar', form.calendar || 'solar');
  setMsSegValue('[data-ms-gender]', 'data-ms-gender', form.gender || 'male');
  setMsSegValue('[data-ms-leap]', 'data-ms-leap', form.lunar_leap ? '1' : '0');
  const leapWrap = document.getElementById('msLeapWrap');
  if (leapWrap) leapWrap.classList.toggle('fallback-hidden', form.calendar !== 'lunar');
  const hourUnk = !!form.hour_unknown;
  const btn = document.getElementById('msHourUnknownBtn');
  if (btn) {
    btn.setAttribute('aria-pressed', hourUnk ? 'true' : 'false');
    document.getElementById('msHour').disabled = hourUnk;
    document.getElementById('msMinute').disabled = hourUnk;
  }
}

function setMsSegValue(sel, attr, val) {
  document.querySelectorAll(sel).forEach((b) => {
    const match = b.getAttribute(attr) === val;
    b.classList.toggle('active', match);
    b.setAttribute('aria-pressed', match ? 'true' : 'false');
  });
}

async function runManseryeokCompute() {
  const btn = document.getElementById('msSajuSubmitBtn');
  const body = collectSajuFormBody();
  setMsSajuStatus('사주 계산 중…');
  if (btn) btn.disabled = true;
  try {
    const res = await fetch(API.compute, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) throw new Error(parseApiError(json, res));
    applySajuProfile(json.profile);
    try {
      localStorage.setItem(MS_PROFILE_KEY, JSON.stringify({ form: body, profile: json.profile }));
    } catch (_) { /* ignore */ }
    setMsSajuStatus('');
  } catch (e) {
    setMsSajuStatus(e.message || String(e), true);
  } finally {
    if (btn) btn.disabled = false;
  }
}

function setMsSajuStatus(msg, isError = false) {
  const status = document.getElementById('msSajuStatus');
  if (!status) return;
  const text = msg || '';
  status.textContent = text;
  status.classList.toggle('error', !!isError);
  status.classList.toggle('fallback-hidden', !text);
}

function parseApiError(json, res) {
  let d = json?.detail ?? json?.message ?? res.statusText;
  if (Array.isArray(d)) d = d.map((x) => x.msg || JSON.stringify(x)).join('; ');
  if (d && typeof d === 'object') d = JSON.stringify(d);
  return String(d);
}

function applySajuProfile(profile, opts = {}) {
  _sajuProfile = profile;
  renderSajuSummary(profile);
  renderMsFortune(profile.fortune);
  applyMatchDropdowns(profile.match_params);
  prefillMonthFilters(profile.birth_month_label);
  renderMsIlwoonPane(profile);
  updateTaekilGuide();
  if (!opts.silent) {
    document.getElementById('msSajuSummary')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    setTimeout(() => {
      document.querySelector('[data-tab="calendar"]')?.click();
    }, 400);
  }
}

function renderSajuSummary(p) {
  const box = document.getElementById('msSajuSummary');
  if (!box) return;
  const name = p.user_name ? `${escHtml(p.user_name)}님 · ` : '';
  const solar = p.solar?.label || '';
  const lunar = p.lunar?.label || '';
  const pillars = (p.pillars || []).map((row) => `
    <div class="ms-saju-pillar">
      <div class="lab">${escHtml(row.label)}</div>
      <div class="gz">${escHtml(row.pillar)}</div>
      <div class="sub">${escHtml(row.label_kr)}</div>
    </div>
  `).join('');
  const mp = p.match_params || {};
  const il = p.ilwoon_today || {};
  const sins = (p.sinsal_highlights || []).slice(0, 3).map((s) =>
    `${escHtml(s.신살)}(${escHtml(s.길흉)})`
  ).join(' · ');
  box.innerHTML = `
    <div class="ms-saju-summary-head">
      <h3>${name}일간 ${escHtml(p.day_master)}(${escHtml(p.day_master_kr)}) · ${escHtml(p.day_master_element)}</h3>
      <span class="ms-saju-meta">${escHtml(solar)}</span>
    </div>
    <div class="ms-saju-pillars">${pillars}</div>
    <p class="ms-saju-meta"><strong>음력</strong> ${escHtml(lunar)} · <strong>용신</strong> ${escHtml(p.yongsin?.용신_오행 || '')} · <strong>기신</strong> ${escHtml(p.yongsin?.기신_오행 || '')}</p>
    <p class="ms-saju-meta">${escHtml(p.yongsin?.판단_요약 || '')}</p>
    <p class="ms-saju-meta"><strong>오늘 일운</strong> ${escHtml(il.간지 || '')} ${escHtml(il.간지한글 || '')} — ${escHtml(il.길흉등급 || '')} · ${escHtml((il.한줄판정 || '').slice(0, 80))}</p>
    ${sins ? `<p class="ms-saju-meta"><strong>신살</strong> ${sins}</p>` : ''}
  `;
  box.classList.remove('fallback-hidden');
}

function renderMsFortune(fortune) {
  const wrap = document.getElementById('msFortuneWrap');
  if (!wrap) return;
  if (!fortune?.sewoon) {
    wrap.innerHTML = '';
    wrap.classList.add('fallback-hidden');
    return;
  }

  const se = fortune.sewoon;
  const mo = fortune.monthly || {};
  const cy = fortune.center_year || se.year;

  const domainHtml = (se.domains || []).map((d) => `
    <span class="ms-fort-domain" title="${escHtml(d.label)}">
      <span class="ms-fort-domain-lab">${escHtml(d.label)}</span>
      <span class="ms-fort-domain-stars">${escHtml(d.bar || '')}</span>
    </span>
  `).join('');

  const luckKw = Array.isArray(se.luck_keywords) ? se.luck_keywords.slice(0, 4) : [];
  const cautKw = Array.isArray(se.caution_keywords) ? se.caution_keywords.slice(0, 4) : [];
  const kwHtml = [
    luckKw.length ? `<p class="ms-fort-kw good">✅ ${luckKw.map((k) => escHtml(String(k))).join(' · ')}</p>` : '',
    cautKw.length ? `<p class="ms-fort-kw caution">⚠️ ${cautKw.map((k) => escHtml(String(k))).join(' · ')}</p>` : '',
  ].join('');

  const monthCells = (mo.months || []).map((m) => `
    <div class="ms-fort-month ms-fort-month--${m.grade_class || 'mid'}" title="${escHtml(m.summary || '')}">
      <div class="ms-fort-month-emo">${escHtml(m.emoji || '⚪')}</div>
      <div class="ms-fort-month-num">${m.slot}월</div>
      <div class="ms-fort-month-gz">${escHtml(m.ganzhi || '')}</div>
      <div class="ms-fort-month-grade">${escHtml(m.grade || '')}</div>
    </div>
  `).join('');

  const bestLine = (mo.best_months || []).slice(0, 3).map((b) =>
    `${b.절월번호}월(${escHtml(b.월주간지 || '')})`
  ).join(', ');
  const badLine = (mo.caution_months || []).slice(0, 3).map((b) =>
    `${b.절월번호}월(${escHtml(b.월주간지 || '')})`
  ).join(', ');

  const storyHtml = (se.story || []).map((p) =>
    `<p class="ms-fort-story-p">${escHtml(p)}</p>`
  ).join('');

  const pos = se.position || {};
  const posIntro = (pos.intro || []).map((p) => `<p class="ms-fort-pos-p">${escHtml(p)}</p>`).join('');
  const posImpacts = (pos.impacts || []).map((p) => `<li>${escHtml(p)}</li>`).join('');
  const posAssign = (pos.assignments || []).map((a) => `
    <div class="ms-fort-assign-card">
      <h5>${escHtml(a.title || '')}</h5>
      <p class="ms-fort-assign-meta"><strong>맞물림</strong> ${escHtml(a.status || '')}</p>
      <p class="ms-fort-assign-meta">${escHtml(a.role || '')}</p>
      <p class="ms-fort-assign-pred">${escHtml(a.prediction || '')}</p>
    </div>
  `).join('');

  const phasesHtml = (se.phases || []).map((ph) => `
    <div class="ms-fort-phase ms-fort-phase--${ph.grade_class || 'mid'}">
      <div class="ms-fort-phase-head">
        <strong>${escHtml(ph.label || '')}</strong>
        <span class="ms-fort-phase-period">${escHtml(ph.period || '')}</span>
        <span class="ms-fort-phase-badge">${escHtml(ph.grade || '')}</span>
      </div>
      ${(ph.paragraphs || []).map((p) => `<p class="ms-fort-phase-p">${escHtml(p)}</p>`).join('')}
      ${(ph.highlight_months || []).length
        ? `<p class="ms-fort-phase-hl">💡 ${ph.highlight_months.map((m) => escHtml(m)).join(' · ')}</p>` : ''}
    </div>
  `).join('');

  const eventsHtml = (se.event_notes || []).length
    ? `<ul class="ms-fort-events">${(se.event_notes || []).map((e) => `<li>${escHtml(e)}</li>`).join('')}</ul>` : '';

  wrap.innerHTML = `
    <section class="ms-fortune-sewoon">
      <h3 class="ms-fort-title">${cy}년 총운 <span class="han-inline">(세운 ${escHtml(se.pillar || '')})</span></h3>
      <div class="ms-fort-hero ms-fort-hero--${se.grade_class || 'mid'}">
        <span class="ms-fort-grade-badge">${escHtml(se.grade || '')}</span>
        <span class="ms-fort-stars">${escHtml(se.stars_bar || '')}</span>
        <span class="ms-fort-pillar-kr">${escHtml(se.pillar_kr || '')}</span>
        ${se.nayin ? `<span class="ms-fort-nayin">${escHtml(se.nayin)}</span>` : ''}
      </div>
      <p class="ms-fort-sip">천간 십신 <strong>${escHtml(se.sip_gan || '')}</strong> · 지지 <strong>${escHtml(se.sip_zhi || '')}</strong></p>
      <p class="ms-fort-headline">${escHtml(se.headline || '')}</p>
      ${domainHtml ? `<div class="ms-fort-domains">${domainHtml}</div>` : ''}
      ${kwHtml}
      ${storyHtml ? `<div class="ms-fort-story">${storyHtml}</div>` : ''}
      <p class="ms-fort-closing">${escHtml(se.closing || '')}</p>
      <details class="ms-fort-details" open>
        <summary>📖 올해 세운이 사주에 놓이는 위치·궁별 배당</summary>
        <div class="ms-fort-details-body">
          ${posIntro}
          ${posImpacts ? `<ul class="ms-fort-impact-list">${posImpacts}</ul>` : ''}
          ${posAssign ? `<div class="ms-fort-assign-grid">${posAssign}</div>` : ''}
          ${eventsHtml}
        </div>
      </details>
      <h4 class="ms-fort-subtitle">초 · 중 · 후 — 한 해 흐름</h4>
      <div class="ms-fort-phases">${phasesHtml}</div>
      ${se.ipchun_note ? `<p class="ms-fort-note">${escHtml(se.ipchun_note)}</p>` : ''}
    </section>
    <section class="ms-fortune-monthly">
      <h3 class="ms-fort-title">${cy}년 월별 운세</h3>
      <p class="ms-fort-note">${escHtml(mo.slot_note || '절기 기준 월(입춘부터 1월)입니다.')}</p>
      <div class="ms-fort-month-strip">${monthCells}</div>
      ${mo.first_half ? `<p class="ms-fort-half">📈 ${escHtml(mo.first_half)}</p>` : ''}
      ${mo.second_half ? `<p class="ms-fort-half">📉 ${escHtml(mo.second_half)}</p>` : ''}
      ${bestLine ? `<p class="ms-fort-tip good">💚 좋은 흐름: ${bestLine}</p>` : ''}
      ${badLine ? `<p class="ms-fort-tip caution">🔴 조심할 달: ${badLine}</p>` : ''}
    </section>
    <p class="ms-fort-disclaimer">참고용 안내입니다. 중요한 결정은 여러 정보를 함께 보세요.</p>
  `;
  wrap.classList.remove('fallback-hidden');
}

function goToSajuMatchTab() {
  const tab = document.querySelector('[data-tab="saju"]');
  if (tab) tab.click();
  const target = document.getElementById('tab-saju') || document.getElementById('sajuGrid');
  if (target) {
    requestAnimationFrame(() => {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }
}

function applyMatchDropdowns(mp) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el && val) el.value = val;
  };
  set('matchShinsin', mp.shinsin);
  set('matchSinsal', mp.sinsal);
  set('matchGyeok', mp.gyeokguk);
  set('matchOhaeng', mp.ohaeng);
}

function renderSajuBrief(brief) {
  const box = document.getElementById('sajuBriefBox');
  if (!box || !brief) return;
  const cards = (brief.param_cards || []).map((c) => `
    <div class="ms-param-card">
      <span class="ms-param-label">${escHtml(c.label)}</span>
      <strong class="ms-param-term">${escHtml(c.term)}</strong>
      <p>${escHtml(c.plain)}</p>
    </div>
  `).join('');
  box.innerHTML = `
    <h3 class="ms-brief-head">${escHtml(brief.headline || '')}</h3>
    <p class="ms-brief-lead">${escHtml(brief.lead || '')}</p>
    ${cards ? `<div class="ms-param-grid">${cards}</div>` : ''}
    <p class="ms-brief-note">${escHtml(brief.matched_note || '')}</p>
  `;
  box.classList.remove('fallback-hidden');
}

function renderInsightCard(ins) {
  const evs = (ins.events || []).map((e) =>
    `<span class="ms-insight-ev">${escHtml(e)}</span>`
  ).join('');
  return `
    <article class="ms-insight-card">
      <span class="ms-insight-theme">${escHtml(ins.theme || '')}</span>
      <h4 class="ms-insight-title">${escHtml(ins.title || '')}</h4>
      <p class="ms-insight-summary">${escHtml(ins.summary || '')}</p>
      <p class="ms-insight-why">💡 ${escHtml(ins.why || '')}</p>
      <p class="ms-insight-tip">✅ ${escHtml(ins.tip || '')}</p>
      ${evs ? `<div class="ms-insight-evs">${evs}</div>` : ''}
    </article>
  `;
}

function renderSajuInsights(insights, docs) {
  const grid = document.getElementById('sajuGrid');
  const refWrap = document.getElementById('sajuRefWrap');
  const refGrid = document.getElementById('sajuRefGrid');
  if (!grid) return;

  const groups = insights?.groups || [];
  const items = insights?.items || [];

  if (!items.length) {
    grid.innerHTML = '<div class="ms-empty">아직 연결된 안내가 없습니다. 상단에서 사주를 계산해 주세요.</div>';
    if (refWrap) refWrap.classList.add('fallback-hidden');
    return;
  }

  let html = '';
  if (groups.length > 1) {
    html = groups.map((g) => `
      <section class="ms-insight-group">
        <h3 class="ms-insight-group-title">${escHtml(g.theme)}</h3>
        <div class="ms-insight-group-list">
          ${(g.items || []).map((ins) => renderInsightCard(ins)).join('')}
        </div>
      </section>
    `).join('');
  } else {
    html = `<div class="ms-insight-group-list">${items.map((ins) => renderInsightCard(ins)).join('')}</div>`;
  }
  grid.innerHTML = html;

}

function renderSajuMatchedDocs(_p) {
  /* 내 사주 안내 탭 숨김 — API 데이터는 유지, UI는 추후 운세 개편 시 사용 */
}

function prefillMonthFilters(monthLabel) {
  if (!monthLabel) return;
  const taekilMonth = document.getElementById('taekilMonth');
  if (taekilMonth) taekilMonth.value = monthLabel;
}

/* ══════════════════════════════════════════════════════
   TAB 1: 일운·달력 (KT 사주 품 일운 UI)
══════════════════════════════════════════════════════ */
function initCalendarTab() {
  bindMsIlwoonCollapse();
  renderMsIlwoonPane(_sajuProfile);
}

function bindMsIlwoonCollapse() {
  const det = document.getElementById('msIlwoonCollapse');
  if (!det || det.dataset.bound) return;
  det.dataset.bound = '1';
  const hint = document.getElementById('msIlwoonCollapseHint');
  const syncHint = () => {
    if (hint) hint.textContent = det.open ? '접기' : '펼치기';
  };
  det.addEventListener('toggle', () => {
    syncHint();
    rememberMsIlwoonOpen();
  });
  syncHint();
}

function setMsIlwoonCollapseVisible(show, open = true) {
  const det = document.getElementById('msIlwoonCollapse');
  const empty = document.getElementById('msIlwoonEmpty');
  if (empty) empty.classList.toggle('fallback-hidden', !!show);
  if (!det) return;
  det.hidden = !show;
  if (show) {
    const saved = sessionStorage.getItem('ms_ilwoon_open');
    det.open = saved === null ? open : saved === '1';
    bindMsIlwoonCollapse();
    const hint = document.getElementById('msIlwoonCollapseHint');
    if (hint) hint.textContent = det.open ? '접기' : '펼치기';
  }
}

function rememberMsIlwoonOpen() {
  const det = document.getElementById('msIlwoonCollapse');
  if (det && !det.hidden) {
    try {
      sessionStorage.setItem('ms_ilwoon_open', det.open ? '1' : '0');
    } catch (_) { /* ignore */ }
  }
}

function msTodayISO() {
  const d = new Date();
  const p = (x) => String(x).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function renderMsIlwoonPane(profile) {
  const pane = document.getElementById('msIlwoonPane');
  const guide = document.getElementById('msIlwoonGuide');
  if (!pane) return;

  const pack = profile?.ilwoon;
  const today = pack?.['오늘'];
  if (!today) {
    setMsIlwoonCollapseVisible(false);
    pane.innerHTML = '';
    if (guide) {
      guide.innerHTML = '상단에서 <strong>사주 계산</strong>을 하면 오늘 일진·시간대 운세·이번 주·이번 달 달력이 표시됩니다.';
    }
    return;
  }
  setMsIlwoonCollapseVisible(true, true);

  const isoToday = msTodayISO();
  const name = profile.user_name ? `${escHtml(profile.user_name)}님 · ` : '';
  if (guide) {
    guide.textContent = `${name}사주에 맞춘 오늘 일운과 이번 달 일진 달력입니다.`;
  }

  const detHead = today['오늘_일진_상세'];
  const subExtra = detHead?.['오늘의_십신'] ? ` · 십신 ${escHtml(detHead['오늘의_십신'])}` : '';
  const stems = Array.isArray(detHead?.['천간_원국_메모'])
    ? detHead['천간_원국_메모'].map((s) => escHtml(String(s))).join(' · ')
    : '';

  let hourHtml = '';
  const hours = today['시간대별_운세'];
  if (Array.isArray(hours) && hours.length) {
    const items = hours.map((h) => {
      const gh = escHtml(h['길흉'] || '');
      const ghCls = gh === '길' ? 'ms-il-gh-good' : gh === '흉' ? 'ms-il-gh-bad' : 'ms-il-gh-mid';
      return `<li><strong>${escHtml(h['시지'] || '')}시 (${escHtml(h['시간대'] || '')})</strong> <span class="${ghCls}">[${gh}]</span> ${escHtml(h['시주간지'] || '')}·${escHtml(h['시간천간십신'] || '')} — ${escHtml(h['한줄'] || '')}</li>`;
    }).join('');
    hourHtml = `<h4 class="ms-il-section-title">오늘 시간대별 운세 (十二時)</h4><ul class="ms-il-hour-list">${items}</ul>`;
  }

  let recHtml = '';
  const rec = today['오늘_추천행동'];
  if (rec && typeof rec === 'object') {
    const luckNums = Array.isArray(rec['행운_숫자']) ? rec['행운_숫자'].join(', ') : '';
    const goodLi = (rec['하면_좋은_일'] || []).map((x) => `<li>${escHtml(String(x))}</li>`).join('');
    const badLi = (rec['피해야_할_일'] || []).map((x) => `<li>${escHtml(String(x))}</li>`).join('');
    recHtml = `
      <div class="ms-il-rec-grid">
        <div class="ms-il-rec-card ms-il-rec-good"><h5>하면 좋은 일</h5><ul>${goodLi}</ul></div>
        <div class="ms-il-rec-card ms-il-rec-bad"><h5>피해야 할 일</h5><ul>${badLi}</ul></div>
      </div>
      <p class="ms-il-luck">행운 방향·색상·숫자: <strong>${escHtml(rec['행운_방향'] || '—')}</strong> · ${escHtml(rec['행운_색상'] || '—')} · <strong>${escHtml(luckNums || '—')}</strong></p>`;
  }

  const weekPack = pack['이번주'];
  const weekCells = (weekPack?.일자별 || []).map((d) => {
    const isTd = (d['양력문자열'] || '') === isoToday;
    const color = d['표시색'];
    const cls = [
      'ms-il-week-cell',
      isTd ? 'ms-il-week-today' : '',
      color === 'green' ? 'ms-il-week-good' : '',
      color === 'red' ? 'ms-il-week-bad' : '',
    ].filter(Boolean).join(' ');
    const prev = d['미리보기'] || {};
    return `<div class="${cls}" title="${escHtml(d['한줄판정'] || '')}">
      <div class="ms-il-week-emo">${escHtml(prev['이모지등급'] || '')}</div>
      <div class="ms-il-week-dow">${escHtml(d['요일한글'] || '')}</div>
      <div class="ms-il-week-dom">${d['일'] != null ? escHtml(String(d['일'])) : ''}</div>
      <div class="ms-il-week-gz">${escHtml(d['간지'] || '')}</div>
      <div class="ms-il-week-hint">${escHtml(prev['핵심한마디'] || d['한줄판정'] || '')}</div>
    </div>`;
  }).join('');

  const mo = pack['이번달'];
  const wdays = ['월', '화', '수', '목', '금', '토', '일'];
  let calRows = '';
  (mo?.달력 || []).forEach((week) => {
    let cells = '';
    week.forEach((cell) => {
      if (cell['패딩']) {
        cells += `<div class="ms-il-cal-cell ms-il-cal-pad">${cell['일'] ?? ''}</div>`;
        return;
      }
      const cls = [
        'ms-il-cal-cell',
        cell['표시색'] === 'green' ? 'ms-il-cal-good' : '',
        cell['표시색'] === 'red' ? 'ms-il-cal-bad' : '',
        (cell['양력문자열'] || '') === isoToday ? 'ms-il-cal-today' : '',
      ].filter(Boolean).join(' ');
      const markers = cell['달력_표시'] || {};
      const badgeStr = [...(markers['길표시'] || []), ...(markers['흉경고'] || [])].join('');
      const tip = [cell['한줄판정'], ...(markers['길표시'] || []), ...(markers['흉경고'] || [])].filter(Boolean).join(' | ');
      cells += `<div class="${cls}" title="${escHtml(tip)}"><span class="ms-il-cal-dom">${cell['일'] ?? ''}</span><span class="ms-il-cal-badges">${escHtml(badgeStr)}</span></div>`;
    });
    calRows += `<div class="ms-il-cal-row">${cells}</div>`;
  });

  const detailHtml = detHead ? `
    <div class="ms-il-detail">
      <h5>오늘 일진 상세</h5>
      <p>${escHtml(detHead['내러티브'] || '')}</p>
      ${stems ? `<p class="ms-il-detail-stems">${stems}</p>` : ''}
    </div>` : '';

  pane.innerHTML = `
    ${pack['안내'] ? `<p class="ms-il-note">${escHtml(pack['안내'])}</p>` : ''}
    <div class="ms-il-hero">
      <div class="ms-il-hero-date">${escHtml(today['양력문자열'] || isoToday)} · ${escHtml(today['요일한글'] || '')}요일</div>
      <div class="ms-il-hero-gz">${escHtml(today['간지'] || '')}</div>
      <div class="ms-il-hero-sub">${escHtml(today['간지한글'] || '')} · 길흉등급 ${escHtml(today['길흉등급'] || '')} (${escHtml(today['표시색한글'] || '')})${subExtra}</div>
    </div>
    <p class="ms-il-quote">${escHtml(today['한줄판정'] || '')}</p>
    ${detailHtml}
    ${hourHtml}
    ${recHtml}
    <div class="ms-il-week">
      <h4 class="ms-il-section-title">이번 주 미리보기 (월~일)</h4>
      <div class="ms-il-week-strip">${weekCells}</div>
    </div>
    <div class="ms-il-cal-section">
      <h4 class="ms-il-section-title">이번 달 일진 달력 (${mo?.연 ?? ''}.${String(mo?.월 ?? '').padStart(2, '0')})</h4>
      <div class="ms-il-cal-grid">
        <div class="ms-il-cal-row ms-il-cal-head">${wdays.map((w) => `<div>${w}</div>`).join('')}</div>
        ${calRows}
      </div>
    </div>`;
}

/* ══════════════════════════════════════════════════════
   TAB 2: 택일 (만세력 宜·忌 계산)
══════════════════════════════════════════════════════ */
function initTaekilTab() {
  const eventSel = document.getElementById('taekilEvent');
  const monthSel = document.getElementById('taekilMonth');
  if (eventSel) eventSel.addEventListener('change', resetTaekilResults);
  if (monthSel) monthSel.addEventListener('change', resetTaekilResults);
  updateTaekilGuide();
}

function resetTaekilResults() {
  const goodEl = document.getElementById('taekilGoodList');
  const badEl = document.getElementById('taekilBadList');
  const sumEl = document.getElementById('taekilSummary');
  if (goodEl) {
    goodEl.dataset.loaded = '';
    goodEl.innerHTML = '<div class="ms-empty">행사·월을 선택한 뒤 「택일 계산」을 눌러 주세요.</div>';
  }
  if (badEl) badEl.innerHTML = '';
  if (sumEl) sumEl.style.display = 'none';
}

function updateTaekilGuide() {
  const guide = document.getElementById('taekilGuide');
  if (!guide) return;
  if (!_sajuProfile) {
    guide.innerHTML = '먼저 상단에서 <strong>사주 계산</strong>을 해 주세요.';
    return;
  }
  const name = _sajuProfile.user_name ? `${escHtml(_sajuProfile.user_name)}님 · ` : '';
  guide.innerHTML =
    `${name}<strong>행사 유형</strong>과 <strong>달(1~12월)</strong>을 고른 뒤 「택일 계산」을 누르면 그 달의 길한 날·피할 날만 표시됩니다.`;
}

function taekilPrerequisiteMessage() {
  if (!_sajuProfile) {
    return '먼저 상단에서 생년월일을 입력하고 「사주 계산」을 눌러 주세요.';
  }
  const month = document.getElementById('taekilMonth')?.value || '';
  if (!month) {
    return '행사 유형과 달(1~12월)을 선택해 주세요.';
  }
  return '';
}

const TAEKIL_GRADE_CLASS = {
  '대길': 'tk-grade-best',
  '길': 'tk-grade-good',
  '평': 'tk-grade-mid',
  '흉': 'tk-grade-bad',
  '대흉': 'tk-grade-worst',
};

async function runTaekil() {
  const event = document.getElementById('taekilEvent')?.value || '결혼';
  const month = document.getElementById('taekilMonth')?.value || '';
  const goodEl = document.getElementById('taekilGoodList');
  const badEl  = document.getElementById('taekilBadList');
  const sumEl  = document.getElementById('taekilSummary');

  const prereq = taekilPrerequisiteMessage();
  if (prereq) {
    goodEl.innerHTML = `<div class="ms-empty">${escHtml(prereq)}</div>`;
    badEl.innerHTML = '';
    if (sumEl) sumEl.style.display = 'none';
    return;
  }

  goodEl.innerHTML = '<div class="ms-loading">해당 월 길일·흉일 계산 중…</div>';
  badEl.innerHTML = '';

  try {
    const params = new URLSearchParams({ event, month, limit: '30' });
    const res  = await fetch(`${API.taekil}?${params}`);
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || '택일 계산 실패');

    sumEl.style.display = 'block';
    sumEl.textContent =
      `${json.event_label || event} · ${month} — ` +
      `길한 날 ${json.good_days.length}건 · 피할 날 ${json.avoid_days.length}건`;

    goodEl.dataset.loaded = '1';
    goodEl.innerHTML = json.good_days.length
      ? renderTaekilDaysGrouped(json.good_days, true, month)
      : '<div class="ms-empty">이 달에는 조건에 맞는 길일이 없습니다. 다른 월이나 행사를 바꿔 보세요.</div>';

    badEl.innerHTML = json.avoid_days.length
      ? renderTaekilDaysGrouped(json.avoid_days, false, month)
      : '<div class="ms-empty">이 달에 특별히 피할 만한 날은 없습니다.</div>';
  } catch (e) {
    goodEl.innerHTML = `<div class="ms-empty">오류: ${escHtml(String(e.message || e))}</div>`;
    sumEl.style.display = 'none';
  }
}

function filterTaekilMonth(month) {
  const sel = document.getElementById('taekilMonth');
  if (sel) sel.value = month || '';
  runTaekil();
}

function renderTaekilMonthOverview(overview, show) {
  const box = document.getElementById('taekilMonthOverview');
  const grid = document.getElementById('taekilMonthGrid');
  const line = document.getElementById('taekilOverviewLine');
  const picks = document.getElementById('taekilOverviewPicks');
  if (!box || !grid) return;

  if (!show || !overview?.months?.length) {
    box.hidden = true;
    return;
  }

  box.hidden = false;
  if (line) line.textContent = overview.summary_line || '';
  if (picks) {
    const best = (overview.best_months || []).map((m) => `<span class="pick-good">${escHtml(m)}</span>`).join('');
    const avoid = (overview.avoid_months || []).map((m) => `<span class="pick-bad">${escHtml(m)}</span>`).join('');
    picks.innerHTML =
      (best ? `<span class="pick-label">추천 달</span> ${best}` : '') +
      (avoid ? `<span class="pick-label">주의 달</span> ${avoid}` : '');
  }

  grid.innerHTML = overview.months.map((m) => {
    const cls = m.has_data ? `ms-month-cell tk-month-${m.rating_class || 'mid'}` : 'ms-month-cell tk-month-empty';
    const stats = m.has_data
      ? `길 ${m.good_count} · 흉 ${m.avoid_count}`
      : '달력 없음';
    const sub = m.has_data && m.best_day
      ? escHtml(String(m.best_day).replace(/^\d{1,2}월\s*/, '').slice(0, 18))
      : '';
    return `
      <button type="button" class="${cls}" role="listitem"
        ${m.has_data ? `onclick="filterTaekilMonth('${escHtml(m.month)}')"` : 'disabled'}
        aria-label="${escHtml(m.month)} ${escHtml(m.month_rating)}">
        <span class="ms-month-name">${escHtml(m.month)}</span>
        <span class="ms-month-rating">${escHtml(m.month_rating)}</span>
        <span class="ms-month-stats">${escHtml(stats)}</span>
        ${sub ? `<span class="ms-month-best">${sub}</span>` : ''}
      </button>`;
  }).join('');
}

function _taekilMonthSortKey(month) {
  const m = String(month || '').match(/^(\d{1,2})월/);
  return m ? parseInt(m[1], 10) : 99;
}

function renderTaekilDaysGrouped(days, isGood, monthFilter) {
  if (monthFilter) {
    return days.map((d) => renderTaekilDayCard(d, isGood)).join('');
  }
  const groups = {};
  days.forEach((d) => {
    const m = (d.calendar_month || '기타').trim();
    if (!groups[m]) groups[m] = [];
    groups[m].push(d);
  });
  const keys = Object.keys(groups).sort((a, b) => _taekilMonthSortKey(a) - _taekilMonthSortKey(b));
  if (keys.length <= 1) {
    return days.map((d) => renderTaekilDayCard(d, isGood)).join('');
  }
  return keys.map((m) => `
    <section class="ms-taekil-month-group">
      <h4 class="ms-taekil-month-heading">${escHtml(m)}</h4>
      ${groups[m].map((d) => renderTaekilDayCard(d, isGood)).join('')}
    </section>
  `).join('');
}

function renderTaekilDayCard(d, isGood) {
  const cls = TAEKIL_GRADE_CLASS[d.grade] || 'tk-grade-mid';
  const hitStr = isGood
    ? (d.yi_display || (d.yi_hits_kr || d.yi_hits || []).join(' · ') || d.yi_raw?.slice(0, 48) || '')
    : (d.ji_display || (d.ji_hits_kr || d.ji_hits || []).join(' · ') || d.ji_raw?.slice(0, 48) || '');
  const src = escHtml((d.source_display || d.source_chapter || '').slice(0, 48));
  let dayLabel = d.day_label_kr || d.day_label || '';
  const calMonth = (d.calendar_month || '').trim();
  if (calMonth && dayLabel && !dayLabel.startsWith(calMonth)) {
    dayLabel = `${calMonth} ${dayLabel}`;
  }
  const ganjiLine = d.ganji_display || d.ganji_kr || d.ganji || '';
  const yiJiTag = isGood ? '의(宜)' : '기(忌)';
  return `
    <article class="ms-taekil-day ${cls}" role="button" tabindex="0"
      onclick="openModal('${escHtml(d.source_id || '')}')"
      onkeydown="if(event.key==='Enter')openModal('${escHtml(d.source_id || '')}')">
      <div class="ms-taekil-day-head">
        <span class="ms-taekil-day-label">${escHtml(dayLabel)}</span>
        <span class="ms-taekil-ganji">${escHtml(ganjiLine)}</span>
        <span class="ms-taekil-grade">${escHtml(d.grade)}</span>
      </div>
      <p class="ms-taekil-verdict">${escHtml(d.verdict)}</p>
      <p class="ms-taekil-hits"><span class="ms-yiji-tag">${yiJiTag}</span> ${escHtml(hitStr)}</p>
      <p class="ms-taekil-src">${src}</p>
    </article>
  `;
}

/* ══════════════════════════════════════════════════════
   TAB: 찾아보기
══════════════════════════════════════════════════════ */
function initSearchEnter() {
  document.getElementById('searchKeyword').addEventListener('keydown', e => {
    if (e.key === 'Enter') doSearch();
  });
}

async function doSearch() {
  const keyword    = document.getElementById('searchKeyword').value.trim();
  const category   = document.getElementById('searchCategory').value;
  const event      = document.getElementById('searchEvent').value;
  const difficulty = document.getElementById('searchDifficulty').value;

  const grid = document.getElementById('searchGrid');
  const info = document.getElementById('searchInfo');
  grid.innerHTML = '<div class="ms-loading">검색 중…</div>';
  info.style.display = 'none';

  const params = new URLSearchParams();
  if (keyword)    params.set('keyword',    keyword);
  if (category)   params.set('category',   category);
  if (event)      params.set('event',      event);
  if (difficulty) params.set('difficulty', difficulty);
  params.set('limit', '50');

  try {
    const res  = await fetch(`${API.search}?${params}`);
    const json = await res.json();

    const condParts = [];
    if (keyword)    condParts.push(`키워드 "${keyword}"`);
    if (category)   condParts.push(`카테고리 ${category}`);
    if (event)      condParts.push(`행사 ${event}`);
    if (difficulty) condParts.push(`난이도 ${DIFF_LABEL[difficulty]}`);

    if (condParts.length) {
      info.textContent = `${condParts.join(' · ')} — 총 ${json.total}건 검색됨`;
      info.style.display = 'block';
    }

    renderCards(grid, json.data, '');
  } catch (e) {
    grid.innerHTML = '<div class="ms-empty">검색 중 오류가 발생했습니다.</div>';
  }
}

/* ══════════════════════════════════════════════════════
   TAB 3: 사주 매칭
══════════════════════════════════════════════════════ */
async function doSajuMatch() {
  const shinsin  = document.getElementById('matchShinsin').value;
  const sinsal   = document.getElementById('matchSinsal').value;
  const gyeokguk = document.getElementById('matchGyeok').value;
  const ohaeng   = document.getElementById('matchOhaeng').value;

  const grid = document.getElementById('sajuGrid');
  const info = document.getElementById('sajuInfo');
  grid.innerHTML = '<div class="ms-loading">안내 정리 중…</div>';
  info.style.display = 'none';

  if (!shinsin && !sinsal && !gyeokguk && !ohaeng) {
    grid.innerHTML = '<div class="ms-empty">고급 모드에서는 최소 하나의 조건을 선택해 주세요. 보통은 상단 「사주 계산」만으로 충분합니다.</div>';
    return;
  }

  const params = new URLSearchParams();
  if (shinsin)  params.set('shinsin',  shinsin);
  if (sinsal)   params.set('sinsal',   sinsal);
  if (gyeokguk) params.set('gyeokguk', gyeokguk);
  if (ohaeng)   params.set('ohaeng',   ohaeng);
  params.set('limit', '20');

  try {
    const res  = await fetch(`${API.saju}?${params}`);
    const json = await res.json();

    if (json.brief) renderSajuBrief(json.brief);
    if (info) {
      info.style.display = 'block';
      info.textContent = json.brief?.matched_note
        || `쉬운 안내 ${json.total}건을 정리했습니다.`;
    }
    renderSajuInsights(json.insights, json.data || []);
  } catch (e) {
    grid.innerHTML = '<div class="ms-empty">안내를 불러오지 못했습니다.</div>';
  }
}

/* ══════════════════════════════════════════════════════
   TAB 4: 카테고리
══════════════════════════════════════════════════════ */
function initCategoryTab() {
  // 카운트 배지 업데이트
  updateCategoryCount();

  // 카테고리 버튼
  document.querySelectorAll('.ms-cat-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ms-cat-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      loadCategory(btn.dataset.cat);
    });
  });

  // 초기 전체 로드
  loadCategory('');
}

function updateCategoryCount() {
  const cats = ['역법','명리','혼인','풍수','길흉','제례'];
  const total = document.getElementById('cnt-all');
  if (total) total.textContent = _allData.length;

  cats.forEach(cat => {
    const el = document.getElementById(`cnt-${cat}`);
    if (el) el.textContent = _allData.filter(d => d.category === cat).length;
  });
}

function loadCategory(cat) {
  const grid = document.getElementById('categoryGrid');
  const data = cat
    ? _allData.filter(d => d.category === cat)
    : _allData;

  // priority_rank 높은 순 정렬
  const sorted = [...data].sort((a,b) =>
    (b.practical?.priority_rank || 0) - (a.practical?.priority_rank || 0)
  );

  renderCards(grid, sorted, '');
}

/* ══════════════════════════════════════════════════════
   공통: 카드 렌더
══════════════════════════════════════════════════════ */
function renderCards(container, items, _infoText) {
  if (!items || !items.length) {
    container.innerHTML = '<div class="ms-empty">해당하는 항목이 없습니다.</div>';
    return;
  }

  container.innerHTML = items.map(item => buildCard(item)).join('');

  // 카드 클릭 이벤트
  container.querySelectorAll('.ms-card').forEach(card => {
    card.addEventListener('click', () => openModal(card.dataset.id));
  });
}

function buildCard(item) {
  const catCls  = CAT_CLASS[item.category] || 'cat-기타';
  const diffCls = DIFF_CLASS[item.difficulty_level] || '';
  const diffLbl = DIFF_LABEL[item.difficulty_level] || item.difficulty_level;

  const tags = (item.keywords || []).slice(0, 3).map(k =>
    `<span class="ms-card-tag">${escHtml(k)}</span>`
  ).join('');

  const title = msTitle(item);
  const desc = msCardDesc(item);

  const events = (item.practical?.applicable_events || []).slice(0,3).join(' · ');

  return `
<article class="ms-card" data-id="${escHtml(item.id)}" tabindex="0"
  role="button" aria-label="${escHtml(title)}">
  <span class="ms-card-cat ${catCls}">${item.category}</span>
  <h3 class="ms-card-title">${escHtml(title)}</h3>
  ${desc ? `<p class="ms-card-desc">${escHtml(desc)}</p>` : ''}
  ${events ? `<p style="font-size:0.75rem;color:var(--ms-gold);margin:0 0 8px">📌 ${escHtml(events)}</p>` : ''}
  <div class="ms-card-footer">
    <span class="ms-card-diff ${diffCls}">${diffLbl}</span>
    <div class="ms-card-tags">${tags}</div>
    <span class="ms-card-more">자세히 →</span>
  </div>
</article>`;
}

/* ══════════════════════════════════════════════════════
   모달 상세
══════════════════════════════════════════════════════ */
async function openModal(id) {
  try {
    const res  = await fetch(API.item(id));
    if (!res.ok) throw new Error('not found');
    const item = await res.json();
    _curModal  = item;
    renderModal(item);
  } catch (e) {
    // 로컬 폴백
    const item = _allData.find(d => d.id === id);
    if (item) { _curModal = item; renderModal(item); }
  }
}

function renderModal(item) {
  const catCls  = CAT_CLASS[item.category] || 'cat-기타';
  const mc      = item.match_conditions || {};
  const cq      = item.content_quality || {};
  const pr      = item.practical || {};
  const kg      = item.knowledge_graph || {};

  // 매칭 조건 태그
  const shinsinTags = (mc['십신']||[]).map(s => `<span class="ms-cond-tag shinsin">${s}</span>`).join('');
  const sinsalTags  = (mc['신살']||[]).map(s => `<span class="ms-cond-tag sinsal">${s}</span>`).join('');
  const gyeokTags   = (mc['격국']||[]).map(g => `<span class="ms-cond-tag gyeok">${g}</span>`).join('');
  const allConds    = shinsinTags + sinsalTags + gyeokTags;

  // 적용 행사
  const events = (pr.applicable_events||[]).map(e =>
    `<span class="ms-cond-tag">${e}</span>`
  ).join('');

  // 품질 배지
  const qualityBadge = cq.confidence_score
    ? `<span style="font-size:0.72rem;color:var(--ms-ink-light)">
        신뢰도 ${Math.round(cq.confidence_score * 100)}% · ${cq.ocr_quality || ''} · ${cq.source_authority || ''}
       </span>` : '';

  document.getElementById('modalContent').innerHTML = `
    <div class="ms-modal-cat">
      <span class="ms-card-cat ${catCls}">${item.category}</span>
      ${qualityBadge}
    </div>
    <h2 class="ms-modal-title">${escHtml(msTitle(item))}</h2>
    ${item.display_chapter_hanja ? `<p class="ms-modal-hanja-sub">${escHtml(item.display_chapter_hanja)}</p>` : ''}

    ${msModalBeginner(item) ? `
    <div class="ms-modal-section">
      <div class="ms-modal-section-label">💡 입문 해설</div>
      <div class="ms-modal-beginner">${escHtml(msModalBeginner(item))}</div>
    </div>` : ''}

    <div class="ms-modal-section">
      <div class="ms-modal-section-label">📖 한글 해석</div>
      <p class="ms-modal-text">${escHtml(msBodyPrimary(item))}</p>
    </div>

    ${msOriginal(item) ? `
    <div class="ms-modal-section">
      <div class="ms-modal-section-label">📜 원문 (한글 병기)</div>
      <div class="ms-modal-text ms-original-body">${escHtml(msOriginal(item))}</div>
    </div>` : ''}

    ${allConds ? `
    <div class="ms-modal-section">
      <div class="ms-modal-section-label">🔗 사주 매칭 조건</div>
      <div class="ms-modal-conditions">${allConds}</div>
    </div>` : ''}

    ${events ? `
    <div class="ms-modal-section">
      <div class="ms-modal-section-label">📌 적용 행사</div>
      <div class="ms-modal-conditions">${events}</div>
    </div>` : ''}

    <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid var(--ms-border);
      font-size:0.72rem;color:var(--ms-ink-light)">
      출처: ${escHtml(item.source_book || '')} · 파일: ${escHtml(item.page_filename || '')}
    </div>
  `;

  const modal = document.getElementById('detailModal');
  const content = document.getElementById('modalContent');
  document.getElementById('modalBackdrop').classList.add('open');
  modal.classList.add('open');
  content.scrollTop = 0;
  document.body.style.overflow = 'hidden';
  modal.focus({ preventScroll: true });
}

function closeModal() {
  document.getElementById('modalBackdrop').classList.remove('open');
  document.getElementById('detailModal').classList.remove('open');
  document.body.style.overflow = '';
  _curModal = null;
}

// ESC 키 닫기
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

/* ══════════════════════════════════════════════════════
   인쇄 · PDF
══════════════════════════════════════════════════════ */
function printPage() {
  window.print();
}

function printModal() {
  if (!_curModal) return;
  const win = window.open('', '_blank', 'width=700,height=900');
  win.document.write(`
    <!DOCTYPE html><html lang="ko"><head>
    <meta charset="UTF-8">
    <title>${msTitle(_curModal)}</title>
    <style>
      body { font-family: 'Noto Serif KR', serif; padding: 2rem; color: #1a1209; line-height:1.8; }
      h1 { font-size: 1.4rem; margin-bottom: 0.5rem; }
      .label { font-size: 0.75rem; color: #888; font-weight: 600;
               letter-spacing: 0.08em; margin: 1.2rem 0 0.3rem;
               border-bottom: 1px solid #ddd; padding-bottom: 4px; }
      .hanja { background: #f8f3e8; padding: 12px; border-radius: 6px;
               font-size: 0.85rem; white-space: pre-line; }
      .meta { font-size: 0.72rem; color: #999; margin-top: 2rem; padding-top: 1rem;
              border-top: 1px solid #eee; }
    </style>
    </head><body>
    <h1>${escHtml(msTitle(_curModal))}</h1>
    <p style="color:#888;font-size:0.82rem">${escHtml(_curModal.category)} · ${escHtml(_curModal.sub_category)}</p>
    ${msModalBeginner(_curModal)
      ? `<div class="label">입문 해설</div><p>${escHtml(msModalBeginner(_curModal))}</p>` : ''}
    <div class="label">한글 해석</div>
    <p>${escHtml(msBodyPrimary(_curModal))}</p>
    <div class="label">원문 (한글 병기)</div>
    <div class="hanja">${escHtml(msOriginal(_curModal))}</div>
    <div class="meta">출처: ${escHtml(_curModal.source_book || '')} · ${escHtml(_curModal.page_filename || '')}</div>
    </body></html>
  `);
  win.document.close();
  win.focus();
  setTimeout(() => win.print(), 500);
}

/* ══════════════════════════════════════════════════════
   공유
══════════════════════════════════════════════════════ */
function shareItem() {
  if (!_curModal) return;
  const url   = `${location.origin}/manseryeok#${_curModal.id}`;
  const title = _curModal.ux_meta?.share_format?.kakao_title || msTitle(_curModal);
  const desc  = _curModal.ux_meta?.share_format?.kakao_desc  || msCardDesc(_curModal) || msBodyPrimary(_curModal).slice(0, 120);

  if (navigator.share) {
    navigator.share({ title, text: desc, url }).catch(() => copyToClipboard(url));
  } else {
    copyToClipboard(url);
  }
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('링크가 복사되었습니다');
  }).catch(() => {
    showToast('클립보드 복사 실패 — 직접 복사해주세요');
  });
}

/* ══════════════════════════════════════════════════════
   URL 해시 라우팅 (직접 링크)
══════════════════════════════════════════════════════ */
window.addEventListener('load', () => {
  const hash = location.hash.replace('#', '');
  if (hash && hash.match(/^\d{3}_\d{3}$/)) {
    setTimeout(() => openModal(hash), 600);
  }
});

/* ══════════════════════════════════════════════════════
   토스트 알림
══════════════════════════════════════════════════════ */
function showToast(msg) {
  const el = document.createElement('div');
  el.textContent = msg;
  Object.assign(el.style, {
    position:'fixed', bottom:'2rem', left:'50%',
    transform:'translateX(-50%)',
    background:'rgba(26,18,9,0.9)', color:'#f5e8c8',
    padding:'10px 20px', borderRadius:'20px',
    fontSize:'0.85rem', zIndex:'999',
    boxShadow:'0 4px 20px rgba(0,0,0,0.3)',
    transition:'opacity 0.3s',
  });
  document.body.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 2500);
}

/* ══════════════════════════════════════════════════════
   유틸
══════════════════════════════════════════════════════ */
function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '…' : str;
}
