# SNAKE-06: Speed up

Size: S

## Story

As a player, I want the snake to move faster as I eat, so that the game stays a challenge.

## Acceptance criteria

1. Given a new game, when the game starts, then the tick is 150 ms.
2. Given the snake eats food, when the total food eaten in this game becomes 5, 10, 15 and so on, then the tick becomes 15 ms shorter.
3. Given the tick becomes shorter, when the tick reaches 60 ms, then the tick does not become shorter.
