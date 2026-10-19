# Lighthouse Arcade

Small browser games for a Claude Code workshop. All code is fictional.

## Run

- Each game is one file: `games/<name>/index.html` with inline CSS and JavaScript.
- Open `games/<name>/index.html` directly in a browser. There is no build step, no package manager and no server.
- Games must work offline. Do not load a CDN, web fonts or other remote files, because the games run from a double click on laptops without network.
- Add each new game to the list in `index.html`.

## Stories

- Acceptance criteria are in `stories/`. Each file has an ID, for example SNAKE-03.
- To implement a story, use the start-from-user-story skill. For a rough request with no story yet, use the user-story-grooming skill.

## Checks

- There is no test runner. Do not add test files or test frameworks.
- Put game logic in small functions. In your report, tell which acceptance criteria you checked and how.

## Conventions the code does not show

- Keep high scores in localStorage under the key `lighthouse.<game>.highscore`.
- Before a commit, run the team-code-review skill, because the team reviews each diff against its story.
- Start the first line of a commit message with the story ID: `SNAKE-03: Keep high score in localStorage`.

## Reports

- Keep the final report short: what changed, which criteria pass, open questions.

## History

- The change history is in `docs/full-history.md`. Read it only when a task needs it.

## Compact instructions

When you compact, keep the story ID, the status of each acceptance criterion and the list of changed files.
