"""Find Claude Code projects, sessions and subagent logs on disk."""
import glob
import json
import os

HEAD_BYTES = 64 * 1024
TAIL_BYTES = 256 * 1024


def default_claude_dir():
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if env:
        return os.path.expanduser(env)
    return os.path.join(os.path.expanduser("~"), ".claude")


def _json_lines(data):
    for line in data.split(b"\n"):
        line = line.strip()
        if not line.startswith(b"{"):
            continue
        try:
            yield json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue


def _first_prompt(rec):
    msg = rec.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    else:
        return None
    text = text.strip()
    if not text or text.startswith("<") or rec.get("isMeta"):
        return None
    return text[:120]


class Discovery:
    def __init__(self, claude_dir):
        self.claude_dir = claude_dir
        self.projects_dir = os.path.join(claude_dir, "projects")
        self._meta_cache = {}  # path -> (size, mtime, meta)

    def session_files(self):
        return glob.glob(os.path.join(glob.escape(self.projects_dir), "*", "*.jsonl"))

    def _read_meta(self, path, st):
        cached = self._meta_cache.get(path)
        if cached and cached[0] == st.st_size and cached[1] == st.st_mtime:
            return cached[2]
        meta = {"cwd": None, "title": None, "firstPrompt": None}
        try:
            with open(path, "rb") as f:
                head = f.read(HEAD_BYTES)
                if st.st_size > HEAD_BYTES:
                    f.seek(max(HEAD_BYTES, st.st_size - TAIL_BYTES))
                    tail = f.read()
                else:
                    tail = b""
        except OSError:
            return meta
        for rec in _json_lines(head):
            if not meta["cwd"] and rec.get("cwd"):
                meta["cwd"] = rec["cwd"]
            if rec.get("type") == "user" and not meta["firstPrompt"]:
                meta["firstPrompt"] = _first_prompt(rec)
            if rec.get("type") == "ai-title" and rec.get("aiTitle"):
                meta["title"] = rec["aiTitle"]
        for rec in _json_lines(tail):
            if rec.get("type") == "ai-title" and rec.get("aiTitle"):
                meta["title"] = rec["aiTitle"]
            if not meta["cwd"] and rec.get("cwd"):
                meta["cwd"] = rec["cwd"]
        self._meta_cache[path] = (st.st_size, st.st_mtime, meta)
        return meta

    def list_sessions(self):
        sessions = []
        for path in self.session_files():
            try:
                st = os.stat(path)
            except OSError:
                continue
            if st.st_size == 0:
                continue
            meta = self._read_meta(path, st)
            project_dir = os.path.basename(os.path.dirname(path))
            cwd = meta["cwd"]
            sessions.append({
                "id": os.path.splitext(os.path.basename(path))[0],
                "path": path,
                "projectDir": project_dir,
                "cwd": cwd,
                "project": os.path.basename(cwd.rstrip("/\\")) if cwd else project_dir,
                "title": meta["title"] or meta["firstPrompt"],
                "mtime": st.st_mtime,
                "size": st.st_size,
            })
        sessions.sort(key=lambda s: s["mtime"], reverse=True)
        return sessions

    @staticmethod
    def subagent_files(session_path):
        base = os.path.splitext(session_path)[0]
        out = []
        for path in sorted(glob.glob(os.path.join(glob.escape(base), "subagents", "*.jsonl"))):
            meta_path = path[: -len(".jsonl")] + ".meta.json"
            meta = {}
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except (OSError, ValueError):
                pass
            agent_id = os.path.splitext(os.path.basename(path))[0]
            if agent_id.startswith("agent-"):
                agent_id = agent_id[len("agent-"):]
            out.append({"id": agent_id, "path": path, "meta": meta})
        return out
