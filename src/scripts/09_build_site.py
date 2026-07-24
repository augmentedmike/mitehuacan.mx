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
import re
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
 --livebg:rgba(255,255,255,.72);--livebrd:rgba(0,113,227,.35);--ok:#1a7f37;--accsh:rgba(0,113,227,.30)}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0e0e12;--panel:rgba(28,28,34,.6);
 --ink:#f5f5f7;--ink2:#98989d;--line:rgba(255,255,255,.10);--accent:#0a84ff;--chip:rgba(66,66,74,.5);
 --glass:rgba(24,24,30,.55);--hl:rgba(255,255,255,.08);--shadow:0 8px 32px rgba(0,0,0,.5);
 --g1:rgba(10,132,255,.14);--g2:rgba(255,140,60,.05);--livebg:rgba(16,42,74,.45);
 --livebrd:rgba(10,132,255,.45);--ok:#2ecc71;--accsh:rgba(10,132,255,.35)}}
:root[data-theme=dark]{--bg:#0e0e12;--panel:rgba(28,28,34,.6);
 --ink:#f5f5f7;--ink2:#98989d;--line:rgba(255,255,255,.10);--accent:#0a84ff;--chip:rgba(66,66,74,.5);
 --glass:rgba(24,24,30,.55);--hl:rgba(255,255,255,.08);--shadow:0 8px 32px rgba(0,0,0,.5);
 --g1:rgba(10,132,255,.14);--g2:rgba(255,140,60,.05);--livebg:rgba(16,42,74,.45);
 --livebrd:rgba(10,132,255,.45);--ok:#2ecc71;--accsh:rgba(10,132,255,.35)}
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
footer.site .ft2{font-size:12.5px;opacity:.9}
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
<div><a href="/">Combis</a> · <a href="/eventos/"><span class="es">Eventos</span><span class="en">Events</span></a> · <a href="/descubre/"><span class="es">Descubre</span><span class="en">Discover</span></a> · <a href="/directorio/"><span class="es">Directorio</span><span class="en">Directory</span></a> · <a href="/roadmap/">Roadmap</a></div>
<div class="ft2"><a href="/nosotros/"><span class="es">Nosotros</span><span class="en">About</span></a> · <a href="/nosotros/#unete"><span class="es">Únete al equipo</span><span class="en">Join the team</span></a> · <a href="/patrocinar/"><span class="es">Patrocina</span><span class="en">Sponsor</span></a> · <a href="/legal/privacidad/"><span class="es">Privacidad</span><span class="en">Privacy</span></a> · <a href="/legal/terminos/"><span class="es">Términos</span><span class="en">Terms</span></a></div>
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
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="MiTehuacán">
<meta property="og:locale" content="es_MX">
<meta property="og:image" content="{DOMAIN}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{DOMAIN}/og-image.png">
<meta name="apple-mobile-web-app-title" content="MiTehuacán">
<link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
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
<meta property="og:title" content="MiTehuacán — el portal de Tehuacán">
<meta property="og:description" content="Mapa y rutas de combi de Tehuacán, gratis. Y el directorio de negocios de la ciudad.">
<meta property="og:type" content="website">
<meta property="og:url" content="{DOMAIN}/descubre/">
<meta property="og:site_name" content="MiTehuacán">
<meta property="og:image" content="{DOMAIN}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{DOMAIN}/og-image.png">
<meta name="theme-color" content="#0a0b12">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="MiTehuacán">
<link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
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
.ev{cursor:pointer;transition:border-color .15s,box-shadow .15s}
.ev:hover{border-color:var(--accent)}
.ev-more{margin-left:auto;color:var(--accent);font-weight:600;white-space:nowrap}
/* details bottom-sheet, mirrors the combi map's #sheet2 */
.evsheet-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:60;display:none;opacity:0;transition:opacity .2s}
.evsheet-backdrop.show{display:flex;align-items:flex-end;justify-content:center;opacity:1}
.evsheet{background:var(--bg);color:var(--ink);width:100%;max-width:520px;border-radius:20px 20px 0 0;
 padding:8px 20px 24px;box-shadow:0 -8px 40px rgba(0,0,0,.3);position:relative;max-height:88dvh;overflow:auto}
.evsheet-backdrop.show .evsheet{animation:evPanelIn .28s cubic-bezier(.32,.72,0,1) both}
@keyframes evPanelIn{from{transform:translateY(100%)}to{transform:translateY(0)}}
@media(min-width:560px){.evsheet-backdrop.show{align-items:center}.evsheet{border-radius:20px}}
.evs-handle{width:38px;height:5px;border-radius:99px;background:var(--line);margin:6px auto 14px}
.evs-x{position:absolute;top:12px;right:14px;background:none;border:none;font-size:26px;line-height:1;color:var(--ink2);cursor:pointer}
.evs-date{font-size:13px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.03em}
.evs-t{font-size:20px;font-weight:700;line-height:1.3;margin:4px 40px 10px 0}
.evs-tags{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:2px}
.evs-rows{display:flex;flex-direction:column;gap:9px;font-size:14.5px;margin-top:14px;border-top:1px solid var(--line);padding-top:14px}
.evs-row{display:flex;gap:10px;align-items:flex-start}
.evs-ic{flex:none;opacity:.85}
.evs-acts{display:flex;flex-direction:column;gap:9px;margin-top:18px}
.evs-btn{display:block;text-align:center;padding:12px;border-radius:12px;font-weight:600;font-size:14.5px;
 border:1px solid var(--line);color:var(--ink);text-decoration:none}
.evs-btn.primary{background:var(--accent);color:#fff;border-color:transparent;box-shadow:0 3px 12px var(--accsh)}
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
 var shown=[];   // the currently rendered list, indexed by the card's data-i
 function render(){
  var list=data.filter(function(e){return filter==='all'||e.k===filter;});
  shown=list;
  if(!list.length){root.innerHTML='<p class="ev-empty">'+(L()?'No upcoming events.':'No hay eventos próximos.')+'</p>';return;}
  var out='',cur='';
  list.forEach(function(e,i){
   var f=fmt(e.d),mk=f.y+'-'+f.m,MN=(L()?EN:MES);
   if(mk!==cur){cur=mk;out+='<div class="month">'+MN[f.m]+' '+f.y+'</div>';}
   var cat=CAT[e.k]||CAT.otro;
   out+='<div class="ev" data-i="'+i+'" role="button" tabindex="0">'+
    '<div class="date"><div class="d">'+f.d+'</div><div class="m">'+MN[f.m].slice(0,3)+'</div></div>'+
    '<div class="body"><div class="t">'+esc(e.t)+'</div><div class="meta">'+
    '<span class="cat '+e.k+'">'+cat[L()]+'</span>'+
    '<span>'+esc(e.v)+'</span>'+
    (e.tm?'<span>'+e.tm+'</span>':'')+
    (e.x?'<span class="confirm">'+(L()?'date to confirm':'fecha por confirmar')+'</span>':'')+
    '<span class="ev-more">'+(L()?'details':'ver más')+' ›</span>'+
    '</div></div></div>';
  });
  root.innerHTML='<div class="ev-count">'+list.length+(L()?' events':' eventos')+'</div>'+out;
  [].forEach.call(root.querySelectorAll('.ev'),function(c){
   var e=shown[+c.dataset.i];
   c.onclick=function(){openEv(e);};
   c.onkeydown=function(ev){if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();openEv(e);}};
  });
 }
 // ---- details sheet: an in-page panel, like the combi map's, instead of jumping offsite
 var backdrop,sheet;
 function buildSheet(){
  backdrop=document.createElement('div');backdrop.className='evsheet-backdrop';
  sheet=document.createElement('div');sheet.className='evsheet';
  sheet.setAttribute('role','dialog');sheet.setAttribute('aria-modal','true');
  backdrop.appendChild(sheet);document.body.appendChild(backdrop);
  backdrop.addEventListener('click',function(ev){if(ev.target===backdrop)closeEv();});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape')closeEv();});
 }
 function closeEv(){if(backdrop){backdrop.classList.remove('show');document.body.style.overflow='';}}
 function openEv(e){
  if(!backdrop)buildSheet();
  var f=fmt(e.d),MN=(L()?EN:MES),cat=CAT[e.k]||CAT.otro;
  var lon=e.c&&e.c[0],lat=e.c&&e.c[1],hasLoc=isFinite(lon)&&isFinite(lat);
  var h='<div class="evs-handle"></div><button class="evs-x" aria-label="'+(L()?'Close':'Cerrar')+'">&times;</button>'+
   '<div class="evs-date">'+f.d+' '+MN[f.m]+' '+f.y+'</div>'+
   '<h2 class="evs-t">'+esc(e.t)+'</h2>'+
   '<div class="evs-tags"><span class="cat '+e.k+'">'+cat[L()]+'</span>'+
   (e.x?'<span class="confirm">'+(L()?'date to confirm':'fecha por confirmar')+'</span>':'')+'</div>';
  var rows='';
  if(e.v)rows+='<div class="evs-row"><span class="evs-ic">📍</span><span>'+esc(e.v)+'</span></div>';
  if(e.tm)rows+='<div class="evs-row"><span class="evs-ic">🕒</span><span>'+esc(e.tm)+'</span></div>';
  if(rows)h+='<div class="evs-rows">'+rows+'</div>';
  var acts='';
  if(hasLoc)acts+='<a class="evs-btn primary" href="/?to='+(+lon).toFixed(5)+','+(+lat).toFixed(5)+
   '&n='+encodeURIComponent(e.t)+'">'+(L()?'Get there by combi':'Cómo llegar en combi')+'</a>';
  if(e.u)acts+='<a class="evs-btn" href="'+esc(e.u)+'" target="_blank" rel="noopener">'+
   (L()?'Original post':'Ver publicación original')+'</a>';
  if(acts)h+='<div class="evs-acts">'+acts+'</div>';
  sheet.innerHTML=h;
  sheet.querySelector('.evs-x').onclick=closeEv;
  backdrop.classList.add('show');document.body.style.overflow='hidden';
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

    # ---- /directorio : the service & store directory (app-of-apps module).
    # Each sponsor gets a Google-Maps-style "homepage": name, category, phone,
    # every location, and labeled placeholders (Fotos / Precios y especiales) that
    # a later content-agent will fill. Data source: resources/map-data/sponsors.js
    # (const SPONSORS = {...};), also copied into the build for the map layer.
    sponsors_raw = (ROOT / "resources" / "map-data" / "sponsors.js").read_text(encoding="utf-8")
    sponsors_json = sponsors_raw.split("const SPONSORS = ", 1)[1].strip()
    if sponsors_json.endswith(";"):
        sponsors_json = sponsors_json[:-1]
    SPONSORS = json.loads(sponsors_json)
    sp_all = SPONSORS.get("sponsors", {})

    def _has_content(sp):
        # keep sponsors with at least one real location detail (addr/hours/phone);
        # drops empty seeds but keeps OXXO & 3B (both carry real branch data).
        return any(l.get("addr") or l.get("hours") or l.get("phone")
                   for l in sp.get("locations", []))

    dir_sponsors = sorted(
        ((sid, sp) for sid, sp in sp_all.items() if _has_content(sp)),
        key=lambda kv: kv[1]["name"].lower())

    D_PIN = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
             'stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12'
             'a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="2.6"/></svg>')
    D_CLOCK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
               'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/>'
               '<path d="M12 7v5l3.5 2"/></svg>')
    D_PHONE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
               'stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 '
               '19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3'
               'a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8.1 9.8a16 16 0 0 0 6 6l1.3-1.3a2 '
               '2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.8 2Z"/></svg>')

    dir_style = """<style>
.dir-intro{color:var(--ink2);font-size:14.5px;max-width:44em;margin:2px 0 0}
.dir-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:18px 0 4px}
.dir-card{display:flex;flex-direction:column;gap:9px;padding:15px 14px;border:1px solid var(--line);
 border-radius:16px;background:var(--panel);box-shadow:var(--shadow),inset 0 1px 0 var(--hl);
 text-decoration:none;color:inherit}
.dir-card:active{transform:translateY(1px)}
.dir-logo{width:56px;height:56px;border-radius:13px;object-fit:contain;background:#fff;
 border:1px solid var(--line);padding:6px}
.dir-card .nm{font-weight:700;font-size:15.5px;line-height:1.25}
.dir-cat{display:inline-block;font-size:11px;font-weight:700;padding:2px 9px;border-radius:99px;
 background:var(--chip);color:var(--ink2);border:1px solid var(--line);width:fit-content}
.dir-br{font-size:12.5px;color:var(--ink2);margin-top:auto;display:inline-flex;align-items:center;gap:5px}
.dir-br svg{width:14px;height:14px;opacity:.7}
/* --- "list your business free" call to action --- */
.dir-cta{display:flex;align-items:center;gap:13px;margin:18px 0 2px;padding:15px 15px;border-radius:16px;
 text-decoration:none;color:#fff;background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 62%,#7b5cff));
 box-shadow:0 6px 22px var(--accsh)}
.dir-cta:active{transform:translateY(1px)}
.dir-cta .cta-ic{flex:none;width:44px;height:44px;border-radius:12px;background:rgba(255,255,255,.18);
 display:flex;align-items:center;justify-content:center}
.dir-cta .cta-ic svg{width:24px;height:24px;stroke:#fff;fill:none;stroke-width:1.9;
 stroke-linecap:round;stroke-linejoin:round}
.dir-cta .cta-tx{flex:1;min-width:0}
.dir-cta .cta-tx b{display:block;font-size:15.5px;font-weight:800;line-height:1.2}
.dir-cta .cta-tx small{display:block;font-size:13px;opacity:.92;margin-top:2px}
.dir-cta .cta-go{flex:none;font-weight:800;font-size:14px;background:#fff;color:var(--accent);
 padding:9px 15px;border-radius:99px;white-space:nowrap}
/* --- self-registered businesses (from /api/negocios) --- */
.dir-h2{font-size:17px;font-weight:800;margin:28px 0 2px}
#negocios:empty{display:none}
.neg-empty{color:var(--ink2);font-size:14px;padding:12px 0 2px}
.neg-card{position:relative;display:flex;flex-direction:column;gap:7px;padding:14px 30px 14px 14px;
 border:1px solid var(--line);border-radius:16px;background:var(--panel);box-shadow:var(--shadow),inset 0 1px 0 var(--hl);
 text-align:left;width:100%;cursor:pointer;color:inherit;font:inherit}
.neg-card:active{transform:translateY(1px)}
.neg-card .nm{font-weight:700;font-size:15.5px;line-height:1.25}
.neg-card .desc{font-size:13px;color:var(--ink2);line-height:1.4}
.neg-card .mrow{font-size:12.5px;color:var(--ink2);display:flex;flex-wrap:wrap;gap:4px 8px}
.neg-card .neg-go{position:absolute;right:12px;top:50%;transform:translateY(-50%);color:var(--ink2);font-size:22px;line-height:1}
.neg-badge{align-self:flex-start;font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:99px;
 background:color-mix(in srgb,var(--ok) 16%,transparent);color:var(--ok)}
/* --- slide-in business detail panel (slug = ?n=<slug>) --- */
#neg-panel{position:fixed;inset:0;z-index:60;background:var(--bg);overflow-y:auto;
 transform:translateX(100%);transition:transform .28s ease;visibility:hidden}
#neg-panel.show{transform:translateX(0);visibility:visible}
.np-head{position:sticky;top:0;background:var(--bg);padding:10px 14px;border-bottom:1px solid var(--line);z-index:1}
.np-back{background:var(--chip);border:1px solid var(--line);border-radius:99px;width:42px;height:42px;
 font-size:22px;line-height:1;color:var(--ink);cursor:pointer}
#neg-panel-body{padding:18px 16px 40px;max-width:560px;margin:0 auto}
.np-name{font-size:22px;font-weight:800;line-height:1.2;margin:0 0 4px}
.np-cat{color:var(--ink2);font-size:14px;margin:6px 0 12px}
.np-desc{font-size:15px;line-height:1.5;margin:0 0 8px}
.np-row{display:flex;justify-content:space-between;gap:14px;padding:11px 0;border-top:1px solid var(--line);font-size:14px}
.np-row span{color:var(--ink2);flex:none}.np-row b{text-align:right}
.np-soc{margin:14px 0 0;font-size:14px;display:flex;gap:12px;flex-wrap:wrap}
.np-actions{display:flex;gap:12px;align-items:center;margin-top:22px}
.np-wa{display:inline-flex;align-items:center;justify-content:center;width:52px;height:52px;border-radius:99px;
 background:#25d366;color:#fff;text-decoration:none}
.np-map{display:inline-flex;align-items:center;padding:14px 18px;border-radius:99px;font-weight:700;
 background:color-mix(in srgb,var(--accent) 14%,transparent);color:var(--accent);text-decoration:none}
/* --- sponsor profile page --- */
.pf-head{display:flex;gap:14px;align-items:center;margin:8px 0 2px}
.pf-logo{width:78px;height:78px;border-radius:18px;object-fit:contain;background:#fff;
 border:1px solid var(--line);padding:9px;flex:none}
.pf-name{font-size:22px;font-weight:800;line-height:1.15;margin:0}
.pf-meta{margin-top:7px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.pf-call{display:inline-flex;align-items:center;gap:8px;padding:10px 16px;border-radius:99px;
 background:var(--accent);color:#fff;text-decoration:none;font-weight:600;font-size:14px;
 box-shadow:0 4px 16px var(--accsh);margin:16px 0 2px}
.pf-call svg{width:16px;height:16px}
.pf-sec{margin:24px 0 0}
.pf-sec h2{font-size:16px;margin:0 0 10px}
.pf-soon{border:1px dashed var(--line);border-radius:14px;padding:22px 16px;text-align:center;
 color:var(--ink2);background:var(--chip)}
.pf-soon .big{font-size:15px;font-weight:700;color:var(--ink)}
.pf-soon .sm{font-size:13px;margin-top:3px}
.pf-count{font-size:13px;color:var(--ink2);margin:0 0 10px}
.pf-loc{display:flex;gap:12px;padding:13px 14px;border:1px solid var(--line);border-radius:14px;
 background:var(--panel);box-shadow:var(--shadow),inset 0 1px 0 var(--hl);margin-bottom:10px}
.pf-loc .pin{flex:none;width:34px;height:34px;border-radius:99px;background:var(--g1);
 display:flex;align-items:center;justify-content:center;color:var(--accent)}
.pf-loc .pin svg{width:18px;height:18px}
.pf-loc .info{flex:1;min-width:0}
.pf-loc .addr{font-weight:600;font-size:14.5px;line-height:1.35}
.pf-loc .hrs{font-size:13px;color:var(--ink2);margin-top:3px;display:flex;align-items:center;gap:6px}
.pf-loc .hrs svg{width:13px;height:13px;opacity:.7;flex:none}
.pf-loc .maplink{font-size:13px;font-weight:600;margin-top:5px;display:inline-block}
</style>"""

    def _cat(t):
        return f'<span class="dir-cat">{html.escape(t)}</span>'

    def _branches(n):
        return (f'<span class="dir-br">{D_PIN}'
                f'<span class="es">{n} {"sucursal" if n == 1 else "sucursales"}</span>'
                f'<span class="en">{n} {"branch" if n == 1 else "branches"}</span></span>')

    # directory listing: one card per sponsor -> its homepage
    cards = []
    for sid, sp in dir_sponsors:
        n = len(sp["locations"])
        cards.append(
            f'<a class="dir-card" href="/directorio/{sid}/">'
            f'<img class="dir-logo" src="/{sp["logo"]}" alt="{html.escape(sp["name"])}" loading="lazy">'
            f'<div class="nm">{html.escape(sp["name"])}</div>{_cat(sp["type"])}{_branches(n)}</a>')
    # self-registered businesses render below the sponsors, fetched live from
    # /api/negocios. category slug -> Spanish label comes from the alta form
    # itself (single source of truth), so a new category never needs a 2nd edit.
    alta_html = (ROOT / "src" / "app" / "directorio" / "alta.html").read_text(encoding="utf-8")
    cat_labels = {v: t for v, t in re.findall(r'<option value="([^"]+)">([^<]+)</option>', alta_html) if v}
    # list + slide-in detail panel. rendering/logic live in /directorio/negocios.js
    # (a real file, not an escaped string); the category label map is passed in via a
    # global built from the alta form so it never drifts.
    neg_section = (
        '<h2 class="dir-h2"><span class="es">Negocios de Tehuacán</span>'
        '<span class="en">Tehuacán businesses</span></h2>'
        '<div id="negocios" class="dir-grid"></div>'
        '<div id="neg-empty" class="neg-empty" hidden>'
        '<span class="es">Aún no hay negocios registrados. ¡Sé el primero!</span>'
        '<span class="en">No businesses registered yet. Be the first!</span></div>'
        '<div id="neg-panel" role="dialog" aria-modal="true">'
        '<div class="np-head"><button class="np-back" type="button" onclick="__negClose()" aria-label="Volver">←</button></div>'
        '<div id="neg-panel-body"></div></div>'
        '<script>window.NEG_CATS=' + json.dumps(cat_labels, ensure_ascii=False) + ';</script>'
        '<script src="/directorio/negocios.js" defer></script>')
    dir_body = (dir_style +
        '<h1><span class="es">Directorio</span><span class="en">Directory</span></h1>'
        '<p class="dir-intro"><span class="es">Negocios y servicios de Tehuacán. Cada negocio tiene su '
        'página con sus sucursales, horarios y teléfono — y muy pronto fotos, precios y ofertas.</span>'
        '<span class="en">Businesses and services in Tehuacán. Each has its own page with branches, hours '
        'and phone — and soon photos, prices and deals.</span></p>'
        '<a class="dir-cta" href="/directorio/alta.html">'
        '<span class="cta-ic"><svg viewBox="0 0 24 24"><path d="M3 9l1.6-5h14.8L21 9"/>'
        '<path d="M4 9v10a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V9"/><path d="M9.5 20v-5.5h5V20"/></svg></span>'
        '<span class="cta-tx">'
        '<b><span class="es">¿Tienes un negocio en Tehuacán?</span>'
        '<span class="en">Own a business in Tehuacán?</span></b>'
        '<small><span class="es">Aparece gratis en el directorio · 2 minutos, sin costo</span>'
        '<span class="en">Get listed free · 2 minutes, no cost</span></small></span>'
        '<span class="cta-go"><span class="es">Aparecer</span><span class="en">List it</span></span></a>'
        '<div class="dir-grid">' + "".join(cards) + '</div>' + neg_section)
    (APPROOT / "directorio").mkdir(parents=True, exist_ok=True)
    (APPROOT / "directorio" / "index.html").write_text(
        page("Directorio de negocios — MiTehuacán",
             "Directorio de negocios y servicios de Tehuacán, Puebla: sucursales, horarios y teléfonos.",
             dir_body, f"{DOMAIN}/directorio/",
             crumb_items=[(bi("Inicio", "Home"), "/"), (bi("Directorio", "Directory"), None)],
             title_en="Business directory — MiTehuacán"),
        encoding="utf-8")

    # one Google-Maps-style homepage per sponsor
    for sid, sp in dir_sponsors:
        locs = sp["locations"]
        n = len(locs)
        phone = next((l["phone"] for l in locs if l.get("phone")), None)
        call = ""
        if phone:
            tel = "".join(c for c in phone if c.isdigit() or c == "+")
            call = (f'<a class="pf-call" href="tel:{tel}">{D_PHONE}'
                    f'<span class="es">Llamar</span><span class="en">Call</span>'
                    f' · {html.escape(phone)}</a>')
        rows = []
        for l in locs:
            addr = l.get("addr")
            addr_html = (html.escape(addr) if addr else
                         '<span class="es">Ubicación en el mapa</span>'
                         '<span class="en">Location on the map</span>')
            hrs = l.get("hours")
            hrs_html = (f'{D_CLOCK}{html.escape(hrs)}' if hrs else
                        f'{D_CLOCK}<span class="es">Horario por confirmar</span>'
                        '<span class="en">Hours to confirm</span>')
            maps = f'https://www.google.com/maps/search/?api=1&query={l["lat"]},{l["lon"]}'
            rows.append(
                f'<div class="pf-loc"><div class="pin">{D_PIN}</div><div class="info">'
                f'<div class="addr">{addr_html}</div><div class="hrs">{hrs_html}</div>'
                f'<a class="maplink" href="{maps}" target="_blank" rel="noopener">'
                f'<span class="es">Ver en mapa →</span><span class="en">View on map →</span></a>'
                f'</div></div>')
        pf_body = (dir_style +
            '<div class="pf-head">'
            f'<img class="pf-logo" src="/{sp["logo"]}" alt="{html.escape(sp["name"])}">'
            f'<div><h1 class="pf-name">{html.escape(sp["name"])}</h1>'
            f'<div class="pf-meta">{_cat(sp["type"])}{_branches(n)}</div></div></div>'
            + call +
            # Fotos — placeholder for the future content pipeline
            '<div class="pf-sec"><h2><span class="es">Fotos</span><span class="en">Photos</span></h2>'
            '<div class="pf-soon"><div class="big"><span class="es">Próximamente</span>'
            '<span class="en">Coming soon</span></div>'
            '<div class="sm"><span class="es">Fotos del negocio muy pronto.</span>'
            '<span class="en">Business photos coming soon.</span></div></div></div>'
            # Precios / Especiales — placeholder
            '<div class="pf-sec"><h2><span class="es">Precios y especiales</span>'
            '<span class="en">Prices &amp; specials</span></h2>'
            '<div class="pf-soon"><div class="big"><span class="es">Próximamente</span>'
            '<span class="en">Coming soon</span></div>'
            '<div class="sm"><span class="es">Ofertas y precios muy pronto.</span>'
            '<span class="en">Deals and prices coming soon.</span></div></div></div>'
            # Sucursales — the real data
            '<div class="pf-sec"><h2><span class="es">Sucursales</span><span class="en">Branches</span></h2>'
            f'<p class="pf-count"><span class="es">{n} '
            f'{"ubicación" if n == 1 else "ubicaciones"}</span>'
            f'<span class="en">{n} {"location" if n == 1 else "locations"}</span></p>'
            + "".join(rows) + '</div>')
        (APPROOT / "directorio" / sid).mkdir(parents=True, exist_ok=True)
        (APPROOT / "directorio" / sid / "index.html").write_text(
            page(f'{sp["name"]} — Directorio MiTehuacán',
                 f'{sp["name"]}: {sp["type"]} en Tehuacán, Puebla. Sucursales, horarios y teléfono.',
                 pf_body, f"{DOMAIN}/directorio/{sid}/",
                 crumb_items=[(bi("Inicio", "Home"), "/"),
                              (bi("Directorio", "Directory"), "/directorio/"),
                              (html.escape(sp["name"]), None)],
                 title_en=f'{sp["name"]} — MiTehuacán Directory'),
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

    # ---- /nosotros (company presence + join the team) and /patrocinar (sponsors),
    # plus /legal/*. Copy grounded in what the code actually does — no fabricated
    # contact info or metrics. Leads land in the existing feedback table (/api/feedback),
    # tagged in the message so the founder can tell them apart in the review queue.
    co_style = """<style>
.co-hero{padding:8px 0 2px}
.co-hero h1{font-size:30px;margin:0;letter-spacing:-.4px}
.co-hero h1 span{color:var(--accent)}
.lead{font-size:16.5px;color:var(--ink2);line-height:1.6;margin:12px 0 0;max-width:40em}
.co-sec{margin:30px 0 0}
.co-sec>h2{font-size:12.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--accent);margin:0 0 12px;font-weight:700}
.co-p{font-size:15px;color:var(--ink);line-height:1.65;margin:0 0 12px;max-width:40em}
.co-p.mut{color:var(--ink2)}
.co-grid{display:grid;grid-template-columns:1fr;gap:14px}
.co-card{padding:16px 17px;border:1px solid var(--line);border-radius:16px;background:var(--panel);
 box-shadow:var(--shadow),inset 0 1px 0 var(--hl)}
.co-card .k{font-weight:700;font-size:16px;margin:0 0 5px}
.co-card p{font-size:14px;color:var(--ink2);line-height:1.58;margin:0}
.tier{position:relative;padding:18px;border:1px solid var(--line);border-radius:18px;background:var(--panel);
 box-shadow:var(--shadow),inset 0 1px 0 var(--hl);margin:0 0 14px}
.tier .lvl{font-size:11.5px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.07em}
.tier h3{font-size:19px;margin:2px 0 1px}
.tier .price{font-size:13.5px;color:var(--ink2);font-weight:600;margin:0 0 11px}
.tier ul{margin:0;padding-left:19px;font-size:14.5px;line-height:1.65;color:var(--ink)}
.tier ul li{margin:2px 0}
.tier ul li::marker{color:var(--accent)}
.tier.top{border-color:var(--livebrd);background:var(--livebg)}
.tier .ribbon{position:absolute;top:15px;right:16px;font-size:11px;font-weight:700;padding:4px 10px;border-radius:99px;background:var(--accent);color:#fff;box-shadow:0 2px 10px var(--accsh)}
.ldwrap{margin:26px 0 0;padding:18px;border:1px solid var(--line);border-radius:18px;background:var(--panel);box-shadow:var(--shadow),inset 0 1px 0 var(--hl)}
.ldwrap h2{font-size:18px;margin:0 0 4px}
.ldwrap .sub{font-size:13.5px;color:var(--ink2);margin:0 0 12px;line-height:1.55}
.ldform{display:flex;flex-direction:column;gap:9px}
.ldform textarea,.ldform input.fb-contact,.ldform select{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink);font:inherit;font-size:15px}
.ldform textarea{min-height:76px;resize:vertical}
.ldform textarea:focus,.ldform input:focus,.ldform select:focus{outline:2px solid var(--accent);outline-offset:-1px}
.ldform button{background:var(--accent);color:#fff;border:none;border-radius:10px;padding:12px;font:inherit;font-weight:600;cursor:pointer}
.fb-hp{display:none!important}
.fb-thanks{color:var(--accent);font-weight:600;margin:6px 0}
.note{margin:20px 0 0;padding:13px 15px;border:1px solid var(--line);border-radius:12px;background:var(--chip);font-size:13px;color:var(--ink2);line-height:1.55}
.co-legal{margin:24px 0 0;font-size:13px;color:var(--ink2);line-height:1.6}
.co-legal a{color:var(--accent);text-decoration:none}
.lg{max-width:42em}
.lg h1{font-size:27px;margin:0 0 4px}
.lg .upd{font-size:13px;color:var(--ink2);margin:0 0 20px}
.lg h2{font-size:17px;margin:24px 0 8px}
.lg p{font-size:14.5px;line-height:1.65;color:var(--ink);margin:0 0 10px}
.lg ul{padding-left:20px;margin:0 0 10px}
.lg li{font-size:14.5px;line-height:1.6;color:var(--ink);margin:3px 0}
.lg a{color:var(--accent)}
</style>"""
    LEAD_JS = """<script>
document.querySelectorAll('.ldform').forEach(function(f){
 f.addEventListener('submit',function(e){e.preventDefault();
  var hp=f.querySelector('.fb-hp').value;
  var msg=f.querySelector('textarea').value.trim();
  if(!hp&&msg.length<5)return;
  var sel=f.querySelector('select');var role=sel&&sel.value?sel.value:'';
  var tag=f.dataset.tag||'';
  var full=(tag?'['+tag+(role?' · '+role:'')+'] ':'')+msg;
  f.querySelector('button').disabled=true;
  fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
   kind:'idea',message:full,contact:f.querySelector('.fb-contact').value.trim(),page:location.pathname,website:hp
  })}).then(function(){ldthx(f);}).catch(function(){ldthx(f);});
 });
});
function ldthx(f){var en=document.documentElement.lang==='en';
 f.innerHTML='<p class="fb-thanks">'+(en?'Thanks — we\\'ll be in touch soon.':'¡Gracias! Te contactamos pronto.')+'</p>';}
</script>"""

    def lead_form(tag, anchor, title_es, title_en, sub_es, sub_en, ph_es, ph_en, options):
        opts = ''.join('<option>' + html.escape(o) + '</option>' for o in options)
        select = ('<select aria-label="' + html.escape(title_es) + '">'
                  '<option value="" selected>' + html.escape('Elige una opción / Choose one') + '</option>'
                  + opts + '</select>') if options else ''
        return ('<div class="ldwrap" id="' + anchor + '">'
                '<h2>' + bi(title_es, title_en) + '</h2>'
                '<p class="sub">' + bi(sub_es, sub_en) + '</p>'
                '<form class="ldform" data-tag="' + tag + '">'
                + select +
                '<textarea required maxlength="1500" data-ph-es="' + html.escape(ph_es) + '" '
                'data-ph-en="' + html.escape(ph_en) + '" placeholder="' + html.escape(ph_es) + '"></textarea>'
                '<input type="text" maxlength="120" class="fb-contact" '
                'data-ph-es="WhatsApp (así te contactamos)" data-ph-en="WhatsApp (so we can reach you)" '
                'placeholder="WhatsApp (así te contactamos)">'
                '<input type="text" class="fb-hp" tabindex="-1" autocomplete="off" aria-hidden="true">'
                '<button type="submit">' + bi('Enviar', 'Send') + '</button>'
                '</form></div>')

    def co_card(t_es, t_en, d_es, d_en):
        return ('<div class="co-card"><div class="k">' + bi(t_es, t_en) + '</div>'
                '<p>' + bi(d_es, d_en) + '</p></div>')

    def tier(lvl, name_es, name_en, price_es, price_en, feats, top=False, ribbon=None):
        lis = ''.join('<li>' + bi(a, b) + '</li>' for a, b in feats)
        rib = ('<span class="ribbon">' + bi(ribbon[0], ribbon[1]) + '</span>') if ribbon else ''
        cls = 'tier top' if top else 'tier'
        return ('<div class="' + cls + '">' + rib
                + '<div class="lvl">' + bi('Nivel ' + lvl, 'Level ' + lvl) + '</div>'
                '<h3>' + bi(name_es, name_en) + '</h3>'
                '<p class="price">' + bi(price_es, price_en) + '</p>'
                '<ul>' + lis + '</ul></div>')

    # ---- /nosotros
    nosotros_body = co_style + (
        '<div class="co-hero"><h1>' + bi('Nosotros', 'About us') + '</h1>'
        '<p class="lead">' + bi(
            'MiTehuacán es un proyecto local, sin financiamiento externo, hecho por y para tehuacaneros. '
            'Estamos construyendo el portal digital de la ciudad —empezando por las combis— y buscamos '
            'gente de aquí para llevarlo al siguiente nivel.',
            'MiTehuacán is a local project, with no outside funding, built by and for the people of Tehuacán. '
            'We are building the city\'s digital portal —starting with the combis— and we\'re looking for '
            'local people to take it to the next level.') + '</p></div>'
        '<div class="co-sec"><h2>' + bi('Qué estamos construyendo', 'What we\'re building') + '</h2>'
        '<p class="co-p">' + bi(
            'Hoy: un mapa con más de 80 rutas de combi y un planificador de viajes, gratis y sin cuenta. '
            'Sigue: eventos de la ciudad, un directorio de negocios y una herramienta para planear fiestas. '
            'La meta a largo plazo es simple: ser el primer lugar donde buscas cuando necesitas algo en Tehuacán.',
            'Today: a map with 80+ combi routes and a trip planner, free and with no account. '
            'Next: city events, a business directory, and a party-planning tool. '
            'The long-term goal is simple: to be the first place you look when you need anything in Tehuacán.')
        + '</p>'
        '<p class="co-p mut">' + bi(
            'Todo lo que hace un vecino es gratis. El mapa y sus datos son abiertos (ODbL). '
            'Crecemos de forma orgánica, por los códigos QR pegados en los combis —no con presupuesto de publicidad.',
            'Everything a resident does is free. The map and its data are open (ODbL). '
            'We grow organically, through the QR codes stuck inside the combis —not with an ad budget.')
        + '</p></div>'
        '<div class="co-sec"><h2>' + bi('Únete al equipo', 'Join the team') + '</h2>'
        '<p class="co-p">' + bi(
            'Somos pocos y apenas empezamos. Si eres de Tehuacán y quieres construir algo que use toda la ciudad, '
            'hay lugar para ti en uno de estos tres frentes:',
            'We\'re a small team and just getting started. If you\'re from Tehuacán and want to build something the '
            'whole city uses, there\'s a place for you on one of these three fronts:') + '</p>'
        '<div class="co-grid">'
        + co_card('Estudiantes', 'Students',
            'Servicio social, prácticas profesionales o un portafolio real: programación, diseño, mapas y GIS, '
            'mercadotecnia y contenido. Trabaja en un producto vivo y llévate experiencia que sí cuenta.',
            'Social service, internships, or a real portfolio: programming, design, maps and GIS, marketing and '
            'content. Work on a live product and walk away with experience that actually counts.')
        + co_card('Ventas y promotores', 'Sales & promoters',
            'Da de alta negocios y patrocinadores, corredor por corredor. Pago por resultados. '
            'Si sabes tocar puertas y te mueves por las calles de Tehuacán, esto es para ti.',
            'Sign up businesses and sponsors, corridor by corridor. Pay for results. '
            'If you know how to knock on doors and move around the streets of Tehuacán, this is for you.')
        + co_card('Socios de negocio', 'Business partners',
            'Imprenta, publicidad, alianzas con líneas de combi o capital semilla local. '
            '¿Tienes un negocio o un recurso que embona con esto? Hablemos.',
            'Printing, advertising, partnerships with combi lines, or local seed capital. '
            'Do you have a business or a resource that fits with this? Let\'s talk.')
        + '</div></div>'
        + lead_form('EQUIPO', 'unete', 'Quiero unirme', 'I want to join',
            'Cuéntanos quién eres y cómo quieres sumarte. Te contactamos por WhatsApp.',
            'Tell us who you are and how you\'d like to help. We\'ll reach you on WhatsApp.',
            'Ej: soy estudiante de sistemas y me interesa el servicio social…',
            'e.g. I\'m a CS student interested in doing social service…',
            ['Estudiante / servicio social', 'Ventas / promotor', 'Socio de negocio', 'Otro'])
        + '<p class="co-legal">' + bi('Al colaborar con nosotros aceptas nuestros ',
            'By collaborating with us you accept our ')
        + '<a href="/legal/terminos/">' + bi('Términos', 'Terms') + '</a>'
        + bi(' y el ', ' and our ')
        + '<a href="/legal/privacidad/">' + bi('Aviso de Privacidad', 'Privacy Notice') + '</a>.</p>'
        + LEAD_JS)
    (APPROOT / "nosotros").mkdir(parents=True, exist_ok=True)
    (APPROOT / "nosotros" / "index.html").write_text(
        page("Nosotros — MiTehuacán",
             "MiTehuacán es un proyecto local sin financiamiento, hecho por y para tehuacaneros. "
             "Buscamos estudiantes, promotores de ventas y socios de negocio para llevarlo al siguiente nivel.",
             nosotros_body, f"{DOMAIN}/nosotros/",
             crumb_items=[(bi("Inicio", "Home"), "/"), (bi("Nosotros", "About"), None)],
             title_en="About — MiTehuacán"),
        encoding="utf-8")

    # ---- /patrocinar
    patrocinar_body = co_style + (
        '<div class="co-hero"><h1>' + bi('Patrocina MiTehuacán', 'Sponsor MiTehuacán') + '</h1>'
        '<p class="lead">' + bi(
            'Cada día, miles de personas se suben a un combi en Tehuacán. Tu marca puede viajar con ellas: '
            'en el sticker con código QR que abre el mapa, y en el mapa mismo.',
            'Every day, thousands of people board a combi in Tehuacán. Your brand can ride with them: '
            'on the QR sticker that opens the map, and on the map itself.') + '</p></div>'
        '<div class="co-sec"><h2>' + bi('Por qué funciona', 'Why it works') + '</h2>'
        '<div class="co-grid">'
        + co_card('El QR es la puerta', 'The QR is the doorway',
            'Cada combi lleva un sticker con QR que abre el mapa. Tu logo va justo en esa puerta, la que la gente escanea.',
            'Every combi carries a QR sticker that opens the map. Your logo sits right on that doorway —the one people scan.')
        + co_card('Presencia diaria', 'Daily presence',
            'El combi es el medio más visto de la ciudad. Tu marca se ve en cada viaje, todos los días.',
            'The combi is the most-seen medium in the city. Your brand shows on every trip, every day.')
        + co_card('Local y medible', 'Local and measurable',
            'Pines en el mapa por ruta y por zona, cerca de donde de verdad están tus clientes.',
            'Pins on the map by route and area, close to where your customers actually are.')
        + co_card('Apoyas algo de aquí', 'You back something local',
            'Patrocinar mantiene gratis un servicio para toda la ciudad. Tu marca queda del lado bueno.',
            'Sponsoring keeps a citywide service free. Your brand ends up on the right side of it.')
        + '</div></div>'
        '<div class="co-sec"><h2>' + bi('Niveles de patrocinio', 'Sponsorship levels') + '</h2>'
        + tier('1', 'Aliado', 'Ally', 'desde $199 MXN / mes · una ruta', 'from $199 MXN / mo · one route', [
            ('Tu logo en los stickers con QR dentro de los combis de una ruta.',
             'Your logo on the QR stickers inside one route\'s combis.'),
            ('Mención como aliado en esta página.', 'Listed as an ally on this page.')])
        + tier('2', 'Presencia', 'Presence', 'desde $399 MXN / mes', 'from $399 MXN / mo', [
            ('Todo lo del Nivel 1.', 'Everything in Level 1.'),
            ('Un mini-mapa de tus sucursales impreso en el sticker.', 'A mini-map of your locations printed on the sticker.'),
            ('Pin de tu negocio en el mapa en vivo, como destino.', 'A pin for your business on the live map, as a destination.')])
        + tier('3', 'Destacado', 'Featured', 'desde $799 MXN / mes · varias rutas', 'from $799 MXN / mo · several routes', [
            ('Todo lo del Nivel 2, en varias rutas o un corredor completo.', 'Everything in Level 2, across several routes or a whole corridor.'),
            ('Logo y pin destacado en la app para las rutas que pasan cerca de ti.', 'Featured logo and pin in the app for routes that pass near you.'),
            ('Apareces como "Recomendado" en tu categoría y zona.', 'You appear as "Recommended" in your category and area.')],
            top=True, ribbon=('Más popular', 'Most popular'))
        + tier('4', 'Socio de temporada', 'Season partner', 'a convenir · prepago por temporada', 'let\'s talk · prepaid by season', [
            ('Presencia en toda la ciudad, no solo una ruta.', 'Presence across the whole city, not just one route.'),
            ('Colocación prioritaria y co-branding en materiales impresos.', 'Priority placement and co-branding on printed materials.'),
            ('Sé el patrocinador ancla de tu categoría.', 'Be the anchor sponsor for your category.')])
        + '<p class="note">' + bi(
            'Precios de lanzamiento, indicativos. Se ajustan por ruta, zona y temporada, y hay opción de trueque '
            '(imprenta, publicidad, servicios). El acuerdo final siempre se firma por escrito.',
            'Indicative launch prices. They adjust by route, area and season, and barter is possible '
            '(printing, advertising, services). The final agreement is always put in writing.') + '</p></div>'
        + lead_form('PATROCINIO', 'contacto', 'Quiero patrocinar', 'I want to sponsor',
            'Dinos qué nivel te interesa y de qué es tu negocio. Te mandamos los detalles por WhatsApp.',
            'Tell us which level interests you and what your business is. We\'ll send details on WhatsApp.',
            'Ej: tengo una farmacia en El Paseo, me interesa el Nivel 2…',
            'e.g. I run a pharmacy on El Paseo, I\'m interested in Level 2…',
            ['Nivel 1 · Logo en sticker', 'Nivel 2 · Logo + mini-mapa', 'Nivel 3 · Destacado en el mapa',
             'Nivel 4 · Socio de temporada', 'Trueque / otro'])
        + '<p class="co-legal">' + bi('Consulta nuestros ', 'See our ')
        + '<a href="/legal/terminos/">' + bi('Términos', 'Terms') + '</a>'
        + bi(' y ', ' and ')
        + '<a href="/legal/privacidad/">' + bi('Aviso de Privacidad', 'Privacy Notice') + '</a>.</p>'
        + LEAD_JS)
    (APPROOT / "patrocinar").mkdir(parents=True, exist_ok=True)
    (APPROOT / "patrocinar" / "index.html").write_text(
        page("Patrocina — MiTehuacán",
             "Pon tu marca donde se mueve la ciudad: en los stickers con QR de los combis y en el mapa en vivo. "
             "Cuatro niveles de patrocinio, desde tu logo en el sticker hasta socio de temporada.",
             patrocinar_body, f"{DOMAIN}/patrocinar/",
             crumb_items=[(bi("Inicio", "Home"), "/"), (bi("Patrocina", "Sponsor"), None)],
             title_en="Sponsor — MiTehuacán"),
        encoding="utf-8")

    # ---- /legal/privacidad + /legal/terminos. Grounded in the actual code:
    # no login, no ad networks, no third-party trackers; IPs are one-way hashed
    # for rate-limiting (see functions/api/feedback.js, reportes.js); form contact
    # and self-listed businesses are the only personal data stored.
    priv_es = (
        '<h1>Aviso de Privacidad</h1><p class="upd">Última actualización: julio 2026</p>'
        '<p>MiTehuacán es un proyecto local en Tehuacán, Puebla. Este aviso explica qué datos tratamos y cómo. '
        'En resumen: pedimos lo mínimo, no vendemos nada y no te rastreamos con publicidad.</p>'
        '<h2>Qué NO hacemos</h2><ul>'
        '<li>No necesitas cuenta ni contraseña para usar el mapa.</li>'
        '<li>No usamos redes de publicidad ni rastreadores de terceros.</li>'
        '<li>No vendemos ni compartimos tus datos con terceros para publicidad.</li>'
        '<li>No enviamos correo no deseado.</li></ul>'
        '<h2>Qué datos tratamos</h2><ul>'
        '<li><b>Uso del mapa:</b> conteos anónimos y agregados. Tu dirección IP se convierte en un identificador '
        'irreversible (hash) solo para evitar spam; no la guardamos en claro.</li>'
        '<li><b>Formularios (ideas, unirte al equipo, patrocinar):</b> guardamos tu mensaje y el contacto que nos '
        'dejes (por ejemplo tu WhatsApp o nombre) para responderte.</li>'
        '<li><b>Alta de negocios:</b> los datos que publicas de tu negocio (nombre, categoría, contacto) se muestran '
        'de forma pública en el directorio, porque ese es su propósito.</li></ul>'
        '<h2>Para qué los usamos</h2>'
        '<p>Únicamente para operar el servicio: mostrar el directorio, responderte, moderar contenido y evitar abuso. '
        'Nada más.</p>'
        '<h2>Tus derechos</h2>'
        '<p>Puedes acceder, rectificar, cancelar u oponerte al tratamiento de tus datos (derechos ARCO, conforme a la '
        'ley mexicana). Escríbenos desde el formulario de <a href="/nosotros/#unete">Nosotros</a> y atenderemos tu '
        'solicitud.</p>'
        '<h2>Cambios</h2>'
        '<p>Si este aviso cambia, actualizaremos la fecha de arriba. El uso continuo del servicio implica la '
        'aceptación de la versión vigente.</p>')
    priv_en = (
        '<h1>Privacy Notice</h1><p class="upd">Last updated: July 2026</p>'
        '<p>MiTehuacán is a local project in Tehuacán, Puebla. This notice explains what data we handle and how. '
        'In short: we ask for the minimum, we sell nothing, and we don\'t track you with advertising.</p>'
        '<h2>What we do NOT do</h2><ul>'
        '<li>You don\'t need an account or password to use the map.</li>'
        '<li>We use no ad networks and no third-party trackers.</li>'
        '<li>We don\'t sell or share your data with third parties for advertising.</li>'
        '<li>We don\'t send spam.</li></ul>'
        '<h2>What data we handle</h2><ul>'
        '<li><b>Map usage:</b> anonymous, aggregate counts. Your IP address is turned into an irreversible identifier '
        '(a hash) only to prevent spam; we don\'t store it in the clear.</li>'
        '<li><b>Forms (ideas, joining the team, sponsoring):</b> we store your message and any contact you leave '
        '(such as your WhatsApp or name) so we can reply.</li>'
        '<li><b>Business listings:</b> the business data you publish (name, category, contact) is shown publicly in '
        'the directory, because that is its purpose.</li></ul>'
        '<h2>What we use it for</h2>'
        '<p>Only to run the service: show the directory, reply to you, moderate content, and prevent abuse. '
        'Nothing else.</p>'
        '<h2>Your rights</h2>'
        '<p>You may access, rectify, cancel, or object to the handling of your data (ARCO rights, under Mexican law). '
        'Write to us from the form on <a href="/nosotros/#unete">About</a> and we\'ll handle your request.</p>'
        '<h2>Changes</h2>'
        '<p>If this notice changes, we\'ll update the date above. Continued use of the service means you accept the '
        'current version.</p>')
    terms_es = (
        '<h1>Términos de Uso</h1><p class="upd">Última actualización: julio 2026</p>'
        '<p>Al usar MiTehuacán aceptas estos términos. Están escritos en lenguaje sencillo a propósito.</p>'
        '<h2>El servicio</h2>'
        '<p>MiTehuacán es un servicio gratuito e informativo para Tehuacán y su región. Hacemos nuestro mejor '
        'esfuerzo para que la información sea correcta, pero las rutas, horarios y tarifas de los combis cambian; '
        'no somos una autoridad de transporte y no garantizamos exactitud. Verifica antes de viajar.</p>'
        '<h2>Contenido que aportas</h2>'
        '<p>Si das de alta un negocio, envías una idea o reportas algo, confirmas que la información es tuya o tienes '
        'derecho a compartirla, y que es veraz. Podemos moderar, editar o quitar contenido que sea falso, spam o '
        'inapropiado.</p>'
        '<h2>Datos abiertos</h2>'
        '<p>Los datos del mapa (rutas y trazos) se comparten bajo la Open Database License (ODbL) 1.0, con '
        'atribución a OpenStreetMap y a los proyectos ciudadanos de mapeo de la región.</p>'
        '<h2>Patrocinadores y colaboradores</h2>'
        '<p>Los patrocinios y las colaboraciones pagadas se rigen por un acuerdo por escrito aparte. Los precios '
        'publicados en <a href="/patrocinar/">Patrocina</a> son indicativos y de lanzamiento.</p>'
        '<h2>Sin garantía</h2>'
        '<p>El servicio se ofrece "tal cual". No nos hacemos responsables de decisiones tomadas con base en la '
        'información del sitio. Úsalo con criterio.</p>'
        '<h2>Contacto</h2>'
        '<p>¿Dudas? Escríbenos desde el formulario de <a href="/nosotros/#unete">Nosotros</a>.</p>')
    terms_en = (
        '<h1>Terms of Use</h1><p class="upd">Last updated: July 2026</p>'
        '<p>By using MiTehuacán you accept these terms. They\'re written in plain language on purpose.</p>'
        '<h2>The service</h2>'
        '<p>MiTehuacán is a free, informational service for Tehuacán and its region. We do our best to keep the '
        'information correct, but combi routes, schedules, and fares change; we\'re not a transit authority and we '
        'don\'t guarantee accuracy. Check before you travel.</p>'
        '<h2>Content you contribute</h2>'
        '<p>If you list a business, send an idea, or report something, you confirm the information is yours or you '
        'have the right to share it, and that it\'s truthful. We may moderate, edit, or remove content that is false, '
        'spam, or inappropriate.</p>'
        '<h2>Open data</h2>'
        '<p>The map data (routes and traces) is shared under the Open Database License (ODbL) 1.0, with attribution '
        'to OpenStreetMap and to the region\'s citizen mapping projects.</p>'
        '<h2>Sponsors and collaborators</h2>'
        '<p>Sponsorships and paid collaborations are governed by a separate written agreement. Prices published on '
        '<a href="/patrocinar/">Sponsor</a> are indicative and introductory.</p>'
        '<h2>No warranty</h2>'
        '<p>The service is provided "as is." We\'re not responsible for decisions made based on the information on '
        'the site. Use good judgment.</p>'
        '<h2>Contact</h2>'
        '<p>Questions? Write to us from the form on <a href="/nosotros/#unete">About</a>.</p>')
    priv_body = co_style + '<div class="lg"><div class="es">' + priv_es + '</div><div class="en">' + priv_en + '</div></div>'
    terms_body = co_style + '<div class="lg"><div class="es">' + terms_es + '</div><div class="en">' + terms_en + '</div></div>'
    (APPROOT / "legal" / "privacidad").mkdir(parents=True, exist_ok=True)
    (APPROOT / "legal" / "privacidad" / "index.html").write_text(
        page("Aviso de Privacidad — MiTehuacán",
             "Cómo trata MiTehuacán tus datos: lo mínimo, sin publicidad ni rastreadores de terceros.",
             priv_body, f"{DOMAIN}/legal/privacidad/",
             crumb_items=[(bi("Inicio", "Home"), "/"), (bi("Privacidad", "Privacy"), None)],
             title_en="Privacy Notice — MiTehuacán"),
        encoding="utf-8")
    (APPROOT / "legal" / "terminos").mkdir(parents=True, exist_ok=True)
    (APPROOT / "legal" / "terminos" / "index.html").write_text(
        page("Términos de Uso — MiTehuacán",
             "Los términos de uso de MiTehuacán, en lenguaje sencillo: servicio gratuito, datos abiertos ODbL.",
             terms_body, f"{DOMAIN}/legal/terminos/",
             crumb_items=[(bi("Inicio", "Home"), "/"), (bi("Términos", "Terms"), None)],
             title_en="Terms of Use — MiTehuacán"),
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
