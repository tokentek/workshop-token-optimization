# Lab 2: Build the snake game and measure it

Time: 19 minutes. You work for 14 minutes: 9 minutes to build, 5 minutes to measure, score and post. Repo: lighthouse-arcade.

Board: BOARD_LINK (the facilitator adds the link before the workshop)

Windows: use Git Bash, not PowerShell.

Everyone builds the same game with the same prompt. Only the model and the effort change. You watch Claude work, and you measure the cost yourself. At the end of the workshop, we compare the cells.

## Your cell

- Your table tent gives your model: haiku, sonnet or opus.
- Your seat card gives your effort: low, medium or high.
- Your seat ID is your table letter and your seat number. Example: `B3`.

| Tables | Model | Seats 1 and 2 | Seats 3 and 4 | Seats 5 and 6 |
|---|---|---|---|---|
| A, D, G | haiku | low | medium | high |
| B, E, H | sonnet | low | medium | high |
| C, F, J | opus | low | medium | high |

The two REFERENCE rows on the board are builds that the presenter made before the workshop with the same steps: Fable 5.1 at medium and Opus 5.5 at xhigh.

## Before you start: two predictions

Write them on your token card:

- the cell that makes a 6 of 6 game at the lowest cost,
- the output tokens of your own build.

## Part A: Build (9 minutes)

### Step 1: Start Claude Code with your model and effort

1. Type `cd ~/lighthouse-arcade`.
2. Type `ls games/snake`. If you see `index.html`, type `rm -rf games/snake`. Claude must start from an empty folder.
3. Type `claude --model <model> --effort <effort> --permission-mode acceptEdits`. Example for seat B3: `claude --model sonnet --effort medium --permission-mode acceptEdits`.
4. Look at the status line. Make sure that it shows your model and your effort, for example `Sonnet 5.5 (medium)`. It shows `cache n/a` until the first reply.
   No status line? The welcome text shows the model. Type `/effort status` to see the effort.
5. Optional: type `/usage`. Write the percent of your current session from the plan usage on your token card. On Team, this percent is the real cost.

What the flags do:

- `--model` and `--effort` set your cell for the whole session. Do not type `/model` or `/effort` later. A change makes another cell, and on Sonnet and Haiku it also makes the cache cold.
- `--permission-mode acceptEdits` lets Claude write the game file without a question. Without the flag, Claude Code starts in auto mode, and the runs in the room are not the same.

### Step 2: Type the prompt line

1. Wait until helper H4 calls your model. Opus starts first, then Sonnet, then Haiku. Opus needs the most time.
2. Type `Do the task in stories/snake-race-prompt.md`. Press Enter. Note the time.

Everyone types the same line. Claude reads the prompt file and the six stories. Then it writes `games/snake/index.html`.
If you prefer, paste the text of `stories/snake-race-prompt.md` instead. Write "pasted" in the note column.

### Step 3: Watch the status line

Do not type while Claude works. Look at these parts:

No status line? Watch the line next to the spinner. You read the cost in step 5.

| Part | What it tells you |
|---|---|
| Cost (💰) | The estimated cost so far. It grows one step at each request. Each tool call is one request. Each request sends the whole session again |
| Cache countdown | It goes back to about 60:00 at each request. Each request reads the cache and keeps it warm |
| Context bar (🧠) | How full the context window is. A one file game uses a small part of 1M tokens |
| The line next to the spinner, for example `(2m 14s · ↓ 4.1k tokens)` | The time of this turn and the output tokens so far. Output includes thinking. At high effort, it grows also when you see no text |

### Step 4: Stop rule

- If Claude asks to run a command, choose No. Then type `Continue without commands.` Write "asked" in the note column.
- Do not choose "Yes, and switch to auto mode".
- If Claude stops with a question or with a plan only, type `Continue. Build the game now.` Do this one time. Write "nudged" in the note column.
- 8 minutes after you pressed Enter, press Esc one time. Also press Esc when the clock on the screen is full. Write "stopped" in the finished column. A stopped game still counts. You score the file that exists.

Did Claude finish before the clock? Continue with Part B now.

## Part B: Measure, score, post (5 minutes)

### Step 5: Read /usage

1. Type `/usage`.
2. In the Session block, find these lines. Write the values on your token card.

| Line | What it means | Board column |
|---|---|---|
| `Total cost` | The estimated cost of this session at list price, for all models. It is the same number as in the status line. On Team you do not get a bill. The tokens use your usage limit | `cost_usd` |
| `Total duration (API)` | The time that the model worked. Write it in minutes with one decimal. Example: `4m 12s` is `4.2` | `minutes` |
| `Usage by model`, the line of your model: `output` | The tokens that Claude wrote, thinking included. Output costs 5 times the input price | `output_tokens` |
| The same line: `cache read` | The session that Claude Code sent again from the cache. It costs 5 percent of the input price (10 percent on Haiku 5.5) | token card |
| The same line: `cache write` | New context that Claude Code put in the cache for 1 hour. It costs 2 times the input price | token card |
| The same line: `input` | New tokens that did not come from the cache. Usually small | token card |
| `Prompt cache (main)` | The number of requests, the percent of input from the cache, and the misses. Expect 0 misses and `warm (1h TTL)` | token card |

If you see two model lines, use the output of your own model. The total cost includes both lines.

Example output tokens: `9.9k output` is `9900`.

### Step 6: Read /context

1. Type `/context`.
2. Read the total, for example `29k/1M tokens (3%)`. It is the same percent as in the status line.
3. Find the Memory files line. It is the CLAUDE.md of lighthouse-arcade. Claude Code sent it again with each request. You fix this type of file in Lab 3.
4. Type `/exit`.

### Step 7: Open and score your game

1. Type `tools/open-game.sh`. Your game opens in your browser.
2. Do the seven checks in `labs/scoring-checklist.md`. You have 90 seconds.

You score your own game. Each check is yes or no, so another person gets the same score.

### Step 8: Type your row on the board

1. Open the board. Find the row with your seat ID.
2. Type your values in these columns: `cost_usd`, `minutes`, `output_tokens`, `score_0_6`, `playable`, `finished`, `note`.

Example: seat B3, cost 0.20, minutes 4.2, output tokens 9900, score 5, playable yes, finished yes.

## The board columns

| # | Column | Example | From |
|---|---|---|---|
| 1 | seat | `B3` | pre-filled |
| 2 | model | `sonnet` | pre-filled |
| 3 | effort | `medium` | pre-filled |
| 4 | cost_usd | `0.20` | `/usage`, Total cost |
| 5 | minutes | `4.2` | `/usage`, Total duration (API) |
| 6 | output_tokens | `9900` | `/usage`, output of your model |
| 7 | score_0_6 | `5` | scoring checklist |
| 8 | playable | `yes` | scoring checklist, check 1 |
| 9 | finished | `yes` or `stopped` | step 4 |
| 10 | note | `asked`, `nudged`, `pasted`, `no run` | step 2 and step 4 |

## Stretch tasks (after you post)

1. Multiply: the Memory files tokens from step 6 times the requests from step 5. This is about how many tokens of CLAUDE.md Claude Code sent in your build. Compare it with your cache read.
2. Run one more cell headless. It runs in its own folder and does not change your game:
   1. Type `tools/race.sh <model> <effort> <seat>h`. Use a cell that is not yours. Example: `tools/race.sh haiku high B3h`.
   2. Wait for the result line. It stops after 8 minutes at the latest.
   3. Paste the line into the `seat` cell of a challenge row on the board. It fills the columns from `seat` to `output_tokens`.
   4. Type `tools/open-game.sh <seat>h`. Score the game. Type the score in the same row.
3. Write a shorter prompt:
   1. Type `cp stories/snake-race-prompt.md my-prompt.md`.
   2. Change the prompt in `my-prompt.md`. Try to get a 6 of 6 game for fewer tokens.
   3. Type `RACE_PROMPT=my-prompt.md tools/race.sh haiku medium <seat>x`.
   4. Paste the line in a challenge row. Score the game with `tools/open-game.sh <seat>x`.
   5. Open `results/<your run>.json`. Find `modelUsage`. Check if a subagent ran.
      Note: `total_cost_usd` includes subagents. `usage` shows only the main loop.

## Debrief question

Which cell gave a 6 of 6 game at the lowest cost, and was the most expensive game also the best?
