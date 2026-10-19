# Headless Chrome screenshots of this dashboard show "Loading session…"

## What went wrong

`chrome --headless=new --screenshot=… URL` (and `--dump-dom`) captured the page with only
"Loading session…" in it, sometimes on the first try, sometimes on every try. The server log showed
`200` for `/api/session`, and `curl` got the full body in 0.01 s.

Chrome's net log (`--log-net-log=net.json`) showed the cause: the `/api/session` fetch and the
`/api/events` EventSource were **CANCELLED about 6 ms after the page load event**. Headless capture
mode takes the shot at load time and stops in-flight requests. The page loads its data with
`fetch` after load and keeps an SSE stream open, so the capture always races the data.
`--virtual-time-budget` does not help either: the SSE stream never ends, so virtual time never runs out.

It looks like a bug in the dashboard, but it is not.

## How to check the page instead

Drive Chrome through the DevTools protocol: start Chrome with `--remote-debugging-port`, open the
page, wait, then call `Page.captureScreenshot` and `Runtime.evaluate` (clicks, row counts, drawer
text). A stdlib-only Python client is about 80 lines (websocket handshake + framing + `call()`).
This also lets you click segments, open subagent groups and append lines to a log file to check
live updates.

## Avoid

- Do not trust one-shot `--screenshot` / `--dump-dom` for pages that load data after `load` or
  keep a stream open.
- Do not run two headless Chrome instances with the same `--user-data-dir`; the second one exits
  without a screenshot.
- Truncating a log file that a running server writes to (`: > log`) leaves NUL bytes in it; read it
  with `tr -d '\000'`.
