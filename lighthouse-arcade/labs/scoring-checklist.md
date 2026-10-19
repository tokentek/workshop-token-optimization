# Scoring checklist

Time: 90 seconds. Score your own game. Each check is yes or no.

If you pressed Esc, score the file that exists.

Do the checks in this order. Give one point for each check from 2 to 7.

| # | Check | Story | Point |
|---|---|---|---|
| 1 | Look at the game. Does it start, and does the snake move? Write "playable yes" or "playable no". If no, the score is 0. Stop here. | | none |
| 2 | Press the arrow keys. Then press W, A, S and D. Does the snake turn? | SNAKE-01 | 1 |
| 3 | Steer the snake to the food. Does the snake grow by one segment? | SNAKE-02 | 1 |
| 4 | Eat more food until the score is 10. Compare the speed now with the speed at 0 food. Does the snake move faster? | SNAKE-06 | 1 |
| 5 | Look at the screen. Does the score show, and does it go up? | SNAKE-03, part 1 | 1 |
| 6 | Steer the snake into a wall. Does "Game over" show? | SNAKE-04 | 1 |
| 7 | Press Space or Enter. Does a new game start, and does the high score from the last game still show? Give one point only if both answers are yes. | SNAKE-05 and SNAKE-03, part 2 | 1 |

Total: 0 to 6.

Write the total in the `score_0_6` column of your row.
Write "yes" or "no" in the `playable` column of your row.
