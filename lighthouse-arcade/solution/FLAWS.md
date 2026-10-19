# Answer key: the 12 planted flaws in CLAUDE.md

This key is for the facilitator and for the Lab 3 stretch task.
The weak file is `CLAUDE.md` (240 lines). The fixed file is `solution/CLAUDE.fixed.md` (38 lines).
The branch `solution/claude-md` has the fixed file as `CLAUDE.md`.

Use one test for each line: "Would Claude make a mistake without this line?" If the answer is no, remove the line.

| # | Flaw | Lines in CLAUDE.md | Why it costs tokens or quality | Fix |
|---|---|---|---|---|
| 1 | Emphasis everywhere | 3, 9, 10, 15, 16, 17, 36, 37, 82, 230, 231, 236 to 240 (16 lines) | Capitals, CRITICAL and MUST were fixes for older models. Current models follow them too much, so they overtrigger. | Write each rule once in calm words. Give the reason. Example: "Before a commit, run the team-code-review skill, because the team reviews each diff against its story." |
| 2 | Contradiction | 9 "Always write tests first." and 44 "Never add test files to this repo." (37 and 237 repeat them) | Claude must guess which rule wins. It can pick either one, and it spends tokens on the conflict. | Keep one rule. The fixed file says: "There is no test runner. Do not add test files or test frameworks." |
| 3 | Missing file and command | 15 `/lint-all`, 16 `scripts/deploy.sh` | Neither exists. `docs/full-history.md` says both were removed. Claude searches for them or tells you that they are missing. | Remove both lines. `/doctor prompt-audit` finds references to files and commands that do not exist. |
| 4 | Old model workaround | 12 "Use extended thinking with budget_tokens set to 16000" | Current models decide how much to think. In Claude Code, effort controls the depth, not budget_tokens. The line has no effect and costs tokens on every turn. | Remove the line. Use `/effort` for harder tasks. |
| 5 | Overtrigger wording | 14 "If in doubt, use the team-code-review skill." and 240 "whenever you can" | Claude starts the review skill when it is not needed. Each review is a forked run that costs tokens. | Say when to use it and why: "Before a commit, run the team-code-review skill, because ..." |
| 6 | Content Claude can discover | 30 to 32 "What is HTML", 46 to 78 folder listing | Claude knows what HTML is. It can list the folders with one tool call. The listing also goes out of date. | Remove both sections. |
| 7 | Pasted style guide | 108 to 227 (about 80 rules) | It loads on every turn. Most rules are generic. A linter checks style and uses no tokens. | Remove it. If the team needs style checks, add a linter config. Keep only conventions the code does not show. |
| 8 | Workflow in CLAUDE.md | 80 to 106 (23 steps) | A mandatory story and plan template for every task. It loads on every turn, and it makes Claude write a long plan and a long summary for each task, also for a one line fix. That adds output tokens, the most expensive token. | Move the story steps to the user-story-grooming skill and the build steps to the start-from-user-story skill. A skill body loads only when Claude uses it. The fixed file has one line that points to the skills. |
| 9 | Expensive import | 23 `@docs/full-history.md` | An `@import` expands at launch. About 400 lines of history load on every turn. An import does not reduce the cost. | Replace it with a plain path: "The change history is in docs/full-history.md. Read it only when a task needs it." |
| 10 | Negative phrasing (and a personal preference) | 13 "Do not use markdown. I read your answers in a plain terminal ..." and 238 | A "do not" rule does not say what to do. It is also one person's preference in a shared file. | Say what to do: "Keep the final report short: what changed, which criteria pass, open questions." Put personal preferences in `CLAUDE.local.md` or in `~/.claude/CLAUDE.md`. |
| 11 | Vague rule | 11 "Write good, clean code." | Claude cannot act on it. It adds tokens and no information. | Remove it, or replace it with a specific convention. |
| 12 | Model specific line | 5 "You are Opus 4.6. Do not create subagents." and 239 | The team uses another model now. The line is wrong for every other model, and it blocks a useful tool. | Remove it. Agree on one team model, then tune one CLAUDE.md for it. Run `/doctor prompt-audit` when the model changes. |

## Race safety

None of the flaws stops a one-file HTML build. The flaws cost tokens and quality, so a race run with this CLAUDE.md still makes a game.
The contradiction about tests can make Claude write test code inside the game file. The workflow makes Claude write a plan and a summary. Both add output tokens.

## Missing on purpose

The weak file does not say these facts. Claude cannot find them in the code, so the fixed file adds them:

- "Open games/<name>/index.html directly. There is no build step."
- "Games must work offline. Do not load a CDN."
- "Acceptance criteria are in stories/."
- The localStorage key convention `lighthouse.<game>.highscore`.
- A `# Compact instructions` section.

## Also stale on purpose: the old-commit-helper skill

`.claude/skills/old-commit-helper/SKILL.md` is the audit and uninstall target for the stretch task.
It has capitals for emphasis, a forced 10 line plan, a `budget_tokens` setting, a model name from 2024 and a script that does not exist.
Its description is loaded on every turn, also when nobody uses the skill.
Fix: remove the skill folder. The team-code-review skill and the commit convention in CLAUDE.md cover the same need.

## How to check your result

1. Type `git switch solution/claude-md` to see the fixed file as `CLAUDE.md`.
2. Type `claude`, then `/context`. Compare the memory files total with your run on `main`.
3. Type `git switch main` when you finish.
