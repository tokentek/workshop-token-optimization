"""Turn the records of one Claude Code transcript into dashboard rows.

Two modes, detected per file:

* request mode: the log has ``api-request`` records (Claude Code 2.1.300+).
  Each request payload is rebuilt exactly and checked against
  ``requestDigest``.
* fallback mode: older logs. Requests are inferred from the transcript
  (one per assistant message id) and the context is rebuilt from user
  lines, rendered attachments and earlier assistant blocks.

Only the total input per request is exact. The split into items is an
estimate (see ``_split``), and the UI marks it as such.
"""
import copy
import hashlib
import json
import re
from collections import defaultdict

CATEGORIES = [
    ("tools", "Tool definitions"),
    ("system", "System prompt"),
    ("instructions", "CLAUDE.md & instructions"),
    ("skills", "Skills"),
    ("reminders", "Reminders & context"),
    ("user", "User prompts"),
    ("assistant", "Assistant text"),
    ("thinking", "Thinking"),
    ("tool_use", "Tool calls"),
    ("tool_result", "Tool results"),
    ("compaction", "Compaction summary"),
    ("unattributed", "Not attributed"),
]

CHARS_PER_TOKEN_TEXT = 2.7  # calibrated on Opus 5.x logs: exact growth vs. text size
CHARS_PER_TOKEN_JSON = 2.3
IMAGE_TOKENS = 1600
# Outside this ratio band (exact total / estimate) the estimate is not stretched.
SCALE_MIN, SCALE_MAX = 0.6, 1.6
MERGE_BYTE_LIMIT = 8_000_000

# Known headings inside injected text. A text block is cut at these points so
# that, for example, a skill listing inside a system reminder gets its own item.
MARKERS = [
    (r"Codebase and user instructions are shown below", "instructions", "Instructions header"),
    (r"Contents of [^\n]*?\.md[^\n]*:", "instructions", None),
    (r"The following skills are available", "skills", "Skill listing"),
    (r"Base directory for this skill", "skills", "Loaded skill"),
    (r"The following deferred tools are now available", "reminders", "Deferred tool list"),
    (r"The following tools just became available", "reminders", "New tools notice"),
    (r"Available agent types", "reminders", "Agent type listing"),
    (r"# MCP Server Instructions", "reminders", "MCP server instructions"),
    (r"# Environment", "reminders", "Environment"),
    (r"As you answer the user's questions, you can use the following context", "reminders", "Session context (git status, email)"),
    (r"Attribution for git commits", "reminders", "Git attribution"),
    (r"<total_tokens>", "reminders", "Token budget reminder"),
    (r"Called the \w+ tool with the following input", "tool_result", "Attached file"),
    (r"While auto mode is active", "reminders", "Auto mode notice"),
    (r"The user hasn't heard from you in a while", "reminders", "Progress nudge"),
    (r"Note: [^\n]* was modified", "reminders", "File changed notice"),
]
MARKER_RE = re.compile("|".join("(?:^(?:<system-reminder>\\n)?(%s))" % m[0] for m in MARKERS), re.M)
MARKER_RES = [re.compile(m[0]) for m in MARKERS]

ATTACHMENT_CATEGORY = {
    "instructions": "instructions",
    "nested_memory": "instructions",
    "skill_listing": "skills",
    "invoked_skills": "skills",
    "file": "tool_result",
    "compact_file_reference": "tool_result",
}


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def _content_list(content):
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return content
    return []


def _short(text, n=70):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _tool_input_summary(name, inp):
    if not isinstance(inp, dict):
        return ""
    for key in ("file_path", "notebook_path", "path"):
        if isinstance(inp.get(key), str) and inp[key]:
            return "/".join(inp[key].replace("\\", "/").rstrip("/").split("/")[-2:])
    for key in ("command", "pattern", "url", "query", "skill", "description", "prompt"):
        if inp.get(key):
            value = str(inp[key])
            if key == "command":
                value = re.sub(r'^\s*cd\s+("[^"]*"|\S+)\s*&&\s*', "", value)
            return _short(value, 60)
    return ""


def _largest_remainder(values, total):
    """Round floats to ints that add up to ``total`` exactly."""
    floors = [int(v) for v in values]
    rest = total - sum(floors)
    if rest > 0:
        order = sorted(range(len(values)), key=lambda i: values[i] - floors[i], reverse=True)
        for i in order[:rest]:
            floors[i] += 1
    return floors


def _split(weights, total):
    """Split an exact token total over items with estimated weights.

    Returns (tokens per item, unattributed tokens, note).
    """
    est = sum(weights)
    if total <= 0:
        return [0] * len(weights), 0, None
    if est <= 0:
        return [0] * len(weights), total, None
    ratio = total / est
    if ratio > SCALE_MAX:
        toks = [int(round(w)) for w in weights]
        return toks, total - sum(toks), "Part of the input is not matched to logged content."
    toks = _largest_remainder([w * ratio for w in weights], total)
    note = None
    if ratio < SCALE_MIN:
        note = "Estimates were larger than the reported total and were scaled down."
    return toks, 0, note


class Item:
    __slots__ = ("cat", "label", "chars", "weight", "ref", "first_row", "hidden_owner")

    def __init__(self, cat, label, chars, weight, ref, hidden_owner=None):
        self.cat = cat
        self.label = label
        self.chars = chars
        self.weight = weight
        self.ref = ref  # ("text", str, start, end) | ("json", obj)
        self.first_row = None
        self.hidden_owner = hidden_owner  # signature key of a hidden thinking block


class AssistantGroup:
    __slots__ = ("id", "blocks", "usage", "model", "request_ref", "ts", "synthetic", "speed",
                 "hash", "dirty", "record_count")

    def __init__(self, msg_id):
        self.id = msg_id
        self.blocks = []
        self.usage = None
        self.model = None
        self.request_ref = None
        self.ts = None
        self.synthetic = False
        self.speed = None
        self.hash = None
        self.dirty = True
        self.record_count = 0


def usage_from(raw):
    if not raw:
        return None
    cc = raw.get("cache_creation") or {}
    write = raw.get("cache_creation_input_tokens") or 0
    w1h = cc.get("ephemeral_1h_input_tokens") or 0
    w5m = cc.get("ephemeral_5m_input_tokens")
    if w5m is None:
        w5m = write - w1h
    details = raw.get("output_tokens_details") or {}
    return {
        "input": raw.get("input_tokens") or 0,
        "cacheRead": raw.get("cache_read_input_tokens") or 0,
        "cacheWrite": write,
        "cacheWrite5m": w5m,
        "cacheWrite1h": w1h,
        "output": raw.get("output_tokens") or 0,
        "thinking": details.get("thinking_tokens"),
    }


class Transcript:
    """State for one JSONL file. Feed records with ``ingest``; call ``build``."""

    def __init__(self, kind="main"):
        self.kind = kind
        self.reset()

    def reset(self):
        self.cand = {}            # message hash -> message, from transcript lines
        self.canon_cache = {}     # message hash -> canonical bytes
        self.blobs = {}           # message hash -> message, from api-request-blob
        self.groups = {}          # assistant message id -> AssistantGroup
        self.group_order = []
        self.hash_owner = {}      # assistant message hash -> message id
        self.sig_owner = {}       # thinking signature prefix -> message id
        self.shapes = {}
        self.requests = []
        self.req_by_id = {}
        self.refs_memo = {}
        self.req_cache = {}       # request id -> resolved structure
        self.shape_cache = {}
        self.msg_items_cache = {}
        self.events = []          # ordered events for fallback mode
        self.snapshot = None
        self.title = None
        self.tool_names = {}      # tool_use id -> name
        self.user_runs = []       # runs of consecutive user lines: [role, [contents], expanded]
        self.run_open = False
        self._searched = {}       # missing hash -> user line count at last search
        self.items = []
        self.item_index = {}
        self.record_count = 0
        self.first_ts = None
        self.last_ts = None
        self.cwd = None

    # ------------------------------------------------------------------ ingest
    def ingest(self, records):
        for rec in records:
            self._ingest_one(rec)

    def _ingest_one(self, rec):
        t = rec.get("type")
        self.record_count += 1
        ts = rec.get("timestamp")
        if ts:
            self.first_ts = self.first_ts or ts
            self.last_ts = ts
        if rec.get("cwd") and not self.cwd:
            self.cwd = rec["cwd"]
        if self.kind == "main" and rec.get("isSidechain"):
            return
        if t == "user":
            self._ingest_user(rec)
        elif t == "assistant":
            self._ingest_assistant(rec)
        elif t == "api-request-blob":
            self.blobs[rec["hash"]] = rec["message"]
        elif t == "api-request-shape":
            self.shapes[rec["shapeHash"]] = rec["shape"]
        elif t == "api-request":
            if rec.get("id") not in self.req_by_id:
                self.requests.append(rec)
                self.req_by_id[rec["id"]] = rec
        elif t == "attachment":
            att = rec.get("attachment") or {}
            if att.get("type") == "prompt_snapshot" and self.snapshot is None:
                self.snapshot = att
            if rec.get("rendered"):
                self.events.append(("att", rec))
        elif t == "system":
            if rec.get("subtype") == "compact_boundary":
                self.events.append(("compact", rec))
        elif t == "ai-title":
            self.title = rec.get("aiTitle") or self.title

    def _ingest_user(self, rec):
        msg = rec.get("message") or {}
        content = msg.get("content")
        role = msg.get("role", "user")
        self._add_candidate({"role": role, "content": content})
        if isinstance(content, str):
            # A typed prompt is logged as a string but sent as one text block.
            self._add_candidate({"role": role, "content": _content_list(content)})
        # Consecutive user lines can be sent as one API message.
        if not self.run_open:
            self.user_runs.append([role, [], False])
            self.run_open = True
        run = self.user_runs[-1][1]
        run.append(content)
        for k in range(2, min(len(run), 4) + 1):
            merged = []
            for part in run[-k:]:
                merged.extend(_content_list(part))
            self._add_candidate({"role": role, "content": merged})
        self.events.append(("user", rec))

    def _add_candidate(self, message):
        c = canon(message)
        h = hashlib.sha256(c.encode("utf-8")).hexdigest()
        if h not in self.cand:
            self.cand[h] = message
            self.canon_cache[h] = c.encode("utf-8")

    def _search_runs(self, wanted):
        """Look for a missing hash among longer merges of consecutive user lines.

        Only a match is kept, so memory stays flat. Each hash is searched again
        only when new user lines have arrived since the last search."""
        lines = sum(len(run[1]) for run in self.user_runs)
        if self._searched.get(wanted) == lines:
            return
        self._searched[wanted] = lines
        for role, contents, _ in self.user_runs:
            if len(contents) <= 4:
                continue
            for i in range(len(contents)):
                merged, size = [], 0
                for j in range(i, min(len(contents), i + 64)):
                    merged.extend(_content_list(contents[j]))
                    if j - i < 4:
                        continue
                    c = canon({"role": role, "content": merged}).encode("utf-8")
                    if len(c) > MERGE_BYTE_LIMIT:
                        break
                    if hashlib.sha256(c).hexdigest() == wanted:
                        message = {"role": role, "content": list(merged)}
                        self.cand[wanted] = message
                        self.canon_cache[wanted] = c
                        return

    def _ingest_assistant(self, rec):
        self.run_open = False
        msg = rec.get("message") or {}
        mid = msg.get("id") or rec.get("uuid")
        g = self.groups.get(mid)
        if g is None:
            g = AssistantGroup(mid)
            self.groups[mid] = g
            self.group_order.append(mid)
            self.events.append(("asst", mid))
        g.record_count += 1
        g.model = msg.get("model") or g.model
        g.ts = g.ts or rec.get("timestamp")
        g.request_ref = rec.get("requestRef") or g.request_ref
        if msg.get("model") == "<synthetic>" or rec.get("isApiErrorMessage"):
            g.synthetic = True
        if msg.get("usage"):
            g.usage = msg["usage"]
            g.speed = msg["usage"].get("speed") or g.speed
        blocks = msg.get("content") or []
        if isinstance(blocks, str):
            blocks = [{"type": "text", "text": blocks}]
        idx = rec.get("apiBlockIndex")
        for b in blocks:
            if idx is not None and len(blocks) == 1:
                while len(g.blocks) <= idx:
                    g.blocks.append(None)
                g.blocks[idx] = b
            else:
                g.blocks.append(b)
            if b.get("type") in ("tool_use", "server_tool_use"):
                self.tool_names[b.get("id")] = b.get("name")
            sig = b.get("signature") if b.get("type") == "thinking" else b.get("data") if b.get("type") == "redacted_thinking" else None
            if sig:
                self.sig_owner[sig[:80]] = mid
        g.dirty = True

    # ------------------------------------------------------------------ helpers
    def _refresh_groups(self):
        for g in self.groups.values():
            if not g.dirty:
                continue
            g.dirty = False
            if any(b is None for b in g.blocks):
                g.hash = None
                continue
            message = {"role": "assistant", "content": g.blocks}
            c = canon(message).encode("utf-8")
            h = hashlib.sha256(c).hexdigest()
            g.hash = h
            self.cand[h] = message
            self.canon_cache[h] = c
            self.hash_owner[h] = g.id

    def _resolve(self, h):
        if h in self.blobs:
            return self.blobs[h]
        return self.cand.get(h)

    def _canon_bytes(self, h, message):
        b = self.canon_cache.get(h)
        if b is None:
            b = canon(message).encode("utf-8")
            self.canon_cache[h] = b
        return b

    def _refs(self, rid):
        if rid in self.refs_memo:
            return self.refs_memo[rid]
        rec = self.req_by_id.get(rid)
        if rec is None:
            return None
        base = []
        if rec.get("base"):
            base = self._refs(rec["base"])
            if base is None:
                return None
        refs = base[: rec.get("keep", 0)] + list(rec.get("tail") or [])
        self.refs_memo[rid] = refs
        return refs

    def _register(self, key, factory):
        idx = self.item_index.get(key)
        if idx is None:
            idx = len(self.items)
            self.items.append(factory())
            self.item_index[key] = idx
        return idx

    # ------------------------------------------------------------ classification
    def _text_items(self, text, role, meta=False):
        """Cut a text block at known headings. Returns [(cat, label, start, end, marked)]."""
        cuts = []
        for m in MARKER_RE.finditer(text):
            start = m.start()
            for i, r in enumerate(MARKER_RES):
                if m.group(i + 1) is not None:
                    cuts.append((start, i))
                    break
        if not cuts:
            cat, label = self._default_text_class(text, role, meta)
            return [(cat, label, 0, len(text), False)]
        out = []
        if cuts[0][0] > 0:
            head = text[: cuts[0][0]]
            if len(head.strip()) > 40:
                cat, label = self._default_text_class(head, role, meta)
                out.append((cat, label, 0, cuts[0][0], False))
            else:
                cuts[0] = (0, cuts[0][1])
        for n, (start, mi) in enumerate(cuts):
            end = cuts[n + 1][0] if n + 1 < len(cuts) else len(text)
            _, cat, label = MARKERS[mi]
            if label is None:
                m = re.search(r"Contents of ([^\n]*?\.md)", text[start:end])
                label = "File: " + (m.group(1).split("/")[-1] if m else "instructions")
            out.append((cat, label, start, end, True))
        return out

    @staticmethod
    def _default_text_class(text, role, meta):
        s = text.lstrip()
        if role == "assistant":
            return "assistant", _short(s, 60) or "Assistant text"
        if role == "system":
            return "reminders", _short(s, 60) or "System message"
        if s.startswith("<command-name>"):
            m = re.search(r"<command-name>([^<]*)</command-name>", s)
            return "user", "Slash command " + (m.group(1) if m else "")
        if s.startswith("<local-command"):
            return "reminders", "Local command output"
        if s.startswith("<task-notification>"):
            return "reminders", "Background task notification"
        if s.startswith("<system-reminder>") or meta:
            return "reminders", _short(s.replace("<system-reminder>", ""), 60) or "System reminder"
        return "user", "Prompt: " + _short(s, 60)

    def _block_specs(self, role, block, meta=False):
        """Return item specs (sub, cat, label, chars, weight, ref, hidden_owner) for one content block."""
        t = block.get("type")
        if t == "text":
            text = block.get("text") or ""
            out = []
            for n, (cat, label, s, e, _) in enumerate(self._text_items(text, role, meta)):
                chars = e - s
                out.append((n, cat, label, chars, chars / CHARS_PER_TOKEN_TEXT, ("text", text, s, e), None))
            return out
        if t in ("thinking", "redacted_thinking"):
            text = block.get("thinking") or ""
            if text.strip():
                return [(0, "thinking", "Thinking: " + _short(text, 50), len(text),
                         len(text) / CHARS_PER_TOKEN_TEXT, ("text", text, 0, len(text)), None)]
            sig = (block.get("signature") or block.get("data") or "")[:80] or "?"
            return [(0, "thinking", "Thinking (hidden)", 0, 0.0, ("json", block), sig)]
        if t in ("tool_use", "server_tool_use"):
            name = block.get("name") or "tool"
            inp = block.get("input")
            c = canon(inp)
            label = name + (": " + _tool_input_summary(name, inp) if _tool_input_summary(name, inp) else "")
            return [(0, "tool_use", label, len(c), 12 + len(c) / CHARS_PER_TOKEN_JSON, ("json", inp), None)]
        if t == "tool_result" or (t or "").endswith("_tool_result"):
            name = self.tool_names.get(block.get("tool_use_id"), t if t != "tool_result" else "tool")
            content = block.get("content")
            text_len, images = 0, 0
            for part in _content_list(content):
                if part.get("type") == "text":
                    text_len += len(part.get("text") or "")
                elif part.get("type") == "image":
                    images += 1
                else:
                    text_len += len(canon(part))
            label = ("Agent result" if name in ("Agent", "Task") else "Result: " + name)
            if block.get("is_error"):
                label += " (error)"
            weight = 8 + text_len / CHARS_PER_TOKEN_TEXT + images * IMAGE_TOKENS
            return [(0, "tool_result", label, text_len, weight, ("json", content), None)]
        if t == "tool_addition":
            d = ((block.get("tool") or {}).get("definition")) or {}
            c = canon(d)
            return [(0, "tools", "Tool added: " + (d.get("name") or "?"), len(c),
                     len(c) / CHARS_PER_TOKEN_JSON, ("json", d), None)]
        if t == "image":
            return [(0, "user" if role == "user" else "tool_result", "Image", 0, IMAGE_TOKENS, ("json", {"type": "image"}), None)]
        c = canon(block)
        return [(0, "reminders", t or "block", len(c), len(c) / CHARS_PER_TOKEN_JSON, ("json", block), None)]

    def _message_specs(self, h, message):
        specs = self.msg_items_cache.get(h)
        if specs is None:
            role = message.get("role", "user")
            specs = []
            for bi, block in enumerate(_content_list(message.get("content"))):
                if not isinstance(block, dict):
                    continue
                for spec in self._block_specs(role, block):
                    specs.append((bi,) + spec)
            self.msg_items_cache[h] = specs
        return specs

    def _shape_items(self, shape_hash, shape):
        cached = self.shape_cache.get(shape_hash)
        if cached:
            return cached
        tool_idx, sys_idx = [], []
        for tool in shape.get("tools") or []:
            c = canon(tool)
            name = tool.get("name") or tool.get("type") or "tool"
            key = "tool:" + hashlib.sha256(c.encode("utf-8")).hexdigest()
            tool_idx.append(self._register(key, lambda c=c, name=name, tool=tool: Item(
                "tools", ("MCP tool: " if name.startswith("mcp__") else "Tool: ") + name, len(c),
                len(c) / CHARS_PER_TOKEN_JSON, ("json", tool))))
        for n, block in enumerate(shape.get("system") or []):
            text = block.get("text") or canon(block)
            key = "sys:%d:%s" % (n, hashlib.sha256(text.encode("utf-8")).hexdigest())
            label = "System prompt part %d: %s" % (n + 1, _short(text, 50))
            sys_idx.append(self._register(key, lambda text=text, label=label: Item(
                "system", label, len(text), len(text) / CHARS_PER_TOKEN_TEXT, ("text", text, 0, len(text)))))
        self.shape_cache[shape_hash] = (tool_idx, sys_idx)
        return tool_idx, sys_idx

    # ----------------------------------------------------------- request mode
    def _resolve_request(self, rec):
        rid = rec["id"]
        cached = self.req_cache.get(rid)
        if cached is not None:
            return cached
        refs = self._refs(rid)
        shape = self.shapes.get(rec.get("shapeHash"))
        if refs is None or shape is None:
            return None
        messages = []
        for h in refs:
            m = self._resolve(h)
            if m is None:
                self._search_runs(h)
                m = self._resolve(h)
            if m is None:
                return None
            messages.append(m)
        tool_idx, sys_idx = self._shape_items(rec["shapeHash"], shape)
        items = list(tool_idx) + list(sys_idx)
        block_end = {}  # (message pos, block index) -> position in items of the last sub-item
        occ = defaultdict(int)
        for pos, (h, m) in enumerate(zip(refs, messages)):
            n = occ[h]
            occ[h] += 1
            for bi, sub, cat, label, chars, weight, ref, owner in self._message_specs(h, m):
                key = "m:%s:%d:%d:%d" % (h, n, bi, sub)
                items.append(self._register(key, lambda: Item(cat, label, chars, weight, ref, owner)))
                block_end[(pos, bi)] = len(items) - 1
        markers = []
        for mark in rec.get("cacheControl") or []:
            path = mark.get("path") or []
            pos = None
            if len(path) >= 2 and path[0] == "tools" and isinstance(path[1], int) and path[1] < len(tool_idx):
                pos = path[1]
            elif len(path) >= 2 and path[0] == "system" and isinstance(path[1], int) and path[1] < len(sys_idx):
                pos = len(tool_idx) + path[1]
            elif len(path) >= 4 and path[0] == "messages":
                pos = block_end.get((path[1], path[3]))
            if pos is not None:
                markers.append({"after": pos, "ttl": (mark.get("value") or {}).get("ttl", "5m")})
        verified = self._verify(rec, shape, refs, messages)
        result = {"items": items, "markers": markers, "verified": verified}
        self.req_cache[rid] = result
        return result

    def _verify(self, rec, shape, refs, messages):
        expected = rec.get("requestDigest")
        if not expected:
            return None
        try:
            top = dict(rec.get("params") or {})
            top.update(shape)
            overrides = {}
            copied = set()
            for mark in rec.get("cacheControl") or []:
                path = mark["path"]
                if path[0] == "messages":
                    i = path[1]
                    if i not in overrides:
                        overrides[i] = copy.deepcopy(messages[i])
                    target = overrides[i]
                    rest = path[2:]
                else:
                    key = path[0]
                    if key not in copied:
                        top[key] = copy.deepcopy(top[key])
                        copied.add(key)
                    target = top[key]
                    rest = path[1:]
                for comp in rest:
                    target = target[comp]
                target["cache_control"] = mark["value"]
            hasher = hashlib.sha256()
            hasher.update(b"{")
            for n, key in enumerate(sorted(list(top.keys()) + ["messages"])):
                if n:
                    hasher.update(b",")
                hasher.update(canon(key).encode("utf-8") + b":")
                if key == "messages":
                    hasher.update(b"[")
                    for i, (h, m) in enumerate(zip(refs, messages)):
                        if i:
                            hasher.update(b",")
                        if i in overrides:
                            hasher.update(canon(overrides[i]).encode("utf-8"))
                        else:
                            hasher.update(self._canon_bytes(h, m))
                    hasher.update(b"]")
                else:
                    hasher.update(canon(top[key]).encode("utf-8"))
            hasher.update(b"}")
            return hasher.hexdigest() == expected
        except (KeyError, IndexError, TypeError):
            return False

    def _request_rows(self):
        by_ref = {}
        for mid in self.group_order:
            g = self.groups[mid]
            if g.request_ref and not g.synthetic:
                by_ref[g.request_ref] = g
        rows = []
        for rec in self.requests:
            res = self._resolve_request(rec)
            g = by_ref.get(rec["id"])
            params = rec.get("params") or {}
            if res is None:
                state = "pending"
            elif res["verified"] is True:
                state = "verified"
            elif res["verified"] is False:
                state = "mismatch"
            else:
                state = "unverified"
            rows.append({
                "id": rec["id"],
                "ts": rec.get("timestamp"),
                "model": params.get("model") or (g.model if g else None),
                "effort": (params.get("output_config") or {}).get("effort"),
                "source": rec.get("querySource") or "main",
                "shape": rec.get("shapeHash"),
                "cfg": canon([params.get("thinking"), params.get("context_management"), params.get("speed")]),
                "state": state,
                "items": res["items"] if res else [],
                "markers": res["markers"] if res else [],
                "group": g,
            })
        return rows

    # ---------------------------------------------------------- fallback mode
    def _fallback_rows(self):
        baseline = []
        snap = self.snapshot
        if snap:
            for n, text in enumerate(snap.get("systemPrompt") or []):
                if not isinstance(text, str) or not text.strip() or text.startswith("__SYSTEM_PROMPT"):
                    continue
                baseline.append(self._register("snap:sys:%d" % n, lambda text=text, n=n: Item(
                    "system", "System prompt part %d: %s" % (n + 1, _short(text, 50)), len(text),
                    len(text) / CHARS_PER_TOKEN_TEXT, ("text", text, 0, len(text)))))
            for tool in snap.get("tools") or []:
                c = canon(tool)
                name = tool.get("name", "tool")
                baseline.append(self._register("snap:tool:" + name, lambda c=c, name=name, tool=tool: Item(
                    "tools", "Tool: " + name, len(c), len(c) / CHARS_PER_TOKEN_JSON, ("json", tool))))
        ctx = list(baseline)
        rows = []
        started = {}
        for n, ev in enumerate(self.events):
            kind = ev[0]
            if kind == "compact":
                ctx = list(baseline)
            elif kind == "user":
                rec = ev[1]
                msg = rec.get("message") or {}
                role = msg.get("role", "user")
                if rec.get("isCompactSummary"):
                    ctx = list(baseline)
                for bi, block in enumerate(_content_list(msg.get("content"))):
                    if not isinstance(block, dict):
                        continue
                    for sub, cat, label, chars, weight, ref, owner in self._block_specs(role, block, rec.get("isMeta")):
                        if rec.get("isCompactSummary"):
                            cat, label = "compaction", "Compaction summary"
                        key = "u:%s:%d:%d" % (rec.get("uuid") or n, bi, sub)
                        ctx.append(self._register(key, lambda: Item(cat, label, chars, weight, ref, owner)))
            elif kind == "att":
                rec = ev[1]
                att = rec.get("attachment") or {}
                cat_default = ATTACHMENT_CATEGORY.get(att.get("type"), "reminders")
                for k, part in enumerate(rec.get("rendered") or []):
                    text = part.get("content") if isinstance(part, dict) else None
                    if not isinstance(text, str):
                        continue
                    for sub, (cat, label, s, e, marked) in enumerate(self._text_items(text, "system", True)):
                        if not marked:
                            cat = cat_default
                            label = (att.get("type") or "attachment").replace("_", " ").capitalize()
                        key = "a:%s:%d:%d" % (rec.get("uuid") or n, k, sub)
                        ctx.append(self._register(key, lambda: Item(
                            cat, label, e - s, (e - s) / CHARS_PER_TOKEN_TEXT, ("text", text, s, e))))
            elif kind == "asst":
                mid = ev[1]
                g = self.groups[mid]
                if g.synthetic:
                    continue
                if mid not in started:
                    started[mid] = True
                    rows.append({
                        "id": mid, "ts": g.ts, "model": g.model, "effort": None, "source": "main",
                        "shape": None, "cfg": None, "state": "estimated", "items": list(ctx), "markers": [], "group": g,
                    })
                for bi, block in enumerate(g.blocks):
                    if block is None:
                        continue
                    for sub, cat, label, chars, weight, ref, owner in self._block_specs("assistant", block):
                        key = "g:%s:%d:%d" % (mid, bi, sub)
                        ctx.append(self._register(key, lambda: Item(cat, label, chars, weight, ref, owner)))
        return rows

    # ------------------------------------------------------------------ build
    def _hidden_weights(self):
        """Hidden thinking has no text: use the thinking tokens the response reported,
        shared over the hidden thinking blocks of that response. Resolved on every
        build, so the result does not depend on the order lines were read."""
        share = {}
        for idx, item in enumerate(self.items):
            sig = item.hidden_owner
            if not sig:
                continue
            owner = self.sig_owner.get(sig)
            if owner not in share:
                g = self.groups.get(owner)
                think = ((usage_from(g.usage) if g else None) or {}).get("thinking") or 0
                hidden = sum(1 for b in (g.blocks if g else []) if b and (
                    b.get("type") == "redacted_thinking" or (b.get("type") == "thinking" and not (b.get("thinking") or "").strip())))
                share[owner] = think / hidden if hidden else 0.0
            item.weight = share[owner]

    def build(self, pricing):
        self._refresh_groups()
        mode = "request" if self.requests else "fallback"
        rows = self._request_rows() if mode == "request" else self._fallback_rows()
        self._hidden_weights()

        out_rows = []
        prev_by_source = {}
        for n, row in enumerate(rows):
            g = row.pop("group")
            usage = usage_from(g.usage) if g else None
            total = None if usage is None else usage["input"] + usage["cacheRead"] + usage["cacheWrite"]
            items = row.pop("items")
            prev = prev_by_source.get(row["source"])
            prefix = (prev is not None and len(prev["_items"]) <= len(items)
                      and items[: len(prev["_items"])] == prev["_items"])
            note = None
            base = None
            keep = 0
            if total is None:
                # Response not logged yet: reuse the previous split, estimate the rest.
                if prefix:
                    keep = len(prev["_items"])
                    base = prev["index"]
                    toks = prev["_toks"] + [int(round(self.items[i].weight)) for i in items[keep:]]
                    unattr = prev["unattributed"]
                else:
                    toks = [int(round(self.items[i].weight)) for i in items]
                    unattr = 0
                note = "Waiting for the response: numbers are estimates."
            elif (prefix and prev["model"] == row["model"] and prev["_shape"] == row["shape"]
                  and prev["_cfg"] == row["cfg"] and total - prev["total"] > 0):
                keep = len(prev["_items"])
                new_toks, new_unattr, note = _split([self.items[i].weight for i in items[keep:]], total - prev["total"])
                toks = prev["_toks"] + new_toks
                unattr = prev["unattributed"] + new_unattr
                base = prev["index"]
            else:
                toks, unattr, note = _split([self.items[i].weight for i in items], total)
                if prev is not None and row["state"] != "pending":
                    note = note or "Context changed since the previous request (new split)."
            for i in items[keep:]:
                if self.items[i].first_row is None:
                    self.items[i].first_row = n
            cats = defaultdict(int)
            if base is not None:
                cats.update(prev["cats"])
                cats.pop("unattributed", None)
            for i, tk in zip(items[keep:], toks[keep:]):
                cats[self.items[i].cat] += tk
            cats = {c: v for c, v in cats.items() if v}
            if unattr:
                cats["unattributed"] = unattr
            model = row["model"] or (g.model if g else None)
            out = {
                "index": n,
                "id": row["id"],
                "ts": row["ts"],
                "model": model,
                "modelLabel": pricing.label(model) if model else None,
                "effort": row["effort"],
                "source": row["source"],
                "state": row["state"],
                "usage": usage,
                "total": total,
                "unattributed": unattr,
                "cats": cats,
                "markers": row["markers"],
                "note": note,
                "base": base,
                "keep": keep,
                "add": [[i, tk] for i, tk in zip(items[keep:], toks[keep:])],
                "cost": pricing.cost(model, usage, g.speed if g else None),
                "uncachedCost": pricing.uncached_cost(model, usage, g.speed if g else None),
                "contextWindow": pricing.context_window(model),
                "toolUseIds": [b.get("id") for b in (g.blocks if g else []) if b and b.get("type") == "tool_use"],
                "stopReason": None,
            }
            out_rows.append(out)
            if total is not None and row["state"] != "pending":
                prev_by_source[row["source"]] = dict(out, _items=items, _toks=toks, _shape=row["shape"], _cfg=row["cfg"])
        errors = []
        for mid in self.group_order:
            g = self.groups[mid]
            if g.synthetic:
                text = " ".join((b.get("text") or "") for b in g.blocks if b and b.get("type") == "text")
                errors.append({"ts": g.ts, "text": _short(text or "API error", 300)})
        return {
            "mode": mode,
            "errors": errors,
            "title": self.title,
            "cwd": self.cwd,
            "firstTs": self.first_ts,
            "lastTs": self.last_ts,
            "items": [[it.cat, it.label, it.chars, it.first_row] for it in self.items],
            "rows": out_rows,
        }

    # --------------------------------------------------------------- content
    def item_content(self, idx, limit=400_000):
        if idx < 0 or idx >= len(self.items):
            return None
        item = self.items[idx]
        ref = item.ref
        if ref[0] == "text":
            text = ref[1][ref[2]: ref[3]]
            fmt = "text"
        else:
            obj = ref[1]
            if isinstance(obj, str):
                text, fmt = obj, "text"
            elif isinstance(obj, list) and all(isinstance(p, dict) for p in obj):
                parts = []
                for p in obj:
                    if p.get("type") == "text":
                        parts.append(p.get("text") or "")
                    elif p.get("type") == "image":
                        parts.append("[image]")
                    else:
                        parts.append(json.dumps(p, indent=2, ensure_ascii=False))
                text, fmt = "\n\n".join(parts), "text"
            else:
                text, fmt = json.dumps(obj, indent=2, ensure_ascii=False), "json"
        truncated = len(text) > limit
        return {
            "cat": item.cat,
            "label": item.label,
            "chars": item.chars,
            "firstRow": item.first_row,
            "format": fmt,
            "hidden": bool(item.hidden_owner),
            "truncated": truncated,
            "content": text[:limit],
        }
