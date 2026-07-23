/* MiTehuacán app switcher — a top-center button showing the current app with a
 * chevron, opening a centered popover to jump between apps (Combis / Eventos /
 * Directorio / …). Self-injecting, theme- + language-aware, no external deps.
 * Drop into any page: <script src="/combis/appsw.js" defer></script>
 * (the combis app loads it relatively as "appsw.js"). */
(function () {
  if (window.__appsw) return; window.__appsw = 1;

  var I = {
    bus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v11"/><path d="M4 11h16"/><path d="M2 17h20"/><circle cx="8" cy="19.5" r="1.5"/><circle cx="16" cy="19.5" r="1.5"/></svg>',
    cal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9h18"/><path d="M8 2.5v4M16 2.5v4"/></svg>',
    list: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/></svg>',
    home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 11 9-8 9 8"/><path d="M5 9.5V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.5"/></svg>',
    compass: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5 5-2z"/></svg>'
  };

  // combis (rutas) is the HOME module — it lives at /. Others are subpaths.
  var APPS = [
    { k: 'combis',   href: '/',          es: 'Combis',   en: 'Combis',   des_es: 'rutas de combis',      des_en: 'combi routes',   ic: I.bus },
    { k: 'eventos',  href: '/eventos/',  es: 'Eventos',  en: 'Events',   des_es: 'fiestas y eventos',    des_en: 'events & fiestas', ic: I.cal },
    { k: 'descubre', href: '/descubre/', es: 'Descubre', en: 'Discover', des_es: 'novedades, negocios y más', des_en: 'news, places & more', ic: I.compass }
  ];

  function cur() {
    var p = location.pathname;
    if (p.indexOf('/eventos') === 0) return 'eventos';
    if (p.indexOf('/descubre') === 0) return 'descubre';
    return 'combis';   // the home module at /
  }
  function en() { return (document.documentElement.lang || 'es') === 'en'; }
  function app(k) { for (var i = 0; i < APPS.length; i++) if (APPS[i].k === k) return APPS[i]; return APPS[3]; }

  var CSS =
    '#appsw-btn{display:inline-flex;align-items:center;gap:7px;padding:7px 11px;border-radius:99px;flex:none;margin-left:8px;' +
    'font:600 14px system-ui,-apple-system,sans-serif;cursor:pointer;border:1px solid rgba(0,0,0,.10);' +
    'background:rgba(255,255,255,.82);color:#1d1d1f;-webkit-backdrop-filter:blur(18px) saturate(180%);' +
    'backdrop-filter:blur(18px) saturate(180%);box-shadow:0 2px 10px rgba(0,0,0,.12)}' +
    '#appsw-btn svg{width:17px;height:17px;color:#0071e3}' +
    '#appsw-btn .chev{margin-left:1px;opacity:.5;transition:transform .2s}' +
    '#appsw-btn.open .chev{transform:rotate(180deg)}' +
    '#appsw-btn.hint{animation:appswHint 1.4s ease 3}' +
    '@keyframes appswHint{0%,100%{transform:translateY(0)}12%{transform:translateY(-3px)}24%{transform:translateY(0)}}' +
    '#appsw-pop{position:fixed;inset:0;z-index:1201;display:none}#appsw-pop.on{display:block}' +
    '#appsw-back{position:absolute;inset:0;background:rgba(0,0,0,.42)}' +
    '#appsw-card{position:absolute;top:calc(54px + env(safe-area-inset-top));left:50%;transform:translateX(-50%);' +
    'width:min(340px,92vw);background:rgba(255,255,255,.94);color:#1d1d1f;border-radius:18px;overflow:hidden;' +
    'border:1px solid rgba(0,0,0,.08);box-shadow:0 22px 60px rgba(0,0,0,.32);animation:appswIn .18s ease;' +
    '-webkit-backdrop-filter:blur(24px) saturate(180%);backdrop-filter:blur(24px) saturate(180%)}' +
    '@keyframes appswIn{from{opacity:0;transform:translate(-50%,-8px)}to{opacity:1;transform:translate(-50%,0)}}' +
    '.appsw-head{display:flex;justify-content:space-between;align-items:center;padding:12px 14px 11px;font-weight:700;font-size:15px;border-bottom:1px solid rgba(0,0,0,.08)}' +
    '.appsw-head b span{color:#0071e3}' +
    '.appsw-x{border:0;background:none;font-size:19px;line-height:1;cursor:pointer;color:inherit;opacity:.55;padding:2px 4px}' +
    '.appsw-row{display:flex;align-items:center;gap:12px;padding:13px 14px;text-decoration:none;color:inherit;border-bottom:1px solid rgba(0,0,0,.05)}' +
    '.appsw-row:last-child{border-bottom:0}.appsw-row:active,.appsw-row:hover{background:rgba(0,113,227,.07)}' +
    '.appsw-row.on{background:rgba(0,113,227,.06)}' +
    '.appsw-row svg{width:22px;height:22px;color:#0071e3;flex:none}' +
    '.appsw-row .tx{flex:1;min-width:0}.appsw-row .tx b{display:block;font-size:15px;font-weight:600}' +
    '.appsw-row .tx span{font-size:12.5px;opacity:.62}' +
    '.appsw-row .dot{width:8px;height:8px;border-radius:99px;background:#0071e3;flex:none}' +
    '.appsw-soon{padding:11px 14px;font-size:12.5px;opacity:.5;display:flex;align-items:center;gap:8px}' +
    '.appsw-soon span{font-size:16px;line-height:1}' +
    /* the switcher sits inline right after the brand, so both flow together on the
       left; the brand stays visible everywhere. The switcher is the section nav,
       so hide only the redundant in-header section links. */
    'header.site nav a:not(.lng):not(.thm){display:none}' +
    '#topbar .brand .suffix{display:none}' +   /* "· Combis" — the switcher already names the section */
    dark(':root[data-theme=dark]') +
    '@media(prefers-color-scheme:dark){' + dark(':root:not([data-theme=light])') + '}';

  function dark(sel) {
    return sel + ' #appsw-btn{background:rgba(40,40,46,.86);color:#f5f5f7;border-color:rgba(255,255,255,.12)}' +
      sel + ' #appsw-card{background:rgba(32,32,38,.94);color:#f5f5f7;border-color:rgba(255,255,255,.10)}' +
      sel + ' .appsw-head{border-color:rgba(255,255,255,.10)}' +
      sel + ' .appsw-row{border-color:rgba(255,255,255,.06)}' +
      sel + ' .appsw-row:active,' + sel + ' .appsw-row:hover,' + sel + ' .appsw-row.on{background:rgba(10,132,255,.14)}';
  }

  var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);

  var btn = document.createElement('button');
  btn.id = 'appsw-btn'; btn.setAttribute('aria-haspopup', 'true'); btn.setAttribute('aria-expanded', 'false');
  var pop = document.createElement('div'); pop.id = 'appsw-pop';
  // place the switcher inline right after the brand so the two flow together on
  // the left; the header's controls (gear / toggles) stay on the right.
  var brand = document.querySelector('#topbar .brand, header.site .brand');
  if (brand && brand.parentNode) brand.parentNode.insertBefore(btn, brand.nextSibling);
  else document.body.appendChild(btn);
  document.body.appendChild(pop);

  function renderBtn() {
    var a = app(cur());
    btn.innerHTML = a.ic + '<span class="lbl">' + (en() ? a.en : a.es) + '</span>' +
      '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>';
  }
  function renderPop() {
    var c = cur();
    var rows = APPS.map(function (a) {
      return '<a class="appsw-row' + (a.k === c ? ' on' : '') + '" href="' + a.href + '">' + a.ic +
        '<span class="tx"><b>' + (en() ? a.en : a.es) + '</b><span>' + (en() ? a.des_en : a.des_es) + '</span></span>' +
        (a.k === c ? '<span class="dot"></span>' : '') + '</a>';
    }).join('');
    pop.innerHTML = '<div id="appsw-back"></div><div id="appsw-card" role="menu">' +
      '<div class="appsw-head"><b>mi<span>tehuacán</span></b><button class="appsw-x" aria-label="cerrar">✕</button></div>' +
      rows +
      '<div class="appsw-soon"><span>+</span>' + (en() ? 'more apps coming soon' : 'más apps pronto') + '</div></div>';
    pop.querySelector('#appsw-back').onclick = close;
    pop.querySelector('.appsw-x').onclick = close;
  }
  function open() { renderPop(); pop.classList.add('on'); btn.classList.add('open'); btn.setAttribute('aria-expanded', 'true'); }
  function close() { pop.classList.remove('on'); btn.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); }
  btn.onclick = function () { pop.classList.contains('on') ? close() : open(); };
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

  renderBtn();
  // re-label on language change (the toggles flip <html lang>)
  new MutationObserver(function () { renderBtn(); if (pop.classList.contains('on')) renderPop(); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });

  // one-time discovery hint (pulse the chevron) until first open
  try {
    if (!localStorage.appswSeen) {
      btn.classList.add('hint');
      btn.addEventListener('click', function () { try { localStorage.appswSeen = 1; } catch (e) {} btn.classList.remove('hint'); }, { once: true });
    }
  } catch (e) {}
})();
