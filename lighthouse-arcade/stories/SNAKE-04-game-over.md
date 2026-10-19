# SNAKE-04: Game over

Size: S

## Story

As a player, I want the game to end when the snake hits a wall or itself, so that the game has a clear rule to lose.

## Acceptance criteria

1. Given the snake moves, when the head moves into a wall, then the game stops and the text "Game over" shows.
2. Given the snake has 5 or more segments, when the head moves into its own body, then the game stops and the text "Game over" shows.
3. Given the game is over, when I press an arrow key, then the snake does not move.

## Notes

- The edges of the grid are walls. The snake does not wrap to the other side.
