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

/* ══════════════════════════════════════════════════════
   초기화
══════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  await loadAllData();
  initTabs();
  initSajuPanel();
  initCalendarTab();
  initTaekilTab();
  initCategoryTab();
  initSearchEnter();
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
  const status = document.getElementById('msSajuStatus');
  const btn = document.getElementById('msSajuSubmitBtn');
  const body = collectSajuFormBody();
  status.textContent = '사주 계산 중…';
  status.classList.remove('error');
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
    status.textContent = '계산 완료 — 아래 탭에서 달력·택일·문헌을 확인하세요.';
  } catch (e) {
    status.textContent = e.message || String(e);
    status.classList.add('error');
  } finally {
    if (btn) btn.disabled = false;
  }
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
  applyMatchDropdowns(profile.match_params);
  renderSajuMatchedDocs(profile);
  prefillMonthFilters(profile.birth_month_label);
  if (!opts.silent) {
    document.getElementById('msSajuSummary')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    setTimeout(() => {
      document.querySelector('[data-tab="saju"]')?.click();
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
    <p class="ms-saju-linked">만세력 매칭: 십신 ${escHtml(mp.shinsin || '-')} · 신살 ${escHtml(mp.sinsal || '-')} · 격국 ${escHtml(mp.gyeokguk || '-')} · 용신 ${escHtml(mp.ohaeng || '-')} ·
      <button type="button" class="ms-saju-linked-btn" onclick="goToSajuMatchTab()">관련 문헌 ${p.matched_total ?? 0}건</button></p>
  `;
  box.classList.remove('fallback-hidden');
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

function renderSajuMatchedDocs(p) {
  const grid = document.getElementById('sajuGrid');
  const info = document.getElementById('sajuInfo');
  if (!grid) return;
  const docs = p.matched_docs || [];
  if (info) {
    info.style.display = 'block';
    info.textContent = `사주 연동 — 관련 고전 문헌 ${p.matched_total ?? docs.length}건 (상위 ${docs.length}건 표시)`;
  }
  if (docs.length) renderCards(grid, docs, '');
  else grid.innerHTML = '<div class="ms-empty">매칭된 문헌이 없습니다. 조건을 조정해 보세요.</div>';
}

function prefillMonthFilters(monthLabel) {
  if (!monthLabel) return;
  const taekilMonth = document.getElementById('taekilMonth');
  if (taekilMonth) taekilMonth.value = monthLabel;
  document.querySelectorAll('.ms-month-btn').forEach((b) => {
    b.classList.toggle('active', b.dataset.month === monthLabel);
  });
  if (_sajuProfile) loadCalendar(monthLabel);
}

/* ══════════════════════════════════════════════════════
   TAB 1: 달력·절기
══════════════════════════════════════════════════════ */
function initCalendarTab() {
  // 절기 띠 렌더
  renderJeolgiStrip();

  // 월 버튼
  document.querySelectorAll('.ms-month-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ms-month-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      loadCalendar(btn.dataset.month);
    });
  });
}

function renderJeolgiStrip() {
  const strip = document.getElementById('jeolgiStrip');
  // 절기표 항목 추출
  const jeolgi = _allData.filter(d => d.sub_category === '절기표·월표');
  if (!jeolgi.length) { strip.innerHTML = ''; return; }

  // 24절기 키워드 추출
  const keywords24 = ['대한','소한','동지','입춘','우수','경칩','춘분','청명','곡우',
    '입하','소만','망종','하지','소서','대서','처서','입추','백로','추분','상강','한로','입동','소설','대설'];

  let html = keywords24.map(k =>
    `<button class="ms-jeolgi-chip" onclick="searchByJeolgi('${k}')">${k}</button>`
  ).join('');
  strip.innerHTML = html;
}

async function loadCalendar(month) {
  const grid = document.getElementById('calendarGrid');
  grid.innerHTML = '<div class="ms-loading">불러오는 중…</div>';
  try {
    const url = month ? `${API.calendar}?month=${encodeURIComponent(month)}` : API.calendar;
    const res  = await fetch(url);
    const json = await res.json();
    renderCards(grid, json.data, `${month || '전체'} 달력 항목 ${json.total}건`);
  } catch (e) {
    grid.innerHTML = '<div class="ms-empty">데이터를 불러올 수 없습니다.</div>';
  }
}

function searchByJeolgi(keyword) {
  // 검색 탭으로 이동 후 검색
  document.querySelector('[data-tab="search"]').click();
  document.getElementById('searchKeyword').value = keyword;
  doSearch();
}

/* ══════════════════════════════════════════════════════
   TAB 2: 택일 (만세력 宜·忌 계산)
══════════════════════════════════════════════════════ */
function initTaekilTab() {
  const tab = document.querySelector('[data-tab="taekil"]');
  if (!tab) return;
  tab.addEventListener('click', () => {
    const good = document.getElementById('taekilGoodList');
    if (good && good.querySelector('.ms-empty') && !good.dataset.loaded) {
      runTaekil();
    }
  });
}

const TAEKIL_GRADE_CLASS = {
  '대길': 'tk-grade-best',
  '길': 'tk-grade-good',
  '평': 'tk-grade-mid',
  '흉': 'tk-grade-bad',
  '대흉': 'tk-grade-worst',
};

async function runTaekil() {
  const event = document.getElementById('taekilEvent')?.value || '택일';
  const month = document.getElementById('taekilMonth')?.value || '';
  const goodEl = document.getElementById('taekilGoodList');
  const badEl  = document.getElementById('taekilBadList');
  const sumEl  = document.getElementById('taekilSummary');
  const theory = document.getElementById('taekilTheoryGrid');

  goodEl.innerHTML = '<div class="ms-loading">만세력 달력 분석 중…</div>';
  badEl.innerHTML = '';
  theory.innerHTML = '<div class="ms-loading">관련 문헌 불러오는 중…</div>';

  try {
    const params = new URLSearchParams({ event, limit: '30' });
    if (month) params.set('month', month);
    const res  = await fetch(`${API.taekil}?${params}`);
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || '택일 계산 실패');

    const monthLabel = month || '전체';
    sumEl.style.display = 'block';
    sumEl.textContent =
      `${json.event_label || event} · ${monthLabel} — ` +
      `분석 ${json.total_parsed_days}일 · 길일 ${json.good_days.length} · 피할 날 ${json.avoid_days.length}`;

    goodEl.dataset.loaded = '1';
    goodEl.innerHTML = json.good_days.length
      ? json.good_days.map(d => renderTaekilDayCard(d, true)).join('')
      : '<div class="ms-empty">조건에 맞는 길일이 없습니다. 월을 바꾸거나 행사 유형을 조정해 보세요.</div>';

    badEl.innerHTML = json.avoid_days.length
      ? json.avoid_days.map(d => renderTaekilDayCard(d, false)).join('')
      : '<div class="ms-empty">강한 흉일 후보가 없습니다.</div>';

    const docs = json.related_docs || [];
    if (docs.length) {
      renderCards(theory, docs, `관련 문헌 ${docs.length}건`);
    } else {
      theory.innerHTML = '<div class="ms-empty">관련 문헌이 없습니다.</div>';
    }
  } catch (e) {
    goodEl.innerHTML = `<div class="ms-empty">오류: ${escHtml(String(e.message || e))}</div>`;
    theory.innerHTML = '';
    sumEl.style.display = 'none';
  }
}

function renderTaekilDayCard(d, isGood) {
  const cls = TAEKIL_GRADE_CLASS[d.grade] || 'tk-grade-mid';
  const hits = (isGood ? d.yi_hits : d.ji_hits) || [];
  const hitStr = hits.length ? hits.join(' · ') : (isGood ? d.yi_raw?.slice(0, 40) : d.ji_raw?.slice(0, 40)) || '';
  const src = d.source_chapter ? escHtml(d.source_chapter.slice(0, 28)) : '';
  const calMonth = d.calendar_month ? ` · ${escHtml(d.calendar_month)}` : '';
  return `
    <article class="ms-taekil-day ${cls}" role="button" tabindex="0"
      onclick="openModal('${escHtml(d.source_id || '')}')"
      onkeydown="if(event.key==='Enter')openModal('${escHtml(d.source_id || '')}')">
      <div class="ms-taekil-day-head">
        <span class="ms-taekil-day-label">${escHtml(d.day_label)}</span>
        <span class="ms-taekil-ganji">${escHtml(d.ganji)}</span>
        <span class="ms-taekil-grade">${escHtml(d.grade)}</span>
      </div>
      <p class="ms-taekil-verdict">${escHtml(d.verdict)}</p>
      <p class="ms-taekil-hits">${isGood ? '宜' : '忌'}: ${escHtml(hitStr)}</p>
      <p class="ms-taekil-src">${src}${calMonth}</p>
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
  grid.innerHTML = '<div class="ms-loading">매칭 중…</div>';
  info.style.display = 'none';

  if (!shinsin && !sinsal && !gyeokguk && !ohaeng) {
    grid.innerHTML = '<div class="ms-empty">최소 하나의 조건을 선택해주세요.</div>';
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

    const condList = [shinsin, sinsal, gyeokguk, ohaeng].filter(Boolean);
    info.textContent = `조건 [${condList.join(', ')}] — 관련 문헌 ${json.total}건 매칭됨`;
    info.style.display = 'block';

    renderCards(grid, json.data, '');
  } catch (e) {
    grid.innerHTML = '<div class="ms-empty">매칭 중 오류가 발생했습니다.</div>';
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

  const desc = item.beginner_explanation || item.modern_interpretation || item.korean_translation || '';

  const events = (item.practical?.applicable_events || []).slice(0,3).join(' · ');

  return `
<article class="ms-card" data-id="${escHtml(item.id)}" tabindex="0"
  role="button" aria-label="${escHtml(item.chapter)}">
  <span class="ms-card-cat ${catCls}">${item.category}</span>
  <h3 class="ms-card-title">${escHtml(item.chapter)}</h3>
  <p class="ms-card-desc">${escHtml(desc)}</p>
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
    <h2 class="ms-modal-title">${escHtml(item.chapter)}</h2>

    ${item.beginner_explanation ? `
    <div class="ms-modal-section">
      <div class="ms-modal-section-label">💡 입문 해설</div>
      <div class="ms-modal-beginner">${escHtml(item.beginner_explanation)}</div>
    </div>` : ''}

    <div class="ms-modal-section">
      <div class="ms-modal-section-label">📖 현대 해석</div>
      <p class="ms-modal-text">${escHtml(item.modern_interpretation || item.korean_translation || '')}</p>
    </div>

    <div class="ms-modal-section">
      <div class="ms-modal-section-label">📜 원문 (한문·한글)</div>
      <div class="ms-modal-text hanja">${escHtml(truncate(item.original_text, 600))}</div>
    </div>

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

    ${(kg.see_also||[]).length ? `
    <div class="ms-modal-section">
      <div class="ms-modal-section-label">🔁 관련 문헌</div>
      <div class="ms-modal-conditions">
        ${(kg.see_also||[]).map(rid => {
          const rel = _allData.find(d => d.id === rid);
          return rel
            ? `<button class="ms-cond-tag" style="cursor:pointer;border-color:var(--ms-gold);color:var(--ms-gold)"
                onclick="openModal('${rid}')">${escHtml(rel.chapter.slice(0,20))}…</button>`
            : '';
        }).join('')}
      </div>
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
    <title>${_curModal.chapter}</title>
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
    <h1>${escHtml(_curModal.chapter)}</h1>
    <p style="color:#888;font-size:0.82rem">${escHtml(_curModal.category)} · ${escHtml(_curModal.sub_category)}</p>
    ${_curModal.beginner_explanation
      ? `<div class="label">입문 해설</div><p>${escHtml(_curModal.beginner_explanation)}</p>` : ''}
    <div class="label">현대 해석</div>
    <p>${escHtml(_curModal.modern_interpretation || _curModal.korean_translation || '')}</p>
    <div class="label">원문</div>
    <div class="hanja">${escHtml(_curModal.original_text || '')}</div>
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
  const title = _curModal.ux_meta?.share_format?.kakao_title || _curModal.chapter;
  const desc  = _curModal.ux_meta?.share_format?.kakao_desc  || _curModal.beginner_explanation || '';

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
