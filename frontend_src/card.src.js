/* Mosquito Watch card - mosquito-borne diseases per Thai province (DDC Report 506).
 * Ships with the Mosquito Watch Thailand integration and finds its sensors on its own.
 * Province outlines: thailand.json by Apisit Toompakdee (MIT), simplified. */
const MW_VERSION = "0.2.0";
const MW_ICON = "/*__ICON__*/";
const MW_GEO = /*__GEO__*/;

const LEVEL_COLOR = { low: "#4fc3f7", normal: "#66bb6a", elevated: "#ffb300", high: "#ef5350" };
const LEVEL_RANK = { low: 0, normal: 1, elevated: 2, high: 3 };
const DIS_ORDER = ["dengue", "malaria", "chikungunya", "zika"];

const I18N = {
  en: {
    title: "Mosquito Watch", lvl: { low: "Below normal", normal: "Normal", elevated: "Elevated", high: "High" },
    cases4: "cases in 4 weeks", usual: "usual", year: "this year", sameLast: "same time last year",
    trend: { rising: "rising", falling: "falling", steady: "steady" }, week: "Week", wk: "W",
    weeks12: "Last 12 weeks", median: "5-year median", cases: "cases", none: "No sensors found - add the Mosquito Watch Thailand integration.",
    loading: "Loading surveillance data…", source: "DDC · Digital Disease Surveillance (Report 506)", home: "Home",
    worst: "Highest level in the region", region: "Region",
  },
  de: {
    title: "Mosquito Watch", lvl: { low: "Unter normal", normal: "Normal", elevated: "Erhöht", high: "Hoch" },
    cases4: "Fälle in 4 Wochen", usual: "üblich", year: "dieses Jahr", sameLast: "gleicher Zeitraum Vorjahr",
    trend: { rising: "steigend", falling: "fallend", steady: "gleichbleibend" }, week: "Woche", wk: "KW",
    weeks12: "Letzte 12 Wochen", median: "5-Jahres-Median", cases: "Fälle", none: "Keine Sensoren gefunden - richte die Integration Mosquito Watch Thailand ein.",
    loading: "Überwachungsdaten werden geladen…", source: "DDC · Digitale Krankheitsüberwachung (Report 506)", home: "Zuhause",
    worst: "Höchste Stufe in der Region", region: "Region",
  },
  th: {
    title: "เฝ้าระวังโรคจากยุง", lvl: { low: "ต่ำกว่าปกติ", normal: "ปกติ", elevated: "สูงกว่าปกติ", high: "สูง" },
    cases4: "ราย ใน 4 สัปดาห์", usual: "ปกติ", year: "ปีนี้", sameLast: "ช่วงเดียวกันปีก่อน",
    trend: { rising: "เพิ่มขึ้น", falling: "ลดลง", steady: "คงที่" }, week: "สัปดาห์", wk: "สัปดาห์",
    weeks12: "12 สัปดาห์ล่าสุด", median: "มัธยฐาน 5 ปี", cases: "ราย", none: "ไม่พบเซนเซอร์ - ติดตั้ง Mosquito Watch Thailand",
    loading: "กำลังโหลดข้อมูลเฝ้าระวัง…", source: "กรมควบคุมโรค · ระบบเฝ้าระวังโรคดิจิทัล (รง.506)", home: "บ้าน",
    worst: "ระดับสูงสุดในภูมิภาค", region: "ภูมิภาค",
  },
};
const DIS_NAME = {
  en: { dengue: "Dengue", malaria: "Malaria", chikungunya: "Chikungunya", zika: "Zika" },
  de: { dengue: "Dengue", malaria: "Malaria", chikungunya: "Chikungunya", zika: "Zika" },
  th: { dengue: "ไข้เลือดออก", malaria: "มาลาเรีย", chikungunya: "ชิคุนกุนยา", zika: "ซิกา" },
};

// province outlines: "x0,y0,dx,dy,...;ring2" in 1/1000 degree
const _geoCache = {};
function rings(name) {
  if (_geoCache[name]) return _geoCache[name];
  const src = MW_GEO[name];
  if (!src) return (_geoCache[name] = []);
  const out = src.split(";").map((r) => {
    const v = r.split(",").map(Number);
    let x = v[0], y = v[1];
    const pts = [[x / 1000, y / 1000]];
    for (let i = 2; i < v.length; i += 2) { x += v[i]; y += v[i + 1]; pts.push([x / 1000, y / 1000]); }
    return pts;
  });
  return (_geoCache[name] = out);
}
function bboxOf(names) {
  let a = [999, 999, -999, -999];
  for (const n of names) for (const r of rings(n)) for (const [x, y] of r) {
    if (x < a[0]) a[0] = x; if (y < a[1]) a[1] = y; if (x > a[2]) a[2] = x; if (y > a[3]) a[3] = y;
  }
  return a;
}
function centroid(name) {
  const rs = rings(name);
  if (!rs.length) return null;
  const r = rs.reduce((m, x) => (x.length > m.length ? x : m), rs[0]);
  let A = 0, cx = 0, cy = 0;
  for (let i = 0; i < r.length; i++) {
    const [x0, y0] = r[(i + r.length - 1) % r.length], [x1, y1] = r[i];
    const c = x0 * y1 - x1 * y0; A += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c;
  }
  return A ? [cx / (3 * A), cy / (3 * A)] : r[0];
}
function inside(pt, name) {
  for (const r of rings(name)) {
    let c = false;
    for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      const [xi, yi] = r[i], [xj, yj] = r[j];
      if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) c = !c;
    }
    if (c) return true;
  }
  return false;
}
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

class MosquitoWatchCard extends HTMLElement {
  static getStubConfig() { return {}; }
  static getConfigForm() {
    return {
      schema: [
        { name: "title", selector: { text: {} } },
        { name: "disease", selector: { select: { mode: "dropdown", options: DIS_ORDER.map((d) => ({ value: d, label: DIS_NAME.en[d] })) } } },
        { name: "map_height", selector: { number: { min: 180, max: 600, step: 10, mode: "box", unit_of_measurement: "px" } } },
      ],
      computeLabel: (s) => ({ title: "Title", disease: "Disease shown first", map_height: "Map height" }[s.name]),
    };
  }

  setConfig(config) {
    this._config = { map_height: 320, ...config };
    this._disease = this._config.disease || null;
    this._sel = null;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._key = "";
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const ents = Object.values(hass.states).filter((s) => s.attributes && s.attributes.weekly_cases && s.attributes.province && s.attributes.disease);
    const key = ents.map((s) => s.entity_id + s.last_updated).join("|") + (hass.locale && hass.locale.language);
    if (key === this._key) return;
    this._key = key;
    this._ents = ents;
    this._render();
  }

  getCardSize() { return 8; }
  getGridOptions() { return { columns: 12, min_columns: 6, rows: "auto" }; }

  _t() {
    const l = ((this._hass && this._hass.locale && this._hass.locale.language) || "en").split("-")[0];
    this._lang = I18N[l] ? l : "en";
    return I18N[this._lang];
  }

  _model() {
    const m = {};
    for (const s of this._ents || []) {
      const raw = s.attributes;
      if (!LEVEL_COLOR[s.state]) continue;
      // attributes can come from any sensor that looks like ours: numbers are forced to numbers, keys to plain words
      const n = (v) => { const x = parseFloat(v); return Number.isFinite(x) ? x : null; };
      const list = (v) => (Array.isArray(v) ? v.map((x) => n(x) ?? 0) : []);
      const disease = String(raw.disease).toLowerCase().replace(/[^a-z0-9_-]/g, "");
      if (!disease) continue;
      const a = {
        ...raw, disease,
        cases_last_4_weeks: n(raw.cases_last_4_weeks) ?? 0, expected_last_4_weeks: n(raw.expected_last_4_weeks),
        ratio: n(raw.ratio), cases_this_year: n(raw.cases_this_year), cases_same_period_last_year: n(raw.cases_same_period_last_year),
        weekly_cases: list(raw.weekly_cases), weekly_median: list(raw.weekly_median),
      };
      (m[disease] = m[disease] || {})[String(raw.province)] = { state: s.state, a, id: s.entity_id };
    }
    return m;
  }

  _homeProvince(names) {
    const h = this._hass && this._hass.config;
    if (!h || h.longitude == null) return null;
    const pt = [h.longitude, h.latitude];
    return names.find((n) => inside(pt, n)) || null;
  }

  _render() {
    if (!this.shadowRoot || !this._hass) return;
    const T = this._t();
    const model = this._model();
    const diseases = DIS_ORDER.filter((d) => model[d]);
    if (!diseases.length) {
      const anyEnts = (this._ents || []).length;
      this.shadowRoot.innerHTML = `<style>${CSS}</style><ha-card><div class="mw empty"><img class="logo" src="${MW_ICON}" alt=""><span>${anyEnts ? T.loading : T.none}</span></div></ha-card>`;
      return;
    }
    if (!this._disease || !model[this._disease]) this._disease = diseases[0];
    const dm = model[this._disease];
    const names = Object.keys(dm).sort();
    const home = this._homeProvince(names);
    if (!this._sel || !dm[this._sel]) this._sel = home || names.slice().sort((a, b) => LEVEL_RANK[dm[b].state] - LEVEL_RANK[dm[a].state])[0];
    const sample = dm[this._sel].a;
    const wk = (sample.latest_week || "").split("-W")[1];
    const wkStart = sample.latest_week_start ? new Date(sample.latest_week_start + "T00:00:00") : null;
    const fmtD = (d) => d.toLocaleDateString(this._hass.locale.language, { day: "numeric", month: "short" });
    const wkRange = wkStart ? `${fmtD(wkStart)} – ${fmtD(new Date(wkStart.getTime() + 6 * 864e5))}` : "";
    const dn = (d) => (DIS_NAME[this._lang] || DIS_NAME.en)[d];
    const pn = (n) => (this._lang === "th" ? dm[n] && dm[n].a.province_th : n) || n;

    // disease tabs: worst level and the region's cases in 4 weeks
    const tabs = diseases.map((d) => {
      const rows = Object.values(model[d]);
      const worst = rows.reduce((m, r) => (LEVEL_RANK[r.state] > LEVEL_RANK[m] ? r.state : m), "low");
      const sum = rows.reduce((s, r) => s + (r.a.cases_last_4_weeks || 0), 0);
      return `<button class="tab ${d === this._disease ? "on" : ""}" data-d="${d}"><i style="background:${LEVEL_COLOR[worst]}"></i>${esc(dn(d))}<span>${sum}</span></button>`;
    }).join("");

    this.shadowRoot.innerHTML = `<style>${CSS}</style>
<ha-card><div class="mw">
  <div class="hd">
    <img class="logo" src="${MW_ICON}" alt="">
    <div class="ttl"><b>${esc(this._config.title || T.title)}</b><span>${esc(names.map(pn).join(" · "))}</span></div>
    <div class="wk"><b>${T.wk} ${esc(wk || "–")}</b><span>${esc(wkRange)}</span></div>
  </div>
  <div class="tabs">${tabs}</div>
  <div class="body">
    <div class="map" style="--mh:${Number(this._config.map_height) || 320}px">${this._mapSvg(dm, names, home, pn)}</div>
    <div class="side">${this._detail(dm[this._sel], T, pn, dn)}${this._ranking(dm, names, T, pn)}</div>
  </div>
  <div class="ft"><span>${esc(T.source)}</span><span class="lg">${["low", "normal", "elevated", "high"].map((l) => `<i style="background:${LEVEL_COLOR[l]}"></i>${esc(T.lvl[l])}`).join("")}</span></div>
</div></ha-card>`;

    const mapEl = this.shadowRoot.querySelector(".map");
    if (mapEl) {
      if (this._ro) this._ro.disconnect();
      this._ro = new ResizeObserver(() => {
        const r = mapEl.getBoundingClientRect();
        if (!r.width || !r.height) return;
        const a = r.width / r.height;
        if (!this._aspect || Math.abs(a - this._aspect) / this._aspect > 0.04 || Math.abs(r.width - (this._mapW || 0)) > 40) { this._aspect = a; this._mapW = r.width; this._render(); }
      });
      this._ro.observe(mapEl);
    }
    this.shadowRoot.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => { this._disease = b.dataset.d; this._render(); }));
    this.shadowRoot.querySelectorAll("[data-p]").forEach((el) => el.addEventListener("click", () => { this._sel = el.dataset.p; this._render(); }));
    this.shadowRoot.querySelectorAll("[data-more]").forEach((el) => el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId: el.dataset.more }, bubbles: true, composed: true }));
    }));
  }

  _mapSvg(dm, names, home, pn) {
    // view: the selected provinces plus a margin, keeping the aspect sensible
    let [x0, y0, x1, y1] = bboxOf(names);
    const padX = Math.max((x1 - x0) * 0.12, 0.12), padY = Math.max((y1 - y0) * 0.12, 0.12);
    x0 -= padX; x1 += padX; y0 -= padY; y1 += padY;
    const lat0 = (y0 + y1) / 2, k = Math.cos((lat0 * Math.PI) / 180);
    // widen or heighten the view to the shape of the map box, so the region fills it
    const aspect = this._aspect || 1.5;
    const ratio = ((x1 - x0) * k) / (y1 - y0);
    if (ratio < aspect) { const add = ((y1 - y0) * aspect / k - (x1 - x0)) / 2; x0 -= add; x1 += add; }
    else { const add = (((x1 - x0) * k) / aspect - (y1 - y0)) / 2; y0 -= add; y1 += add; }
    const W = Math.round(this._mapW || 700), sx = W / ((x1 - x0) * k), H = Math.round((y1 - y0) * sx);
    const P = ([x, y]) => [((x - x0) * k * sx).toFixed(1), ((y1 - y) * sx).toFixed(1)];
    const path = (n) => rings(n).map((r) => "M" + r.map(P).map((p) => p.join(",")).join("L") + "Z").join("");
    const all = Object.keys(MW_GEO).filter((n) => {
      const [a, b, c, d] = bboxOf([n]);
      return c >= x0 && a <= x1 && d >= y0 && b <= y1;
    });
    const ctx = all.filter((n) => !dm[n]).map((n) => `<path class="ctx" d="${path(n)}"/>`).join("");
    const sel = names.map((n) => {
      const r = dm[n], col = LEVEL_COLOR[r.state];
      return `<path class="pv ${n === this._sel ? "sel" : ""}" data-p="${esc(n)}" d="${path(n)}" style="--c:${col}"/>`;
    }).join("");
    const lbl = names.map((n) => {
      const c = centroid(n);
      if (!c) return "";
      const [cx, cy] = P(c), r = dm[n];
      const big = n === this._sel;
      return `<g class="lb ${big ? "sel" : ""}" data-p="${esc(n)}" transform="translate(${cx},${cy})">
        <text class="cn" y="-3">${r.a.cases_last_4_weeks}</text>${big || W >= 520 ? `<text class="nm" y="${big ? 14 : 11}">${esc(pn(n))}</text>` : ""}</g>`;
    }).join("");
    let pin = "";
    const h = this._hass.config;
    if (h && h.longitude != null && h.longitude > x0 && h.longitude < x1 && h.latitude > y0 && h.latitude < y1) {
      const [px, py] = P([h.longitude, h.latitude]);
      pin = `<g class="pin" transform="translate(${px},${py})"><circle class="pulse" r="7"/><circle r="5.5"/><circle class="dot" r="2.2"/></g>`;
    }
    return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">
      <defs>
        <radialGradient id="sea" cx="35%" cy="55%" r="80%"><stop offset="0" stop-color="#0f2a3d"/><stop offset="1" stop-color="#081521"/></radialGradient>
        <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="rgba(120,180,220,.05)" stroke-width="1"/></pattern>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <rect width="${W}" height="${H}" fill="url(#sea)"/><rect width="${W}" height="${H}" fill="url(#grid)"/>
      <g>${ctx}</g><g>${sel}</g><g>${lbl}</g>${pin}
    </svg>`;
  }

  _detail(r, T, pn, dn) {
    const a = r.a, col = LEVEL_COLOR[r.state];
    const exp = a.expected_last_4_weeks;
    const arrow = { rising: "↗", falling: "↘", steady: "→" }[a.trend] || "";
    const wc = a.weekly_cases || [], md = a.weekly_median || [];
    const max = Math.max(1, ...wc.map((v) => v || 0), ...md.map((v) => v || 0));
    const bw = 100 / wc.length;
    const bars = wc.map((v, i) => {
      const h = ((v || 0) / max) * 46;
      const last4 = i >= wc.length - 4;
      return `<rect x="${(i * bw + bw * 0.18).toFixed(2)}" y="${(50 - h).toFixed(2)}" width="${(bw * 0.64).toFixed(2)}" height="${h.toFixed(2)}" rx="0.8" fill="${last4 ? col : "rgba(255,255,255,.22)"}"/>`;
    }).join("");
    const line = md.map((v, i) => `${i ? "L" : "M"}${(i * bw + bw / 2).toFixed(2)},${(50 - ((v || 0) / max) * 46).toFixed(2)}`).join("");
    const yl = a.cases_same_period_last_year;
    return `<div class="det" style="--c:${col}">
      <div class="dh"><div><b>${esc(pn(a.province))}</b><span>${esc(this._lang === "th" ? a.province : a.province_th)}</span></div>
        <span class="badge" data-more="${esc(r.id)}">${esc(T.lvl[r.state])}</span></div>
      <div class="big"><b>${a.cases_last_4_weeks}</b><span>${esc(T.cases4)}<br><em>${esc(T.usual)} ≈ ${exp}${a.ratio != null ? ` · ×${a.ratio}` : ""} · ${arrow} ${esc(T.trend[a.trend] || "")}</em></span></div>
      <div class="chart"><svg viewBox="0 0 100 52" preserveAspectRatio="none">${bars}<path d="${line}" class="med"/></svg>
        <div class="cl"><span>${esc(T.weeks12)}</span><span><i class="mdl"></i>${esc(T.median)}</span></div></div>
      <div class="yr"><span><b>${a.cases_this_year}</b> ${esc(T.year)}</span>${yl != null ? `<span>${yl} ${esc(T.sameLast)}</span>` : ""}</div>
    </div>`;
  }

  _ranking(dm, names, T, pn) {
    const rows = names.slice().sort((a, b) => (LEVEL_RANK[dm[b].state] - LEVEL_RANK[dm[a].state]) || ((dm[b].a.ratio || 0) - (dm[a].a.ratio || 0)));
    return `<div class="rk">${rows.map((n) => {
      const r = dm[n], a = r.a, col = LEVEL_COLOR[r.state];
      const pct = Math.min(100, ((a.ratio || 0) / 2.5) * 100);
      return `<div class="row ${n === this._sel ? "on" : ""}" data-p="${esc(n)}"><span class="rn">${esc(pn(n))}</span>
        <span class="bar"><i style="width:${pct}%;background:${col}"></i><u></u></span>
        <span class="rv" style="color:${col}">${a.cases_last_4_weeks}<small>/${a.expected_last_4_weeks}</small></span></div>`;
    }).join("")}</div>`;
  }
}

const CSS = `
:host { --gold: #d4af37; }
ha-card { overflow: hidden; background: linear-gradient(160deg, #15161a 0%, #101114 100%); border: 1px solid rgba(212,175,55,.18); }
.mw { padding: 14px; color: #e8e8ea; font-family: var(--primary-font-family, Roboto, sans-serif); container-type: inline-size; }
.mw.empty { display: flex; align-items: center; gap: 12px; opacity: .8; }
.hd { display: flex; align-items: center; gap: 12px; }
.logo { width: 46px; height: 46px; filter: drop-shadow(0 2px 6px rgba(239,83,80,.35)); }
.ttl { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.ttl b { font-size: 17px; letter-spacing: .02em; color: var(--gold); }
.ttl span { font-size: 12px; opacity: .65; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wk { display: flex; flex-direction: column; align-items: flex-end; font-size: 11.5px; opacity: .8; }
.wk b { font-size: 13px; color: #fff; }
.tabs { display: flex; gap: 6px; margin: 12px 0 10px; flex-wrap: wrap; }
.tab { display: flex; align-items: center; gap: 6px; padding: 6px 11px; border-radius: 999px; border: 1px solid rgba(255,255,255,.1); background: rgba(255,255,255,.03); color: #ddd; font: inherit; font-size: 12.5px; cursor: pointer; transition: all .2s; }
.tab i { width: 8px; height: 8px; border-radius: 50%; box-shadow: 0 0 6px currentColor; }
.tab span { opacity: .55; font-size: 11px; }
.tab.on { border-color: var(--gold); background: rgba(212,175,55,.12); color: #fff; }
.body { display: grid; grid-template-columns: 1fr; gap: 12px; }
@container (min-width: 620px) { .body { grid-template-columns: 1.35fr 1fr; } .body .map { height: auto; min-height: clamp(var(--mh), 34cqw, 640px); } }
.map { position: relative; height: var(--mh); border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,.07); background: #081521; }
.map svg { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.ctx { fill: #1d2024; stroke: #2c3036; stroke-width: 1; }
.pv { fill: var(--c); fill-opacity: .28; stroke: var(--c); stroke-width: 1.6; stroke-linejoin: round; cursor: pointer; transition: fill-opacity .2s; }
.pv:hover { fill-opacity: .42; }
.pv.sel { fill-opacity: .45; stroke: var(--gold); stroke-width: 2.4; filter: url(#glow); }
.lb { cursor: pointer; text-anchor: middle; paint-order: stroke; }
.lb text { stroke: rgba(6,12,18,.85); stroke-width: 3px; stroke-linejoin: round; }
.lb .cn { font-size: 19px; font-weight: 700; fill: #fff; }
.lb .nm { font-size: 11px; fill: rgba(255,255,255,.75); letter-spacing: .04em; }
.lb.sel .cn { font-size: 26px; fill: var(--gold); }
.lb.sel .nm { font-size: 12.5px; fill: #fff; }
.pin circle { fill: var(--gold); stroke: #111; stroke-width: 2; }
.pin .dot { fill: #111; stroke: none; }
.pin .pulse { fill: none; stroke: var(--gold); stroke-width: 2; animation: pulse 2.2s ease-out infinite; transform-box: fill-box; transform-origin: center; }
@keyframes pulse { 0% { transform: scale(1); opacity: .9; } 100% { transform: scale(3.2); opacity: 0; } }
.side { display: flex; flex-direction: column; gap: 10px; }
.det { border-radius: 12px; padding: 12px; background: linear-gradient(135deg, color-mix(in srgb, var(--c) 16%, #17181c), #141518 70%); border: 1px solid color-mix(in srgb, var(--c) 45%, transparent); }
.dh { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.dh div { display: flex; flex-direction: column; }
.dh b { font-size: 16px; }
.dh span { font-size: 12px; opacity: .6; }
.badge { padding: 4px 10px; border-radius: 999px; background: var(--c); color: #111; font-weight: 700; font-size: 12px; cursor: pointer; white-space: nowrap; }
.big { display: flex; align-items: center; gap: 10px; margin: 8px 0 6px; }
.big b { font-size: 40px; line-height: 1; color: var(--c); font-weight: 700; }
.big span { font-size: 12.5px; opacity: .9; line-height: 1.35; }
.big em { font-style: normal; opacity: .65; font-size: 11.5px; }
.chart svg { width: 100%; height: 64px; display: block; }
.chart .med { fill: none; stroke: var(--gold); stroke-width: .8; stroke-dasharray: 2 1.2; vector-effect: non-scaling-stroke; }
.cl { display: flex; justify-content: space-between; font-size: 10.5px; opacity: .55; margin-top: 2px; }
.mdl { display: inline-block; width: 12px; border-top: 2px dashed var(--gold); vertical-align: middle; margin-right: 4px; }
.yr { display: flex; justify-content: space-between; gap: 8px; margin-top: 8px; font-size: 11.5px; opacity: .8; flex-wrap: wrap; }
.yr b { color: #fff; font-size: 13px; }
.rk { display: flex; flex-direction: column; gap: 2px; }
.row { display: grid; grid-template-columns: minmax(80px, 1.1fr) 1fr auto; align-items: center; gap: 8px; padding: 5px 8px; border-radius: 8px; cursor: pointer; font-size: 12.5px; }
.row:hover, .row.on { background: rgba(255,255,255,.05); }
.row.on .rn { color: var(--gold); }
.bar { position: relative; height: 6px; border-radius: 3px; background: rgba(255,255,255,.07); overflow: hidden; }
.bar i { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 3px; }
.bar u { position: absolute; left: 40%; top: -2px; bottom: -2px; border-left: 1px dashed rgba(212,175,55,.7); }
.rv { font-weight: 700; font-variant-numeric: tabular-nums; }
.rv small { opacity: .5; font-weight: 400; }
.ft { display: flex; justify-content: space-between; gap: 10px; margin-top: 10px; font-size: 10.5px; opacity: .55; flex-wrap: wrap; }
.lg { display: flex; gap: 10px; flex-wrap: wrap; }
.lg i { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 4px; }
`;

customElements.define("mosquito-watch-card", MosquitoWatchCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "mosquito-watch-card",
  name: "Mosquito Watch",
  description: "Map of dengue, malaria, chikungunya and Zika per Thai province against the 5-year median (Mosquito Watch Thailand).",
  preview: true,
  documentationURL: "https://github.com/mb26-dev/ha-dengue-watch",
});
console.info(`%c MOSQUITO-WATCH-CARD %c ${MW_VERSION} `, "background:#ef5350;color:#fff;font-weight:700", "background:#222;color:#d4af37");
