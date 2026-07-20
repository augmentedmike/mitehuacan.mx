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
    "osm":        {"cmd": [PY, "src/scripts/16_refresh_pois.py"],   "desc": "OSM POIs + places (Overpass)"},
    "denue":      {"cmd": [PY, "src/scripts/17_build_denue.py"],    "desc": "DENUE establishments (needs resources/poi/denue_puebla.csv)"},
    "calles":     {"cmd": [PY, "src/scripts/20_build_streets.py"],  "desc": "streets + esquinas (Overpass)"},
    "prospectos": {"cmd": [PY, "src/scripts/18_prospects.py"],      "desc": "per-route prospect sheets"},
    "stickers":   {"cmd": [PY, "src/scripts/19_generate_stickers.py"], "desc": "QR sticker PNGs + sheets"},
    "build":      {"cmd": [PY, "src/scripts/09_build_site.py"],     "desc": "build the deployable site"},
}
CHAINS = {"full": ["osm", "denue", "calles", "build"]}

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
    t0 = time.time()
    with open(log, "w") as fh:
        fh.write(f"$ {' '.join(spec['cmd'])}\n# started {ts.isoformat()}\n\n")
        fh.flush()
        p = subprocess.run(spec["cmd"], cwd=REPO, stdout=fh, stderr=subprocess.STDOUT)
    dur = round(time.time() - t0, 1)
    tail = "".join(log.read_text(errors="replace").splitlines(keepends=True)[-4:]).strip()
    rec = {"name": name, "start": ts.isoformat(), "dur_s": dur, "exit": p.returncode,
           "log": log.name, "tail": tail[-300:]}
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
    return '<div class="ag"><div><b>'+n+'</b><div class="d">'+esc(a.desc)+'</div></div>'+
      (running?'<span class="st run">corriendo '+ago(running.start)+'</span>'
              :'<button onclick="launch(\\''+n+'\\')">▶</button>')+'</div>';
  }).join('')+'<div class="ag"><div><b>full</b><div class="d">osm → denue → calles → build</div></div>'+
    (Object.keys(d.running).length?'<span class="st run">…</span>':'<button onclick="launch(\\'full\\')">▶▶</button>')+'</div>';
  const latestByName={};
  d.runs.forEach(r=>{if(!(r.name in latestByName))latestByName[r.name]=r;});
  const bad=Object.values(latestByName).filter(r=>r.exit!==0);
  $('alert').style.display=bad.length?'block':'none';
  $('alert').textContent=bad.length?('⚠️ última corrida FALLÓ: '+bad.map(r=>r.name).join(', ')+' — revisa el log abajo'):'';
  $('runs').innerHTML=d.runs.slice(0,40).map((r,i)=>
    '<div class="run" onclick="toggle(this,\\''+r.log+'\\')"><div class="row">'+
    '<b>'+r.name+'</b><span class="st '+(r.exit===0?'ok':'fail')+'">'+(r.exit===0?'ok':'exit '+r.exit)+'</span>'+
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
    if args[:1] == ["dash"]:
        RUNS.mkdir(exist_ok=True)
        print("dashboard: http://localhost:8790  (ctrl-c para salir)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8790), H).serve_forever()
        return
    print(__doc__)


if __name__ == "__main__":
    main()
