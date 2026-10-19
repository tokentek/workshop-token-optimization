# Lighthouse Arcade: full change history

This file lists every release since the start of the project. All content is fictional.

## 0.1.0 (2023-01-26)

Owner: Team Anchor

- Changed: Lighthouse Keeper: the high score key now uses the lighthouse prefix.
- Changed: Ferry Crossing: the ball speed is now 6 px per frame instead of 5.
- Fixed: Blocks: the last row was not visible on small screens.
- Fixed: Rocks: the game over text showed twice.
- Build: added webpack 4 for all games.

## 0.2.0 (2023-02-18)

Owner: Team Harbor

- Changed: Pong: the timer now uses requestAnimationFrame.
- Changed: Ferry Crossing: the font size of the score is now 20 px.
- Fixed: Ferry Crossing: the last row was not visible on small screens.
- Build: moved from webpack to Rollup.

## 0.3.0 (2023-03-09)

Owner: Team Beacon

- Changed: Memory: the high score key now uses the lighthouse prefix.
- Fixed: Breakout: a click on the canvas selected text.
- Build: removed Rollup. Each game is one HTML file again.

## 0.4.0 (2023-03-28)

Owner: Team Keel

- Changed: Lighthouse Keeper: the font size of the score is now 20 px.
- Changed: Mines: the ball speed is now 6 px per frame instead of 5.
- Fixed: Harbor Pilot: the high score was not saved in private windows.
- Fixed: Memory: a click on the canvas selected text.
- Tooling: added the lint-all command for the old CI.
- Added: the game Pong is now on the start page.

## 0.5.0 (2023-04-17)

Owner: Team Harbor

- Changed: Breakout: the canvas now scales to the window width.
- Changed: Memory: the font size of the score is now 20 px.
- Fixed: Mines: the level counter started at 0 instead of 1.
- Tooling: removed the old CI. The lint-all command is gone.

## 0.6.0 (2023-05-17)

Owner: Team Harbor

- Changed: Memory: the timer now uses requestAnimationFrame.
- Changed: Ferry Crossing: the ball speed is now 6 px per frame instead of 5.
- Fixed: Memory: a click on the canvas selected text.
- Deploy: added scripts/deploy.sh for the old intranet server.

## 0.7.0 (2023-06-20)

Owner: Team Beacon

- Changed: Memory: the game now pauses when the browser tab is hidden.
- Changed: Mines: the high score key now uses the lighthouse prefix.
- Fixed: Rocks: the score did not reset after a new game.
- Fixed: Harbor Pilot: the game over text showed twice.
- Deploy: the intranet server was shut down. Removed scripts/deploy.sh.

## 0.8.0 (2023-07-19)

Owner: Team Keel

- Changed: Lighthouse Keeper: the font size of the score is now 20 px.
- Changed: Harbor Pilot: the start screen now shows the controls.
- Fixed: Breakout: the score did not reset after a new game.
- Docs: rewrote the README.
- Added: the game Blocks is now on the start page.

## 0.9.0 (2023-08-03)

Owner: Team Keel

- Changed: Harbor Pilot: the game now pauses when the browser tab is hidden.
- Fixed: Mines: the game over text showed twice.
- Fixed: Ferry Crossing: the game over text showed twice.
- Docs: added user stories for new games in stories/.

## 0.10.0 (2023-08-28)

Owner: Team Anchor

- Changed: Breakout: the canvas now scales to the window width.
- Changed: Harbor Pilot: the game now pauses when the browser tab is hidden.
- Fixed: Rocks: the score did not reset after a new game.
- Fixed: Rocks: the last row was not visible on small screens.
- Tests: added Jest tests for Breakout.

## 0.11.0 (2023-09-26)

Owner: Team Beacon

- Changed: Harbor Pilot: the high score key now uses the lighthouse prefix.
- Changed: Ferry Crossing: the start screen now shows the controls.
- Fixed: Harbor Pilot: the game over text showed twice.
- Fixed: Harbor Pilot: the last row was not visible on small screens.
- Tests: removed Jest. The arcade has no package manager now.

## 0.12.0 (2023-10-24)

Owner: Team Beacon

- Changed: Ferry Crossing: the colors now use the arcade palette from index.html.
- Fixed: Breakout: a click on the canvas selected text.
- Fixed: Memory: the score did not reset after a new game.
- Index: the start page now lists games in a grid.
- Added: the game Memory is now on the start page.

## 0.13.0 (2023-11-20)

Owner: Team Beacon

- Changed: Ferry Crossing: the font size of the score is now 20 px.
- Changed: Blocks: the colors now use the arcade palette from index.html.
- Fixed: Breakout: the level counter started at 0 instead of 1.
- Index: removed the link to the old leaderboard server.

## 0.14.0 (2023-12-22)

Owner: Team Keel

- Changed: Breakout: the font size of the score is now 20 px.
- Changed: Pong: the timer now uses requestAnimationFrame.
- Fixed: Breakout: the game over text showed twice.
- Fixed: Mines: the score did not reset after a new game.
- Process: reviews now use the team-code-review skill.

## 0.15.0 (2024-01-09)

Owner: Team Beacon

- Changed: Breakout: the game now pauses when the browser tab is hidden.
- Changed: Harbor Pilot: the canvas now scales to the window width.
- Fixed: Breakout: the score did not reset after a new game.
- Process: user stories now use Given, When, Then criteria.

## 0.16.0 (2024-01-23)

Owner: Team Anchor

- Changed: Harbor Pilot: the canvas now scales to the window width.
- Changed: Memory: the game now pauses when the browser tab is hidden.
- Fixed: Blocks: a click on the canvas selected text.
- Build: added webpack 4 for all games.
- Added: the game Mines is now on the start page.

## 0.17.0 (2024-02-14)

Owner: Team Anchor

- Changed: Breakout: sound is now off by default.
- Fixed: Memory: the restart key also scrolled the page.
- Build: moved from webpack to Rollup.

## 0.18.0 (2024-03-11)

Owner: Team Beacon

- Changed: Blocks: the timer now uses requestAnimationFrame.
- Fixed: Mines: the level counter started at 0 instead of 1.
- Fixed: Blocks: the high score was not saved in private windows.
- Build: removed Rollup. Each game is one HTML file again.

## 0.19.0 (2024-03-22)

Owner: Team Keel

- Changed: Memory: the ball speed is now 6 px per frame instead of 5.
- Fixed: Mines: two keys in one frame could reverse the direction.
- Tooling: added the lint-all command for the old CI.

## 0.20.0 (2024-04-12)

Owner: Team Anchor

- Changed: Breakout: the ball speed is now 6 px per frame instead of 5.
- Changed: Blocks: the canvas now scales to the window width.
- Fixed: Ferry Crossing: the last row was not visible on small screens.
- Fixed: Rocks: two keys in one frame could reverse the direction.
- Tooling: removed the old CI. The lint-all command is gone.
- Added: the game Rocks is now on the start page.

## 0.21.0 (2024-05-02)

Owner: Team Beacon

- Changed: Rocks: the high score key now uses the lighthouse prefix.
- Fixed: Harbor Pilot: a click on the canvas selected text.
- Deploy: added scripts/deploy.sh for the old intranet server.

## 0.22.0 (2024-05-26)

Owner: Team Beacon

- Changed: Lighthouse Keeper: the timer now uses requestAnimationFrame.
- Changed: Pong: the start screen now shows the controls.
- Fixed: Lighthouse Keeper: the last row was not visible on small screens.
- Fixed: Pong: the score did not reset after a new game.
- Deploy: the intranet server was shut down. Removed scripts/deploy.sh.

## 0.23.0 (2024-06-26)

Owner: Team Beacon

- Changed: Mines: the timer now uses requestAnimationFrame.
- Changed: Lighthouse Keeper: the high score key now uses the lighthouse prefix.
- Fixed: Memory: the score did not reset after a new game.
- Docs: rewrote the README.

## 0.24.0 (2024-07-20)

Owner: Team Keel

- Changed: Ferry Crossing: the font size of the score is now 20 px.
- Changed: Blocks: the start screen now shows the controls.
- Fixed: Mines: two keys in one frame could reverse the direction.
- Fixed: Mines: the last row was not visible on small screens.
- Docs: added user stories for new games in stories/.
- Added: the game Ferry Crossing is now on the start page.

## 0.25.0 (2024-08-04)

Owner: Team Anchor

- Changed: Breakout: the colors now use the arcade palette from index.html.
- Fixed: Memory: the score did not reset after a new game.
- Fixed: Breakout: the level counter started at 0 instead of 1.
- Tests: added Jest tests for Breakout.

## 0.26.0 (2024-09-02)

Owner: Team Keel

- Changed: Harbor Pilot: the game now pauses when the browser tab is hidden.
- Changed: Lighthouse Keeper: the canvas now scales to the window width.
- Fixed: Breakout: the score did not reset after a new game.
- Fixed: Memory: the restart key also scrolled the page.
- Tests: removed Jest. The arcade has no package manager now.

## 0.27.0 (2024-10-03)

Owner: Team Anchor

- Changed: Ferry Crossing: sound is now off by default.
- Fixed: Blocks: a click on the canvas selected text.
- Fixed: Blocks: a click on the canvas selected text.
- Index: the start page now lists games in a grid.

## 0.28.0 (2024-10-23)

Owner: Team Keel

- Changed: Breakout: the high score key now uses the lighthouse prefix.
- Changed: Breakout: the high score key now uses the lighthouse prefix.
- Fixed: Memory: the last row was not visible on small screens.
- Fixed: Breakout: two keys in one frame could reverse the direction.
- Index: removed the link to the old leaderboard server.
- Added: the game Lighthouse Keeper is now on the start page.

## 0.29.0 (2024-11-11)

Owner: Team Anchor

- Changed: Harbor Pilot: the font size of the score is now 20 px.
- Changed: Blocks: the ball speed is now 6 px per frame instead of 5.
- Fixed: Lighthouse Keeper: the last row was not visible on small screens.
- Fixed: Lighthouse Keeper: the restart key also scrolled the page.
- Process: reviews now use the team-code-review skill.

## 0.30.0 (2024-12-04)

Owner: Team Harbor

- Changed: Rocks: the timer now uses requestAnimationFrame.
- Changed: Breakout: sound is now off by default.
- Fixed: Breakout: the game over text showed twice.
- Process: user stories now use Given, When, Then criteria.

## 0.31.0 (2024-12-22)

Owner: Team Anchor

- Changed: Ferry Crossing: the ball speed is now 6 px per frame instead of 5.
- Changed: Ferry Crossing: the font size of the score is now 20 px.
- Fixed: Harbor Pilot: the last row was not visible on small screens.
- Build: added webpack 4 for all games.

## 0.32.0 (2025-01-13)

Owner: Team Harbor

- Changed: Mines: the game now pauses when the browser tab is hidden.
- Changed: Breakout: the colors now use the arcade palette from index.html.
- Fixed: Mines: the game over text showed twice.
- Build: moved from webpack to Rollup.
- Added: the game Harbor Pilot is now on the start page.

## 0.33.0 (2025-02-01)

Owner: Team Keel

- Changed: Breakout: the font size of the score is now 20 px.
- Changed: Mines: the timer now uses requestAnimationFrame.
- Fixed: Lighthouse Keeper: a click on the canvas selected text.
- Build: removed Rollup. Each game is one HTML file again.

## 0.34.0 (2025-02-25)

Owner: Team Beacon

- Changed: Pong: the start screen now shows the controls.
- Fixed: Memory: the level counter started at 0 instead of 1.
- Fixed: Ferry Crossing: a click on the canvas selected text.
- Tooling: added the lint-all command for the old CI.

## 0.35.0 (2025-03-22)

Owner: Team Harbor

- Changed: Lighthouse Keeper: the colors now use the arcade palette from index.html.
- Changed: Mines: the high score key now uses the lighthouse prefix.
- Fixed: Memory: the level counter started at 0 instead of 1.
- Fixed: Mines: two keys in one frame could reverse the direction.
- Tooling: removed the old CI. The lint-all command is gone.

## 0.36.0 (2025-04-23)

Owner: Team Harbor

- Changed: Mines: the game now pauses when the browser tab is hidden.
- Changed: Harbor Pilot: the game now pauses when the browser tab is hidden.
- Fixed: Lighthouse Keeper: the restart key also scrolled the page.
- Fixed: Rocks: the level counter started at 0 instead of 1.
- Deploy: added scripts/deploy.sh for the old intranet server.
- Added: the game Breakout is now on the start page.

## 0.37.0 (2025-05-05)

Owner: Team Harbor

- Changed: Lighthouse Keeper: the game now pauses when the browser tab is hidden.
- Fixed: Blocks: the high score was not saved in private windows.
- Deploy: the intranet server was shut down. Removed scripts/deploy.sh.

## 0.38.0 (2025-05-23)

Owner: Team Beacon

- Changed: Mines: the font size of the score is now 20 px.
- Fixed: Blocks: two keys in one frame could reverse the direction.
- Docs: rewrote the README.

## 0.39.0 (2025-06-20)

Owner: Team Keel

- Changed: Blocks: the font size of the score is now 20 px.
- Changed: Blocks: the high score key now uses the lighthouse prefix.
- Fixed: Blocks: the last row was not visible on small screens.
- Docs: added user stories for new games in stories/.

## 0.40.0 (2025-07-23)

Owner: Team Anchor

- Changed: Lighthouse Keeper: the ball speed is now 6 px per frame instead of 5.
- Changed: Lighthouse Keeper: the colors now use the arcade palette from index.html.
- Fixed: Mines: the restart key also scrolled the page.
- Tests: added Jest tests for Breakout.
- Added: the game Pong is now on the start page.

## 0.41.0 (2025-08-13)

Owner: Team Beacon

- Changed: Rocks: the timer now uses requestAnimationFrame.
- Changed: Mines: the high score key now uses the lighthouse prefix.
- Fixed: Harbor Pilot: the last row was not visible on small screens.
- Fixed: Lighthouse Keeper: the high score was not saved in private windows.
- Tests: removed Jest. The arcade has no package manager now.

## 0.42.0 (2025-08-26)

Owner: Team Anchor

- Changed: Blocks: the game now pauses when the browser tab is hidden.
- Changed: Blocks: the high score key now uses the lighthouse prefix.
- Fixed: Memory: a click on the canvas selected text.
- Index: the start page now lists games in a grid.

## 0.43.0 (2026-09-30)

Owner: Team Beacon

- Removed: the old Snake game. A new Snake is planned in stories/SNAKE-01 to SNAKE-08.
- Docs: the folder games/snake/ is empty until the new game is built.
