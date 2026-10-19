# Seating plan for Lab 2

One plan for the whole workshop. Nobody changes seats.

## Table tents

Tables of 6. Each table tent names the table and the model. There is no table I.

| Tent | Model |
|---|---|
| `TABLE A · HAIKU` | haiku |
| `TABLE B · SONNET` | sonnet |
| `TABLE C · OPUS` | opus |
| `TABLE D · HAIKU` | haiku |
| `TABLE E · SONNET` | sonnet |
| `TABLE F · OPUS` | opus |
| `TABLE G · HAIKU` | haiku |
| `TABLE H · SONNET` | sonnet |
| `TABLE J · OPUS` | opus |

## Seat cards

Put six seat cards on each table.

| Seat | Card | Effort |
|---|---|---|
| 1 and 2 | `LOW` | low |
| 3 and 4 | `MEDIUM` | medium |
| 5 and 6 | `HIGH` | high |

The seat ID is the table letter and the seat number. Example: `B3` is sonnet at medium effort.

| People | Tables | Runs per cell |
|---|---|---|
| 36 | A to F | 4 |
| 54 | A to J | 6 |

## Neighbor help

Seat 1 helps seat 2. Seat 3 helps seat 4. Seat 5 helps seat 6.

## Start order

Helper H4 calls the models for the start, 20 seconds apart. The slowest model starts first, so that the room finishes at about the same time. It also spreads the load on the shared limits.

| Call | Tables | Model |
|---|---|---|
| 1 | C, F, J | opus |
| 2 (after 20 seconds) | B, E, H | sonnet |
| 3 (after 40 seconds) | A, D, G | haiku |

Each person scores their own game. There is no laptop swap.

## Reference runs

The presenter makes two reference builds before the workshop (Monday 19 October), on a Premium seat, with the steps in `labs/LAB2.md`:

- Fable 5.1 at medium effort: `claude --model fable --effort medium --permission-mode acceptEdits`
- Opus 5.5 at xhigh effort: `claude --model opus --effort xhigh --permission-mode acceptEdits`

Both rows are on the board as REFERENCE rows (`REF-FABLE` and `REF-OPUS`). Fable is not in the participant build, because Standard seats pay usage credits for Fable. Between the two builds, type `rm -rf games/snake`.
