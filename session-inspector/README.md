# Session Inspector

A local dashboard that shows what is inside your Claude Code sessions: system prompt, tool
definitions, CLAUDE.md, skills, prompts, responses, thinking, tool calls, tool results and cache use.
Made for the token-optimization workshop.

Each API request is one bar. The bar shows everything the model read for that request. Every new
request adds a new bar below, so you can see the context grow.

## Install Python

The dashboard needs Python 3.9 or newer. It uses no other packages.

First, check if you already have it. Open a terminal and type:

```bash
python3 --version      # macOS / Linux
py --version           # Windows
```

If you see `Python 3.9` or higher, go to [Start](#start). If not, install Python:

### macOS

Use one of these:

- **Apple developer tools** (Python 3.9, fastest): type `xcode-select --install` and follow the
  dialog. macOS can also open this dialog for you when you first type `python3`.
- **Homebrew** (newer Python): type `brew install python`.
- **Installer**: download the macOS installer from <https://www.python.org/downloads/> and run it.

### Windows

Use one of these:

- **winget**: type `winget install Python.Python.3.12` in PowerShell.
- **Installer**: download the Windows installer from <https://www.python.org/downloads/>.
  On the first screen, select **"Add python.exe to PATH"**, then click **Install Now**.

Close the terminal and open a new one. Then type `py --version` to check.

### Linux

Most distributions already have Python 3. If not:

```bash
sudo apt install python3      # Debian / Ubuntu
sudo dnf install python3      # Fedora
```

## Start

Nothing else to install.

```bash
python3 serve.py
```

The browser opens `http://127.0.0.1:8765`. Then use Claude Code as usual in another terminal: new
requests show up within about one second.

Options:

| Option | Default | Use |
|---|---|---|
| `--port 8765` | 8765 | Other port |
| `--claude-dir PATH` | `$CLAUDE_CONFIG_DIR` or `~/.claude` | Other Claude Code data folder |
| `--no-browser` | off | Do not open a browser |
| `--pricing FILE` | `pricing.json` | Other price table |

On Windows use `py serve.py`. The server only listens on `127.0.0.1`. Set `SI_DEBUG=1` to log every
HTTP request to the terminal.

### Port already in use

- If the dashboard is already running, `serve.py` tells you and opens the browser at it.
- If another program uses port 8765, start on another port: `python3 serve.py --port 8766`.
- To stop a dashboard that runs in the background: `pkill -f serve.py` (macOS / Linux).

## What you see

The page uses a dark synthwave look. Effects (glow, sky, sun, moving grid) are only in the header
and the top band; the data rows stay flat and calm.

- **Top:** session picker. "Follow latest" jumps to the newest session in any project.
  **FX** turns the visual effects on or off (colours do not change). `?fx=0` in the URL turns them
  off. Effects are off when the system asks for more contrast; animation stops with "reduce motion".
- **Tiles:** *Current context* is the big one, with a bar that shows how full the context window is
  (orange above 80%). Then peak context, requests, all input tokens read, cache hit rate, output
  tokens and estimated cost.
- **Key bar** (stays visible when you scroll): view, scale, subagents, auto-scroll and the colour legend.
  Click a colour in the legend to highlight it in all bars.
- **Bars:** one per request. Two views:
  - *By type*: one segment per content type, same order in every bar.
  - *Payload order*: content in the order it is sent. A white line on top marks content that is new
    in that request. ▲ marks a cache breakpoint.
  - Faint vertical lines mark every 50k or 100k tokens.
- **Thin strip under each bar:** cache **read** (dark, cheap), **write** (mid, extra cost once),
  **not cached** (bright, full price). Exact numbers. A "!" next to the cache % in the row label
  means less than 80% came from the cache.
- **Row label:** request number, size, ✓ when the payload was verified, the model when it changes,
  then time, cache % and cost.
- **Click a segment** to see the items in it and their full text. **Click a request label** for exact
  token numbers, cost, and what was new in that request.
- **Subagents:** collapsed groups under the request that started them. Click to open.
- **Largest items:** the biggest items in the selected request.

## What is exact and what is estimated

- Exact (from the API response in the log): total input per request, cache read, cache write,
  uncached input, output and thinking tokens.
- Exact (Claude Code 2.1.300 and newer): the content of each request. Claude Code writes the request
  payload to the log, and the dashboard rebuilds it and checks it against the request digest
  (✓ next to the request number).
- Estimated (≈): how many tokens each part uses. The log has no per-part counts. The dashboard
  splits the exact total by text size, and uses the exact growth between two requests for the
  new parts. Hidden thinking is sized by the thinking tokens the response reported.
- Older logs (no request records): the context is inferred from the transcript. The system prompt
  and tool definitions are often not in the log; that part is shown as **Not attributed**.
- Cost is an **API-equivalent estimate** from `pricing.json`. Subscription plans are not billed
  this way. Edit `pricing.json` if prices change.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The last test runs the parser over all logs in `~/.claude/projects` (skipped if there are none).

## Files

| Path | Purpose |
|---|---|
| `serve.py` | HTTP server, live updates (Server-Sent Events), file watching |
| `inspector/tailer.py` | Reads only new lines from a growing JSONL file |
| `inspector/discovery.py` | Finds projects, sessions and subagent logs |
| `inspector/session.py` | Rebuilds requests, classifies content, splits tokens |
| `inspector/pricing.py`, `pricing.json` | Cost estimate |
| `static/` | The web page (plain HTML, CSS and JavaScript) |
| `static/fonts/` | Orbitron display font (SIL Open Font License, see `OFL-Orbitron.txt`), served locally |
