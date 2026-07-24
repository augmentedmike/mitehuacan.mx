/* Directory of self-registered businesses (public read of /api/negocios).
   The list shows compact cards; tapping one slides in a full detail panel with a
   shareable slug URL (?n=<slug>). Contact (WhatsApp icon) lives in the panel, not
   the list. Category slug -> label comes from window.NEG_CATS (built from the alta
   form so it never drifts). */
(function () {
  var CATS = window.NEG_CATS || {};
  var box = document.getElementById('negocios');
  var panel = document.getElementById('neg-panel');
  var pbody = document.getElementById('neg-panel-body');
  if (!box || !panel) return;
  var list = [], bySlug = {};

  var WA = '<svg viewBox="0 0 32 32" width="24" height="24" fill="currentColor" aria-hidden="true">' +
    '<path d="M16 3C9 3 3.5 8.5 3.5 15.5c0 2.4.7 4.7 1.9 6.7L3 29l7-1.8c1.9 1 4 1.6 6.1 1.6 7 0 12.5-5.5 ' +
    '12.5-12.5S23 3 16 3zm0 22.8c-1.9 0-3.7-.5-5.3-1.5l-.4-.2-4.1 1.1 1.1-4-.3-.4a10.2 10.2 0 0 1-1.6-5.6' +
    'C5.5 9.6 10.2 5 16 5s10.5 4.6 10.5 10.5S21.8 25.8 16 25.8zm5.8-7.9c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.2' +
    '-.2.3-.8 1-.9 1.1-.2.2-.3.2-.6.1-1.8-.9-3-1.6-4.2-3.6-.3-.5.3-.5.9-1.6.1-.2 0-.4 0-.5-.1-.2-.7-1.7-1-2.3' +
    '-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.2.2 2.2 3.4 5.4 4.7 3.2 1.4 3.2.9 ' +
    '3.8.9.6-.1 1.9-.8 2.1-1.5.3-.8.3-1.4.2-1.5-.1-.2-.3-.2-.6-.4z"/></svg>';

  function L(c) { return CATS[c] || (c ? c.replace(/-/g, ' ').replace(/\b\w/g, function (m) { return m.toUpperCase(); }) : ''); }
  function E(s) { var d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }
  function slug(s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 50); }
  function slugFor(n) { return slug(n.name) + '-' + n.id; }

  function card(n, i) {
    var cat = L(n.category) + (n.category2 ? ' · ' + L(n.category2) : '');
    var meta = [n.address, n.colonia, n.hours].filter(Boolean).map(E).join(' · ');
    return '<button class="neg-card" type="button" onclick="__negOpen(' + i + ')">' +
      (n.verified ? '<span class="neg-badge">Verificado</span>' : '') +
      '<div class="nm">' + E(n.name) + '</div>' +
      (cat ? '<span class="dir-cat">' + E(cat) + '</span>' : '') +
      (n.description ? '<div class="desc">' + E(String(n.description).slice(0, 150)) + '</div>' : '') +
      (meta ? '<div class="mrow">' + meta + '</div>' : '') +
      '<span class="neg-go" aria-hidden="true">›</span></button>';
  }

  function detail(n) {
    var cat = L(n.category) + (n.category2 ? ' · ' + L(n.category2) : '');
    var w = String(n.whatsapp || n.phone || '').replace(/\D/g, '');
    var out = '<h2 class="np-name">' + E(n.name) + '</h2>' +
      (n.verified ? '<span class="neg-badge">Verificado</span>' : '') +
      (cat ? '<div class="np-cat">' + E(cat) + '</div>' : '') +
      (n.description ? '<p class="np-desc">' + E(n.description) + '</p>' : '');
    var rows = [];
    if (n.address || n.colonia) rows.push(['Dirección', [n.address, n.colonia].filter(Boolean).join(', ')]);
    if (n.hours) rows.push(['Horario', n.hours]);
    if (n.service_area) rows.push(['Zonas que atiende', n.service_area]);
    if (n.price_from) rows.push(['Precio desde', '$' + n.price_from + (n.price_note ? ' ' + n.price_note : '')]);
    rows.forEach(function (r) { out += '<div class="np-row"><span>' + E(r[0]) + '</span><b>' + E(r[1]) + '</b></div>'; });
    var soc = [];
    if (n.facebook) soc.push('<a href="' + E(n.facebook) + '" rel="nofollow noopener">Facebook</a>');
    if (n.instagram) soc.push('<a href="https://instagram.com/' + E(String(n.instagram).replace(/^@/, '')) + '" rel="nofollow noopener">Instagram</a>');
    if (n.website) soc.push('<a href="' + E(n.website) + '" rel="nofollow noopener">Sitio web</a>');
    if (soc.length) out += '<div class="np-soc">' + soc.join(' · ') + '</div>';
    var acts = '';
    if (w) acts += '<a class="np-wa" href="https://wa.me/52' + w + '" rel="nofollow noopener" aria-label="WhatsApp">' + WA + '</a>';
    if (n.has_location && n.lat && n.lon) acts += '<a class="np-map" href="/?to=' + n.lon + ',' + n.lat + '&n=' + encodeURIComponent(n.name) + '&biz=' + slugFor(n) + '">Ver en el mapa</a>';
    if (acts) out += '<div class="np-actions">' + acts + '</div>';
    return out;
  }

  function curSlug() { var m = /[?&]n=([^&]+)/.exec(location.search); return m ? m[1] : null; }

  window.__negOpen = function (i) {
    var n = list[i]; if (!n) return;
    pbody.innerHTML = detail(n);
    pbody.scrollTop = 0;
    panel.classList.add('show');
    document.documentElement.style.overflow = 'hidden';
    var s = slugFor(n);
    if (curSlug() !== s) history.pushState({ neg: s }, '', '?n=' + s);
  };
  window.__negClose = function (fromPop) {
    panel.classList.remove('show');
    document.documentElement.style.overflow = '';
    if (!fromPop && curSlug()) history.pushState({}, '', location.pathname);
  };
  window.addEventListener('popstate', function () {
    var s = curSlug();
    if (s && bySlug[s] != null) window.__negOpen(bySlug[s]);
    else window.__negClose(true);
  });

  fetch('/api/negocios').then(function (r) { return r.json(); }).then(function (d) {
    list = (d && d.businesses) || [];
    var empty = document.getElementById('neg-empty');
    if (!list.length) { if (empty) empty.hidden = false; return; }
    list.forEach(function (n, i) { bySlug[slugFor(n)] = i; });
    box.innerHTML = list.map(card).join('');
    var s = curSlug();
    if (s && bySlug[s] != null) window.__negOpen(bySlug[s]);
  }).catch(function () {});
})();
