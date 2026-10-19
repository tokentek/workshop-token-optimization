# Run sheet

Workshop: "How you get more done on fewer tokens". Claude Code for Stena Line developers.
Sessions: Tuesday 20 October and Wednesday 21 October 2026. 150 minutes each. Presenter: Daniel Eliasson, TokenTek.

T+0 is the start of the session. Doors open at T-15 for the setup clinic. The clinic is not part of the 150 minutes.

## 1. Minutes per block

| T+ | Min | Block | Helper focus |
|---|---|---|---|
| -15 | 15 | Setup clinic | H1 leads. H2 takes Windows. All helpers fix failed prechecks |
| 0 | 6 | Opening: the whole session is sent again; Team usage | |
| 6 | 5 | Part 1: Tokens (two votes) | |
| 11 | 7 | Part 2: What one turn sends (30 s live `/context` demo) | |
| 18 | 15 | Lab 1: Look inside your own session (1.5 min walkthrough, 11 min work, 2.5 min debrief) | H1 status line problems. H2 Windows |
| 33 | 15 | Part 3: Cost and cache (raise your hand guess; 1 min live cold cache demo) | |
| 48 | 6 | Part 4: Size and quality | |
| 54 | 9 | Part 5: Model, effort, prompting (six questions slide) | H3 opens the board |
| 63 | 2 | Buffer 1 | |
| 65 | 19 | Lab 2: Build and measure (3 min why, predict and where to read; 9 min build clock; 5 min measure, score and post clock; 2 min walkthroughs) | H4 calls the start order: Opus, Sonnet, Haiku, 20 s apart. H1 status line and permission questions. H2 Windows. H3 watches the board |
| 84 | 10 | Break (late rows go on the board) | H3 asks each seat with an empty row |
| 94 | 11 | Part 6: What loads at start, CLAUDE.md, one team model, skills | |
| 105 | 17 | Lab 3: Audit your own CLAUDE.md (2 min walkthrough, 13 min work, 2 min debrief) | All helpers. H3 exports the board at T+119 |
| 122 | 5 | Buffer 2. H3 types the medians into the reveal grid | H3 types the medians |
| 127 | 8 | Race reveal and debrief | H3 shows the board |
| 135 | 7 | Closing question | |
| 142 | 6 | Bonus, optional: buddy programming with Codex (three roles, delegation and resume, recorded demo 1 min). Only if time is left | |
| 148 | 2 | Reserve | |
| 150 | | End. The command card is a hidden appendix. Do not present it | |

Totals: theory and demos 59 min, labs 51 min, reveal and closing 15 min, break 10 min, buffer and reserve 9 min, optional bonus 6 min. Sum 150.

### Buffer rules

1. Use Buffer 1 first.
2. Start Lab 2 at T+65 at the latest. Then the build clock starts at about T+69 and every build stops by T+78. The score clock ends at about T+83:20. The break starts at T+84 at the latest.
3. If you do not need Buffer 1, start Lab 2 at T+63. If many builds still run when the build clock is full, give them the extra 2 minutes. Otherwise give a 12 minute break. The break ends at T+94.
4. If you start Lab 2 after T+66, say only the first SAY line on the `lab2-why` slide (about 30 s saved) and skip the IF IT FAILS examples on the `build` slide.
5. If you do not need Buffer 2 for the board, take open questions until T+127. Do not start new content.
6. Keep the 2 minute reserve for the end. Do not plan content in it.
7. If you are more than 2 minutes behind at the Part 4 divider (T+48), skip the "Power users:" SAY lines in Parts 4 and 5 (about 1 min). If needed, use 1 minute of Buffer 1 for Part 5.
8. If you are more than 2 minutes behind at the Part 6 divider (T+94), skip every "Power users:" SAY line in Part 6, the settings.local.json line on the team model slide and the ASK on line 2 of the CLAUDE.md slide (about 45 s). The "If time permits" line on the buddy programming slide in the bonus is skipped by default.
9. If the closing question ends after T+144, skip the bonus. End the session on the closing answers.

## 2. Helper roles

Four helpers, one for each 10 to 12 people.

| Helper | Role |
|---|---|
| H1 | Leads the setup clinic. Then helps with status line problems in Lab 1. Sends the prework reminder on Monday 19 October |
| H2 | Windows, Git Bash and WSL problems in all labs |
| H3 | Owns the board. Watches the rows fill. Flags rows with an empty score and rows with `stopped`. Asks each seat with an empty row in the break. Types the medians into the reveal grid in Buffer 2 |
| H4 | Time keeper. Gives the presenter a 2 minute signal before each block ends. Calls the start order in Lab 2: Opus, then Sonnet after 20 seconds, then Haiku after 40 seconds. Watches for rate limit errors during the build |

Each helper has a printed copy of this run sheet, `facilitator/seating.md` and `labs/LAB1.md` to `labs/LAB3.md`.

## 3. Checklist before T+0

The agenda slide notes point here.

1. Make sure that each person submitted the PRECHECK line. The prework in the README has 7 steps:
   1. Type `claude update`. Make sure that the version is 2.1.283 or later.
   2. Clone lighthouse-arcade into the home folder, so that the path is `~/lighthouse-arcade`.
   3. Install jq. On Windows, use Git Bash or WSL.
   4. Type `~/lighthouse-arcade/tools/precheck.sh`. Submit the PRECHECK line in the form.
   5. Start claude in your own repo. Type `/context`. Write the total on your token card.
   6. In lighthouse-arcade, type `claude --model haiku --effort low --permission-mode acceptEdits`. Type `Reply OK`, then `/usage`. Make sure that the `Usage by model` line names `claude-haiku-5-5`. Type `/exit`.
   7. Do not set `CLAUDE_CODE_EFFORT_LEVEL` or `ANTHROPIC_API_KEY` in your shell profile.
2. Test the venue network and the proxy with two laptops. Run `tools/precheck.sh` (risk R12). Have a hotspot ready for the presenter.
3. Put the table tents, seat cards, token cards, command cards and scoring checklists on the tables.
4. Open the board. Check the rows for the tables in the room and the two REFERENCE rows. Check the board link in `labs/LAB2.md`.
5. Write the start order on the whiteboard: 1 Opus (C, F, J), 2 Sonnet (B, E, H), 3 Haiku (A, D, G).
6. Open a second terminal. At T-5, start a Claude Code session with a 5 minute cache: type `FORCE_PROMPT_CACHING_5M=1 claude`. Send one prompt during Lab 1. This session is cold when you show it in Part 3 (risk R16).
7. Keep the dry run screenshots ready: `/context`, the cold `/usage`, and `/doctor prompt-audit`.
8. Open `facilitator/codex-demo/README.md`, `review.md` and the three usage files in a separate window.
9. In the opening, ask participants to avoid other heavy Claude work today. The seat limits are shared with Claude chat and Cowork (risk R9).

A valid PRECHECK line ends with `RESULT=PASS`. The line `RESULT=PASS_NO_NET` means that the person skipped the network test. Ask them to run the precheck again without `PRECHECK_SKIP_NET`.

## 4. Prework timeline

| Date | Action |
|---|---|
| Monday 12 October 2026 | Send the prework mail with the form link |
| Friday 16 October 2026 | Deadline. Each participant submits the PRECHECK line in the form |
| Monday 19 October 2026 | H1 sends a reminder to each person with no PASS line |
| Workshop day, T-15 | Setup clinic for the rest |

## 5. Day-before checklist (Monday 19 October 2026)

1. Run `tools/precheck.sh` on a Team seat. Expect `RESULT=PASS`.
2. Make three builds on a Team seat with the exact steps in `labs/LAB2.md`: haiku low, sonnet medium and opus high. Measure the time from Enter to the end. Expect 3 to 8 minutes. If opus high needs more than 8 minutes, keep the stop rule, and say at the reveal that some high effort builds stopped. After each build, type `rm -rf games/snake`.
3. Check the `/usage` output of these builds. It must show `Total cost`, `Total duration (API)`, `Usage by model` and `Prompt cache (main)`. Save one screenshot. If the lines differ from the `lab2-read` slide, update the slide and `labs/LAB2.md`.
4. Run all 9 cells headless for the backup board:

   ```
   tools/race.sh haiku low DRY-HL
   tools/race.sh haiku medium DRY-HM
   tools/race.sh haiku high DRY-HH
   tools/race.sh sonnet low DRY-SL
   tools/race.sh sonnet medium DRY-SM
   tools/race.sh sonnet high DRY-SH
   tools/race.sh opus low DRY-OL
   tools/race.sh opus medium DRY-OM
   tools/race.sh opus high DRY-OH
   ```

   Score each game with `tools/open-game.sh DRY-HL`, and so on. Each run must have `games/snake/index.html`. If a run has no game file, read `results/<run>.json`. Find what stopped the build (for example a line in CLAUDE.md or in the prompt). Fix it, commit, and run the cell again. Check that the `minutes` field is not 0 (it reads `duration_api_ms`, else `duration_ms`).
5. Make the two reference builds on a Premium seat, with the steps in `labs/LAB2.md`:
   - `claude --model fable --effort medium --permission-mode acceptEdits` (REF-FABLE)
   - `claude --model opus --effort xhigh --permission-mode acceptEdits` (REF-OPUS)

   Type the prompt line, read `/usage`, score the game, and type `rm -rf games/snake` between the builds. Fill the two REFERENCE rows.
6. Fill the backup board: paste the 9 DRY lines into the `seat` cells of rows A1 to J6 of a copy (one per cell), add the scores, and fill the REFERENCE rows. Mark the copy "headless dry run".
6a. Check auto memory (risk R8). After the interactive builds, type `/memory` in lighthouse-arcade. If a build wrote to MEMORY.md, empty it. Participants make one build each, so their memory does not change their cell.
7. Record the Codex demo (section 7).
8. Test `/doctor prompt-audit` on lighthouse-arcade. Write down how long it takes. Save a screenshot as a backup for Lab 3.
9. Test that `/team-code-review` runs, and that it is not the built-in `/code-review` (risk R17).
10. Read the TTL in `/usage` on a Team seat. Expect 1h (risk R4). If it shows 5m, use the 6 times figure in Part 3 and show 05:00 for both timers.
11. Run `/model` on a Team seat. Run `codex` and read the default model (risk R1). GPT-5.5 left Codex on 14 October 2026.
12. Test a team default model: add `"model": "opus"` to `.claude/settings.json` in a test repo, start `claude`, and read the model in the status line. Remove it after the test.
13. Test the value format of `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL=1h claude` (command card, power user block). If it fails, change the card.
14. Take screenshots for the fallbacks: `/context` before the first prompt, and a cold `/usage`.
15. Ask the Team admin for the seat types (Standard or Premium) and the current usage (risks R3 and R9).
16. Re-read the Claude pricing page and the Codex models page (risks R1 and R6).
17. Run `tools/precheck.sh` on a Mac, a Linux laptop and a Windows laptop with Git Bash (risks R13 and R15).
18. Print: token cards (one for each person), scoring checklists (one for each table), command cards as A5 (one for each seat), table tents and seat cards.
19. Test the deck in PowerPoint (section 12).
20. Get the written approval from Stena Line IT security for the Codex dry run, also for fictional code (risk R10).

## 6. During the build and the break

- H4 calls the start order: Opus now, Sonnet after 20 seconds, Haiku after 40 seconds. People start `claude` before the call and type the prompt line on the call.
- Each person checks the status line before the prompt line: the model and the effort of the cell. Without a status line: the welcome text and `/effort status`.
- A permission question for a command: the person chooses No and types `Continue without commands.` Never "Yes, and switch to auto mode".
- A question or a plan only: the person types `Continue. Build the game now.` one time and writes `nudged` in the note column.
- Stop rule: 8 minutes after Enter, or when the build clock is full, the person presses Esc and writes `stopped` in the finished column. A stopped game still counts.
- A rate limit error: wait 1 minute and type the line again. If it fails again, the person scores the game of the neighbor seat (same cell) and writes `no run` in the note column.
- People who finish early continue with Part B in `labs/LAB2.md`, then a stretch task.
- At the start of the break, say the return time aloud. Write it on the whiteboard.
- In the break, H3 asks each seat with an empty row to type it.
- Start Part 6 on time.

## 7. How to record the Codex demo (dry run, Monday 19 October 2026)

There is no participant lab for Codex. You show recorded output only, for 1 minute. Use lighthouse-arcade, which has only fictional code.

1. In lighthouse-arcade, type `git switch -c codex-demo`.
2. Give the demo a game to change. Type `cp examples/snake-reference.html games/snake/index.html`.
3. Type `git add games/snake/index.html` and `git commit -m "SNAKE-01 to SNAKE-06: Reference game for the demo"`.
4. Type `claude`. Implement SNAKE-07 with the start-from-user-story skill: `Use the start-from-user-story skill for SNAKE-07.`
5. Type `/usage`. Save the output as `facilitator/codex-demo/usage-before.txt`.
6. Ask Claude to run this command:

   ```
   git diff HEAD | codex exec --sandbox read-only -o /tmp/codex-review.md "Review the diff on stdin. Output ONLY findings: severity, file:line, problem, fix. If none, write 'No findings'." >/dev/null 2>/tmp/codex-progress.log; cat /tmp/codex-review.md
   ```

7. Copy `/tmp/codex-review.md` to `facilitator/codex-demo/review.md`.
8. Type `/usage`. Save the output as `facilitator/codex-demo/usage-after.txt`.
9. Ask Claude to fix the findings. Then ask Claude to run the resume command from `facilitator/codex-demo/README.md`:

   ```
   codex exec --sandbox read-only resume --last -o /tmp/codex-recheck.md "Check the fixes. List what is still open." >/dev/null 2>>/tmp/codex-progress.log; cat /tmp/codex-recheck.md
   ```

10. Copy `/tmp/codex-recheck.md` to `facilitator/codex-demo/recheck.md`.
11. Run the resume one more time with `--json`. Make sure that the thread id in the `thread.started` event is the same as the session id at the top of `/tmp/codex-progress.log`. If `--last` finds no session, `codex exec` starts a new session and shows no error. Check in the dry run that `codex exec` writes a session id line to stderr.
12. Type `/clear`. Ask Claude to review the same diff with the team-code-review skill. Type `/usage`. Save the output as `facilitator/codex-demo/usage-claude-review.txt`.
13. Copy the five files to the `main` branch. Commit them. Do not merge the `codex-demo` branch into `main`, because `games/snake/` must stay empty for Lab 2.

In the workshop, show three captures: before, after, and the same review by team-code-review. The full command and the meaning of each flag are in `facilitator/codex-demo/README.md`.

If the Codex plugin works, also run `/codex:review --wait` once (risk R11). If it names old models, show `codex exec` only.

## 8. How to set up the board

1. Create a shared sheet (Microsoft Excel online or Google Sheets) that every participant can edit.
2. Import `facilitator/board-template.csv` into the first tab. The tab has these parts:
   - Pre-numbered rows A1 to J6 with seat, model and effort.
   - Two REFERENCE rows, `REF-FABLE` and `REF-OPUS`. Fill them with the reference builds.
   - Ten challenge rows at the bottom, for race.sh lines.
3. Keep the column order: `seat, model, effort, cost_usd, minutes, output_tokens, score_0_6, playable, finished, note`. Participants type the values by hand. A race.sh line pasted into the `seat` cell fills the 6 columns from `seat` to `output_tokens`.
4. Freeze the header row. Format `cost_usd` with 2 decimals and `minutes` with 1 decimal. Test a paste of a DRY line into a challenge row.
5. Hide or delete the rows of tables that are not in the room. For 36 people, keep A1 to F6.
6. Add a second tab with a pivot table for each cell (model and effort): the median `cost_usd`, the median `score_0_6`, the median `output_tokens` and the median `minutes`. Leave out the REFERENCE and challenge rows.
7. Make a copy of the board with the dry run lines. This is the backup board.
8. Make a short link and a QR code. Put the link in `labs/LAB2.md` (replace BOARD_LINK) and print the QR code on the table tents.

## 9. Reveal

1. At T+119, H3 exports the board as CSV and reads the medians for each cell from the pivot tab: cost, score, output tokens and minutes.
2. In Buffer 2, H3 types the median cost and the median score into the 9 cells of the reveal grid on the reveal slide. Each cell is a plain text box. Format: `$0.41 · 5/6`.
3. At T+124, the presenter looks at the board and the medians and chooses the headline:
   - Variant A: "Higher effort used more output tokens but did not always make a better game". Use it when the median output tokens grow with effort and the score does not.
   - Variant B: "Higher effort made a better game at a higher cost". Use it when the score grows with effort.
4. Hide the slide with the other variant.
5. If the board has no data, use the backup board from the headless dry run. Say that the numbers are from the dry run.

## 10. Closing and cleanup

1. Ask the closing question. Each person writes the answer on the token card. Three or four people say it aloud.
2. Say: "Two controls: keep the cache warm, keep the context small. Which one does your change use?"
2a. If the closing ends at T+144 or earlier, show the bonus (buddy programming with Codex) until T+148. Otherwise skip it (buffer rule 9).
3. If participants used race.sh, tell them how to remove its folders. Show these two commands:

   ```
   rm -rf ~/lighthouse-runs
   git -C ~/lighthouse-arcade worktree prune
   ```

4. After the session, export the board as CSV. Save a screenshot of the reveal grid.
5. Two weeks later, send the follow-up mail (section 11).

## 11. Follow-up mail (send two weeks after the workshop)

Subject: Fewer tokens: your Lab 2 results and your one change

Hello,

Two weeks ago you took part in the Claude Code workshop "How you get more done on fewer tokens". Thank you for your work on the board.

The Lab 2 results are attached. The cheapest 6 of 6 game came from [CELL] at [COST] USD. The most expensive game came from [CELL] at [COST] USD, with a score of [SCORE] of 6. The challenge column was won by [SEAT] with [COST] USD.

At the end of the workshop, you wrote one change on your token card. Please reply to this mail with three short answers:

1. Did you commit the change to your repo?
2. What changed in `/context` or `/usage` after the change?
3. What stopped you, if you did not make the change?

Three reminders:

- Type `/context` at the start of a session to see what loads before your first prompt.
- Keep the cache warm. Pick the model before your first prompt. A pause longer than the cache time makes the next turn cold.
- Type `/doctor prompt-audit` when your team changes the default model.

If you used race.sh and did not remove its folders, type `rm -rf ~/lighthouse-runs` and then `git -C ~/lighthouse-arcade worktree prune`.

Team leads: we would like to talk with you about a team default model. Reply if you want a meeting.

The lab kit stays available: lighthouse-arcade on the Stena Line Git host.

Best regards,
Daniel Eliasson, TokenTek

## 12. Test in PowerPoint before the day

Install the fonts Geist and Geist Mono first (`Geist-fonts.zip`). Then do these checks on the presentation laptop:

1. Open the file. Make sure that PowerPoint shows no repair prompt.
2. Open the Animation Pane. Make sure that the clocks show 660, 540, 300, 600 and 780 s. Do not open the Timing dialog for these animations, because it can cut them to 59 s.
3. Make sure that a divider slide builds with no click.
4. Time one clock with a stopwatch.
5. On a clock slide, click one time. The ring fills. Click again. The deck goes to the next slide. Go back, then click. The clock starts again.
6. While a clock runs, test Alt-Tab (Windows) or Cmd-Tab (macOS), Presenter View and the B key.
7. Make sure that the laptop does not sleep for 13 minutes on power.
8. Make sure that the motion paths on the slope, subagent and Codex flow slides show no flash and no jump.
