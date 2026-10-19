# SNAKE-01: Move the snake

Size: S

## Story

As a player, I want to steer the snake with the keyboard, so that I can control where it goes.

## Acceptance criteria

1. Given a new game, when the page opens, then the snake has 3 segments on a grid of 20 by 20 cells and moves one cell at each tick.
2. Given the snake moves, when I press an arrow key, then the snake turns in that direction.
3. Given the snake moves, when I press W, A, S or D, then the snake turns up, left, down or right.
4. Given the snake moves to the right, when I press the key for left, then the snake does not turn back into itself.
5. Given I press two keys in one tick, when the next tick comes, then the snake uses only the first valid key.

## Notes

- The first tick is 150 ms.
- The game uses one canvas or a grid of div elements. Both are correct.
