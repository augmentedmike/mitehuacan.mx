#!/usr/bin/env python3
"""Generate the mitehuacan.mx static site into /site (Cloudflare Pages ready).

The homepage is a retro portal dashboard for the city; combis is its first section.
The only content page under combis is /combis/acerca/. (Per-route SEO pages were
removed by decision 2026-07-14 — `git log` has the last version if they ever earn
their way back.)

  site/index.html               retro portal dashboard (links into /combis/ etc.)
  site/combis/                  the interactive map app (copied from app)
  site/combis/acerca/           about page
  site/_redirects site/robots.txt site/sitemap.xml
"""
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repo root
REPO = ROOT
SITE = REPO / "build"
DOMAIN = "https://mitehuacan.mx"
SECTION = "combis"
CITY_NAME = "Tehuacán"

# mobile-first: base styles are the phone layout; min-width queries add desktop touches
CSS = """
:root{--bg:#f5f5f7;--panel:rgba(255,255,255,.62);--ink:#1d1d1f;--ink2:#6e6e73;--line:rgba(0,0,0,.08);
 --accent:#0071e3;--chip:rgba(255,255,255,.8);--glass:rgba(255,255,255,.55);--hl:rgba(255,255,255,.75);
 --shadow:0 8px 32px rgba(0,0,0,.08);--g1:rgba(0,113,227,.10);--g2:rgba(255,150,70,.08);
 --livebg:rgba(255,255,255,.72);--livebrd:rgba(0,113,227,.35);--accsh:rgba(0,113,227,.30)}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0e0e12;--panel:rgba(28,28,34,.6);
 --ink:#f5f5f7;--ink2:#98989d;--line:rgba(255,255,255,.10);--accent:#0a84ff;--chip:rgba(66,66,74,.5);
 --glass:rgba(24,24,30,.55);--hl:rgba(255,255,255,.08);--shadow:0 8px 32px rgba(0,0,0,.5);
 --g1:rgba(10,132,255,.14);--g2:rgba(255,140,60,.05);--livebg:rgba(16,42,74,.45);
 --livebrd:rgba(10,132,255,.45);--accsh:rgba(10,132,255,.35)}}
:root[data-theme=dark]{--bg:#0e0e12;--panel:rgba(28,28,34,.6);
 --ink:#f5f5f7;--ink2:#98989d;--line:rgba(255,255,255,.10);--accent:#0a84ff;--chip:rgba(66,66,74,.5);
 --glass:rgba(24,24,30,.55);--hl:rgba(255,255,255,.08);--shadow:0 8px 32px rgba(0,0,0,.5);
 --g1:rgba(10,132,255,.14);--g2:rgba(255,140,60,.05);--livebg:rgba(16,42,74,.45);
 --livebrd:rgba(10,132,255,.45);--accsh:rgba(10,132,255,.35)}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 system-ui,-apple-system,sans-serif;color:var(--ink);background:var(--bg)}
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
 background:radial-gradient(55% 45% at 8% 0%,var(--g1),transparent 65%),
            radial-gradient(45% 40% at 94% 6%,var(--g2),transparent 60%)}
header.site{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px;
 padding:0 14px;height:50px;border-bottom:1px solid var(--line);background:var(--glass);
 -webkit-backdrop-filter:blur(20px) saturate(180%);backdrop-filter:blur(20px) saturate(180%)}
header.site .brand{color:var(--ink);text-decoration:none;font-weight:700;font-size:17px;flex:none}
header.site .brand span{color:var(--accent)}
header.site nav{display:flex;gap:2px;margin-left:auto}
header.site nav a{color:var(--ink2);text-decoration:none;font-size:14px;padding:6px 10px;border-radius:8px;white-space:nowrap}
header.site nav a.on,header.site nav a:active{color:var(--ink);background:var(--chip)}
.crumbs{font-size:13px;color:var(--ink2);padding:10px 0 0}
.crumbs a{color:var(--ink2);text-decoration:none}
.crumbs a:active,.crumbs a:hover{color:var(--accent)}
.crumbs .sep{margin:0 6px;opacity:.6}
.wrap{max-width:900px;margin:0 auto;padding:0 16px 28px}
h1{font-size:23px;margin:.7em 0 .35em;line-height:1.25}
h2{font-size:18px;margin:1.5em 0 .5em}
p{margin:.5em 0}.muted{color:var(--ink2);font-size:14px}
a{color:var(--accent)}
.btn{display:block;text-align:center;background:var(--accent);color:#fff;padding:12px 20px;border-radius:12px;
 text-decoration:none;font-weight:600;margin:8px 0;box-shadow:0 4px 16px var(--accsh)}
.btn.ghost{background:var(--panel);color:var(--ink);border:1px solid var(--line);box-shadow:none}
.btnrow{margin:14px 0}
form#report-form{display:flex;flex-direction:column;gap:10px;max-width:560px}
form#report-form input[type=text],form#report-form textarea{width:100%;padding:11px 12px;
 border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink);
 font:inherit;font-size:15px}
form#report-form input:focus,form#report-form textarea:focus{outline:2px solid var(--accent);outline-offset:-1px}
form#report-form .btn{margin:0;border:none;cursor:pointer;font:inherit;font-weight:600}
footer.site{margin-top:36px;padding:18px 16px calc(18px + env(safe-area-inset-bottom));
 border-top:1px solid var(--line);font-size:13px;color:var(--ink2)}
footer.site .cols{max-width:900px;margin:0 auto;display:flex;flex-direction:column;gap:8px}
footer.site a{color:var(--ink2)}
@media(min-width:640px){
 h1{font-size:27px}
 .btn{display:inline-block;margin:6px 10px 6px 0}
 footer.site .cols{flex-direction:row;justify-content:space-between}
}
html[lang=en] .es{display:none!important}
html[lang=es] .en{display:none!important}
header.site nav a.lng{padding:6px 8px;font-weight:600;font-size:12px;border:1px solid var(--line);border-radius:8px}
html[lang=es] header.site nav a.lng[data-l=es]{display:none}
html[lang=en] header.site nav a.lng[data-l=en]{display:none}
header.site nav a.thm{padding:6px 8px;font-size:14px;line-height:1.3}
.ic-sun{display:none}
:root[data-theme=dark] .ic-sun{display:inline}
:root[data-theme=dark] .ic-moon{display:none}
@media(max-width:480px){header.site{gap:6px;padding:0 10px}header.site nav a{padding:6px 7px;font-size:13px}}
"""

# runs in <head>: sets <html lang> + data-theme before first paint so the .es/.en
# rules and theme vars pick the right state with no flash; TITLES is defined per page
LANG_JS = """<script>
const LANG=(()=>{try{const s=localStorage.mtLang;if(s==='es'||s==='en')return s}catch(e){}
return (navigator.language||'es').toLowerCase().startsWith('en')?'en':'es'})();
document.documentElement.lang=LANG;
const THEME=(()=>{try{const s=localStorage.mtTheme;if(s==='light'||s==='dark')return s}catch(e){}
return matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'})();
document.documentElement.dataset.theme=THEME;
function syncLang(){const L=document.documentElement.lang;
if(window.TITLES&&TITLES[L])document.title=TITLES[L];
document.querySelectorAll('[data-ph-es]').forEach(el=>el.placeholder=L==='en'?el.dataset.phEn:el.dataset.phEs);}
function setLang(l){try{localStorage.mtLang=l}catch(e){}document.documentElement.lang=l;syncLang();return false}
function toggleTheme(){const th=document.documentElement.dataset.theme==='dark'?'light':'dark';
try{localStorage.mtTheme=th}catch(e){}document.documentElement.dataset.theme=th;return false}
addEventListener('DOMContentLoaded',syncLang);
</script>"""

SVG_MOON = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>"""
SVG_SUN = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>"""

LANG_LINKS = f"""<a href="#" class="lng" data-l="es" onclick="return setLang('es')">ES</a>
<a href="#" class="lng" data-l="en" onclick="return setLang('en')">EN</a>
<a href="#" class="thm" onclick="return toggleTheme()" aria-label="tema / theme"><span class="ic-moon">{SVG_MOON}</span><span class="ic-sun">{SVG_SUN}</span></a>"""

NAV = f"""<header class="site">
<a class="brand" href="/">mi<span>tehuacan</span>.mx <span style="color:var(--ink2);font-weight:400">· Combis</span></a>
<nav>
{LANG_LINKS}
</nav>
</header>"""

FOOTER = f"""<footer class="site"><div class="cols">
<div><span class="es">MiTehuacán — el portal libre y gratuito de Tehuacán, Puebla.</span><span class="en">MiTehuacán — the free, open portal of Tehuacán, Puebla.</span><br>
<span class="es">Datos abiertos (ODbL) · código abierto (AGPL) · hecho con proyectos ciudadanos y OpenStreetMap.</span><span class="en">Open data (ODbL) · open source (AGPL) · built on citizen projects and OpenStreetMap.</span><br>
<span class="es">Hecho con ♥ en Tehuacán por</span><span class="en">Built with ♥ in Tehuacán by</span> <a href="https://tylt-dev.vercel.app/" rel="noopener">Tylt</a> · <a href="https://github.com/augmentedmike/mitehuacan.mx" rel="me">GitHub</a></div>
<div><a href="/"><span class="es">Inicio</span><span class="en">Home</span></a> · <a href="/{SECTION}/">Combis</a></div>
</div></footer>"""


def bi(es, en):
    """Bilingual inline text: both languages in the DOM, CSS shows the active one."""
    return f'<span class="es">{es}</span><span class="en">{en}</span>'


def crumbs(items):
    # labels are generator-controlled HTML (may contain bilingual spans) — not escaped
    out = []
    for label, href in items:
        out.append(f'<a href="{href}">{label}</a>' if href else f'<span>{label}</span>')
    return '<nav class="crumbs" aria-label="ruta de navegación">' + '<span class="sep">›</span>'.join(out) + '</nav>'


def page(title, desc, body, canonical, active="", crumb_items=None, title_en=None):
    nav = NAV
    bc = crumbs(crumb_items) if crumb_items else ""
    titles = f"<script>window.TITLES={json.dumps({'es': title, 'en': title_en or title}, ensure_ascii=False)}</script>"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<style>{CSS}</style>
{titles}
{LANG_JS}
</head>
<body>
{nav}
<div class="wrap">
{bc}
{body}
</div>
{FOOTER}
</body>
</html>"""


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    shutil.copytree(ROOT / "src" / "app", SITE / SECTION)
    # generated data artifacts live apart from source; merge them into the build
    for item in (ROOT / "resources" / "map-data").iterdir():
        dest = SITE / SECTION / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    # ---- homepage: the town portal — brand page with one card per section.
    # Combis is live; the rest launch later. Add a card here when a section ships.
    home_css = CSS + """
.hero{padding:34px 0 6px}
.hero h1{font-size:34px;margin:0;letter-spacing:-.5px}
.hero h1 span{color:var(--accent)}
.hero p{font-size:17px;color:var(--ink2);margin:8px 0 0;max-width:34em}
.cards{display:grid;grid-template-columns:1fr;gap:16px;margin:26px 0 8px}
@media(min-width:640px){.cards{grid-template-columns:1fr 1fr}}
.card{position:relative;display:block;padding:20px;border:1px solid var(--line);border-radius:20px;
 background:var(--panel);color:var(--ink);text-decoration:none;
 -webkit-backdrop-filter:blur(20px) saturate(180%);backdrop-filter:blur(20px) saturate(180%);
 box-shadow:var(--shadow),inset 0 1px 0 var(--hl);
 transition:transform .25s ease,box-shadow .25s ease}
a.card:hover{transform:translateY(-2px);box-shadow:0 14px 40px var(--accsh),inset 0 1px 0 var(--hl)}
.card .ico{display:block;margin-bottom:12px;color:var(--accent)}
.card h2{font-size:18px;margin:0 0 4px}
.card p{font-size:14px;color:var(--ink2);margin:0}
.badge{position:absolute;top:16px;right:16px;font-size:11px;font-weight:600;
 padding:4px 10px;border-radius:99px;background:var(--chip);color:var(--ink2);border:1px solid var(--line);
 -webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px)}
a.card.live{grid-column:1/-1;border-color:var(--livebrd);background:var(--livebg)}
a.card.live .badge{background:var(--accent);color:#fff;border-color:transparent;box-shadow:0 2px 10px var(--accsh)}
a.card.live h2{font-size:21px}
a.card.live p{font-size:15px;max-width:38em}
a.card.live .go{display:inline-block;margin-top:14px;background:var(--accent);color:#fff;
 font-weight:600;font-size:15px;padding:11px 20px;border-radius:12px;box-shadow:0 4px 16px var(--accsh);
 transition:filter .2s}
a.card.live:hover .go{filter:brightness(1.08)}
.card.soon{opacity:.75}
.pitch{font-size:14px;color:var(--ink2);margin:18px 0 0}
"""
    icon = lambda paths: ('<span class="ico"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" '
                          'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
                          + paths + '</svg></span>')
    ICO_BUS = icon('<path d="M4 17V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v11"/><path d="M4 11h16"/><path d="M2 17h20"/>'
                   '<circle cx="8" cy="19.5" r="1.5"/><circle cx="16" cy="19.5" r="1.5"/>')
    ICO_BAG = icon('<path d="M6 7h12l1 13H5L6 7Z"/><path d="M9 10V6a3 3 0 0 1 6 0v4"/>')
    ICO_CASE = icon('<rect x="3" y="7" width="18" height="13" rx="2"/>'
                    '<path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><path d="M3 12h18"/>')
    ICO_HOME = icon('<path d="m3 11 9-8 9 8"/><path d="M5 9.5V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.5"/>')
    home_body = f"""
<div class="hero">
<h1>Mi<span>Tehuacán</span></h1>
<p class="es">El portal de Tehuacán, Puebla — servicios libres y gratuitos, hechos por y para tehuacaneros.</p>
<p class="en">The portal of Tehuacán, Puebla — free, open services made by and for the people of Tehuacán.</p>
</div>
<div class="cards">
<a class="card live" href="/{SECTION}/">
 <span class="badge">{bi('Ya disponible', 'Live now')}</span>
 {ICO_BUS}
 <h2>Combis</h2>
 <p class="es">¿En qué combi me voy? Más de 80 rutas en un mapa, con planificador de viajes:
 dinos de dónde sales y a dónde vas, y te decimos qué combi tomar.</p>
 <p class="en">Which combi do I take? 80+ routes on one map, with a trip planner:
 tell us where you start and where you're going, and we'll tell you which combi to take.</p>
 <span class="go">{bi('Abrir el mapa de combis', 'Open the combi map')}</span>
</a>
<div class="card soon">
 <span class="badge">{bi('Próximamente', 'Coming soon')}</span>
 {ICO_BAG}
 <h2>Mi Tianguis</h2>
 <p class="es">El mercado en línea de Tehuacán: compra y vende entre vecinos, sin comisiones.</p>
 <p class="en">Tehuacán's online marketplace: buy and sell between neighbors, commission-free.</p>
</div>
<div class="card soon">
 <span class="badge">{bi('Próximamente', 'Coming soon')}</span>
 {ICO_CASE}
 <h2>{bi('Empleos', 'Jobs')}</h2>
 <p class="es">Chamba local: vacantes de la región y un lugar para ofrecer tu talento.</p>
 <p class="en">Local work: openings around the region and a place to offer your skills.</p>
</div>
<div class="card soon">
 <span class="badge">{bi('Próximamente', 'Coming soon')}</span>
 {ICO_HOME}
 <h2>{bi('Rentas', 'Rentals')}</h2>
 <p class="es">Casas, departamentos y locales en renta, publicados por gente de aquí.</p>
 <p class="en">Houses, apartments and storefronts for rent, listed by local people.</p>
</div>
</div>
<p class="pitch es">Esto apenas empieza — MiTehuacán va a crecer sección por sección.
¿Tienes una idea para el portal? <a href="https://github.com/augmentedmike/mitehuacan.mx">Cuéntanos</a>.</p>
<p class="pitch en">This is only the beginning — MiTehuacán will grow section by section.
Got an idea for the portal? <a href="https://github.com/augmentedmike/mitehuacan.mx">Tell us</a>.</p>
"""
    home_titles = json.dumps({"es": "MiTehuacán — el portal de Tehuacán, Puebla",
                              "en": "MiTehuacán — the portal of Tehuacán, Puebla"}, ensure_ascii=False)
    (SITE / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MiTehuacán — el portal de Tehuacán, Puebla</title>
<meta name="description" content="El portal de Tehuacán, Puebla: mapa y rutas de combis, y pronto tianguis en línea, empleos y rentas. Libre y gratuito.">
<meta name="theme-color" content="#0a0b12">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="MiTehuacán">
<link rel="manifest" href="/{SECTION}/manifest.json">
<link rel="apple-touch-icon" href="/{SECTION}/icon-192.png">
<link rel="canonical" href="{DOMAIN}/">
<style>{home_css}</style>
<script>window.TITLES={home_titles}</script>
{LANG_JS}
</head>
<body>
<header class="site">
<a class="brand" href="/">mi<span>tehuacan</span>.mx</a>
<nav>
<a href="/{SECTION}/">Combis</a>
{LANG_LINKS}
</nav>
</header>
<div class="wrap">
{home_body}
</div>
{FOOTER}
</body>
</html>""", encoding="utf-8")

    # ---- redirects (QR stickers + legacy paths), robots, sitemap
    (SITE / "_redirects").write_text(
        f"# QR stickers resolve via functions/qr/[id].js (route deep-links); no\n"
        f"# static rule here — Pages _redirects would shadow the function.\n"
        f"# legacy: route pages removed 2026-07 -> deep-link into the map\n"
        f"/tehuacan/rutas/* /{SECTION}/?ruta=:splat 301\n"
        f"/appa/* /{SECTION}/ 301\n"
        f"/tehuacan/ /{SECTION}/ 301\n"
        f"# about page removed 2026-07\n"
        f"/acerca/ /{SECTION}/ 301\n"
        f"/{SECTION}/acerca/ /{SECTION}/ 301\n"
        , encoding="utf-8")
    # a real 404 page — without one, Cloudflare Pages SPA-falls-back to the
    # homepage with a 200 for every unmatched path (including removed APIs)
    (SITE / "404.html").write_text(f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>404 — MiTehuacán</title><style>{CSS}</style></head>
<body><div class="wrap" style="padding-top:60px;text-align:center">
<h1>404</h1>
<p class="es">Esta página no existe. <a href="/{SECTION}/">Ir al mapa de combis</a></p>
<p class="en">This page does not exist. <a href="/{SECTION}/">Go to the combi map</a></p>
</div></body></html>""", encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    urls = [f"{DOMAIN}/", f"{DOMAIN}/{SECTION}/"]
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")

    n_pages = len(list(SITE.rglob("index.html")))
    print(f"site built: {n_pages} pages -> {SITE}")


if __name__ == "__main__":
    main()
