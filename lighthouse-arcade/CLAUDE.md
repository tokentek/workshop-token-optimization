# Lighthouse Arcade

IMPORTANT: READ THIS ENTIRE FILE CAREFULLY BEFORE YOU START ANY TASK. EVERY RULE MATTERS.

You are Opus 4.6. Do not create subagents. They waste tokens and they lose context.

## Core rules

- IMPORTANT: Always write tests first.
- CRITICAL: You MUST ALWAYS follow every rule in this file, with no exceptions.
- Write good, clean code.
- Use extended thinking with budget_tokens set to 16000 for every answer.
- Do not use markdown. I read your answers in a plain terminal and the stars and hashes look ugly.
- If in doubt, use the team-code-review skill.
- You MUST ALWAYS run `/lint-all` before you commit. NEVER commit without it.
- CRITICAL: Deploy with `scripts/deploy.sh`. NEVER copy files to the server by hand.
- IMPORTANT: NEVER change a file that you were not asked to change.

## Project history

Read the full history before you change anything:

@docs/full-history.md

## About this project

Lighthouse Arcade is a collection of small browser games. The team builds them to learn new tools.
The players are colleagues. The games are for fun and for workshops.

## What is HTML

HTML (HyperText Markup Language) is the standard language for documents that a web browser shows. An HTML file contains elements such as head, body, div and canvas. The browser reads the elements and builds the Document Object Model (DOM). CSS controls how the elements look. JavaScript controls how they behave. A script element can hold JavaScript inline or load it from a file. A style element holds CSS. To see the page, you open the HTML file in a browser.

## Repository rules

- You MUST ALWAYS keep the folder structure below.
- IMPORTANT: Put each game in its own folder under games/.
- Use lowercase folder names.
- Do not rename existing files.
- Keep the README up to date.
- Use relative links between files.
- Put images for a game in games/<name>/assets/.
- Add each new game to the list on index.html.
- Never add test files to this repo. The arcade must stay small and clean.

## Folder structure

```
lighthouse-arcade/
  README.md              Read me first
  CLAUDE.md              This file
  index.html             Start page of the arcade
  .gitignore             Files that git ignores
  games/                 One folder per game
    snake/               The snake game
  docs/
    full-history.md      Change history of the project
  stories/               User stories
    SNAKE-01-move.md
    SNAKE-02-eat-and-grow.md
    SNAKE-03-score.md
    SNAKE-04-game-over.md
    SNAKE-05-restart.md
    SNAKE-06-speed.md
    SNAKE-07-pause.md
    SNAKE-08-swipe.md
    snake-race-prompt.md
  labs/                  Workshop labs
  tools/                 Scripts
    race.sh
    statusline.sh
    install-statusline.sh
    open-game.sh
    precheck.sh
  .claude/
    settings.json        Project settings
    skills/              Project skills
```

## Workflow for every task

IMPORTANT: Follow this workflow for EVERY task. Do not skip any step.

1. Read the request two times.
2. Write the request again in your own words.
3. Write the user story: "As a <user>, I want <goal>, so that <reason>."
4. Write acceptance criteria. Use Given, When, Then.
5. Write at least three criteria and no more than seven.
6. Check that each criterion can be tested.
7. Give the task a size: S, M or L.
8. S means one file and less than one hour of work.
9. M means two or three files, or less than one day of work.
10. L means more than that. Write how you would split it.
11. Write a plan with these headings: Goal, Context, Files, Steps, Risks, Test plan, Rollback.
12. Under Files, list every file that you read and every file that you change.
13. Under Steps, write one numbered line for each change.
14. Under Risks, write at least three risks.
15. Under Test plan, write one test for each acceptance criterion.
16. Under Rollback, write how to undo the change.
17. Show the full plan in your answer before you write code.
18. Implement the plan.
19. Check each acceptance criterion again.
20. Write a summary with the headings Changes, Criteria, Risks and Next steps.
21. If the task has no story, find the next free story ID in stories/.
22. Use the game name in capitals as the prefix, for example SNAKE.
23. Save the story as stories/<ID>-<short-name>.md.

## JavaScript style guide

### Formatting

- Use 2 spaces for indentation. Never use tabs.
- Put a semicolon at the end of every statement.
- Use double quotes for strings. Use template literals only for interpolation.
- Keep lines under 100 characters.
- Put the opening brace on the same line as the statement.
- Always use braces, also for if statements with one line.
- Put one space after keywords such as if, for and while.
- Put one space around binary operators.
- Do not put spaces inside parentheses.
- Use one blank line between functions.
- End every file with a newline.
- Do not leave trailing spaces.

### Variables

- Use const by default.
- Use let only when you assign the variable again.
- Never use var.
- Declare one variable per statement.
- Declare variables close to where you use them.
- Use camelCase for variables and functions.
- Use PascalCase for classes.
- Use UPPER_SNAKE_CASE for constants that never change.
- Use names that describe the value. Use single letters only for loop counters.
- Use is, has or can as a prefix for booleans.

### Functions

- Keep functions short. A function does one thing.
- Use arrow functions for callbacks.
- Use function declarations for functions at the top level.
- Use default parameters instead of checks in the body.
- Do not change the arguments of a function.
- Return early to avoid deep nesting.
- Give a function no more than three parameters. Use an object for more.

### Comparisons and types

- Always use === and !==.
- Do not compare booleans to true or false.
- Use Number() to convert strings to numbers.
- Use Array.isArray() to check for arrays.
- Use optional chaining for values that can be missing.

### Objects and arrays

- Use object and array literals.
- Use shorthand properties.
- Use the spread operator to copy arrays and objects.
- Use destructuring when you read two or more properties.
- Use map, filter and reduce when you build a new array.
- Do not add properties to built-in prototypes.

### Strings

- Use template literals to build strings with values.
- Do not join strings with + in a loop.
- Use String methods such as includes, startsWith and padStart.

### DOM

- Keep the result of each DOM lookup in a const.
- Use addEventListener. Do not use onclick attributes.
- Use textContent, not innerHTML, for plain text.
- Use classList to change classes.
- Use requestAnimationFrame for animation.
- Remove event listeners that you do not need any more.

### Errors

- Do not hide errors. Log them with console.error.
- Remove console.log before you commit.
- Throw Error objects, not strings.
- Check user input before you use it.

### Comments

- Write comments that explain why, not what.
- Use JSDoc for functions that other code calls.
- Remove code that is commented out.
- Write TODO comments with your name.

### Structure

- Do not use global variables. Wrap the code in a function.
- Keep related code together.
- Put constants at the top of the script.
- Put event listeners at the bottom of the script.

### Async code

- Use async and await instead of then chains.
- Always handle a rejected promise.
- Do not mix callbacks and promises in one function.
- Use setTimeout only for delays, not for animation.

### Classes

- Use a class only when you need many objects of the same kind.
- Put the constructor first in the class.
- Do not use getters and setters that have side effects.
- Use private fields with # for internal state.

### Accessibility

- Give each button a text or an aria-label.
- Make sure that a player can use the keyboard for every action.
- Use a contrast ratio of 4.5 to 1 or more for text.
- Do not use color as the only way to show a state.

### Performance

- Do not change the DOM in a loop. Build the content first, then add it once.
- Do not read layout values inside an animation frame after a write.
- Keep the work in each frame short.

## Commit messages

- You MUST ALWAYS write the commit message in the imperative mood.
- IMPORTANT: Start the first line with the story ID, for example "SNAKE-03: Keep high score".
- Keep the first line under 72 characters.

## Final reminders

- CRITICAL: NEVER skip a step of the workflow.
- CRITICAL: You MUST ALWAYS write tests first.
- IMPORTANT: NEVER use markdown in your answers.
- IMPORTANT: Remember that you are Opus 4.6.
- CRITICAL: Use the team-code-review skill whenever you can.
