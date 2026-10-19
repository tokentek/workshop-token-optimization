# Session Inspector Dashboard — Plan

Date: 2026-10-15
Source: `docs/prompts/initial-prompt.md`

## 1. Goal

A local web dashboard for a token-optimization workshop. It shows the user's Claude Code
sessions from `~/.claude/projects/`, in near real time. Each API request is one horizontal
stacked bar that shows what is in the context window (system prompt, tool definitions,
CLAUDE.md, skills, prompts, responses, thinking, tool calls, tool results, reminders).
A new bar appears under the previous one for each new request. Each segment is clickable
and shows its content. A legend explains the colours. Cache hits are shown per request.

## 2. Decisions (from the user)

| Topic | Decision |
|---|---|
| Runtime | Python 3 standard-library server. Start: `python3 serve.py`, open `http://127.0.0.1:8765`. No other dependencies, no build step, no CDN. |
| Claude Code version | Latest (2.1.300+). Mode is detected per file/request (not by version): recorded API requests when present, else a simple fallback mode. |
| Scope | Follow latest session across all projects (toggle), session picker, subagents, cost in USD. |
| Style | Neutral dashboard, light + dark, colour-blind-safe palette. |

## 3. Facts about the log format (verified on this machine)

- Session file: `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`. One JSON object per line.
- Subagents: `<sessionId>/subagents/agent-<id>.jsonl` + `agent-<id>.meta.json`
  (`agentType`, `description`, `toolUseId` → links to the parent `Agent` tool call).
- Large tool output: `<sessionId>/tool-results/*.txt`.
- `assistant` lines: **one line per content block**. Same `message.id` / `requestId` repeats.
  `usage` can change between the lines of one message (output grows) → keep the latest.
  Synthetic error replies have `model: "<synthetic>"` / `isApiErrorMessage: true` → not a request.
- Usage: `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` = exact total
  input tokens for the request. `output_tokens` separate. `cache_creation.ephemeral_1h/5m` split
  is part of `cache_creation_input_tokens` (do not add twice).
- **Version 2.1.300+ records the full request payload:**
  - `api-request-shape` → `shape.system` (system blocks) + `shape.tools` (full tool definitions), keyed by `shapeHash`.
  - `api-request-blob` → `{hash, message}` for messages that are not in the transcript (system reminders, environment, meta messages).
  - `api-request` → `{id, shapeHash, params, base, keep, tail[], cacheControl[], requestDigest, querySource}`.
    Message list = first `keep` messages of request `base` + `tail` (hashes). Hashes resolve to blobs
    or to canonicalised transcript messages (assistant blocks merged first).
    `requestDigest` lets us verify the rebuild (see §3.1).
  - Assistant lines carry `requestRef` = `api-request.id` → exact link from response (usage) to request.
    (`requestId` is the Anthropic id, a different value.)
  - A request record can appear in the file before the previous response's blocks → resolution
    must wait for later lines (pending state), not use file order.
- Subagent logs seen so far (≤2.1.299) have no request records → they may need fallback mode while the parent is verified.
- Thinking blocks can have `thinking: ""` (hidden) with only a signature, while usage reports
  thousands of thinking tokens → character count can not measure them.
- `params.context_management.edits` = `clear_thinking… keep: all` in this session: thinking is kept.
- Older logs: `attachment.prompt_snapshot` (system prompt strings, sometimes `tools`),
  attachments with `rendered` / `renderedRole`, `user` lines with `isMeta: true` that ARE sent
  (e.g. loaded skill text).

### 3.1 Rebuild algorithm (verified on 15/15 requests)

```python
def digest(v):  # sha256 over compact, key-sorted, UTF-8 JSON
    return sha256(json.dumps(v, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False).encode()).hexdigest()
```

- Candidate messages: every `user` line → `{role, content}` (no merging, `isMeta` included);
  every assistant `message.id` → `{role: "assistant", content: [blocks in order]}`;
  every `api-request-blob` → its full `message` object (keeps extra fields).
- `refs(req) = refs(base)[:keep] + tail`.
- `payload = deepcopy({**params, **shape, "messages": [resolve(h) for h in refs]})`, then set
  `cache_control` at each `cacheControl.path`, then `digest(payload) == requestDigest`.
- Unresolved hash/base → request state `pending`; retry when new lines arrive.
- States per request: `pending`, `verified`, `digest-mismatch` (still shown, with warning), `fallback`.

## 4. Architecture

```
session-inspector/
  serve.py              # entry point: HTTP + SSE, file discovery, watching
  inspector/
    discovery.py        # find Claude dir, projects, sessions, subagents
    tailer.py           # incremental JSONL reader (byte offset, partial lines, truncation)
    model.py            # build requests + segments from records (request mode + fallback mode)
    tokens.py           # token attribution (exact totals, estimated split)
    pricing.py          # cost per request (prices in pricing.json, editable)
  static/
    index.html  app.js  style.css
  pricing.json
  tests/                # unittest + small synthetic fixtures
  README.md             # how to start, what the colours mean, what is estimated
```

- All parsing and accounting in Python (testable, one source of truth). JS only renders.
- `ThreadingHTTPServer`, bind `127.0.0.1` only. Port flag `--port`, data dir flag `--claude-dir`
  (default: `$CLAUDE_CONFIG_DIR` or `~/.claude`). Works on macOS, Linux and Windows (Python 3.9+).
- Session ids are only accepted if they match a discovered file (no path traversal).

### API

| Endpoint | Returns |
|---|---|
| `GET /api/sessions` | Projects + sessions (id, cwd, title from `ai-title`, mtime, size). |
| `GET /api/session/<id>` | Full model: summary, requests, segments, subagents, cost. |
| `GET /api/segment/<session>/<request>/<segment>` | Full content of one segment (lazy, keeps the main payload small). |
| `GET /api/events?session=<id>` (SSE) | `session-updated` (new version number) and `latest-session` (newest session changed). Heartbeat every 15 s. |

- Watcher thread polls file size/mtime every 500 ms (stdlib, cross-platform). The tailer reads
  only new bytes, keeps incomplete lines/UTF-8, resets when the file shrinks or is replaced.
- Watcher also watches the session's `subagents/` folder (new files and appends).
- Every model has a `revision` number. On SSE connect the server sends the current revision at once.
  The client fetches `/api/session/<id>` when the advertised revision is newer than what it has, and
  drops responses for a session it no longer shows. This makes reconnect gap-free.
- "Live" means: as fast as Claude Code writes the log (after each block / request), not token streaming.

## 5. Data model

**Request (one row):** id, timestamp, model, querySource (main / subagent / other), usage
(input, cache read, cache write 5m/1h, output, thinking output), total input, cost, state
(`pending` / `verified` / `digest-mismatch` / `fallback`), segments[], parent tool-use id for
subagent rows. Response linked by `requestRef`; usage = latest snapshot for that message id
(never summed over blocks). Missing usage = "pending", not zero. Synthetic error replies are
shown as error markers, not as requests.

**Segment:** category, label, item count, estimated tokens, chars, `isNew` (first appears in this
request), `cached` hint, reference to content.

Segments are in payload order: tools → system → messages. Consecutive items of the same
category are merged into one segment (click shows the items in it). Items keep a stable identity
(hash) across requests, so the UI can mark new items and show growth. Widths can change when the
estimate changes; a strict "staircase" is not required.

### Categories and colours (legend)

| Category | Source |
|---|---|
| Tool definitions | `shape.tools` (detail: list of tools with size each, MCP tools grouped) |
| System prompt | `shape.system` / `prompt_snapshot.systemPrompt` |
| CLAUDE.md / instructions | `instructions` attachment / matching reminder text |
| Skills | skill listing + loaded skill content (shown as two sub-types in the detail) |
| Other reminders | environment, date, deferred tools, agent listing, MCP instructions, token reminders, etc. |
| User prompt | user text that the human typed |
| Assistant text | assistant `text` blocks |
| Thinking | assistant `thinking` / `redacted_thinking` blocks (hidden thinking: size from `thinking_tokens` of that response, marked ≈) |
| Tool calls | `tool_use` blocks (label shows tool name) |
| Tool results | `tool_result` blocks (label shows tool name; Agent results marked "subagent result") |
| Compaction summary | summary text after a compaction |
| Unattributed | difference between exact total and estimates (both modes, never hidden in another category) |

## 6. Token attribution

The log has exact totals per request, not per segment. Only the totals and the **net input
change** between two requests are exact. A matching digest proves the payload, not the token split.

1. Row total = exact (`input + cache read + cache write`).
2. Item weight = estimated tokens: text chars / 4, JSON (tool schemas, tool input) chars / 3.5;
   hidden thinking = the `thinking_tokens` reported for that response; images = fixed estimate.
3. Base split: scale all item weights so they fill the exact total. If the scale factor is far from 1
   (outside 0.7–1.4), do not scale; show the difference as "Unattributed" (if estimates are bigger
   than the total, scale down and show a warning; never negative segments).
4. Continuity mode (better growth view): if request N has the same model, shape (system + tools),
   and its message list = request N−1 list + new items, then old items keep their tokens and the
   net input change is split over the new items by weight. Else use step 3 for that row and show a note.
5. Fallback mode (no request records): items from the transcript (attachments with `rendered`
   content, user lines incl. `isMeta`, assistant blocks); system/tools from `prompt_snapshot` when
   present, else one "System prompt + tools (unknown)" item; then step 3.

UI always marks estimated numbers with "≈" and explains it in the legend.

## 7. Cache display

- Thin strip under each row on the same scale: cache read | cache write | uncached input.
- Cache-control breakpoints (from `cacheControl`) shown as small markers on the main bar.
- Row label: total input, output, cache hit %, cost.
- Summary: weighted cache hit % = `sum(cache_read) / sum(total_input)`, tokens written to cache,
  cache saving vs. no cache (includes write premium, can be negative).
- Peak context = biggest single request (main thread), not parent + subagent added.

## 8. UI

- **Header:** session picker (grouped by project, newest first), "Follow latest" toggle (all projects), live dot, light/dark toggle.
- **KPI tiles:** requests, peak context, total input, cache hit %, output tokens, estimated cost.
- **Legend:** one chip per category; click a chip to highlight that category in all rows.
- **Rows:** one per request, scale = peak context in session (option: model context window). Time + model + numbers at the left. Subagent rows in a collapsible group under the parent request whose response has the `Agent` tool call (via `toolUseId` in `.meta.json`). Unlinked subagents in an "unlinked" group. Subagent rows use their own timeline; widths are never added to the parent.
- **Detail drawer:** opens on segment click: category, tokens (≈), chars, first request it appeared in, full content as plain text (never `innerHTML`), JSON pretty-print for tool input/schemas.
- **Top consumers:** table of the biggest items in the latest request (e.g. "Bash result 12k ≈").
- Auto-scroll to the newest row while following; stops when the user scrolls up.

## 9. Cost

`pricing.json` with explicit per-model rates per 1M tokens: input, output, cache write 5m, cache
write 1h, cache read — plus source URL and date. Rates checked against current Anthropic pricing at
implementation time (e.g. Opus 5.5 cache read is 0.05× input, not 0.1×). Editable by the host.
Shown as **"estimated API-equivalent USD"** (subscription users do not pay this). Unknown model or
missing usage → "n/a", never counted as zero. Parent and subagent costs are added once each.

## 10. Tests and checks

- `python3 -m unittest` with small synthetic fixtures: split assistant lines with changing usage,
  synthetic error reply, request record before previous response, partial last line + split UTF-8,
  file truncation, `isMeta` skill text, hidden thinking, fallback-mode session, subagent link,
  unresolved hash → pending → resolved.
- Digest check: rebuild requests from this session's real log and compare `requestDigest`.
- Smoke test: run against all local sessions, no crash, report sessions with unresolved hashes.
- Manual: run `serve.py`, use Claude Code in another terminal, see new rows appear.

## 11. Out of scope

- Exact per-segment token counts (would need the token counting API = network + API key).
- Editing or deleting logs. Remote access. Other tools than Claude Code.

## 12. Steps

1. Discovery + tailer + tests.
2. Request-mode model (rebuild, digest verify, pending state) + tests on the real log.
3. Fallback mode + subagents + tests.
4. Token attribution + pricing.
5. Server + SSE (revision handshake).
6. Frontend (rows, legend, drawer, KPIs, picker, follow, subagent groups, theme).
7. README, buddy review, manual run with a live session.

## 13. Implementation notes (done 2026-10-15)

Status: implemented. All steps done. 18 unit tests pass (incl. a run over all local logs).

Changes against the plan, found while building:

- Consecutive user lines can be sent as **one** API message with no blob record (e.g. a Skill
  `tool_result` line + the `isMeta` skill text line). Merges of up to 4 lines are added at once;
  longer merges (up to 64 lines, 8 MB) are searched only when a hash is missing, and only the match is kept.
- Hidden thinking **does** count as input (checked: growth between requests jumps by the reported
  thinking tokens). Weight = reported `thinking_tokens` / hidden blocks of that response, resolved
  on every build, so the result does not depend on read order.
- Characters per token calibrated on Opus 5.x logs: 2.7 (text), 2.3 (JSON).
- Continuity also needs the same `thinking`, `context_management` and `speed` params.
- Each watched session has its own `generation` id; the browser compares (generation, revision).
- Synthetic API error replies are listed in an "API errors" badge, not counted as requests.
- Colours: 8 validated categorical slots (adjacent CVD ΔE ≥ 8.4, normal ΔE ≥ 19.3) + greys for
  reminders, assistant text, compaction; hatch for "Not attributed".
- Prices checked on the official pricing page on 2026-10-15 (Sonnet 5.5 cache read is $0.10).

Not done (accepted): structural sharing of request prefixes in server memory. A 1000-request
stress log used ~73 MB and ~2.5 s for the first load, which is fine for the workshop.
