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
header.site .brand{color:var(--ink);text-decoration:none;font-weight:700;font-size:16px;flex:none;white-space:nowrap}
header.site .brand span{color:var(--accent)}
header.site nav{display:flex;gap:2px;margin-left:auto}
header.site nav a{color:var(--ink2);text-decoration:none;font-size:14px;padding:6px 10px;border-radius:8px;white-space:nowrap}
header.site nav a.on,header.site nav a:active{color:var(--ink);background:var(--chip)}
.crumbs{font-size:13px;color:var(--ink2);padding:10px 0 0}
.crumbs a{color:var(--ink2);text-decoration:none}
.crumbs a:active,.crumbs a:hover{color:var(--accent)}
.crumbs .sep{margin:0 6px;opacity:.6}
.wrap{max-width:480px;margin:0 auto;padding:0 16px 28px}
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
/* no desktop layout — mobile everywhere; on large screens the mobile column is
   wrapped in a phone frame (see the min-width:701px block at the end). */
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
/* All mobile: on anything wider than a phone, render the SAME mobile layout inside
   a phone outline on a dark zinc backdrop — identical treatment to the rutas app,
   so every module looks like one mobile app. The content scrolls inside the frame;
   transform makes the body the containing block so the app-switcher stays in-frame. */
@media(min-width:701px){
 html{background:#18181b;display:flex;align-items:center;justify-content:center;height:100dvh;overflow:hidden}
 body{width:412px;max-width:412px;height:min(884px,96dvh);min-height:0;margin:0;
  border:11px solid #0a0a0b;border-radius:46px;
  box-shadow:0 0 0 2px #3f3f46,0 40px 90px rgba(0,0,0,.6);
  overflow-y:auto;overflow-x:hidden;position:relative;transform:translateZ(0)}
}
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
<a class="brand" href="/">mi<span>tehuacan</span>.mx</a>
<nav>
{LANG_LINKS}
</nav>
</header>"""

FOOTER = f"""<footer class="site"><div class="cols">
<div><span class="es">MiTehuacán — el portal libre y gratuito de Tehuacán, Puebla.</span><span class="en">MiTehuacán — the free, open portal of Tehuacán, Puebla.</span><br>
<span class="es">Datos abiertos (ODbL) · código abierto (AGPL) · hecho con proyectos ciudadanos y OpenStreetMap.</span><span class="en">Open data (ODbL) · open source (AGPL) · built on citizen projects and OpenStreetMap.</span><br>
<span class="es">Hecho con ♥ en Tehuacán por</span><span class="en">Built with ♥ in Tehuacán by</span> <a href="https://tylt-dev.vercel.app/" rel="noopener">Tylt</a> · <a href="https://github.com/augmentedmike/mitehuacan.mx" rel="me">GitHub</a></div>
<div><a href="/">Combis</a> · <a href="/eventos/"><span class="es">Eventos</span><span class="en">Events</span></a> · <a href="/descubre/"><span class="es">Descubre</span><span class="en">Discover</span></a> · <a href="/roadmap/">Roadmap</a></div>
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
<script src="/appsw.js" defer></script>
</body>
</html>"""


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    # The deploy root (vercel.json outputDirectory) IS this folder: the app-of-apps.
    # The HOME module is served at / (rutas/combis today); other modules are subpaths.
    # To change the home module later, copy a different one to APPROOT root.
    APPROOT = SITE / SECTION
    shutil.copytree(ROOT / "src" / "app", APPROOT)   # HOME module (combis) -> served at /
    # generated data artifacts live apart from source; merge them into the build
    for item in (ROOT / "resources" / "map-data").iterdir():
        dest = APPROOT / item.name
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
.fb{margin:28px 0 0;padding:18px;border:1px solid var(--line);border-radius:20px;background:var(--panel)}
.fb-h{font-size:18px;margin:0 0 4px}
.fb-sub{font-size:13.5px;color:var(--ink2);margin:0 0 6px}
.fbform{display:flex;flex-direction:column;gap:8px;margin:14px 0 0}
.fbform+.fbform{border-top:1px solid var(--line);padding-top:14px}
.fbform textarea,.fbform input.fb-contact{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink);font:inherit;font-size:15px}
.fbform textarea{min-height:66px;resize:vertical}
.fbform textarea:focus,.fbform input:focus{outline:2px solid var(--accent);outline-offset:-1px}
.fbform button{background:var(--accent);color:#fff;border:none;border-radius:10px;padding:11px;font:inherit;font-weight:600;cursor:pointer}
.fb-hp{display:none!important}
.fb-thanks{color:var(--accent);font-weight:600;margin:6px 0}
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
    ICO_CAL = icon('<rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9h18"/>'
                   '<path d="M8 2.5v4M16 2.5v4"/><path d="M7.5 13h3v3h-3z"/>')
    home_body = f"""
<div class="hero">
<h1>Mi<span>Tehuacán</span></h1>
<p class="es">El portal de Tehuacán, Puebla — servicios libres y gratuitos, hechos por y para tehuacaneros.</p>
<p class="en">The portal of Tehuacán, Puebla — free, open services made by and for the people of Tehuacán.</p>
</div>
<div class="cards">
<a class="card live" href="/">
 <span class="badge">{bi('Ya disponible', 'Live now')}</span>
 {ICO_BUS}
 <h2>Combis</h2>
 <p class="es">¿En qué combi me voy? Más de 80 rutas en un mapa, con planificador de viajes:
 dinos de dónde sales y a dónde vas, y te decimos qué combi tomar.</p>
 <p class="en">Which combi do I take? 80+ routes on one map, with a trip planner:
 tell us where you start and where you're going, and we'll tell you which combi to take.</p>
 <span class="go">{bi('Abrir el mapa de combis', 'Open the combi map')}</span>
</a>
<a class="card" href="/eventos/">
 <span class="badge">{bi('Nuevo', 'New')}</span>
 {ICO_CAL}
 <h2>{bi('Eventos', 'Events')}</h2>
 <p class="es">La agenda de la ciudad: ferias, fiestas patronales y eventos culturales de Tehuacán y su región.</p>
 <p class="en">The city agenda: fairs, patron-saint fiestas and cultural events across Tehuacán and its region.</p>
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
"""
    # feedback + bug forms -> D1 (no email, no github). Defined apart from the
    # f-string above because it carries braces-heavy JS.
    home_body += '''<div class="fb">
<h2 class="fb-h"><span class="es">Ideas y problemas</span><span class="en">Ideas &amp; problems</span></h2>
<p class="fb-sub"><span class="es">Esto apenas empieza — MiTehuacán crece sección por sección. Cuéntanos qué te gustaría ver o repórtanos una falla. Llega directo a nosotros.</span><span class="en">This is only the beginning — MiTehuacán grows section by section. Tell us what you'd like to see, or report a problem. It comes straight to us.</span></p>
<form class="fbform" data-kind="idea">
<textarea required maxlength="1500" data-ph-es="Comparte una idea…" data-ph-en="Share an idea…" placeholder="Comparte una idea…"></textarea>
<input type="text" maxlength="120" class="fb-contact" data-ph-es="WhatsApp o nombre (opcional)" data-ph-en="WhatsApp or name (optional)" placeholder="WhatsApp o nombre (opcional)">
<input type="text" class="fb-hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<button type="submit"><span class="es">Enviar idea</span><span class="en">Send idea</span></button>
</form>
<form class="fbform" data-kind="bug">
<textarea required maxlength="1500" data-ph-es="Describe el problema…" data-ph-en="Describe the problem…" placeholder="Describe el problema…"></textarea>
<input type="text" maxlength="120" class="fb-contact" data-ph-es="WhatsApp o nombre (opcional)" data-ph-en="WhatsApp or name (optional)" placeholder="WhatsApp o nombre (opcional)">
<input type="text" class="fb-hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<button type="submit"><span class="es">Reportar problema</span><span class="en">Report a problem</span></button>
</form>
</div>
<script>
document.querySelectorAll('.fbform').forEach(function(f){
 f.addEventListener('submit',function(e){e.preventDefault();
  var hp=f.querySelector('.fb-hp').value,msg=f.querySelector('textarea').value.trim();
  if(!hp&&msg.length<5)return;
  f.querySelector('button').disabled=true;
  fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
   kind:f.dataset.kind,message:msg,contact:f.querySelector('.fb-contact').value.trim(),page:location.pathname,website:hp
  })}).then(function(){thx(f);}).catch(function(){thx(f);});
 });
});
function thx(f){var en=document.documentElement.lang==='en';
 f.innerHTML='<p class="fb-thanks">'+(en?'Thanks — we got it.':'¡Gracias! Lo recibimos.')+'</p>';}
</script>'''
    home_titles = json.dumps({"es": "Descubre Tehuacán — MiTehuacán",
                              "en": "Discover Tehuacán — MiTehuacán"}, ensure_ascii=False)
    (APPROOT / "descubre").mkdir(parents=True, exist_ok=True)
    (APPROOT / "descubre" / "index.html").write_text(f"""<!DOCTYPE html>
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
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/icon-192.png">
<link rel="canonical" href="{DOMAIN}/descubre/">
<style>{home_css}</style>
<script>window.TITLES={home_titles}</script>
{LANG_JS}
</head>
<body>
<header class="site">
<a class="brand" href="/">mi<span>tehuacan</span>.mx</a>
<nav>
<a href="/">Combis</a>
<a href="/eventos/"><span class="es">Eventos</span><span class="en">Events</span></a>
{LANG_LINKS}
</nav>
</header>
<div class="wrap">
{home_body}
</div>
{FOOTER}
<script src="/appsw.js" defer></script>
</body>
</html>""", encoding="utf-8")

    # ---- /eventos : the city events calendar (reads the generated /combis/events.js)
    ev_style = """<style>
.ev-intro{color:var(--ink2);font-size:14.5px;max-width:44em}
.ev-filters{display:flex;gap:7px;flex-wrap:wrap;margin:16px 0 4px}
.ev-filters button{font:inherit;font-size:13px;cursor:pointer;padding:6px 12px;border-radius:99px;
 border:1px solid var(--line);background:var(--panel);color:var(--ink2)}
.ev-filters button.on{background:var(--accent);color:#fff;border-color:transparent;box-shadow:0 3px 12px var(--accsh)}
.month{font-size:14px;font-weight:700;color:var(--ink2);text-transform:capitalize;margin:24px 0 10px;
 letter-spacing:.02em;border-bottom:1px solid var(--line);padding-bottom:6px}
.ev{display:flex;gap:14px;padding:13px 14px;border:1px solid var(--line);border-radius:14px;
 background:var(--panel);box-shadow:var(--shadow),inset 0 1px 0 var(--hl);margin-bottom:10px}
.ev .date{flex:none;width:50px;text-align:center;padding-top:2px}
.ev .date .d{font-size:23px;font-weight:800;line-height:1;color:var(--ink)}
.ev .date .m{font-size:11px;text-transform:uppercase;color:var(--accent);font-weight:700;margin-top:2px}
.ev .body{flex:1;min-width:0}
.ev .t{font-weight:600;font-size:15.5px;line-height:1.35}
.ev .meta{font-size:13px;color:var(--ink2);display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:5px}
.ev .meta a{font-weight:600}
.cat{font-size:11px;font-weight:700;padding:2px 9px;border-radius:99px;border:1px solid transparent}
.cat.religioso{background:rgba(147,51,234,.14);color:#9333ea}
.cat.feria{background:rgba(234,88,12,.14);color:#ea580c}
.cat.cultural{background:rgba(2,132,199,.14);color:#0284c7}
.cat.deportivo{background:rgba(22,163,74,.14);color:#16a34a}
.cat.civico{background:rgba(220,38,38,.14);color:#dc2626}
.cat.otro{background:var(--chip);color:var(--ink2)}
.confirm{font-size:11px;font-weight:600;color:#b26b00;background:rgba(217,119,6,.13);padding:2px 8px;border-radius:99px}
:root[data-theme=dark] .confirm{color:#f5b756}
.ev-empty{color:var(--ink2);padding:30px 0}
.ev-count{font-size:13px;color:var(--ink2);margin-top:4px}
</style>"""
    ev_script = """<script src="/events.js"></script>
<script>
(function(){
 var root=document.getElementById('evroot'),bar=document.getElementById('evfilters');
 var data=(typeof EVENTS!=='undefined'&&EVENTS.events)||[];
 // show only today .. next 3 months (computed client-side so it never goes stale)
 (function(){var n=new Date();function p(x){return(x<10?'0':'')+x;}
  function iso(d){return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());}
  var t=iso(n),c=iso(new Date(n.getFullYear(),n.getMonth()+3,n.getDate()));
  data=data.filter(function(e){return e.d>=t&&e.d<=c;});})();
 var MES=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
 var EN=['January','February','March','April','May','June','July','August','September','October','November','December'];
 var CAT={religioso:['Religioso','Religious'],feria:['Feria','Fair'],cultural:['Cultural','Cultural'],
  deportivo:['Deportivo','Sports'],civico:['Cívico','Civic'],otro:['Otro','Other']};
 var filter='all';
 function L(){return document.documentElement.lang==='en'?1:0;}
 function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
 function fmt(iso){var p=iso.split('-');return{y:+p[0],m:+p[1]-1,d:+p[2]};}
 function chips(){
  var cats=['all'];data.forEach(function(e){if(cats.indexOf(e.k)<0)cats.push(e.k);});
  bar.innerHTML=cats.map(function(c){
   var lbl=c==='all'?(L()?'All':'Todos'):(CAT[c]||CAT.otro)[L()];
   return '<button data-c="'+c+'"'+(c===filter?' class="on"':'')+'>'+lbl+'</button>';}).join('');
  [].forEach.call(bar.children,function(b){b.onclick=function(){filter=b.dataset.c;chips();render();};});
 }
 function render(){
  var list=data.filter(function(e){return filter==='all'||e.k===filter;});
  if(!list.length){root.innerHTML='<p class="ev-empty">'+(L()?'No upcoming events.':'No hay eventos próximos.')+'</p>';return;}
  var out='',cur='';
  list.forEach(function(e){
   var f=fmt(e.d),mk=f.y+'-'+f.m,MN=(L()?EN:MES);
   if(mk!==cur){cur=mk;out+='<div class="month">'+MN[f.m]+' '+f.y+'</div>';}
   var cat=CAT[e.k]||CAT.otro;
   out+='<div class="ev"><div class="date"><div class="d">'+f.d+'</div><div class="m">'+MN[f.m].slice(0,3)+'</div></div>'+
    '<div class="body"><div class="t">'+esc(e.t)+'</div><div class="meta">'+
    '<span class="cat '+e.k+'">'+cat[L()]+'</span>'+
    '<span>'+esc(e.v)+'</span>'+
    (e.tm?'<span>'+e.tm+'</span>':'')+
    (e.x?'<span class="confirm">'+(L()?'date to confirm':'fecha por confirmar')+'</span>':'')+
    (e.u?'<a href="'+esc(e.u)+'" target="_blank" rel="noopener">'+(L()?'details':'ver más')+'</a>':'')+
    '</div></div></div>';
  });
  root.innerHTML='<div class="ev-count">'+list.length+(L()?' events':' eventos')+'</div>'+out;
 }
 chips();render();
 [].forEach.call(document.querySelectorAll('.lng'),function(a){a.addEventListener('click',function(){setTimeout(function(){chips();render();},0);});});
})();
</script>"""
    eventos_body = (ev_style +
        '<h1><span class="es">Eventos y fiestas</span><span class="en">Events &amp; fiestas</span></h1>'
        '<p class="ev-intro"><span class="es">La agenda de Tehuacán y su región: ferias, fiestas patronales, '
        'eventos culturales y deportivos. Las marcadas <b>“por confirmar”</b> se derivan del calendario del '
        'santo patrono y aún falta confirmar la fecha local.</span>'
        '<span class="en">What\'s on in Tehuacán and its region: fairs, patron-saint fiestas, cultural and '
        'sporting events. Ones marked <b>“to confirm”</b> are derived from the patron saint\'s calendar and '
        'still need a confirmed local date.</span></p>'
        '<div id="evfilters" class="ev-filters"></div>'
        '<div id="evroot"></div>'
        '<p class="muted" style="margin-top:22px"><a href="/">'
        '<span class="es">← Volver al mapa de combis</span><span class="en">← Back to the combi map</span></a></p>'
        + ev_script)
    (APPROOT / "eventos").mkdir(parents=True, exist_ok=True)
    (APPROOT / "eventos" / "index.html").write_text(
        page("Eventos y fiestas de Tehuacán",
             "Agenda de eventos, ferias y fiestas patronales de Tehuacán, Puebla y su región.",
             eventos_body, f"{DOMAIN}/eventos/",
             crumb_items=[(bi("Inicio", "Home"), "/"), (bi("Eventos", "Events"), None)],
             title_en="Events & fiestas in Tehuacán"),
        encoding="utf-8")

    # ---- /roadmap : the next-year plan, synthesized from the planning docs
    # (business/research/09-organic-phase-reorder.md is canonical; financials +
    # marketing-plan + launch-execution fill the timing). Operating model = the
    # ORGANIC one: supply before demand before money.
    rm_style = """<style>
.rm-principle{font-size:19px;font-weight:800;margin:10px 0 2px;letter-spacing:-.01em}
.rm-principle .hl{color:var(--accent)}
.rm-sub{color:var(--ink2);font-size:14.5px;max-width:46em;margin:4px 0 0}
.rm-legend{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0 4px;font-size:12.5px;color:var(--ink2)}
.rm-legend b{display:inline-flex;align-items:center;gap:6px;font-weight:600}
.rm-dot{width:9px;height:9px;border-radius:99px;display:inline-block}
.dot-live{background:#16a34a}.dot-building{background:var(--accent)}.dot-next{background:#d97706}.dot-planned{background:#8a8a90}.dot-horizon{background:#9333ea}
.rm-period{margin:28px 0 10px}
.rm-period h2{font-size:16.5px;margin:0}
.rm-period .rng{font-size:12.5px;color:var(--accent);font-weight:600;margin-top:1px}
.rm-timeline{position:relative;margin:0 0 0 6px;padding-left:22px;border-left:2px solid var(--line)}
.rm-item{position:relative;margin:0 0 12px;padding:13px 15px;border:1px solid var(--line);border-radius:14px;
 background:var(--panel);box-shadow:var(--shadow),inset 0 1px 0 var(--hl)}
.rm-item::before{content:"";position:absolute;left:-29px;top:16px;width:12px;height:12px;border-radius:99px;border:2px solid var(--bg);background:#8a8a90}
.rm-item.s-live::before{background:#16a34a}
.rm-item.s-building::before{background:var(--accent)}
.rm-item.s-next::before{background:#d97706}
.rm-item.s-planned::before{background:#8a8a90}
.rm-item.s-horizon::before{background:#9333ea}
.rm-item .t{font-weight:600;font-size:15.5px;line-height:1.3}
.rm-item .d{color:var(--ink2);font-size:13.5px;margin-top:4px;line-height:1.5}
.rm-tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}
.rm-tag{font-size:11px;font-weight:700;padding:2px 9px;border-radius:99px}
.rm-tag.free,.rm-tag.supply{background:rgba(22,163,74,.14);color:#16a34a}
.rm-tag.money,.rm-tag.income{background:rgba(234,88,12,.16);color:#ea580c}
.rm-tag.pilot,.rm-tag.demand{background:rgba(147,51,234,.14);color:#9333ea}
.rm-tag.data{background:rgba(2,132,199,.14);color:#0284c7}
.rm-tag.goal{background:var(--chip);color:var(--ink2)}
.rm-note{margin:26px 0 0;padding:13px 15px;border:1px solid var(--line);border-radius:12px;background:var(--chip);font-size:13px;color:var(--ink2);line-height:1.55}
:root[data-theme=dark] .rm-tag.money,:root[data-theme=dark] .rm-tag.income{color:#f5a15f}
</style>"""
    TAG = {"free": ["Gratis", "Free"], "money": ["Primer ingreso", "First revenue"],
           "pilot": ["Piloto", "Pilot"], "data": ["Datos", "Data"], "goal": ["Meta", "Goal"],
           "supply": ["Oferta", "Supply"], "demand": ["Demanda", "Demand"], "income": ["Ingreso", "Revenue"]}
    rm_periods = [
        {"es": "Ahora · Jul 2026", "en": "Now · Jul 2026",
         "res": "Fase 0 · encendido", "ren": "Phase 0 · ignition", "items": [
            {"s": "live", "tes": "Combis (rutas)", "ten": "Combis (routes)",
             "des": "80+ rutas en un mapa con planificador de viajes. La base del modelo: usuarios diarios que llegan gratis por los QR en los combis.",
             "den": "80+ routes on a map with a trip planner. The base of the model: daily users who arrive free via the combi QR stickers.", "tags": ["free"]},
            {"s": "building", "tes": "App de apps", "ten": "App of apps",
             "des": "Una sola app: el inicio son las rutas, con un selector arriba para saltar a Eventos, Descubre y lo que viene. Un solo código, varias apps.",
             "den": "One app: home is the routes, with a top switcher to jump to Eventos, Descubre and what's next. One codebase, many apps.", "tags": []},
            {"s": "building", "tes": "Eventos", "ten": "Events",
             "des": "Agenda de fiestas patronales y eventos de Tehuacán y su región (calendario del santo + Facebook), como calendario del próximo trimestre.",
             "den": "Calendar of patron-saint fiestas and events across Tehuacán and its region (saint's calendar + Facebook), the next three months.", "tags": ["free"]},
            {"s": "next", "tes": "Lanzamiento QR", "ten": "QR launch",
             "des": "Subir los fixes a producción, sembrar e imprimir los stickers, y un blitz de 6 días en el top-10 de rutas + placards de trueque en tienditas.",
             "den": "Ship the fixes to production, seed and print the stickers, and a 6-day blitz on the top-10 routes + barter placards in corner shops.", "tags": ["data"]},
            {"s": "next", "tes": "Mapa completo", "ten": "A complete map",
             "des": "Sembrar cadenas y OXXO desde DENUE como simples pines de destino para que el mapa se vea completo desde el día uno.",
             "den": "Seed chains and OXXO from DENUE as plain destination pins so the map reads complete from day one.", "tags": ["data"]},
         ]},
        {"es": "Ago–Sep 2026", "en": "Aug–Sep 2026",
         "res": "Fase 1 · sembrar la oferta", "ren": "Phase 1 · seed supply", "items": [
            {"s": "next", "tes": "Directorio de proveedores de fiesta", "ten": "Fiesta-vendor directory",
             "des": "Los negocios se dan de alta solos con un QR imprimible en menos de 5 minutos. Sembrado por categorías de fiesta: taquiza, pastel, DJ, decoración, mobiliario, salón, foto y video.",
             "den": "Businesses self-list with a printable QR in under 5 minutes. Seeded around fiesta categories: catering, cake, DJ, decor, furniture, venue, photo & video.", "tags": ["free", "supply"]},
            {"s": "next", "tes": "Alta en campo", "ten": "Field sign-up",
             "des": "El fundador da de alta a los primeros ~50 proveedores, corredor Centro primero. No es venta: es un registro gratis de 2 minutos.",
             "den": "The founder signs up the first ~50 vendors, Centro corridor first. Not a sales call: a free 2-minute sign-up.", "tags": ["supply"]},
            {"s": "next", "tes": "Grabar rutas faltantes", "ten": "Record missing routes",
             "des": "App nativa de grabación (Zinacatepec, corredor Coxcatlán). Base del crowdsourcing: identidad por dispositivo, puntos y referidos.",
             "den": "Native recorder app (Zinacatepec, Coxcatlán corridor). Crowdsourcing groundwork: device identity, points and referrals.", "tags": ["data"]},
            {"s": "next", "tes": "Meta", "ten": "Goal",
             "des": "25 patrocinadores/listados para el mes 3 (incluyendo trueque).",
             "den": "25 sponsors/listings by month 3 (barter included).", "tags": ["goal"]},
         ]},
        {"es": "Oct–Dic 2026", "en": "Oct–Dec 2026",
         "res": "Fase 2–3 · demanda, luego dinero", "ren": "Phase 2–3 · demand, then money", "items": [
            {"s": "planned", "tes": "Fiestas", "ten": "Fiestas",
             "des": "Herramienta gratis para planear fiestas: invitaciones, confirmaciones y lista de pendientes. Genera demanda calificada que ven los proveedores del directorio.",
             "den": "Free party-planning tool: invites, RSVPs, needs list. Generates qualified demand the directory vendors can see.", "tags": ["free", "demand"]},
            {"s": "planned", "tes": "Piloto de conversión", "ten": "Conversion pilot",
             "des": "20 a 40 proveedores con precios de $99 a $299 aleatorizados, para medir la conversión real de gratis a pago — la métrica bisagra de todo el modelo.",
             "den": "20–40 vendors with randomized $99–299 pricing, to measure the real free→paid conversion — the hinge metric of the whole model.", "tags": ["pilot"]},
            {"s": "planned", "tes": "Primer ingreso: Destacado", "ten": "First revenue: Boost",
             "des": "Un impulso de una sola compra (~$199 por 30 días) por liga de pago de WhatsApp → OXXO o SPEI → se publica solo. Sin vendedor y sin cobranza.",
             "den": "A one-shot boost (~$199 for 30 days) via a WhatsApp pay-link → OXXO or SPEI → auto-publishes. No salesperson, no collections.", "tags": ["money"]},
            {"s": "planned", "tes": "Búsqueda inteligente", "ten": "Smart search",
             "des": "Buscar por necesidad ('dentista', 'llantas', 'farmacia') sobre el directorio + los 28,727 negocios de DENUE.",
             "den": "Search by need ('dentist', 'tires', 'pharmacy') over the directory + the 28,727 DENUE businesses.", "tags": []},
            {"s": "planned", "tes": "Meta", "ten": "Goal",
             "des": "50 a 60 patrocinadores para el mes 6; a 10 mil usuarios diarios se puede subir el precio.",
             "den": "50–60 sponsors by month 6; at 10k daily users, pricing can rise.", "tags": ["goal"]},
         ]},
        {"es": "Ene–Mar 2027", "en": "Jan–Mar 2027",
         "res": "Fase 4 · componer el ingreso", "ren": "Phase 4 · compound revenue", "items": [
            {"s": "planned", "tes": "Paquetes de temporada", "ten": "Season packages",
             "des": "Fiesta prepagada por 6 meses y perfiles premium (fotos, horarios, WhatsApp, promociones).",
             "den": "6-month prepaid fiesta packages and premium profiles (photos, hours, WhatsApp, promos).", "tags": ["income"]},
            {"s": "planned", "tes": "Recomendado por categoría", "ten": "Category 'Recommended'",
             "des": "Colocación destacada por categoría y zona, sobre los mismos rieles de pago.",
             "den": "Featured placement by category and zone, on the same payment rails.", "tags": ["income"]},
            {"s": "planned", "tes": "Expansión por corredores", "ten": "Corridor expansion",
             "des": "Corredor por corredor: El Paseo/Bulevar → San Isidro/El Riego → San Lorenzo → foráneas.",
             "den": "Corridor by corridor: El Paseo/Bulevar → San Isidro/El Riego → San Lorenzo → outlying towns.", "tags": []},
            {"s": "planned", "tes": "Meta", "ten": "Goal",
             "des": "100 patrocinadores para el mes 9–12.", "den": "100 sponsors by month 9–12.", "tags": ["goal"]},
         ]},
        {"es": "Abr–Jun 2027", "en": "Apr–Jun 2027",
         "res": "Fase 5+ · mismas vías, nuevas categorías", "ren": "Phase 5+ · same rails, new categories", "items": [
            {"s": "horizon", "tes": "Servicios a domicilio", "ten": "Home services",
             "des": "Plomeros, electricistas, pintores: solicitud → proveedor, sobre el mismo directorio + liga de pago.",
             "den": "Plumbers, electricians, painters: request → provider, on the same directory + pay-link.", "tags": []},
            {"s": "horizon", "tes": "Tianguis y comercio local", "ten": "Tianguis & local commerce",
             "des": "Horarios de tianguis, puestos destacados y promociones.",
             "den": "Tianguis schedules, featured stalls and promotions.", "tags": []},
            {"s": "horizon", "tes": "Empleos y comunidad", "ten": "Jobs & community",
             "des": "Bolsa de trabajo local + eventos comunitarios.",
             "den": "Local job board + community events.", "tags": []},
         ]},
        {"es": "Horizonte", "en": "Horizon",
         "res": "Visión · la homepage digital de Tehuacán", "ren": "Vision · the digital homepage of Tehuacán", "items": [
            {"s": "horizon", "tes": "Motor de recomendación", "ten": "Recommendation engine",
             "des": "Cada evento de vida — cumpleaños, mudanza, casa nueva, negocio nuevo — genera prospectos calificados para los negocios locales. El corazón de la plataforma.",
             "den": "Every life event — birthday, moving, new home, new business — generates qualified leads for local businesses. The heart of the platform.", "tags": []},
            {"s": "horizon", "tes": "La app de todo Tehuacán", "ten": "The everything-Tehuacán app",
             "des": "Marketplace, entregas, taxis, hoteles, citas — el primer lugar donde buscas cuando necesitas algo en Tehuacán.",
             "den": "Marketplace, delivery, taxis, hotels, dating — the first place you look when you need anything in Tehuacán.", "tags": []},
         ]},
    ]
    rm_render = ('''<script>(function(){
var root=document.getElementById('rmroot');
function L(){return document.documentElement.lang==='en'?1:0;}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
var TAG=__TAG__;var P=__P__;
function render(){var h='';P.forEach(function(p){
 h+='<div class="rm-period"><h2>'+esc(L()?p.en:p.es)+'</h2><div class="rng">'+esc(L()?p.ren:p.res)+'</div></div><div class="rm-timeline">';
 p.items.forEach(function(it){
  h+='<div class="rm-item s-'+it.s+'"><div class="t">'+esc(L()?it.ten:it.tes)+'</div><div class="d">'+esc(L()?it.den:it.des)+'</div>';
  if(it.tags&&it.tags.length){h+='<div class="rm-tags">'+it.tags.map(function(t){return '<span class="rm-tag '+t+'">'+esc(TAG[t]?TAG[t][L()]:t)+'</span>';}).join('')+'</div>';}
  h+='</div>';});
 h+='</div>';});
 root.innerHTML=h;}
render();
[].forEach.call(document.querySelectorAll('.lng'),function(a){a.addEventListener('click',function(){setTimeout(render,0);});});
})();</script>''').replace('__TAG__', json.dumps(TAG, ensure_ascii=False)).replace('__P__', json.dumps(rm_periods, ensure_ascii=False))
    roadmap_body = (rm_style +
        '<h1>Roadmap</h1>'
        '<p class="rm-principle"><span class="es">Oferta antes que demanda, antes que <span class="hl">dinero</span>.</span>'
        '<span class="en">Supply before demand before <span class="hl">money</span>.</span></p>'
        '<p class="rm-sub"><span class="es">El próximo año de MiTehuacán: regalar el mapa, dejar que los negocios se den de alta solos por QR, '
        'y cobrar solo cuando ya fluyen prospectos gratis. Crecimiento orgánico, sin equipo de ventas.</span>'
        '<span class="en">MiTehuacan\'s next year: give the map away, let businesses self-list via QR, and only charge once free leads flow. '
        'Organic growth, no sales team.</span></p>'
        '<div class="rm-legend">'
        '<b><span class="rm-dot dot-live"></span><span class="es">En vivo</span><span class="en">Live</span></b>'
        '<b><span class="rm-dot dot-building"></span><span class="es">En construcción</span><span class="en">Building</span></b>'
        '<b><span class="rm-dot dot-next"></span><span class="es">Sigue</span><span class="en">Next</span></b>'
        '<b><span class="rm-dot dot-planned"></span><span class="es">Planeado</span><span class="en">Planned</span></b>'
        '<b><span class="rm-dot dot-horizon"></span><span class="es">Horizonte</span><span class="en">Horizon</span></b>'
        '</div>'
        '<div id="rmroot"></div>'
        '<div class="rm-note"><span class="es"><b>Cómo leerlo.</b> El ingreso del primer año es pequeño a propósito '
        '(~$13,500 MXN base) y depende del piloto de conversión. Las proyecciones grandes (más de $1M MXN) son el escenario '
        'optimista con equipo de ventas — este plan orgánico lo reemplaza: regalar el mapa, alta por QR, y cobrar self-serve '
        'solo cuando ya fluyen prospectos gratis.</span>'
        '<span class="en"><b>How to read it.</b> Year-one revenue is deliberately tiny (~$13,500 MXN base) and hinges on the '
        'conversion pilot. The larger projections (>$1M MXN) are the optimistic sales-led scenario — this organic plan replaces '
        'it: give the map away, QR self-listing, and charge self-serve only once free leads flow.</span></div>'
        + rm_render)
    (APPROOT / "roadmap").mkdir(parents=True, exist_ok=True)
    (APPROOT / "roadmap" / "index.html").write_text(
        page("Roadmap — MiTehuacán",
             "El plan del próximo año de MiTehuacán: transporte, directorio de fiestas, fiestas y monetización orgánica.",
             roadmap_body, f"{DOMAIN}/roadmap/",
             crumb_items=[(bi("Inicio", "Home"), "/"), ("Roadmap", None)],
             title_en="Roadmap — MiTehuacán"),
        encoding="utf-8")

    # ---- redirects (QR stickers + legacy paths) + a real 404.
    # No sitemap / Google canonicalization: growth is LOCAL (QR stickers + shares),
    # not search. OG/share meta stays (WhatsApp/Facebook link previews travel).
    (APPROOT / "_redirects").write_text(
        "# QR stickers resolve via functions/qr/[id].js (route deep-links); no\n"
        "# static rule here — Pages _redirects would shadow the function.\n"
        "# combis moved from /combis to the site root -> keep old links alive\n"
        "/combis/* /:splat 301\n"
        "/combis / 301\n"
        "/tehuacan/rutas/* /?ruta=:splat 301\n"
        "/appa/* / 301\n"
        "/tehuacan/ / 301\n"
        "/acerca/ / 301\n"
        , encoding="utf-8")
    # a real 404 page — without one, Pages SPA-falls-back to the app with a 200
    (APPROOT / "404.html").write_text(f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>404 — MiTehuacán</title><style>{CSS}</style></head>
<body><div class="wrap" style="padding-top:60px;text-align:center">
<h1>404</h1>
<p class="es">Esta página no existe. <a href="/">Ir al mapa de combis</a></p>
<p class="en">This page does not exist. <a href="/">Go to the combi map</a></p>
</div></body></html>""", encoding="utf-8")
    (APPROOT / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")

    mods = sorted(p.parent.name or "/" for p in APPROOT.rglob("index.html"))
    print(f"site built: {len(mods)} modules at {APPROOT} (deploy root; combis at /): "
          + ", ".join("/" if m == SECTION else m for m in mods))


if __name__ == "__main__":
    main()
