# Lab 3: Audit your own CLAUDE.md

Time: 17 minutes. You work for 13 minutes. Repo: your own repo.

Goal: remove one line from your CLAUDE.md that Claude does not need.

Record your results on your token card. Your prework number on the token card is your baseline total.

## Base task

### Step 1: Work on a branch

1. Open a terminal in your own repo.
2. Type `git switch -c claude-md-audit`.
3. Type `claude`.
4. Type `/context`. Record the total and the Memory files line. This is your "before" value.

### Step 2: Type /doctor prompt-audit

1. Type `/doctor prompt-audit`.
2. The audit takes 1 to 3 minutes. Read the findings while it runs.
3. Read the report. Do not accept all edits.

### Step 3: Fix or remove one line

1. Pick one finding that you agree with. Accept that edit.
2. If you agree with no finding, remove one line that fails this test: "Would Claude make a mistake without this line?"

### Step 4: Type /clear, then /context

1. Type `/clear`.
2. Type `/context`.
3. Record the total and the Memory files line. This is your "after" value.
4. Compare the Memory files line before and after. Compare the total with your prework baseline.

Do not push changes to CLAUDE.md to your main branch without your team. All developers use this file.

## If something does not work

- Your repo has no CLAUDE.md: do the base task in `~/lighthouse-arcade`. Then compare your result with `solution/CLAUDE.fixed.md`.
- `/doctor prompt-audit` is not available: type `claude --version`. You need version 2.1.283 or later. Then make sure that the bundled `/claude-api` skill is on. Ask a helper.
- If it still does not work, read your CLAUDE.md line by line. Ask for each line: "Would Claude make a mistake without this line?"

## What to observe and record

- The total and the Memory files line, before and after.
- The number of findings of each type: old model wording, missing files or commands, contradictions.
- The line that you changed.

## Stretch task

1. Type `/doctor prompt-audit .claude/skills`. Record the findings for each skill.
2. Type `/skill-doctor`. Record the skills that you never use.
3. Turn off or remove what you do not use:
   - Type `/skills`. Press `t` to sort by tokens. Press Space on one unused skill to turn it off.
   - Remove a plugin that you do not use. Type `claude plugin uninstall <name>@<marketplace>`.
   - Delete the folder of an unused project skill in `.claude/skills`.
4. Add a `# Compact instructions` section to your CLAUDE.md. Write what Claude must keep when it compacts.
5. In lighthouse-arcade, fix more of the twelve flaws in CLAUDE.md:
   1. Type `cd ~/lighthouse-arcade`.
   2. Type `git switch -c claude-md-audit`. If the branch exists from the base task, type `git switch claude-md-audit`.
   3. Fix the flaws.
   4. Type `git commit -am "Fix CLAUDE.md flaws"`. race.sh uses your last commit, so you must commit first.
   5. Type `tools/race.sh <model> <effort> <seat>x`. Use the model and effort of your Lab 2 cell. It runs the Lab 2 prompt headless, in its own folder.
   6. Compare the cost and the output tokens with your Lab 2 row. Type `tools/open-game.sh <seat>x` and score the game.

## Debrief question

Which instruction in your CLAUDE.md was written for a model that you no longer use?
