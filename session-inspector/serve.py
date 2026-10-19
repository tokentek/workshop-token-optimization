#!/usr/bin/env python3
"""Session Inspector: a local dashboard for Claude Code session logs.

Usage:
    python3 serve.py [--port 8765] [--claude-dir ~/.claude] [--no-browser]

Then open http://127.0.0.1:8765. Only the Python 3.9+ standard library is used.
"""
import argparse
import errno
import json
import mimetypes
import os
import sys
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from urllib.request import urlopen

from inspector.discovery import Discovery, default_claude_dir
from inspector.pricing import Pricing
from inspector.session import CATEGORIES, Transcript
from inspector.tailer import JsonlTail

ROOT = os.path.dirname(os.path.abspath(__file__))
mimetypes.add_type("font/woff2", ".woff2")
STATIC = os.path.join(ROOT, "static")
POLL_SECONDS = 0.5
LIST_SECONDS = 2.0
IDLE_SECONDS = 120


class LiveTranscript:
    def __init__(self, path, kind):
        self.tail = JsonlTail(path)
        self.transcript = Transcript(kind)

    def poll(self):
        reset, records = self.tail.poll()
        if reset:
            self.transcript.reset()
        if records:
            self.transcript.ingest(records)
        return reset or bool(records)


class LiveSession:
    """One watched session: the main log plus its subagent logs."""

    def __init__(self, entry, pricing):
        self.entry = entry
        self.pricing = pricing
        self.main = LiveTranscript(entry["path"], "main")
        self.agents = {}  # agent id -> {"live": LiveTranscript, "meta": {...}}
        self.revision = 0
        # New for every watched-session object (server restart or re-open after idle),
        # so a browser can tell a fresh start from an old revision number.
        self.generation = uuid.uuid4().hex[:12]
        self.lock = threading.Lock()
        self.last_access = time.time()
        self._model = None
        self._model_rev = -1

    def poll(self):
        with self.lock:
            changed = self.main.poll()
            for info in Discovery.subagent_files(self.entry["path"]):
                if info["id"] not in self.agents:
                    self.agents[info["id"]] = {"live": LiveTranscript(info["path"], "agent"), "meta": info["meta"]}
                    changed = True
                elif not self.agents[info["id"]]["meta"] and info["meta"]:
                    self.agents[info["id"]]["meta"] = info["meta"]
                    changed = True
            for agent in self.agents.values():
                changed = agent["live"].poll() or changed
            if changed:
                self.revision += 1
            return changed

    def model(self):
        with self.lock:
            if self._model_rev == self.revision:
                return self._model
            main = self.main.transcript.build(self.pricing)
            agents = []
            owner = {}  # tool_use id -> (agent id or "main", row index)
            for row in main["rows"]:
                for tid in row["toolUseIds"]:
                    owner[tid] = ("main", row["index"])
            built = {}
            for aid, agent in self.agents.items():
                m = agent["live"].transcript.build(self.pricing)
                built[aid] = m
                for row in m["rows"]:
                    for tid in row["toolUseIds"]:
                        owner[tid] = (aid, row["index"])
            for aid, m in built.items():
                meta = self.agents[aid]["meta"] or {}
                parent = owner.get(meta.get("toolUseId"))
                agents.append({
                    "id": aid,
                    "type": meta.get("agentType") or "agent",
                    "description": meta.get("description") or "",
                    "toolUseId": meta.get("toolUseId"),
                    "parent": parent[0] if parent else None,
                    "parentRow": parent[1] if parent else None,
                    "firstTs": m["firstTs"],
                    **m,
                })
            agents.sort(key=lambda a: a["firstTs"] or "")
            self._model = {
                "session": {k: self.entry[k] for k in ("id", "project", "cwd", "title")},
                "generation": self.generation,
                "revision": self.revision,
                "main": main,
                "agents": agents,
                "categories": CATEGORIES,
                "summary": summarize(main, agents),
                "pricing": {"source": self.pricing.source, "checked": self.pricing.checked},
            }
            self._model_rev = self.revision
            return self._model

    def item(self, agent_id, idx):
        with self.lock:
            if agent_id in (None, "", "main"):
                tr = self.main.transcript
            else:
                agent = self.agents.get(agent_id)
                if agent is None:
                    return None
                tr = agent["live"].transcript
            return tr.item_content(idx)


def summarize(main, agents):
    def totals(rows):
        s = {"requests": 0, "input": 0, "cacheRead": 0, "cacheWrite": 0, "output": 0,
             "cost": 0.0, "uncachedCost": 0.0, "costUnknown": 0, "peak": 0}
        for r in rows:
            u = r["usage"]
            if not u:
                continue
            s["requests"] += 1
            s["input"] += r["total"]
            s["cacheRead"] += u["cacheRead"]
            s["cacheWrite"] += u["cacheWrite"]
            s["output"] += u["output"]
            s["peak"] = max(s["peak"], r["total"])
            if r["cost"] is None:
                s["costUnknown"] += 1
            else:
                s["cost"] += r["cost"]
                s["uncachedCost"] += r["uncachedCost"] or 0
        s["cacheHit"] = s["cacheRead"] / s["input"] if s["input"] else None
        return s

    out = {"main": totals(main["rows"])}
    agent_rows = [r for a in agents for r in a["rows"]]
    out["agents"] = totals(agent_rows)
    out["agentCount"] = len(agents)
    both = totals(main["rows"] + agent_rows)
    both["peak"] = out["main"]["peak"]
    out["all"] = both
    return out


class App:
    def __init__(self, claude_dir, pricing):
        self.discovery = Discovery(claude_dir)
        self.pricing = pricing
        self.sessions = {}
        self.listing = []
        self.latest = None
        self.list_revision = 0
        self.cond = threading.Condition()
        self.lock = threading.Lock()
        self.refresh_listing()

    def refresh_listing(self):
        listing = self.discovery.list_sessions()
        latest = listing[0]["id"] if listing else None
        with self.lock:
            changed = [s["id"] for s in listing[:50]] != [s["id"] for s in self.listing[:50]]
            self.listing = listing
            latest_changed = latest != self.latest
            self.latest = latest
        if latest_changed or changed:
            with self.cond:
                self.list_revision += 1
                self.cond.notify_all()

    def find(self, sid):
        with self.lock:
            for s in self.listing:
                if s["id"] == sid:
                    return s
        return None

    def session(self, sid):
        with self.lock:
            live = self.sessions.get(sid)
        if live is None:
            entry = self.find(sid)
            if entry is None:
                return None
            live = LiveSession(entry, self.pricing)
            live.poll()
            with self.lock:
                live = self.sessions.setdefault(sid, live)
        live.last_access = time.time()
        return live

    def watch_forever(self):
        last_list = 0.0
        while True:
            time.sleep(POLL_SECONDS)
            now = time.time()
            if now - last_list >= LIST_SECONDS:
                last_list = now
                try:
                    self.refresh_listing()
                except Exception as exc:  # keep the watcher alive
                    print("listing error:", exc, file=sys.stderr)
            with self.lock:
                live_sessions = list(self.sessions.items())
            changed = False
            for sid, live in live_sessions:
                if now - live.last_access > IDLE_SECONDS:
                    with self.lock:
                        self.sessions.pop(sid, None)
                    continue
                try:
                    changed = live.poll() or changed
                except Exception as exc:
                    print("poll error:", sid, exc, file=sys.stderr)
            if changed:
                with self.cond:
                    self.cond.notify_all()


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            if os.environ.get("SI_DEBUG"):
                sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

        def _json(self, obj, status=200):
            body = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _static(self, rel):
            path = os.path.normpath(os.path.join(STATIC, rel))
            if not path.startswith(STATIC + os.sep) or not os.path.isfile(path):
                return self._json({"error": "not found"}, 404)
            with open(path, "rb") as f:
                body = f.read()
            ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype.endswith("javascript"):
                ctype += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            try:
                if url.path in ("/", "/index.html"):
                    return self._static("index.html")
                if url.path.startswith("/static/"):
                    return self._static(url.path[len("/static/"):])
                if url.path == "/api/sessions":
                    with app.lock:
                        listing = [{k: v for k, v in s.items() if k != "path"} for s in app.listing]
                        latest = app.latest
                    return self._json({"sessions": listing, "latest": latest})
                if url.path == "/api/session":
                    live = app.session(q.get("id", ""))
                    if live is None:
                        return self._json({"error": "unknown session"}, 404)
                    return self._json(live.model())
                if url.path == "/api/item":
                    live = app.session(q.get("id", ""))
                    if live is None:
                        return self._json({"error": "unknown session"}, 404)
                    if q.get("gen") and q["gen"] != live.generation:
                        return self._json({"error": "the session was reloaded; open the item again"}, 409)
                    try:
                        idx = int(q.get("item", "-1"))
                    except ValueError:
                        idx = -1
                    content = live.item(q.get("agent"), idx)
                    if content is None:
                        return self._json({"error": "unknown item"}, 404)
                    return self._json(content)
                if url.path == "/api/events":
                    return self._events(q.get("id"))
                return self._json({"error": "not found"}, 404)
            except (BrokenPipeError, ConnectionResetError):
                return None

        def _events(self, sid):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.close_connection = True
            live = app.session(sid) if sid else None
            sent_rev, sent_list = None, None
            last_beat = time.time()
            try:
                while True:
                    if live is not None:
                        live.last_access = time.time()
                        if live.revision != sent_rev:
                            sent_rev = live.revision
                            self._send("session", {"id": sid, "revision": sent_rev, "generation": live.generation})
                    if app.list_revision != sent_list:
                        sent_list = app.list_revision
                        self._send("sessions", {"latest": app.latest, "revision": sent_list})
                    if time.time() - last_beat > 15:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                        last_beat = time.time()
                    with app.cond:
                        app.cond.wait(timeout=5)
            except (BrokenPipeError, ConnectionResetError, OSError):
                return None

        def _send(self, event, data):
            self.wfile.write(("event: %s\ndata: %s\n\n" % (event, json.dumps(data))).encode("utf-8"))
            self.wfile.flush()

    return Handler


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        # A closed browser tab is normal; do not print a traceback for it.
        if isinstance(sys.exc_info()[1], (ConnectionResetError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


def already_running(url):
    """True when a Session Inspector already answers at this address."""
    try:
        with urlopen(url + "/api/sessions", timeout=2) as res:
            return "sessions" in json.load(res)
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="Local dashboard for Claude Code session logs.")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (default: localhost only)")
    ap.add_argument("--claude-dir", default=default_claude_dir(), help="Claude Code data folder (default: $CLAUDE_CONFIG_DIR or ~/.claude)")
    ap.add_argument("--pricing", default=os.path.join(ROOT, "pricing.json"))
    ap.add_argument("--no-browser", action="store_true", help="do not open a browser window")
    args = ap.parse_args()

    projects = os.path.join(args.claude_dir, "projects")
    if not os.path.isdir(projects):
        print("No Claude Code projects folder at %s. Use --claude-dir." % projects, file=sys.stderr)
        sys.exit(1)
    url = "http://%s:%d" % ("127.0.0.1" if args.host in ("0.0.0.0", "") else args.host, args.port)
    app = App(args.claude_dir, Pricing(args.pricing))
    try:
        server = Server((args.host, args.port), make_handler(app))
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            raise
        if already_running(url):
            print("Session Inspector is already running at %s" % url)
            if not args.no_browser:
                webbrowser.open(url)
            sys.exit(0)
        print("Port %d is used by another program. Start on another port, for example:\n"
              "    python3 serve.py --port %d" % (args.port, args.port + 1), file=sys.stderr)
        sys.exit(1)
    threading.Thread(target=app.watch_forever, daemon=True).start()
    print("Session Inspector running at %s  (reading %s)" % (url, projects))
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
