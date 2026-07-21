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
    # ONLY agents that gather data for the maps (OSM, DENUE, calles, and the
    # discovery scrapers). build/stickers/prospectos are pipeline tools, NOT agents.
    "osm":        {"cmd": [PY, "src/scripts/16_refresh_pois.py"],   "desc": "OSM POIs + places (Overpass)"},
    "denue":      {"cmd": [PY, "src/scripts/17_build_denue.py"],    "desc": "DENUE establishments (needs resources/poi/denue_puebla.csv)"},
    "calles":     {"cmd": [PY, "src/scripts/20_build_streets.py"],  "desc": "streets + esquinas (Overpass)"},
    "google":     {"cmd": [PY, "src/scripts/discover/run.py", "google"],
                   "desc": "Google Maps discovery — sweeps space×category into google.db"},
    "instagram":  {"cmd": [PY, "src/scripts/discover/run.py", "instagram"],
                   "desc": "Instagram discovery — needs YOUR session (sign in below)"},
    "facebook":   {"cmd": [PY, "src/scripts/discover/run.py", "facebook"],
                   "desc": "Facebook discovery — needs YOUR session (sign in below)"},
    "google-verify":    {"cmd": [PY, "src/scripts/discover/run.py", "google", "--verify"],
                         "desc": "re-check google records, mark permanently-closed ones dead (prune)"},
    "instagram-verify": {"cmd": [PY, "src/scripts/discover/run.py", "instagram", "--verify"],
                         "desc": "re-check instagram handles, mark gone ones dead (prune)"},
    "facebook-verify":  {"cmd": [PY, "src/scripts/discover/run.py", "facebook", "--verify"],
                         "desc": "re-check facebook pages, mark gone ones dead (prune)"},
    "denue-dl":   {"cmd": ["bash", "-c",
                           "curl -s -o /tmp/denue_mx.zip https://www.inegi.org.mx/contenidos/masiva/denue/denue_21_csv.zip"
                           " && unzip -o -q /tmp/denue_mx.zip -d /tmp/denue_mx"
                           " && cp /tmp/denue_mx/conjunto_de_datos/denue_inegi_21_.csv resources/poi/denue_puebla.csv"
                           " && echo denue csv actualizado: $(wc -l < resources/poi/denue_puebla.csv) filas"],
                   "desc": "downloads the INEGI DENUE CSV (37MB)"},
}
# daily chain: refresh authoritative layers, sweep discovery, then prune
CHAINS = {"full": ["osm", "denue-dl", "denue", "calles",
                   "google", "instagram", "facebook",
                   "google-verify", "instagram-verify", "facebook-verify"]}

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


DISCOVERY_PLATFORMS = ("google", "instagram", "facebook")


def snapshot_all():
    snaps = {name: snapshot_layer(p) for name, p in LAYERS.items() if p.exists()}
    # seed every discovery layer as empty so a FIRST write still diffs as adds
    disc = REPO / "resources" / "discovery"
    for plat in DISCOVERY_PLATFORMS:
        entries = {}
        f = disc / f"{plat}.jsonl"
        if f.exists():
            for line in f.read_text().splitlines():
                try:
                    c = json.loads(line)
                    entries[("candidate", c["name"], 0, 0)] = c.get("source", "")
                except (ValueError, KeyError):
                    pass
        snaps["discovery-" + plat] = entries
    return snaps


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
        fh.write("\n\n== DATA CHANGES (complete \u2014 nothing summarized) ==\n")
        if not report:
            fh.write("no changes in data layers\n")
        for layer, d in report.items():
            fh.write(f"\n[{layer}] +{len(d['added'])} added, "
                     f"-{len(d['removed'])} removed, ~{len(d['changed'])} changed\n")
            for label, items in (("ADDED", d["added"]), ("REMOVED", d["removed"]),
                                 ("CHANGED", d["changed"])):
                for n in items:
                    fh.write(f"  {label}: {n}\n")
    full = log.read_text(errors="replace")
    tail_src = full.split("== DATA CHANGES")[0]
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


HTML = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>data agents · mitehuacán</title><style>
:root{--bg:#17171b;--panel:#1f1f24;--ink:#ececf0;--ink2:#a5a5b0;--line:#33333a;--accent:#6ea6ff;--ok:#4ade80;--err:#ff7b6b;--warn:#f5a623}
@media(prefers-color-scheme:light){:root{--bg:#fff;--panel:#f7f7f8;--ink:#1a1a1e;--ink2:#55555e;--line:#e2e2e6;--accent:#0f62fe;--ok:#1a7f37;--err:#d4351c;--warn:#b7791f}}
*{box-sizing:border-box}body{margin:0;font:13.5px/1.5 system-ui,sans-serif;color:var(--ink);background:var(--bg);padding:16px}
.wrap{max-width:900px;margin:0 auto}h1{font-size:18px;margin:0 0 2px}
.sub{color:var(--ink2);font-size:12px;margin:0 0 14px}
#alert{display:none;background:rgba(220,60,60,.12);border:1.5px solid var(--err);color:var(--err);border-radius:12px;padding:11px 14px;font-weight:700;margin-bottom:12px}
.tblwrap{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;min-width:640px}
th{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink2);text-align:left;padding:9px 12px;border-bottom:1px solid var(--line)}
td{padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:middle}
tr:last-child td{border-bottom:none}
tbody tr{cursor:pointer}tbody tr:hover td{background:rgba(110,166,255,.06)}
td .d{color:var(--ink2);font-size:11.5px}
.st{padding:2px 10px;border-radius:999px;font-size:11px;font-weight:800;white-space:nowrap}
.st.ok{background:rgba(46,204,113,.15);color:var(--ok)}
.st.fail{background:rgba(220,60,60,.18);color:var(--err)}
.st.run{background:rgba(245,166,35,.2);color:var(--warn)}
.st.warn2{background:rgba(245,166,35,.15);color:var(--warn)}
.st.delta{background:rgba(110,166,255,.15);color:var(--accent)}
.st.none{background:transparent;color:var(--ink2);font-weight:400}
button{border:none;border-radius:8px;padding:6px 12px;background:var(--accent);color:#fff;font-weight:700;cursor:pointer}
button:disabled{opacity:.5}
button.ghost{background:transparent;border:1px solid var(--line);color:var(--ink)}
.loginpanel{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:11px 13px;margin-top:8px;color:var(--ink2);font-size:12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.bar{display:flex;gap:10px;align-items:center;margin:12px 0;flex-wrap:wrap}
a.back{color:var(--accent);text-decoration:none;font-weight:700}
.logrow td{padding:0;border-bottom:1px solid var(--line);cursor:default}
.logrow pre{margin:0;background:var(--bg);padding:11px 13px;font-size:11px;max-height:420px;overflow:auto;white-space:pre-wrap}
.when{color:var(--ink2);font-size:11.5px;white-space:nowrap}
</style></head><body><div class="wrap">
<h1 id="title">Data agents</h1>
<p class="sub" id="subtitle">gather data for the maps · run on THIS machine · logs in .agent-runs/</p>
<div id="alert"></div>
<div id="main"></div>
</div><script>
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/</g,'&lt;');
const ago=iso=>{const s=(Date.now()-new Date(iso))/1e3;
  return s<90?Math.round(s)+' s':s<5400?Math.round(s/60)+' min':s<172800?(s/3600).toFixed(1)+' h':Math.round(s/86400)+' days';};
const stChip=r=>r.exit===0?'<span class="st ok">ok</span>':'<span class="st fail">exit '+r.exit+'</span>';
const dChip=r=>r.delta&&(r.delta['+']||r.delta['-']||r.delta['~'])
  ?'<span class="st delta">+'+r.delta['+']+' \u2212'+r.delta['-']+' ~'+r.delta['~']+'</span>':'<span class="st none">no changes</span>';
const wChip=r=>r.exit===0&&r.warns?'<span class="st warn2">'+r.warns+'</span>':'<span class="st none">0</span>';
let VIEW=null,OPEN={},D=null,LAUNCHED={};
async function refresh(){
  D=await (await fetch('/api/state')).json();
  const latest={};D.runs.forEach(r=>{if(!(r.name in latest))latest[r.name]=r;});
  const bad=Object.values(latest).filter(r=>r.exit!==0);
  $('alert').style.display=bad.length?'block':'none';
  $('alert').textContent=bad.length?('⚠️ last run FAILED: '+bad.map(r=>r.name).join(', ')+' — click the agent to see the log'):'';
  VIEW?renderDetail():renderMain(latest);
  const live=document.querySelector('.logrow pre[data-live]');
  if(live)live.textContent=await (await fetch('/api/log?f='+encodeURIComponent(live.dataset.live)+'&tail=1')).text();
}
function renderMain(latest){
  $('title').textContent='Data agents';
  $('subtitle').innerHTML='gather data for the maps · run on THIS machine · logs in .agent-runs/';
  const rows=Object.entries(D.agents).map(([n,a])=>{
    const r=latest[n],run=D.running[n];
    const estado=run?'<span class="st run">running '+ago(run.start)+'</span>':r?stChip(r):'<span class="st none">never</span>';
    return '<tr onclick="show(\\''+n+'\\')"><td><b>'+n+'</b><div class="d">'+esc(a.desc)+'</div></td>'+
      '<td>'+estado+'</td>'+
      '<td class="when">'+(r?new Date(r.start).toLocaleString('en-US')+'<br>'+ago(r.start)+' ago':'—')+'</td>'+
      '<td>'+(r?r.dur_s+' s':'—')+'</td>'+
      '<td>'+(r?dChip(r):'—')+'</td>'+
      '<td>'+(r?wChip(r):'—')+'</td>'+
      '<td>'+(run?'':'<button onclick="event.stopPropagation();launch(\\''+n+'\\')">▶</button>')+'</td></tr>';
  }).join('');
  $('main').innerHTML='<div class="tblwrap"><table><thead><tr>'+
    '<th>agent</th><th>status</th><th>last run</th><th>duration</th><th>changes</th><th>warnings</th><th></th>'+
    '</tr></thead><tbody>'+rows+'</tbody></table></div>'+
    '<div class="bar">'+(Object.keys(D.running).length
      ?'<span class="st run">chain running…</span>'
      :'<button onclick="launch(\\'full\\')">▶▶ run all</button>')+
    '<span class="d" style="color:var(--ink2);font-size:11.5px">refresh layers → discover (google/ig/fb) → verify &amp; prune · also runs on its own daily at 07:00</span></div>'+
    '<div class="loginpanel">🔑 <b>log into accounts</b> — opens a real Chrome window to sign in; the agent reuses the session, never your password:'+
      ['google','instagram','facebook'].map(p=>'<button class="ghost" id="lg-'+p+'" onclick="doLogin(\\''+p+'\\')">'+
        (LAUNCHED[p]?'✓ '+p+' opened — sign in, then close it':'open '+p)+'</button>').join('')+'</div>';
}
function renderDetail(){
  const n=VIEW,a=D.agents[n],run=D.running[n];
  $('title').textContent=n;
  $('subtitle').innerHTML='<a class="back" href="#" onclick="VIEW=null;OPEN={};refresh();return false">← all agents</a> · '+esc(a?a.desc:'');
  const runs=D.runs.filter(r=>r.name===n);
  const rows=runs.slice(0,80).map(r=>{
    const open=OPEN[r.log];
    return '<tr onclick="toggleLog(\\''+r.log+'\\')">'+
      '<td class="when">'+new Date(r.start).toLocaleString('en-US')+'<br>'+ago(r.start)+'</td>'+
      '<td>'+stChip(r)+'</td><td>'+r.dur_s+' s</td><td>'+dChip(r)+'</td><td>'+wChip(r)+'</td>'+
      '<td class="d" style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(r.tail.split('\\n').pop())+'</td></tr>'+
      (open?'<tr class="logrow"><td colspan="6"><pre id="log-'+r.log+'">loading…</pre></td></tr>':'');
  }).join('');
  $('main').innerHTML='<div class="bar">'+(run
      ?'<span class="st run">running '+ago(run.start)+'</span>'
      :'<button onclick="launch(\\''+n+'\\')">▶ run now</button>')+'</div>'+
    '<div class="tblwrap"><table><thead><tr>'+
    '<th>when</th><th>status</th><th>duration</th><th>changes</th><th>warnings</th><th>last line</th>'+
    '</tr></thead><tbody>'+(rows||'<tr><td colspan="6" class="d">no runs yet</td></tr>')+'</tbody></table></div>'+
    (run?'<div class="tblwrap" style="margin-top:10px"><table><tbody><tr class="logrow"><td><pre data-live="'+run.log.split('/').pop()+'">…</pre></td></tr></tbody></table></div>':'');
  for(const f of Object.keys(OPEN))loadLog(f);
}
function show(n){VIEW=n;OPEN={};refresh();}
function toggleLog(f){OPEN[f]?delete OPEN[f]:OPEN[f]=1;renderDetail();}
async function loadLog(f){
  const el=$('log-'+f);
  if(el&&el.textContent==='loading…')el.textContent=await (await fetch('/api/log?f='+encodeURIComponent(f))).text();
}
async function launch(n){await fetch('/api/run?name='+n,{method:'POST'});setTimeout(refresh,400);}
async function doLogin(p){
  const btn=$('lg-'+p);if(btn){btn.textContent='opening '+p+'…';btn.disabled=true;}
  LAUNCHED[p]=true;
  await fetch('/api/login?platform='+p,{method:'POST'});
}
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
        if u.path == "/api/login":
            plat = (urllib.parse.parse_qs(u.query).get("platform") or [""])[0]
            if plat not in DISCOVERY_PLATFORMS:
                return self.send_error(400)
            disc = str(REPO / "src" / "scripts" / "discover" / "run.py")
            subprocess.Popen([PY, disc, plat, "--login"], cwd=REPO)
            return self._send('{"ok":true}')
        self.send_error(404)


def main():
    args = sys.argv[1:]
    if args[:1] == ["run"] and len(args) > 1:
        names = CHAINS.get(args[1], [args[1]])
        for n in names:
            if n not in AGENTS:
                sys.exit(f"unknown agent: {n} (have: {', '.join(AGENTS)}, full)")
            if run_agent(n) != 0:
                sys.exit(1)
        return
    if args[:1] == ["login"]:
        # opens a real Chrome window per platform so you can sign in to each
        # account the agents will reuse. sessions persist in .agent-auth/.
        plats = args[1:] or list(DISCOVERY_PLATFORMS)
        prof = "default"
        if "--profile" in plats:
            j = plats.index("--profile")
            prof = plats[j + 1] if j + 1 < len(plats) else "default"
            plats = [p for p in plats if p not in ("--profile", prof)]
            plats = plats or list(DISCOVERY_PLATFORMS)
        disc = str(REPO / "src" / "scripts" / "discover" / "run.py")
        for p in plats:
            print(f"\n=== log into {p} (profile: {prof}) — a Chrome window will open ===")
            subprocess.run([PY, disc, p, "--login", "--profile", prof], cwd=REPO)
        print("\nall requested logins done. sessions saved in .agent-auth/")
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
        print(f"daily cron installed: runs 'full' at {hour:02d}:00 -> logs land in the dashboard")
        return
    if args[:1] == ["uninstall-cron"]:
        plist = Path.home() / "Library" / "LaunchAgents" / "mx.mitehuacan.agents.plist"
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
        plist.unlink(missing_ok=True)
        print("daily cron removed")
        return
    if args[:1] == ["dash"]:
        RUNS.mkdir(exist_ok=True)
        # standing issues get flagged on the desktop the moment the console opens
        latest = {}
        for r in load_runs()[::-1]:
            latest[r["name"]] = r
        bad = [n for n, r in latest.items() if r["exit"] != 0]
        if bad:
            notify("Agents failing", ", ".join(bad) + " — check the dashboard")
        print("dashboard: http://localhost:8790  (ctrl-c to quit)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8790), H).serve_forever()
        return
    print(__doc__)


if __name__ == "__main__":
    main()
