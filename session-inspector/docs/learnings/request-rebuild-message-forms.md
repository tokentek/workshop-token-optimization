# Rebuilding API requests from the log: one transcript line ≠ one wire message

## What went wrong

The dashboard rebuilds each `api-request` by resolving message hashes against messages it builds
from the transcript. Twice a hash could not be found, and because every later request reuses the
same message prefix, **all later requests stayed "pending"** (in one session: 35 of 130 rows).

1. A typed prompt is logged as `{"role": "user", "content": "How do I …"}` (a string) but is sent
   to the API as `{"role": "user", "content": [{"type": "text", "text": "How do I …"}]}`.
   The first prompt of a session hid this, because Claude Code also wrote it as an
   `api-request-blob`. Later prompts have no blob.
2. Consecutive user lines can be sent as one message (for example a Skill `tool_result` line plus
   the `isMeta` line with the skill text), again often without a blob.

## How to fix

When you hash transcript messages, add these forms (see `inspector/session.py`, `_ingest_user`
and `_search_runs`):

- the message exactly as logged (`role` + `content`),
- for string content: the one-text-block list form,
- merges of consecutive user lines (content turned into lists and joined).

Then check: every request in a current log should be `verified`. One `pending` row in the middle
of a session almost always means a missing message form, not a broken log.

## Avoid

- Do not test only on the first turns of a session; the first prompt is a special case.
- Do not keep every possible merge in memory; search long runs only for a hash that is missing.
- A `pending` request blocks all later ones. Run the real-log smoke test
  (`python3 -m unittest discover -s tests`) after any parser change and look at the state counts.
