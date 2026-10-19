# Lighthouse Arcade

The lab kit for the Claude Code workshop "How you get more done on fewer tokens".

Lighthouse Arcade is a small arcade of browser games. Each game is one HTML file with inline CSS and JavaScript. You open it with a double click. There is no build, no package manager, no server and no CDN.

## Rules

- All code in this repo is fictional. Use it to practice.
- Do not put company code or company data in this repo.
- The `CLAUDE.md` in this repo is weak on purpose. It has 12 planted flaws. You fix them in Lab 3. Do not copy it to your own repo.
- The skill `old-commit-helper` is stale on purpose. It is a target for the audit in Lab 3.

## Prerequisites

1. Claude Code 2.1.283 or later. Type `claude update`.
2. A claude.ai login with your Team seat. Do not use an API key.
3. `git` and `jq`.
4. A bash shell. On macOS and Linux, use the terminal. On Windows, use Git Bash or WSL, not PowerShell.
5. Only for the optional `tools/race.sh`: a time cap tool. On macOS, `perl` is enough. `brew install coreutils` also works.

Do not set `CLAUDE_CODE_EFFORT_LEVEL` or `ANTHROPIC_API_KEY` in your shell profile. `CLAUDE_CODE_EFFORT_LEVEL` overrides `--effort` in Lab 2. `ANTHROPIC_API_KEY` moves the runs off your Team seat.

## Prework

Do the prework before Friday 16 October 2026.

1. Type `claude update`. Make sure that the version is 2.1.283 or later.
2. Clone this repo into your home folder, so that the path is `~/lighthouse-arcade`.
3. Install git and jq. Then type `jq --version` to check the install.
   - Mac: type `jq --version` first. Recent macOS versions include jq. If it is missing, type `brew install jq`. If `brew` is missing, install Homebrew from brew.sh first.
   - Windows: in PowerShell, type `winget install --id Git.Git -e` and `winget install jqlang.jq`. Close and open Git Bash. Type `jq --version` in Git Bash.
   - Windows with WSL: type `sudo apt install jq` in the WSL terminal.
   - If winget is missing: download `jq-windows-amd64.exe` from jqlang.org. Rename it to `jq.exe` and put it in a folder on PATH.
4. Type `~/lighthouse-arcade/tools/precheck.sh`. Submit the PRECHECK line in the form from the prework mail.
5. Start claude in your own repo. Type `/context`. Write the total on your token card. This is your Lab 3 baseline.
6. Test the Lab 2 start command. In lighthouse-arcade, type `claude --model haiku --effort low --permission-mode acceptEdits`. Type `Reply OK`. Then type `/usage`. Make sure that you see a `Total cost` line and that the `Usage by model` line names `claude-haiku-5-5`. Type `/exit`.
7. Do not set `CLAUDE_CODE_EFFORT_LEVEL` or `ANTHROPIC_API_KEY` in your shell profile.

The precheck line looks like this:

```
PRECHECK|<name>|cc=2.1.290|auth=claude.ai|api_key_env=unset|effort_env=unset|jq=ok|git=ok|timer=perl|audit_skill=ok|parent_claude_md=none|net=ok|RESULT=PASS
```

If the line ends with `RESULT=FAIL`, read the `FIX:` lines above it. If you cannot fix a problem, come to the setup clinic 15 minutes before the workshop.

## Lab 2: build the snake game

1. Type `cd ~/lighthouse-arcade`.
2. Type `claude --model <model> --effort <effort> --permission-mode acceptEdits`. Example: `claude --model sonnet --effort medium --permission-mode acceptEdits`.
3. Type `Do the task in stories/snake-race-prompt.md`.
4. Watch the status line. When Claude stops, type `/usage` and `/context`. Then type `/exit`.
5. Type `tools/open-game.sh` to open your game. Score it with `labs/scoring-checklist.md`.
6. Type your row on the board.

Board: BOARD_LINK (the facilitator adds the link before the workshop)

The full steps are in `labs/LAB2.md`.

### Optional: run more cells headless with race.sh

`tools/race.sh <model> <effort> <seat>` runs the same prompt with `claude -p`, without your input.

- It makes a new git worktree for each run in `../lighthouse-runs/<run>`, so it does not change your Lab 2 game.
- The worktree starts from your last commit. Commit your changes first if you want them in the run.
- It uses `--max-turns 40` and a wall clock cap of 8 minutes.
- It turns off auto memory for the run, so that one run does not change the next run.
- On a Mac, it keeps the laptop awake. On Windows, set Sleep to Never when plugged in.
- It prints one board line with 6 fields, separated by tabs: seat, model, effort, cost_usd, minutes, output_tokens. Paste it into the `seat` cell of a challenge row. It saves the line in `results/<seat>.tsv` and the full JSON in `results/<run>.json`.

## Folders

| Path | Content |
|---|---|
| `CLAUDE.md` | The weak CLAUDE.md with 12 planted flaws (Lab 3) |
| `index.html` | The start page of the arcade |
| `games/snake/` | Empty. In Lab 2, Claude writes `index.html` here. A `race.sh` run writes it in its own worktree |
| `stories/` | User stories SNAKE-01 to SNAKE-08 and the race prompt |
| `docs/full-history.md` | Fictional change history |
| `.claude/skills/` | Three team skills and one stale skill |
| `labs/` | Lab steps, scoring checklist, token card, command card |
| `tools/` | Scripts for the game and the precheck, and optional extras |
| `solution/` | The fixed CLAUDE.md and the answer key. Look at it after Lab 3 |
| `examples/` | A reference snake game for the presenter. Claude is not allowed to read this folder |
| `facilitator/` | Run sheet, board template, seating plan, Codex demo |

The branch `solution/claude-md` has the fixed CLAUDE.md as `CLAUDE.md`.

## Tools

| Command | What it does |
|---|---|
| `tools/race.sh <model> <effort> [seat]` | Optional. Runs one cell headless in its own worktree and prints one board line. `RACE_PROMPT=<file>` uses your own prompt |
| `tools/open-game.sh [seat]` | Opens your Lab 2 game in your browser. With a seat ID, it opens the game of a race.sh run |
| `tools/precheck.sh [name]` | Checks your setup and prints one PRECHECK line |
| `tools/install-statusline.sh` | Optional. A ready status line, if you do not want to use the `/statusline` prompt. Backs up `~/.claude/settings.json`, copies `tools/statusline.sh` to `~/.claude/statusline.sh` and adds the `statusLine` setting. You can run it again |

## Windows

- Use Git Bash or WSL. PowerShell and cmd do not work for the scripts.
- In Git Bash, install jq and make sure that `jq --version` works.
- If `tools/open-game.sh` does not open the browser, open `games/snake/index.html` from Explorer. For a race.sh run, the path is in `results/<seat>.path`.
- During an optional race.sh run, set Sleep to Never when plugged in. Do this in Settings, System, Power.
- The file `.gitattributes` keeps LF line ends in the scripts. Do not change it.

## After the workshop

If you used race.sh, you can remove its folders. Type these two commands:

```
rm -rf ~/lighthouse-runs
git -C ~/lighthouse-arcade worktree prune
```
