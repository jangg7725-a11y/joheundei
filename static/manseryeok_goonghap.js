/* 만세력 — 궁합 탭 (K사주품 /api/goonghap 동일) */
'use strict';

function setMsGhStatus(msg, isError = false) {
  const el = document.getElementById('msGhStatus');
  if (!el) return;
  const text = msg || '';
  el.textContent = text;
  el.classList.toggle('error', !!isError);
  el.classList.toggle('fallback-hidden', !text);
}

function readMsGhNative(which) {
  const p = which === 'a' ? 'a' : 'b';
  return {
    calendar: document.getElementById(`ms-gh-${p}-calendar`).value,
    year: Number(document.getElementById(`ms-gh-${p}-year`).value),
    month: Number(document.getElementById(`ms-gh-${p}-month`).value),
    day: Number(document.getElementById(`ms-gh-${p}-day`).value),
    hour: Number(document.getElementById(`ms-gh-${p}-hour`).value),
    minute: Number(document.getElementById(`ms-gh-${p}-minute`).value),
    gender: document.getElementById(`ms-gh-${p}-gender`).value,
    lunar_leap: document.getElementById(`ms-gh-${p}-leap`).checked,
  };
}

function prefillMsGhPersonAFromSaju() {
  const cal = document.getElementById('msCalendar')?.value || 'solar';
  document.getElementById('ms-gh-a-calendar').value = cal;
  document.getElementById('ms-gh-a-year').value = document.getElementById('msYear')?.value || '';
  document.getElementById('ms-gh-a-month').value = document.getElementById('msMonth')?.value || '';
  document.getElementById('ms-gh-a-day').value = document.getElementById('msDay')?.value || '';
  document.getElementById('ms-gh-a-hour').value = document.getElementById('msHour')?.value ?? 12;
  document.getElementById('ms-gh-a-minute').value = document.getElementById('msMinute')?.value ?? 0;
  document.getElementById('ms-gh-a-gender').value = document.getElementById('msGender')?.value || 'male';
  document.getElementById('ms-gh-a-leap').checked =
    cal === 'lunar' && document.getElementById('msLunarLeap')?.value === '1';
  const nm = (document.getElementById('msUserName')?.value || '').trim();
  if (nm) document.getElementById('ms-gh-name-a').value = nm;
  setMsGhStatus('첫 번째 사람에 상단 사주 입력을 넣었습니다.');
}

function msGhGaugeBar(pct, colorClass) {
  return `<div class="gh-gauge-track"><div class="gh-gauge-fill ${colorClass || ''}" style="width:${pct}%"></div></div>`;
}

function renderMsGhPillarCard(sn) {
  const KR = { year: '年', month: '月', day: '日', hour: '時' };
  const zh = sn.주 || {};
  const ganRow = ['year', 'month', 'day', 'hour'].map((k) => {
    const row = zh[k] || {};
    return `<td class="gh-cell-gz han-inline">${escHtml(row.간 || '')}</td>`;
  }).join('');
  const zhiRow = ['year', 'month', 'day', 'hour'].map((k) => {
    const row = zh[k] || {};
    return `<td class="gh-cell-gz han-inline">${escHtml(row.지 || '')}</td>`;
  }).join('');
  const hdrRow = ['year', 'month', 'day', 'hour'].map((k) => `<th>${KR[k]}</th>`).join('');
  return `
    <div class="gh-chart-card">
      <h4 class="gh-chart-name">${escHtml(sn.표시_이름 || '')}</h4>
      <p class="gh-chart-ec han-inline">${escHtml(sn.eight_char_string || '')}</p>
      <p class="gh-chart-date">${escHtml(sn.양력 || '')} · ${escHtml(sn.음력 || '')}</p>
      <table class="gh-pillar-table">
        <thead><tr>${hdrRow}</tr></thead>
        <tbody><tr>${ganRow}</tr><tr>${zhiRow}</tr></tbody>
      </table>
      <p class="gh-chart-dm">일간 <strong class="han-inline">${escHtml(sn.일간 || '')}</strong>
        (${escHtml(sn.일간_한글 || '')} · ${escHtml(sn.일간_오행 || '')})</p>
    </div>`;
}

function renderMsGhMonthGrid(monthlyArr) {
  if (!monthlyArr || !monthlyArr.length) return '';
  const cells = monthlyArr.map((m) => {
    const emoji = m.이모지 || '⚪';
    const gz = escHtml(m.월주간지 || `${m.절월}월`);
    const cls = emoji === '💚' ? 'gh-mon-good' : emoji === '🔴' ? 'gh-mon-bad' : 'gh-mon-norm';
    return `<div class="gh-mon-cell ${cls}" title="${escHtml(m.핵심한마디 || '')}">
      <span class="gh-mon-gz">${gz}</span>
      <span class="gh-mon-emoji">${emoji}</span>
      <span class="gh-mon-num">${m.절월}절</span>
    </div>`;
  }).join('');
  return `<div class="gh-month-grid">${cells}</div>`;
}

function renderMsGoonghapResult(pack) {
  const mount = document.getElementById('msGoonghapResult');
  if (!mount) return;

  const sc = pack['종합_점수'] || {};
  const side = pack['원국_나란히'] || {};
  const snA = side.A || {};
  const snB = side.B || {};
  const la = escHtml(snA.표시_이름 || 'A');
  const lb = escHtml(snB.표시_이름 || 'B');

  const ilji = pack['기본_일지'] || {};
  const allZ = pack['전체_지지_대조'] || {};
  const ohx = pack['오행_궁합'] || {};
  const ig = pack['일간_궁합'] || {};
  const sip = pack['십신_궁합'] || {};
  const cg = pack['천간합'] || {};
  const ysx = pack['용신_궁합'] || {};
  const sewG = pack['세운_궁합'] || {};
  const cy = sewG.연도 || new Date().getFullYear();

  const pct = sc['하트_게이지_퍼센트'] ?? 0;
  const heartEmoji = sc['하트_이모지'] || '❤️'.repeat(Math.round(pct / 20));
  const marriage = pack['결혼적합도_뱃지'] || '';

  const scoreItems = [
    ['인연 강도', sc['인연_강도'], 'gh-g-bond'],
    ['갈등 가능성', sc['갈등_가능성'], 'gh-g-conf'],
    ['경제 궁합', sc['경제적_궁합'], 'gh-g-econ'],
    ['성격 궁합', sc['성격_궁합'], 'gh-g-pers'],
    ['전체 궁합', sc['전체_궁합'], 'gh-g-over'],
  ];
  const scoreHTML = scoreItems.map(([lab, o, cls]) => {
    if (!o) return '';
    const barPct = (o.별점 || 0) * 20;
    return `<div class="gh-score-row">
      <span class="gh-score-lab">${lab}</span>
      ${msGhGaugeBar(barPct, cls)}
      <span class="gh-stars">${escHtml(o.문자 || '')}</span>
    </div>`;
  }).join('');

  const sewA = sewG[`${snA.표시_이름 || 'A'}_세운`] || sewG.A_세운 || {};
  const sewB = sewG[`${snB.표시_이름 || 'B'}_세운`] || sewG.B_세운 || {};
  const monthlyHTML = renderMsGhMonthGrid(sewG['월별_궁합']);

  const strengths = pack['강점_3가지'] || [];
  const challenges = pack['극복과제_3가지'] || [];
  const advice = pack['핵심조언'] || '';
  const strHTML = strengths.map((s) => `<li>✅ ${escHtml(s)}</li>`).join('');
  const chalHTML = challenges.map((c) => `<li>⚠️ ${escHtml(c)}</li>`).join('');

  const ysA = ysx['A가_느끼는_상대'] || {};
  const ysB = ysx['B가_느끼는_상대'] || {};
  const sipAB = Object.entries(sip)
    .filter(([k]) => k.endsWith('_해설'))
    .map(([, v]) => `<p class="gh-note">${escHtml(String(v))}</p>`)
    .join('');

  const mx = pack['일간_매트릭스'] || {};
  let matrixHTML = '';
  if (mx.found) {
    const mxBody =
      mx['표시_텍스트'] ||
      [mx.core_dynamic, mx.dynamic, mx.strength, mx.friction, mx.growth, mx.daily_hint]
        .filter(Boolean)
        .join('\n\n');
    const mxParas = String(mxBody)
      .split(/\n\n+/)
      .map((p) => `<p class="gh-note">${escHtml(p.trim())}</p>`)
      .join('');
    matrixHTML = `
<div class="gh-detail-block gh-card gh-matrix-block">
  <h4>✨ 천간 매트릭스 궁합 (${escHtml(mx.label || '')})</h4>
  <p class="gh-sub muted-small">${escHtml(mx.mingri_relation || '')}</p>
  ${mxParas}
</div>`;
  }

  mount.hidden = false;
  mount.innerHTML = `
<div class="gh-heart-section">
  <div class="gh-heart-visual">
    <span class="gh-heart-icon">♥</span>
    <div class="gh-heart-track"><div class="gh-heart-fill" style="width:${pct}%"></div></div>
    <span class="gh-heart-pct">${pct}%</span>
  </div>
  <div class="gh-heart-emoji">${heartEmoji}</div>
  <div class="gh-marriage-badge">${escHtml(marriage)}</div>
</div>
<div class="gh-charts-row">
  ${renderMsGhPillarCard(snA)}
  <div class="gh-vs-divider">VS</div>
  ${renderMsGhPillarCard(snB)}
</div>
<div class="gh-scores-block">
  <h4>궁합 점수</h4>
  ${scoreHTML}
</div>
<div class="gh-detail-block gh-card">
  <h4>💑 일지 궁합</h4>
  <p><strong class="gh-couple-type">${escHtml(ilji.커플_유형 || '')} ${(ilji.커플_태그 || []).map((t) => `<span class="gh-tag">${escHtml(t)}</span>`).join('')}</strong></p>
  <p class="gh-note">${escHtml(ilji.스토리 || '')}</p>
  <p class="gh-sub">관계: ${escHtml((ilji.관계_표기 || []).join(' · ') || '—')}</p>
</div>
<div class="gh-detail-block gh-card">
  <h4>🔗 전체 지지 대조 (8글자)</h4>
  <p class="gh-note">${escHtml(allZ['인연_강도_판정'] || '')}</p>
  <p class="gh-sub">합 ${allZ['합_개수'] || 0}개 · 충 ${allZ['충_개수'] || 0}개</p>
  ${(allZ['합_목록'] || []).map((r) => `<p class="gh-sub">💚 합: ${escHtml(r.A_궁)} ${escHtml(r.A_지)} ↔ ${escHtml(r.B_궁)} ${escHtml(r.B_지)}</p>`).join('')}
  ${(allZ['충_목록'] || []).map((r) => `<p class="gh-sub">🔴 충: ${escHtml(r.A_궁)} ${escHtml(r.A_지)} ↔ ${escHtml(r.B_궁)} ${escHtml(r.B_지)}</p>`).join('')}
</div>
<div class="gh-detail-block gh-card">
  <h4>☯ 오행 궁합</h4>
  <div class="gh-ohaeng-dist">
    <p><strong>${la}</strong> ${escHtml(ohx[`${snA.표시_이름 || 'A'}_오행_분포`] || ohx.A_오행_분포 || '')}</p>
    <p><strong>${lb}</strong> ${escHtml(ohx[`${snB.표시_이름 || 'B'}_오행_분포`] || ohx.B_오행_분포 || '')}</p>
  </div>
  <p class="gh-note">${escHtml(ohx.스토리 || '')}</p>
  <p class="gh-sub">오행 보완 점수: ${'★'.repeat(ohx['오행_보완_점수'] || 0)}${'☆'.repeat(5 - (ohx['오행_보완_점수'] || 0))}</p>
</div>
<div class="gh-detail-block gh-card">
  <h4>⚡ 일간 궁합 (${escHtml(ig.유형 || '')})</h4>
  <p class="gh-note">${escHtml(ig.연애_해석 || ig.해설 || '')}</p>
  <p class="gh-note gh-sub">${escHtml(ig.결혼_해석 || '')}</p>
</div>
${matrixHTML}
<div class="gh-detail-block gh-card">
  <h4>🔢 십신으로 보는 궁합</h4>
  ${sipAB || `<p class="gh-note">${escHtml(Object.values(sip).find((v) => typeof v === 'string') || '')}</p>`}
</div>
<div class="gh-detail-block gh-card">
  <h4>🌟 천간합</h4>
  <p class="gh-note">${cg.성립
    ? `<strong>${escHtml(cg.표기 || '')}</strong> — ${escHtml(cg.해설 || '')}`
    : escHtml(cg.해설 || '일간 천간합 해당 없음')}</p>
</div>
<div class="gh-detail-block gh-card">
  <h4>🌿 용신 궁합</h4>
  <p class="gh-note"><strong>${la} 기준</strong> ${escHtml(ysA.등급_한글 || ysA.등급 || '')} — ${escHtml(ysA.해설 || '')}</p>
  <p class="gh-note"><strong>${lb} 기준</strong> ${escHtml(ysB.등급_한글 || ysB.등급 || '')} — ${escHtml(ysB.해설 || '')}</p>
  <p class="gh-sub">${escHtml(ysx['종합_평가'] || '')}</p>
</div>
<div class="gh-detail-block gh-card gh-sewoon-section">
  <h4>📅 ${cy}년 세운 궁합</h4>
  <div class="gh-sewoon-two">
    <div class="gh-sew-person">
      <p><strong>${la}</strong> ${escHtml(sewA.운세등급 || '')} ${escHtml(sewA.별점 || '')}</p>
      <p class="gh-note">${escHtml(sewA.세운_총평 || '')}</p>
    </div>
    <div class="gh-sew-person">
      <p><strong>${lb}</strong> ${escHtml(sewB.운세등급 || '')} ${escHtml(sewB.별점 || '')}</p>
      <p class="gh-note">${escHtml(sewB.세운_총평 || '')}</p>
    </div>
  </div>
  <p class="gh-note gh-sew-couple">${escHtml(sewG['궁합_세운_분석'] || '')}</p>
  <h5>월별 궁합 달력</h5>
  ${monthlyHTML}
  <div class="gh-half-summary">
    <p>📈 ${escHtml(sewG['상반기_총평'] || '')}</p>
    <p>📉 ${escHtml(sewG['하반기_총평'] || '')}</p>
  </div>
  <div class="gh-issues">
    <p>💍 ${escHtml((sewG['올해_주요이슈'] || {})['결혼_동거_가능성'] || '')}</p>
    <p>⚡ ${escHtml((sewG['올해_주요이슈'] || {})['갈등_주의'] || '')}</p>
    <p>💚 함께 좋은 달: ${((sewG['올해_주요이슈'] || {})['함께_좋은_달_TOP3'] || []).join(', ') || '—'}</p>
    <p>🔴 함께 주의 달: ${((sewG['올해_주요이슈'] || {})['함께_주의할_달_TOP3'] || []).join(', ') || '—'}</p>
  </div>
</div>
<div class="gh-story-card">
  <h4>✨ 종합 총평</h4>
  ${(pack['총평'] || '').split('\n').map((l) => `<p>${escHtml(l)}</p>`).join('')}
</div>
<div class="gh-strengths-block gh-card">
  <div class="gh-str-col">
    <h5>💪 이 커플의 강점</h5>
    <ul class="meta-list">${strHTML || '<li>서로를 향한 노력이 가장 큰 강점입니다.</li>'}</ul>
  </div>
  <div class="gh-str-col">
    <h5>🎯 극복 과제</h5>
    <ul class="meta-list">${chalHTML || '<li>꾸준한 소통이 관계를 지킵니다.</li>'}</ul>
  </div>
</div>
<div class="gh-advice-card">
  <span class="gh-advice-icon">💡</span>
  <p class="gh-advice-text">${escHtml(advice)}</p>
</div>
<p class="ms-il-note">${escHtml(pack['참고'] || '')}</p>`;

  const typeEl = mount.querySelector('.gh-couple-type');
  if (typeEl) {
    typeEl.innerHTML =
      escHtml(ilji.커플_유형 || '') +
      ' ' +
      (ilji.커플_태그 || []).map((t) => `<span class="gh-tag">${escHtml(t)}</span>`).join('');
  }
}

function initMsGoonghapTab() {
  const form = document.getElementById('msGoonghapForm');
  if (!form) return;

  const gy = new Date().getFullYear();
  ['ms-gh-a-year', 'ms-gh-b-year'].forEach((id) => {
    const el = document.getElementById(id);
    if (el && !(el.value || '').trim()) el.value = gy;
  });

  document.getElementById('msGhPrefillA')?.addEventListener('click', prefillMsGhPersonAFromSaju);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    setMsGhStatus('궁합 계산 중…');
    const cyEl = document.getElementById('ms-gh-current-year');
    const cyVal = cyEl && cyEl.value.trim() ? Number(cyEl.value) : undefined;
    const body = {
      person_a: readMsGhNative('a'),
      person_b: readMsGhNative('b'),
      name_a: (document.getElementById('ms-gh-name-a').value || '').trim(),
      name_b: (document.getElementById('ms-gh-name-b').value || '').trim(),
      ...(cyVal ? { current_year: cyVal } : {}),
    };
    try {
      const res = await fetch(API.goonghap, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (!res.ok) {
        let detail = json.detail ?? json.message ?? res.statusText;
        if (typeof detail === 'object') detail = JSON.stringify(detail);
        throw new Error(String(detail));
      }
      renderMsGoonghapResult(json.result);
      setMsGhStatus('');
      document.getElementById('msGoonghapResult')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      setMsGhStatus(err.message || String(err), true);
      const mount = document.getElementById('msGoonghapResult');
      if (mount) mount.hidden = true;
    }
  });
}
