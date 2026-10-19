# SNAKE-03: Score and high score

Size: S

## Story

As a player, I want to see my score and my best score, so that I can try to beat my own record.

## Acceptance criteria

1. Given a new game, when the game starts, then the score shows 0 on the screen.
2. Given the snake eats food, when the snake grows, then the score goes up by 1.
3. Given a game ends with a score higher than the high score, when "Game over" shows, then the high score changes to that score.
4. Given I close the browser tab, when I open the game again, then the high score from before still shows.

## Notes

- Keep the high score in localStorage.
- The score and the high score are visible during the game.
