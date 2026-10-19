# Command card

Print as A5, both sides. One card for each seat.

## Measure

| Command | What it does |
|---|---|
| `/context` | Shows what fills the context window now |
| `/usage` | Shows the cache hit share, the last miss, and the usage by skill and plugin |
| `claude -p "..." --output-format json` | Shows the tokens and the estimated cost of one run |
| `/statusline <what you want>` | Claude Code writes it. Example prompt: labs/LAB1.md |

## Keep the context small

| Command | What it does |
|---|---|
| `/clear` | Starts a new empty context. Sends no request |
| `/compact Focus on ...` | Makes one request. Writes a summary of the session |
| `/rewind` | Goes back to an earlier point. The cache stays warm |
| `/btw` | Asks a side question. The question is not kept in the history |
| `/autocompact 200k` | Compacts before the quality drops |

After more than two corrections on one issue, type `/clear`. Then write a better prompt.

## Keep the cache warm

| Command | What it does |
|---|---|
| `/model` | Pick the model before your first prompt. A model switch recomputes all |
| `/effort` | Free on Opus 5.5. A cache miss on Sonnet and Haiku |
| Cache timer | Main session: 1 hour. Subagents: 5 minutes |

## Clean up

| Command | What it does |
|---|---|
| `/doctor prompt-audit` | Finds instructions for old models |
| `/doctor prompt-audit .claude/skills` | Audits your skills |
| `/skill-doctor` | Finds skills that you never use |
| `/skills` | Lists skills. Press t to sort by tokens. Press Space to turn a skill off |
| `claude plugin details <name>` | Shows the always-on tokens of a plugin |
| `claude plugin uninstall <name>@<marketplace>` | Removes a plugin |
| Delete the folder in `.claude/skills` | Removes an unused project skill |

## Three numbers

- A cache read costs 5% of the input price (Opus 5.5, Sonnet 5.5).
- Output costs 5 times the input price.
- One cold turn costs about 8 warm turns.

## Prices in USD per million tokens (input / cache read / output)

| Model | Input | Cache read | Output |
|---|---|---|---|
| Fable 5.1 | 10.00 | 0.25 | 50.00 |
| Opus 5.5 | 4.00 | 0.20 | 20.00 |
| Sonnet 5.5 | 2.00 | 0.10 | 10.00 |
| Haiku 5.5 (prompt up to 100K) | 0.10 | 0.01 | 0.50 |

## Power user

| Command | What it does |
|---|---|
| `claude -p "hello" --model haiku --effort low --max-turns 1 --output-format json \| jq .usage` | Shows the token counts of one prompt |
| Add `.prompt_cache.recache_tokens_if_cold` to `~/.claude/statusline.sh` | Shows the tokens that a cold turn writes again |
| `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL=1h claude` | Sets the cache time for subagents |
| `/subtask <task>` | Starts a fork that reads the cache of the main session |
| `/model opusplan` | Opus for the plan, Sonnet for the work. Each change of model makes the cache cold |
| `effort: low` in the frontmatter of a skill | Overrides the session effort. On Sonnet and Haiku this makes the cache cold |
| `git diff \| codex exec -o review.md "Review this diff. Findings only."` | Codex reviews in its own process. Claude reads only review.md |
| `codex exec --sandbox read-only resume --last "Check the fixes."` | Resumes the last Codex session in this folder. Codex reads its own cache |
| `git diff HEAD \| codex exec --sandbox read-only --output-schema .claude/skills/team-code-review/review.schema.json -o review.json "Review this diff. List findings only."` | Codex findings in a fixed JSON structure (lighthouse-arcade) |

Do not use `--ephemeral` on a review that you want to resume. A sandbox flag goes before `resume`: `codex exec --sandbox read-only resume --last "..."`.

List prices 12 October 2026. On the Team plan, usage is a limit, not a bill.
