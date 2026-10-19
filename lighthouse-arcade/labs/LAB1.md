# Lab 1: Look inside your own session

Time: 15 minutes. You work for 11 minutes. The walkthrough takes about 1.5 minutes and the debrief 2.5 minutes.
Repo: your own repo.

Record your results on your token card.

- Windows: use Git Bash, not PowerShell.
- Desktop app: do steps 2 and 4 only. Open your repo in the Desktop app and type the commands there. The status line needs the CLI.

## Base task

### Step 1: Check your status line

In the presentation, you made a status line with the `/statusline` prompt, or you chose not to. Both are correct.

- You have a status line: you see the model, the cache countdown, the context bar and the cost under the input box. Continue with step 2.
- You want a status line now: type `cd ~/lighthouse-arcade` and `claude`. Type this prompt. When Claude Code is done, type `/exit`. The status line is a user setting, so it shows in every new session. Do not do this in your own repo, because step 2 needs a session with no prompt:

```
/statusline Show model with effort | prompt cache countdown (green, yellow under 20% left, red "cache cold" when expired) | 🧠  context bar (green <50%, yellow <80%, red) |💰 cost, refresh every second.
```

- You do not want a status line: continue with step 2. You read the same numbers in `/usage` and `/context`.

### Step 2: Type /context before your first prompt

1. Go to your own repo. Type `cd <path to your repo>`.
2. Type `claude`.
3. Type `/context`. Do not type a prompt before this step.
4. Record the total tokens in use.
5. Find the largest item that you control: CLAUDE.md, skills, MCP, plugins, memory. Ignore Free space and Autocompact buffer.
6. Record the name and the tokens of that item.

### Step 3: Ask one real question

1. Ask one real question about your repo. Example: `Explain in three lines what the main entry point does.`
2. If you have a status line, look at it while Claude works. Record the context percent and the cache countdown.

### Step 4: Type /usage

1. Type `/usage`.
2. Find the "Prompt cache (main)" line. Record the requests, the percent from cache and the TTL.
3. Expect a TTL of 1h. If it shows 5m, tell a helper.
4. Type `/context` again. Record the change in tokens.

## What to observe and record

- The startup tokens.
- The largest item that you control.
- The cache TTL.
- The percent from cache after one question.

## Stretch task

1. Type `/context all`. Find each CLAUDE.md file and each skill listing.
2. Open a second terminal. For each plugin, type `claude plugin details <name>`. Record the "Always-on" line.
   Note: `/plugin` shows the "Every turn" cost only for plugins from the official Anthropic marketplace.
3. Add the cache hit ratio and the last miss cause to your status line. Type `/statusline Add the cache hit ratio and the last miss cause.` Claude Code reads these fields:
   - `.prompt_cache.hit_ratio`
   - `.prompt_cache.last_miss_cause.causes | join(",")`

   The miss cause needs Claude Code 2.1.260 or later.

## Debrief question

What is the largest item in your startup context? Does Claude need it on every turn?

If your largest item is CLAUDE.md or plugins, you fix it in Lab 3.
