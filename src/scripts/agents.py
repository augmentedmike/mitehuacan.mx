#!/usr/bin/env python3
"""LOCAL agent runner + dashboard. Nothing here deploys anywhere.

Every data agent run on this machine goes through this wrapper so it is
logged, timed, and visible:

    python3 src/scripts/agents.py run <name>       # run one agent, fully logged
    python3 src/scripts/agents.py run full         # the whole weekly chain
    python3 src/scripts/agents.py dash             # dashboard at http://localhost:8790

Runs land in .agent-runs/ (gitignored): one full log per run plus runs.jsonl
(the index). Failures fire a macOS notification. The dashboard lists every
run with status/duration, streams the live log while an agent is running,
lets you launch agents with one click, and shows a red banner if the latest
run of anything failed.
"""
import json
import re
import http.server
import subprocess
import sys
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / ".agent-runs"
INDEX = RUNS / "runs.jsonl"
PY = sys.executable

AGENTS = {
    # SOLO agentes que recolectan datos para los mapas (OSM, DENUE, calles,
    # y a futuro scrapers de descubrimiento: instagram/facebook/google).
    # build/stickers/prospectos son herramientas de pipeline/negocio, NO agentes.
    "osm":        {"cmd": [PY, "src/scripts/16_refresh_pois.py"],   "desc": "OSM POIs + places (Overpass)"},
    "denue":      {"cmd": [PY, "src/scripts/17_build_denue.py"],    "desc": "DENUE establishments (needs resources/poi/denue_puebla.csv)"},
    "calles":     {"cmd": [PY, "src/scripts/20_build_streets.py"],  "desc": "streets + esquinas (Overpass)"},
    "denue-dl":   {"cmd": ["bash", "-c",
                           "curl -s -o /tmp/denue_mx.zip https://www.inegi.org.mx/contenidos/masiva/denue/denue_21_csv.zip"
                           " && unzip -o -q /tmp/denue_mx.zip -d /tmp/denue_mx"
                           " && cp /tmp/denue_mx/conjunto_de_datos/denue_inegi_21_.csv resources/poi/denue_puebla.csv"
                           " && echo denue csv actualizado: $(wc -l < resources/poi/denue_puebla.csv) filas"],
                   "desc": "descarga el CSV DENUE de INEGI (37MB)"},
}
CHAINS = {"full": ["osm", "denue-dl", "denue", "calles"]}

# data layers snapshotted before/after every run so the log records EXACTLY
# what each agent added / removed / changed — the log is the archive
LAYERS = {
    "pois":    REPO / "resources" / "map-data" / "pois.js",
    "places":  REPO / "resources" / "map-data" / "places.js",
    "denue":   REPO / "resources" / "map-data" / "denue.js",
    "calles":  REPO / "resources" / "map-data" / "calles.js",
    "sponsors": REPO / "resources" / "map-data" / "sponsors.js",
}


def snapshot_layer(path):
    """name -> (coords, kind) for every entry in a generated data layer."""
    try:
        t = path.read_text(encoding="utf-8")
        data = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
    except Exception:
        return None
    out = {}
    for key in ("pois", "places", "streets", "cruces"):
        for e in data.get(key, []) if isinstance(data, dict) else []:
            out[(key, e["n"], round(e["c"][0], 5), round(e["c"][1], 5))] = e.get("k", "")
    # sponsors.js shape: {sponsors: {...}, by_route: {...}} — hash-level only
    if not out and isinstance(data, dict):
        out[("_raw", json.dumps(data, sort_keys=True)[:64], 0, 0)] = ""
    return out


def snapshot_all():
    return {name: snapshot_layer(p) for name, p in LAYERS.items() if p.exists()}


def diff_snapshots(before, after):
    """full lists per layer; nothing summarized away."""
    report, totals = {}, {"+": 0, "-": 0, "~": 0}
    for layer in sorted(set(before) | set(after)):
        b, a = before.get(layer), after.get(layer)
        if b is None or a is None:
            continue
        added = sorted(k[1] for k in a.keys() - b.keys())
        removed = sorted(k[1] for k in b.keys() - a.keys())
        changed = sorted(k[1] for k in a.keys() & b.keys() if a[k] != b[k])
        if added or removed or changed:
            report[layer] = {"added": added, "removed": removed, "changed": changed}
            totals["+"] += len(added)
            totals["-"] += len(removed)
            totals["~"] += len(changed)
    return report, totals

RUNNING = {}  # name -> {"log": path, "start": iso}


def notify(title, msg):
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{msg}" with title "{title}" sound name "Basso"'],
                       capture_output=True, timeout=5)
    except Exception:
        pass


def run_agent(name):
    spec = AGENTS[name]
    RUNS.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%d-%H%M%S")
    log = RUNS / f"{stamp}-{name}.log"
    RUNNING[name] = {"log": str(log), "start": ts.isoformat()}
    before = snapshot_all()
    t0 = time.time()
    with open(log, "w") as fh:
        fh.write(f"$ {' '.join(spec['cmd'])}\n# started {ts.isoformat()}\n\n")
        fh.flush()
        p = subprocess.run(spec["cmd"], cwd=REPO, stdout=fh, stderr=subprocess.STDOUT)
    dur = round(time.time() - t0, 1)
    report, totals = diff_snapshots(before, snapshot_all())
    with open(log, "a") as fh:
        fh.write("\n\n== CAMBIOS EN DATOS (completos \u2014 nada se resume) ==\n")
        if not report:
            fh.write("sin cambios en las capas de datos\n")
        for layer, d in report.items():
            fh.write(f"\n[{layer}] +{len(d['added'])} agregados, "
                     f"-{len(d['removed'])} eliminados, ~{len(d['changed'])} modificados\n")
            for label, items in (("AGREGADO", d["added"]), ("ELIMINADO", d["removed"]),
                                 ("MODIFICADO", d["changed"])):
                for n in items:
                    fh.write(f"  {label}: {n}\n")
    full = log.read_text(errors="replace")
    tail_src = full.split("== CAMBIOS")[0]
    tail = "".join(tail_src.splitlines(keepends=True)[-4:]).strip()
    warns = len(re.findall(r"(?im)^.*\b(error|traceback|failed|exception)\b", tail_src))
    rec = {"name": name, "start": ts.isoformat(), "dur_s": dur, "exit": p.returncode,
           "log": log.name, "tail": tail[-300:], "warns": warns,
           "delta": totals, "delta_layers": {k: {"+": len(v["added"]), "-": len(v["removed"]),
                                                  "~": len(v["changed"])} for k, v in report.items()}}
    with open(INDEX, "a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    RUNNING.pop(name, None)
    if p.returncode != 0:
        notify("Agente FALLÓ: " + name, tail[-120:] or f"exit {p.returncode}")
    print(f"[{name}] exit {p.returncode} in {dur}s -> {log}")
    return p.returncode


def load_runs():
    if not INDEX.exists():
        return []
    out = []
    for line in INDEX.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out[::-1]


HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentes locales · mitehuacán</title><style>
:root{--bg:#17171b;--panel:#1f1f24;--ink:#ececf0;--ink2:#a5a5b0;--line:#33333a;--accent:#6ea6ff;--chip:#26262c;--ok:#4ade80;--err:#ff7b6b;--warn:#f5a623}
@media(prefers-color-scheme:light){:root{--bg:#fff;--panel:#f7f7f8;--ink:#1a1a1e;--ink2:#55555e;--line:#e2e2e6;--accent:#0f62fe;--chip:#fff;--ok:#1a7f37;--err:#d4351c;--warn:#b7791f}}
*{box-sizing:border-box}body{margin:0;font:13.5px/1.5 system-ui,sans-serif;color:var(--ink);background:var(--bg);padding:16px}
.wrap{max-width:820px;margin:0 auto}h1{font-size:18px;margin:0 0 2px}
.sub{color:var(--ink2);font-size:12px;margin:0 0 14px}
#alert{display:none;background:rgba(220,60,60,.12);border:1.5px solid var(--err);color:var(--err);border-radius:12px;padding:11px 14px;font-weight:700;margin-bottom:12px}
.agents{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.ag{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:9px 12px;display:flex;gap:9px;align-items:center}
.ag b{font-size:13px}.ag .d{color:var(--ink2);font-size:11px;max-width:190px}
.ag button{border:none;border-radius:8px;padding:6px 12px;background:var(--accent);color:#fff;font-weight:700;cursor:pointer}
.ag button:disabled{opacity:.5}
.run{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:10px 13px;margin:7px 0;cursor:pointer}
.run .row{display:flex;gap:10px;align-items:center}
.st{padding:2px 10px;border-radius:999px;font-size:11px;font-weight:800}
.st.ok{background:rgba(46,204,113,.15);color:var(--ok)}
.st.fail{background:rgba(220,60,60,.18);color:var(--err)}
.st.run{background:rgba(245,166,35,.2);color:var(--warn)}
.st.warn2{background:rgba(245,166,35,.15);color:var(--warn)}
.st.delta{background:rgba(110,166,255,.15);color:var(--accent)}
.ag{cursor:pointer}.ag.sel{outline:2px solid var(--accent)}
.when{margin-left:auto;color:var(--ink2);font-size:11.5px;white-space:nowrap}
.tail{color:var(--ink2);font-size:11.5px;margin-top:4px;white-space:pre-wrap}
pre{display:none;background:var(--bg);border:1px solid var(--line);border-radius:9px;padding:11px;font-size:11px;max-height:420px;overflow:auto;white-space:pre-wrap;margin:8px 0 0}
.run.open pre{display:block}
</style></head><body><div class="wrap">
<h1>Agentes locales</h1>
<p class="sub">corren en ESTA máquina · logs en .agent-runs/ · esta página vive solo en localhost</p>
<div id="alert"></div>
<div class="agents" id="agents"></div>
<div id="runs"></div>
</div><script>
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/</g,'&lt;');
const ago=iso=>{const s=(Date.now()-new Date(iso))/1e3;
  return s<90?Math.round(s)+' s':s<5400?Math.round(s/60)+' min':s<172800?(s/3600).toFixed(1)+' h':Math.round(s/86400)+' días';};
async function refresh(){
  const d=await (await fetch('/api/state')).json();
  $('agents').innerHTML=Object.entries(d.agents).map(([n,a])=>{
    const running=d.running[n];
    return '<div class="ag'+(FILTER===n?' sel':'')+'" onclick="setFilter(\\''+n+'\\')"><div><b>'+n+'</b><div class="d">'+esc(a.desc)+'</div></div>'+
      (running?'<span class="st run">corriendo '+ago(running.start)+'</span>'
              :'<button onclick="event.stopPropagation();launch(\\''+n+'\\')">▶</button>')+'</div>';
  }).join('')+'<div class="ag"><div><b>full</b><div class="d">osm → denue → calles → build</div></div>'+
    (Object.keys(d.running).length?'<span class="st run">…</span>':'<button onclick="launch(\\'full\\')">▶▶</button>')+'</div>';
  const latestByName={};
  d.runs.forEach(r=>{if(!(r.name in latestByName))latestByName[r.name]=r;});
  const bad=Object.values(latestByName).filter(r=>r.exit!==0);
  $('alert').style.display=bad.length?'block':'none';
  $('alert').textContent=bad.length?('⚠️ última corrida FALLÓ: '+bad.map(r=>r.name).join(', ')+' — revisa el log abajo'):'';
  const shown=FILTER?d.runs.filter(r=>r.name===FILTER):d.runs;
  $('runs').innerHTML=(FILTER?'<p class="sub">historial de <b>'+FILTER+'</b> · <a href="#" onclick="setFilter(null);return false" style="color:var(--accent)">ver todos</a></p>':'')+shown.slice(0,60).map((r,i)=>
    '<div class="run" onclick="toggle(this,\\''+r.log+'\\')"><div class="row">'+
    '<b>'+r.name+'</b><span class="st '+(r.exit===0?'ok':'fail')+'">'+(r.exit===0?'ok':'exit '+r.exit)+'</span>'+
    (r.exit===0&&r.warns?'<span class="st warn2">'+r.warns+' avisos</span>':'')+
    (r.delta&&(r.delta['+']||r.delta['-']||r.delta['~'])?'<span class="st delta">+'+r.delta['+']+' \u2212'+r.delta['-']+' ~'+r.delta['~']+'</span>':'')+
    '<span class="d" style="color:var(--ink2);font-size:11.5px">'+r.dur_s+' s</span>'+
    '<span class="when">'+new Date(r.start).toLocaleString('es-MX')+' · hace '+ago(r.start)+'</span></div>'+
    '<div class="tail">'+esc(r.tail)+'</div><pre></pre></div>').join('')||
    '<p class="sub">sin corridas aún — lanza un agente arriba o corre: python3 src/scripts/agents.py run full</p>';
  for(const n of Object.keys(d.running)){
    const el=document.querySelector('.run.open pre');
    if(el&&el.dataset.live)el.textContent=await (await fetch('/api/log?f='+encodeURIComponent(d.running[n].log.split('/').pop())+'&tail=1')).text();
  }
}
async function toggle(el,log){
  el.classList.toggle('open');
  const pre=el.querySelector('pre');
  if(el.classList.contains('open')&&!pre.textContent){
    pre.textContent=await (await fetch('/api/log?f='+encodeURIComponent(log))).text();
  }
}
async function launch(n){await fetch('/api/run?name='+n,{method:'POST'});setTimeout(refresh,400);}
let FILTER=null;
function setFilter(n){FILTER=FILTER===n?null:n;refresh();}
refresh();setInterval(refresh,3000);
</script></body></html>"""


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            return self._send(HTML, "text/html; charset=utf-8")
        if u.path == "/api/state":
            return self._send(json.dumps({
                "agents": {k: {"desc": v["desc"]} for k, v in AGENTS.items()},
                "running": RUNNING, "runs": load_runs()}, ensure_ascii=False))
        if u.path == "/api/log":
            q = urllib.parse.parse_qs(u.query)
            f = (q.get("f") or [""])[0]
            p = RUNS / Path(f).name          # no traversal
            if not p.exists():
                return self._send("(sin log)", "text/plain")
            txt = p.read_text(errors="replace")
            if q.get("tail"):
                txt = "".join(txt.splitlines(keepends=True)[-40:])
            return self._send(txt, "text/plain; charset=utf-8")
        self.send_error(404)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/run":
            name = (urllib.parse.parse_qs(u.query).get("name") or [""])[0]
            names = CHAINS.get(name, [name] if name in AGENTS else [])
            if not names:
                return self.send_error(400)

            def go():
                for n in names:
                    if run_agent(n) != 0:
                        break
            threading.Thread(target=go, daemon=True).start()
            return self._send('{"ok":true}')
        self.send_error(404)


def main():
    args = sys.argv[1:]
    if args[:1] == ["run"] and len(args) > 1:
        names = CHAINS.get(args[1], [args[1]])
        for n in names:
            if n not in AGENTS:
                sys.exit(f"agente desconocido: {n} (hay: {', '.join(AGENTS)}, full)")
            if run_agent(n) != 0:
                sys.exit(1)
        return
    if args[:1] == ["install-cron"]:
        plist = Path.home() / "Library" / "LaunchAgents" / "mx.mitehuacan.agents.plist"
        hour = int(args[2]) if len(args) > 2 else 7
        plist.parent.mkdir(parents=True, exist_ok=True)
        plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>mx.mitehuacan.agents</string>
  <key>ProgramArguments</key><array>
    <string>{PY}</string><string>{Path(__file__).resolve()}</string>
    <string>run</string><string>full</string></array>
  <key>WorkingDirectory</key><string>{REPO}</string>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>{hour}</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>{RUNS}/launchd.log</string>
  <key>StandardErrorPath</key><string>{RUNS}/launchd.log</string>
</dict></plist>""")
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
        subprocess.run(["launchctl", "load", str(plist)], check=True)
        print(f"cron diario instalado: corre 'full' a las {hour:02d}:00 -> logs en el dashboard")
        return
    if args[:1] == ["uninstall-cron"]:
        plist = Path.home() / "Library" / "LaunchAgents" / "mx.mitehuacan.agents.plist"
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
        plist.unlink(missing_ok=True)
        print("cron diario eliminado")
        return
    if args[:1] == ["dash"]:
        RUNS.mkdir(exist_ok=True)
        # standing issues get flagged on the desktop the moment the console opens
        latest = {}
        for r in load_runs()[::-1]:
            latest[r["name"]] = r
        bad = [n for n, r in latest.items() if r["exit"] != 0]
        if bad:
            notify("Agentes con fallas", ", ".join(bad) + " — revisa el dashboard")
        print("dashboard: http://localhost:8790  (ctrl-c para salir)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8790), H).serve_forever()
        return
    print(__doc__)


if __name__ == "__main__":
    main()
