# Synthwave redesign — Plan

Date: 2026-10-15
Request: "Redesign the dashboard to make it more beautiful and in the style of synthwave. Use a UX designer to help you and open the browser in Chrome to view the changes."

## Decisions

- Design spec by a UX-designer agent (full spec below), reviewed by Codex (14 issues fixed in the spec).
- Palette validated again by me with the dataviz validator (JXA port): worst adjacent colour-blind ΔE 13.4 (target 8), normal-vision ΔE 22.2 (floor 15), all fills ≥ 3.5:1 on the plot surface.
- Dark only. The theme button becomes an "FX" toggle (effects on/off, `?fx=0`). FX is off for `prefers-contrast: more` / forced colours; animations off for `prefers-reduced-motion`.
- Orbitron display font is self-hosted in `static/fonts/` (OFL), so the workshop needs no network. System fallback stack if the file is missing.
- Effects only in the header and a hero band (sky, sun, grid). The request rows stay solid with flat data colours.
- UX changes: hero KPI "Current context" with a window gauge, sticky key bar (controls + legend), reversed cache ramp (not cached = bright), leaner row labels (model only when it changes), scale guide lines.

## Steps

1. Font files + licence in `static/fonts/`.
2. `index.html`: hero band + scene, key bar, FX button, group labels.
3. `style.css`: rewrite from the spec tokens and components.
4. `app.js`: FX toggle, colours, `drawRow` changes, KPI order + gauge, row labels, legend aria, layout measuring, drawer `inert`, top table.
5. Check in Chrome (DevTools screenshots at 1500 and 1100 px, FX on/off), open the page in Chrome for the user.
6. Buddy review, tests, README update.

---

# Session Inspector: synthwave redesign spec

Status: design spec, ready to implement. Files touched: `static/index.html`, `static/style.css`, `static/app.js` (small changes only), optional `static/fonts/`.
Screenshots of the current UI used for this spec: `ux-a-top.png`, `ux-a-timeline.png`, `ux-a-drawer.png`, `ux-b-agents.png` in the scratchpad folder.
Palette numbers were computed with the same method as the dataviz validator (Machado 2009 severity 1.0, OKLab ΔE ×100, WCAG contrast). Scripts: `palcheck.py`, `s5.py`, `s6.py` in the scratchpad folder.

---

## 1. Design intent

The page becomes a night drive: a dusk sky, a striped sun and a neon grid sit in a **hero band** behind the session title and KPI tiles, and the sticky header carries a thin sunset line. Below the horizon the data lives on a calm, solid indigo "plot" surface with no effects at all, so the bars are the brightest thing in the room. Neon is a frame, never a filter on the data: glows, gradient text and scanlines appear only on chrome (header, hero, KPI tiles, panel edges, drawer edge). The 12 categories get one hue each (red, blue, orange, aqua, yellow, violet, green, pink plus four tinted neutrals), tuned so every adjacent pair stays apart for colour-blind viewers and survives a washed-out projector. Hierarchy is: current context (hero KPI) first, then the bars, then everything else.

---

## 2. Theme decision: drop light, add "FX" toggle

- **Drop the light theme.** Synthwave is a dark style; a light version would need its own validated palette and would dilute the look. The palette below is tuned for one surface only.
- **Replace the theme button (◐) with an "FX" toggle** (`<button id="fx-btn" aria-pressed="true">FX</button>`). FX on (default): hero scene, glows, gradient text, scanlines, header blur, grid animation. FX off: same colours and layout, flat surfaces, no glow, no animation. Data colours do not change, so the canvas never needs a redraw on toggle.
- Reasons: (1) some projectors or older laptops struggle with blur and glow; (2) a presenter may want a "clean" screenshot; (3) it gives a manual switch for people who find effects distracting.
- Persist as `store.set("fx", bool)`; URL `?fx=0` forces off (useful for screenshots/tests). Ignore old `?theme=` and `si.theme`.
- FX is forced off automatically (in JS, via `matchMedia`) for `prefers-contrast: more` and `forced-colors: active`, so all FX rules switch off and the button shows the real state. In forced-colors mode the canvas keeps its own colours (canvas pixels are not remapped); the row background becomes the system Canvas colour, which is fine because the bars do not depend on it. `prefers-reduced-motion: reduce` keeps the static scene but removes all animation and transitions.
- Implementation: `document.documentElement.dataset.fx = on ? "on" : "off"`. All effect CSS is scoped under `:root[data-fx="on"]`. Remove `applyTheme`, the `matchMedia("(prefers-color-scheme: dark)")` listener and the `@media (prefers-color-scheme)` / `[data-theme]` blocks. Set `color-scheme: dark` on `:root`.

---

## 3. Tokens (complete `:root` block)

Replace lines 1–93 of `style.css` with this. One theme only.

```css
:root {
  color-scheme: dark;

  /* surfaces (night sky, darkest to lightest) */
  --page:        #0b0618;  /* body, pre.content background */
  --plot:        #120a26;  /* request rows panel = bar background; palette validated against this */
  --surface:     #170e30;  /* panels, KPI tiles, drawer, chips, inactive segments */
  --surface-2:   #21153f;  /* inputs, buttons, badges, list hover */
  --row-hover:   #1c1238;  /* request row hover (bars still >= 3:1 on it) */
  --row-focus:   #261a4d;  /* focused request row, selected list item */
  --topbar:      rgba(11, 6, 24, 0.82);   /* FX on; FX off uses --surface */
  --tile:        rgba(23, 14, 48, 0.88);  /* KPI tile over the hero scene */

  /* text (never data colours) */
  --ink:    #f4f0ff;  /* 16.4:1 on --surface, 17.1:1 on --plot */
  --ink-2:  #c8bfe6;  /* 10.6:1 on --surface, 9.0:1 on --row-focus */
  --muted:  #a196c8;  /* 6.8:1 on --surface, 5.8:1 on --row-focus (AA body text everywhere) */

  /* lines */
  --border:    #392a5e;  /* decorative panel borders (1.5:1, non-interactive only) */
  --border-ui: #7a64b8;  /* borders of interactive controls: 3.8:1 on --surface (WCAG 1.4.11) */
  --grid:      #2a1f4a;  /* table rules, scale guides */
  --axis:      #4a3a7a;  /* subagent rail, scrollbar thumb */

  /* chrome accents (lines, edges, glows; NOT for words, see 4.3) */
  --neon-pink:   #ff2e97;
  --neon-cyan:   #3ff0ff;
  --sun-yellow:  #ffd319;
  --sun-orange:  #ff8b3d;
  --dusk-violet: #9d2cff;
  --sunset: linear-gradient(90deg, #ff2e97 0%, #ff8b3d 50%, #ffd319 100%);
  --sunset-v: linear-gradient(180deg, #ffd319 0%, #ff8b3d 45%, #ff2e97 100%);

  /* glows (FX on only) */
  --glow-pink:   0 0 0 1px rgba(255, 46, 151, 0.45), 0 0 14px rgba(255, 46, 151, 0.35);
  --glow-cyan:   0 0 0 1px rgba(63, 240, 255, 0.45), 0 0 14px rgba(63, 240, 255, 0.30);
  --glow-text:   0 0 10px rgba(255, 46, 151, 0.55);
  --shadow-pop:  0 10px 30px rgba(0, 0, 0, 0.6);

  /* status (text allowed; always with a glyph or label) */
  --good: #5ef2a8;  /* 11.9:1 on --surface-2 */
  --warn: #ffb547;  /* 9.6:1 on --surface-2 */

  /* focus */
  --focus: #3ff0ff;
  --focus-halo: rgba(63, 240, 255, 0.28);

  /* category colours (data marks only) */
  --c-tools:        #ff4f4f;  /* neon red */
  --c-system:       #55aaff;  /* electric blue */
  --c-instructions: #ff9a3c;  /* sunset orange */
  --c-skills:       #2fe0c8;  /* aqua */
  --c-reminders:    #6e6394;  /* dusk grey-violet (neutral) */
  --c-user:         #ffe04a;  /* sun yellow */
  --c-assistant:    #d4cfea;  /* moon lavender-white (neutral) */
  --c-thinking:     #8656ff;  /* ultraviolet */
  --c-tool_use:     #39d353;  /* neon green */
  --c-tool_result:  #ff70d6;  /* hot pink */
  --c-compaction:   #a39377;  /* warm sand (neutral) */
  --c-unattributed: #3a2f5c;  /* hatch background */
  --hatch:          #8a80b0;  /* hatch stroke, 3.3:1 on --c-unattributed */

  /* cache strip: ordinal, cheap = quiet, full price = bright (see 7.3) */
  --cache-read:  #433b7a;  /* 2.0:1 on --plot, quiet */
  --cache-write: #9a8cd8;  /* 6.5:1 */
  --cache-none:  #fff4e6;  /* 17.6:1, warm white = "hot", costs full price */

  /* marks drawn on the canvas that are not categories */
  --mark:      #f4f0ff;  /* "new content" tick, cache-breakpoint triangles (17:1 on --plot) */
  --mark-edge: #120a26;  /* 1px outline around triangles = --plot */

  /* type */
  --font-ui: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-display: "Orbitron", "Bahnschrift", "DIN Alternate", "Eurostile", "Futura", "Trebuchet MS", var(--font-ui);
  --font-mono: ui-monospace, "SF Mono", "Cascadia Mono", "JetBrains Mono", Menlo, Consolas, monospace;

  --radius: 8px;
  --radius-sm: 5px;
  --topbar-h: 56px;
}
```

### 3.1 Palette validation (on `--plot` #120a26)

| slot | hex | OKLCH L / C | contrast vs plot | vs row-hover |
|---|---|---|---|---|
| tools | #ff4f4f | 0.68 / 0.21 | 5.9 | 5.4 |
| system | #55aaff | 0.72 / 0.15 | 7.8 | 7.2 |
| instructions | #ff9a3c | 0.78 / 0.16 | 9.1 | 8.3 |
| skills | #2fe0c8 | 0.82 / 0.14 | 11.5 | 10.6 |
| reminders | #6e6394 | 0.53 / 0.08 | 3.5 | 3.25 (lowest) |
| user | #ffe04a | 0.91 / 0.16 | 14.6 | 13.4 |
| assistant | #d4cfea | 0.87 / 0.04 | 12.7 | 11.7 |
| thinking | #8656ff | 0.60 / 0.24 | 4.4 | 4.0 |
| tool_use | #39d353 | 0.76 / 0.21 | 9.7 | 8.9 |
| tool_result | #ff70d6 | 0.75 / 0.21 | 7.8 | 7.1 |
| compaction | #a39377 | 0.67 / 0.04 | 6.4 | 5.9 |
| unattributed | #3a2f5c + hatch #8a80b0 | – | 1.6 (bg) | texture carries it |

Required adjacent pairs (normal / protan / deutan ΔE ×100; target ≥ 15 / ≥ 8 / ≥ 8):

| pair | normal | protan | deutan |
|---|---|---|---|
| tools – system | 33.8 | 26.3 | 25.4 |
| system – instructions | 31.1 | 25.9 | 30.1 |
| instructions – skills | 26.4 | 18.8 | 15.7 |
| skills – user | 22.2 | 15.9 | 20.3 |
| user – thinking | 50.3 | 47.4 | 49.9 |
| thinking – tool_use | 45.8 | 40.3 | 36.9 |
| tool_use – tool_result | 41.6 | 27.4 | 16.4 |
| tool_result – thinking | 24.0 | 13.4 | 23.2 |

Extra real-world neighbours also checked and passing (normal/protan/deutan): tool_result–assistant (in payload order a tool result is followed by the next assistant text) 21.7/20.0/11.5, reminders–tool_result (reminders ride on tool results) 27.4/15.4/22.8, tool_result–compaction 23.4/14.8/12.6, skills–reminders 34.1/34.8/29.4, tools–tool_result 17.6/19.9/17.1, system–thinking 19.8/17.5/13.8, user–tool_use 21.7/8.9/16.2; assistant–thinking, assistant–user and reminders–user are all > 20.

All-pairs check (any two of the 11 fills): worst normal-vision ΔE is 13.9 (skills–tool_use); pairs below CVD 8 are instructions–tool_use 4.2, skills–assistant 5.1, tools–compaction 6.5, tools–tool_use 7.3, skills–tool_result 7.5, system–tool_result 7.8. These are not the pairs that usually touch, but they CAN touch: grouped bars skip absent categories, and payload order can put any two next to each other. Secondary encoding that makes this acceptable: the 2px dark seam between every segment ≥ 5px, the tooltip/drawer naming the category, and legend click-to-highlight. 8 chromatic hues + 3 neutrals cannot all be ≥ 8 apart under CVD; do not claim full all-pairs safety.

### 3.2 Alternates for uncertain slots

| slot | primary | alternate | trade-off |
|---|---|---|---|
| tool_use | #39d353 | **#2fb84f** (emerald, L 0.69) | safer vs user (protan 17 instead of 9) and skills; less neon. thinking–tool_use 41.1/35.2/32.4, tool_use–tool_result 39.5/22.9/15.8 still pass. |
| tool_result | #ff70d6 | **#ff5ad9** (more magenta) | more "synthwave"; tool_result–thinking protan drops to 9.5 (passes, thin margin). |
| thinking | #8656ff | **#9a6bff** (lighter violet, contrast 5.4) | better contrast; tool_result–thinking 19.1/10.8/18.9 and system–thinking gets weaker. |
| assistant | #d4cfea | #c9c2e6 | slightly less bright; tool_result–assistant deutan drops to 8. Do NOT use mid-lavender (#b4aad8): deutan ΔE vs tool_result = 0.7. |
| compaction | #a39377 | #8c7f9e (cool grey) | cooler; reminders–compaction only 9.4. |

---

## 4. Typography

### 4.1 Fonts and loading

- **Display:** Orbitron (Google Fonts, OFL), weights 600 and 800. Preferred: self-host one file `static/fonts/orbitron-latin-wght.woff2` (variable, latin subset, about 20–40 KB) so the workshop needs no network:
  ```css
  @font-face {
    font-family: "Orbitron";
    src: url("/static/fonts/orbitron-latin-wght.woff2") format("woff2");
    font-weight: 400 900; font-display: swap;
  }
  ```
  If self-hosting is not wanted, use `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&display=swap">` (plus `preconnect`). The page must work without it.
- **Fallback chain** (`--font-display`): Bahnschrift (Windows 10+, DIN-like) → DIN Alternate (macOS) → Eurostile → Futura → Trebuchet MS → system UI. With uppercase and wide tracking all of these read "retro tech". Test with Orbitron blocked: KPI values must not wrap at 1024 px (see `clamp()` below).
- **UI:** `--font-ui` for all body text, controls, labels, tables. 14px base, line-height 1.45.
- **Mono:** `--font-mono` for `pre.content`, paths, item names in the drawer list are NOT mono (keep UI font).

### 4.2 Scale

| role | font | size / weight | tracking | case |
|---|---|---|---|---|
| Brand wordmark | display | 15px / 800 | 0.18em | UPPER |
| Session title (meta) | ui | 20px / 650 | -0.01em | as is |
| KPI label | display | 10.5px / 600 | 0.14em | UPPER |
| KPI value (hero) | display | `clamp(28px, 2.4vw, 36px)` / 800 | 0.02em | – |
| KPI value (others) | display | `clamp(18px, 1.5vw, 24px)` / 700 | 0.02em | – |
| KPI sub | ui | 12px / 400 | 0 | as is |
| Panel h2, drawer h3, section-head, control group label | display | 11px / 600 | 0.14em | UPPER |
| Segmented / toggles / chips | ui | 13px (chips 12px) / 500, active 650 | 0 | as is |
| Row label line 1 | ui | 12.5px / 650 (num), 400 rest | 0 | tabular-nums |
| Row label line 2 | ui | 12px / 400 | 0 | tabular-nums |
| Tooltip | ui | 12.5px | 0 | – |
| pre.content | mono | 12.5px / 1.5 | 0 | – |

Rule: display type only for short labels (≤ 4 words) and numbers. Never for sentences, item names or anything a user must read in full.

### 4.3 Text colour rules

- Text uses only `--ink`, `--ink-2`, `--muted`, and `--good`/`--warn` for status words (always with a glyph: ✓, !, ≈, …).
- Accent colours (`--neon-pink`, `--neon-cyan`, sun colours) are for lines, edges, glows and focus rings. The only text that uses them is the brand wordmark (gradient) and the FX button label when pressed. Reason: pink and cyan are close to tool_result and skills; text in those hues would read as data.

---

## 5. Background treatment

Three layers. Data never sits on an effect.

### 5.1 Page

```css
body {
  background:
    radial-gradient(1400px 520px at 50% -220px, rgba(157, 44, 255, 0.16), transparent 70%) no-repeat,
    var(--page);
  color: var(--ink);
  font: 14px/1.45 var(--font-ui);
}
:root[data-fx="off"] body { background: var(--page); }
```

### 5.2 Hero band (only place with the scene)

Wrap `.meta` and `.kpis` in a new section. The horizon is the top edge of the KPI row, so the tiles "stand on" the grid.

```html
<section class="session-hero">
  <div class="scene" aria-hidden="true">
    <div class="sun"></div>
    <div class="ground"><div class="grid"></div></div>
  </div>
  <section class="meta" id="meta"></section>
  <section class="kpis" id="kpis" aria-label="Session totals"></section>
</section>
```

```css
.session-hero { position: relative; isolation: isolate; margin: 0 -16px 14px; padding: 26px 16px 18px; }
.scene { display: none; }
:root[data-fx="on"] .scene {
  display: block; position: absolute; inset: 0; z-index: -1; overflow: hidden; pointer-events: none;
  --horizon: 78px;                       /* JS may set this to the .kpis offsetTop (see note) */
  background:
    /* stars: cheap, static */
    radial-gradient(1px 1px at 8% 22%,  rgba(255,255,255,.7), transparent 60%),
    radial-gradient(1px 1px at 23% 58%, rgba(255,255,255,.5), transparent 60%),
    radial-gradient(1px 1px at 41% 14%, rgba(255,255,255,.6), transparent 60%),
    radial-gradient(1px 1px at 57% 40%, rgba(255,255,255,.4), transparent 60%),
    radial-gradient(1px 1px at 69% 18%, rgba(255,255,255,.6), transparent 60%),
    radial-gradient(1.5px 1.5px at 93% 30%, rgba(255,255,255,.7), transparent 60%),
    /* sun glow behind the sun */
    radial-gradient(260px 140px at calc(100% - 150px) var(--horizon), rgba(255, 46, 151, .38), transparent 70%),
    /* sky: dark at the top (text sits there), magenta near the horizon */
    linear-gradient(180deg, #0b0618 0%, #160a30 calc(var(--horizon) - 40px), #3a0f55 var(--horizon), #0b0618 var(--horizon));
  /* fade the whole band into the page at the bottom */
  -webkit-mask-image: linear-gradient(180deg, #000 0 70%, transparent 100%);
          mask-image: linear-gradient(180deg, #000 0 70%, transparent 100%);
}
/* scanlines: on the scene only, never over tiles or text */
:root[data-fx="on"] .scene::after {
  content: ""; position: absolute; inset: 0;
  background: repeating-linear-gradient(180deg, rgba(0,0,0,.22) 0 1px, transparent 1px 3px);
}

/* the sun: about 3/4 above the horizon; stripes sit in the VISIBLE part (the ground covers the rest) */
.sun {
  position: absolute; right: 64px; top: max(4px, calc(var(--horizon) - 92px));
  width: 120px; aspect-ratio: 1; border-radius: 50%;
  background: var(--sunset-v);
  --stripes: linear-gradient(180deg,
      #000 0 42%, transparent 42% 45%, #000 45% 52%, transparent 52% 56%,
      #000 56% 62%, transparent 62% 67%, #000 67% 72%, transparent 72% 100%);
  -webkit-mask-image: var(--stripes);
          mask-image: var(--stripes);
}
/* 120px sun, top = horizon - 92px: 92px (77%) is visible, so the 4 gaps at 42-72% all show. */

/* ground + perspective grid below the horizon (covers the lower half of the sun) */
.ground {
  position: absolute; left: 0; right: 0; top: var(--horizon); bottom: 0; overflow: hidden;
  background: linear-gradient(180deg, #24093e 0%, #0b0618 85%);
  border-top: 1px solid rgba(255, 211, 25, .55);
  box-shadow: 0 -1px 18px rgba(255, 46, 151, .55);
  perspective: 240px; perspective-origin: 50% 0;
  -webkit-mask-image: linear-gradient(180deg, #000 0 55%, transparent 100%);
          mask-image: linear-gradient(180deg, #000 0 55%, transparent 100%);
}
.grid {
  position: absolute; left: -60%; right: -60%; top: -44px; height: 600px;
  transform-origin: 50% 0; transform: rotateX(64deg);
  background-image:
    linear-gradient(90deg, rgba(255, 46, 151, .55) 1px, transparent 1px),
    linear-gradient(180deg, rgba(255, 46, 151, .55) 1px, transparent 1px);
  background-size: 44px 44px;
  will-change: transform;
  animation: grid-run 7s linear infinite;
}
@keyframes grid-run { from { transform: rotateX(64deg) translateY(0); } to { transform: rotateX(64deg) translateY(44px); } }

@media (max-width: 1099px) { .sun { display: none; } }
@media (prefers-reduced-motion: reduce) { .grid { animation: none; } }
```

Notes:
- `--horizon`: the default 78px matches a one-line meta (with the 26px top padding the sun needs). Set it from JS in one `measureLayout()` function (see section 9) so the horizon always sits 10px above the tiles, also when the meta wraps, on resize, and after the webfont loads.
- The meta text sits in the dark top part of the sky (ink 16.5:1, muted 6.8:1 on #1a0a35). Give `.meta` `padding-right: 260px` at ≥ 1100px so text never runs over the sun.
- KPI tiles use `--tile` (88% opaque) + `backdrop-filter: blur(6px)`; worst case text over grid line: ink-2 9.8:1, muted 6.3:1; over the sun: muted 5.3:1.
- The animation is transform-only on one layer (GPU compositor, no canvas redraw, no layout). Turned off by reduced motion and by FX off.

### 5.3 Everything below the hero

Solid surfaces only. No scanlines, no gradients inside the rows panel, no glow on anything inside `.rows`.

---

## 6. Components

### 6.1 Header (`.topbar`)

```css
.topbar {
  position: sticky; top: 0; z-index: 20; min-height: var(--topbar-h);
  display: flex; align-items: center; gap: 12px; padding: 0 16px;
  background: var(--surface);
}
.topbar::after {                       /* sunset line, also with FX off (1px) */
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 1px; background: var(--sunset);
}
:root[data-fx="on"] .topbar { background: var(--topbar); backdrop-filter: blur(10px) saturate(1.2); }
:root[data-fx="on"] .topbar::after { height: 2px; box-shadow: 0 0 12px rgba(255, 46, 151, .6); }

.brand {
  font: 800 15px/1 var(--font-display); letter-spacing: .18em; text-transform: uppercase;
  color: var(--ink); white-space: nowrap;
}
:root[data-fx="on"] .brand {
  background: var(--sunset-v); -webkit-background-clip: text; background-clip: text; color: transparent;
  filter: drop-shadow(0 0 6px rgba(255, 46, 151, .55));
}
```
(Gradient stops on the dark bar: 13.5 / 8.3 / 5.6 :1, all AA.)

- Session `<select>`: `background: var(--surface-2); border: 1px solid var(--border-ui); border-radius: var(--radius-sm); padding: 7px 32px 7px 10px; appearance: none;` + chevron as inline SVG data-URI in `--ink-2` at right 10px. Hover: border `--neon-pink` at 70%. `option, optgroup { background: var(--surface); color: var(--ink); }`.
- Checkboxes everywhere: `accent-color: var(--neon-cyan);` width/height 15px.
- Live pill: `.live` = 11px display, uppercase, tracking .12em, `--ink-2` text; dot 8px.
  - `.live.on .dot { background: var(--good); box-shadow: 0 0 8px var(--good); }` + FX-on pulse ring:
    ```css
    :root[data-fx="on"] .live.on .dot { position: relative; }
    :root[data-fx="on"] .live.on .dot::after { content:""; position:absolute; inset:-4px; border-radius:50%;
      border:1px solid var(--good); animation: pulse 2.4s ease-out infinite; }
    @keyframes pulse { from { transform: scale(.6); opacity: .9 } to { transform: scale(1.8); opacity: 0 } }
    ```
  - `.live.off`: dot `--warn`, text "reconnecting".
- FX button (replaces ◐): `.icon-btn.fx` text "FX", display font 12px 800 tracking .12em. `aria-pressed="true"`: border `--neon-pink`, `box-shadow: var(--glow-pink)`, text `--ink`. Pressed false: border `--border-ui`, text `--muted`. Title: "Visual effects on/off (does not change the data colours)".
- Order at ≥ 1024: brand · select (grow) · Follow latest · live · FX.

### 6.2 Meta line + badges

- `.meta`: flex wrap, gap 6px 14px, align baseline, margin 0 0 14px.
- `.title`: 20px / 650 `--ink`, max 1 line, ellipsis (`max-width: 60ch`).
- Path span (needs a hook: `el("span", "path", …)` with `title` = full path in `renderMeta()`, app.js:248): `font: 12px var(--font-mono); min-width: 0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; color: var(--muted);` one line with ellipsis, `max-width: 48ch; direction: rtl; text-align: left;` (shows the END of the path, the useful part); full path in `title`.
- `.badge`: `font: 600 11px/1.6 var(--font-ui); padding: 0 8px; border-radius: 999px; background: var(--surface-2); border: 1px solid var(--border); color: var(--ink-2);`
  - `.badge.exact`: `color: var(--good); border-color: rgba(94, 242, 168, .45);` prefix "✓ ".
  - `.badge.est`: `color: var(--warn); border-color: rgba(255, 181, 71, .45);` prefix "≈ " (errors badge: "! ").
  - `button.badge:hover`: `background: var(--row-focus);` FX on: `box-shadow: 0 0 10px rgba(255,181,71,.35)`.

### 6.3 KPI tiles

Hero tile = **Current context**, because it answers the first workshop question ("how full is my context right now?") and it is the number that changes live. New order (change `renderKpis`): Current context (hero) · Peak context · Requests · Input tokens read · Cache hit · Output tokens · Est. cost.

Hero tile gets a context-window gauge (chrome, not a category mark):
```html
<div class="kpi kpi--hero"> label / value / <div class="gauge"><i style="width: 41%"></i></div> / sub "41% of 1.00M window · request #114" </div>
```

```css
.kpis { display: grid; gap: 10px; margin: 0;
  grid-template-columns: minmax(230px, 1.7fr) repeat(6, minmax(0, 1fr)); }
.kpi { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 10px 12px 11px; min-width: 0; position: relative; }
:root[data-fx="on"] .kpi { background: var(--tile); backdrop-filter: blur(6px); }
.kpi .label { font: 600 10.5px/1.2 var(--font-display); letter-spacing: .14em; text-transform: uppercase; color: var(--ink-2); }
.kpi .value { font: 700 clamp(18px, 1.5vw, 24px)/1.15 var(--font-display); letter-spacing: .02em; color: var(--ink);
  margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-variant-numeric: tabular-nums; }
.kpi .sub { font-size: 12px; color: var(--muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.kpi--hero { border-color: var(--border-ui); }
.kpi--hero::before { content: ""; position: absolute; left: -1px; right: -1px; top: -1px; height: 2px;
  border-radius: var(--radius) var(--radius) 0 0; background: var(--sunset); }
.kpi--hero .value { font-size: clamp(28px, 2.4vw, 36px); font-weight: 800; }
:root[data-fx="on"] .kpi--hero { box-shadow: 0 0 24px rgba(255, 46, 151, .18); }
:root[data-fx="on"] .kpi--hero .value { text-shadow: var(--glow-text); }

.gauge { height: 4px; border-radius: 2px; background: var(--grid); margin: 6px 0 4px; overflow: hidden; }
.gauge > i { display: block; height: 100%; background: var(--sunset); border-radius: 2px; }
/* > 80% of window: switch the fill to warn and add "!" in the sub text */
.gauge.high > i { background: var(--warn); }
```
Only the hero value glows. The other six stay flat so the eye lands in one place.

Responsive: 640–1279px: `grid-template-columns: repeat(4, minmax(0, 1fr))`, `.kpi--hero { grid-column: span 2 }` → two even rows (hero + 2, then 4). < 640px: 2 columns, hero spans 2. Class names: the wrapper is `.session-hero`, the tile is `.kpi--hero` (do not reuse one name for both).

### 6.4 Controls row (segmented controls, toggles)

Move `.controls` and `.legend` into one **sticky key bar** at the top of the board (see UX #2):

```html
<section class="keybar"> <div class="controls">…</div> <div class="legend" id="legend"></div> </section>
```
```css
.keybar { position: sticky; top: var(--topbar-h); z-index: 15; background: var(--page);
  padding: 8px 0 8px; margin-bottom: 8px; border-bottom: 1px solid var(--border);
  display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: center; }
.controls { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; }
.ctl-label { font: 600 10.5px var(--font-display); letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }

.seg { display: inline-flex; border: 1px solid var(--border-ui); border-radius: var(--radius-sm); overflow: hidden; }
.seg button { border: 0; background: var(--surface); color: var(--ink-2); padding: 5px 11px; cursor: pointer; font-size: 13px; }
.seg button + button { border-left: 1px solid var(--border-ui); }
.seg button:hover { background: var(--surface-2); color: var(--ink); }
.seg button.on { background: var(--row-focus); color: var(--ink); font-weight: 650; box-shadow: inset 0 -2px 0 var(--neon-pink); }
:root[data-fx="on"] .seg button.on { box-shadow: inset 0 -2px 0 var(--neon-pink), 0 2px 10px -2px rgba(255, 46, 151, .55); }
```
Shorten labels and add group labels: `VIEW [By type | Payload order]`, `SCALE [Session peak | Context window]`. Toggles ("Subagents", "Auto-scroll") as now, `--ink-2`, cyan accent-color.

### 6.5 Legend chips

```css
.legend { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
.chip { display: inline-flex; align-items: center; gap: 6px; padding: 3px 9px 3px 6px; font-size: 12px;
  background: var(--surface); border: 1px solid var(--border-ui); border-radius: 999px; color: var(--ink-2); cursor: pointer; }
.chip.static { border-color: var(--border); }   /* cache chips are not interactive */
.chip:hover { border-color: var(--ink-2); color: var(--ink); }
.chip.on { border-color: var(--neon-cyan); color: var(--ink); background: var(--row-focus); }
:root[data-fx="on"] .chip.on { box-shadow: var(--glow-cyan); }
.chip.dim { color: var(--muted); }          /* text stays AA (6.8:1); do NOT use opacity on the whole chip */
.chip.dim .sw { opacity: .3; }
.chip .sw { width: 12px; height: 12px; border-radius: 3px; flex: none; }   /* flat, no glow, no border */
.sw.hatch { background-image: repeating-linear-gradient(45deg, var(--hatch) 0 1px, transparent 1px 4px); }
.chip.static { cursor: default; }
.legend .sep { width: 1px; align-self: stretch; background: var(--border); margin: 0 6px; }
```
- Add `aria-pressed` on category chips (they are toggles).
- Before the cache chips add `<span class="ctl-label">Cache</span>` so the two keys read as separate groups.
- At ≥ 1440px the controls and the legend fit on one or two lines of the key bar; at < 640px make `.legend` one line with `overflow-x: auto; flex-wrap: nowrap; scrollbar-width: none`.

### 6.6 Request rows

Panel:
```css
.rows { background: var(--plot); border: 1px solid var(--border); border-radius: var(--radius); padding: 6px 0; min-width: 0; position: relative; }
.rows::before { content: ""; position: absolute; left: 12px; right: 12px; top: -1px; height: 1px; background: var(--sunset); opacity: .7; } /* chrome edge, outside the data */
.empty { padding: 32px; color: var(--muted); text-align: center; }
```
Row:
```css
.row { display: grid; grid-template-columns: 210px minmax(0, 1fr); gap: 12px; padding: 3px 12px; align-items: center; }
.row:hover { background: var(--row-hover); }
.row.focus { background: var(--row-focus); box-shadow: inset 3px 0 0 var(--neon-cyan); }
.row .lbl { font-size: 12px; line-height: 1.3; text-align: left; background: none; border: 0; padding: 2px 0; cursor: pointer; min-width: 0; color: var(--ink-2); }
.row .lbl .num  { font-weight: 650; color: var(--ink); font-variant-numeric: tabular-nums; }
.row .lbl .size { font-weight: 650; color: var(--ink); font-variant-numeric: tabular-nums; }
.row .lbl .time { color: var(--muted); font-variant-numeric: tabular-nums; }
.row .lbl .l2 { color: var(--ink-2); font-variant-numeric: tabular-nums; }
.row .lbl .lowcache { color: var(--warn); }          /* "! 69% cache" when < 80% */
.row .st.ok { color: var(--good); } .row .st.warn { color: var(--warn); }
.row canvas { display: block; width: 100%; height: 30px; cursor: pointer; border-radius: 3px; }
.row canvas:focus-visible { outline: 2px solid var(--focus); outline-offset: 1px; }
```
Label content (see UX #4): line 1 `#18 · 137k ✓ [source badge]`, line 2 `14:13:23 · 69% cache · $0.359`, model name only when it differs from the previous row in the same transcript (show it as a small `.badge`).
Label column: 210px at ≥ 1280px, 190px at 1024–1279px.

Subagent rows and group heads:
```css
.row.agent .lbl { border-left: 2px solid var(--axis); padding-left: 8px; }
.group-head { width: 100%; display: flex; gap: 10px; align-items: center; padding: 6px 12px 6px 32px; cursor: pointer;
  background: linear-gradient(90deg, rgba(255, 46, 151, .10), transparent 55%); border: 0;
  border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); color: var(--ink-2); font-size: 12px; text-align: left; }
.group-head:hover { background: linear-gradient(90deg, rgba(255, 46, 151, .18), transparent 65%); color: var(--ink); }
.group-head .caret { width: 12px; color: var(--ink); }
.group-head .kind { font: 600 10.5px var(--font-display); letter-spacing: .14em; text-transform: uppercase; color: var(--ink); }
.group-head[aria-expanded="true"] { box-shadow: inset 2px 0 0 var(--neon-pink); }
.section-head { padding: 12px 12px 4px; font: 600 10.5px var(--font-display); letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }
```
No gradient behind the agent rows themselves (the gradient is on the head only, which has no bars).

### 6.7 Sidebar panels

```css
.board { display: grid; grid-template-columns: minmax(0, 1fr) 330px; gap: 16px; align-items: start; }
.side { position: sticky; top: calc(var(--topbar-h) + var(--keybar-h, 52px) + 8px); display: flex; flex-direction: column; gap: 12px; }
.panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 14px; position: relative; }
.panel::before { content: ""; position: absolute; left: -1px; right: -1px; top: -1px; height: 2px; border-radius: var(--radius) var(--radius) 0 0; background: var(--sunset); opacity: .8; }
.panel.help::before { background: var(--neon-cyan); opacity: .6; }
.panel h2 { font: 600 11px/1.3 var(--font-display); letter-spacing: .14em; text-transform: uppercase; color: var(--ink); margin: 0 0 4px; }
.hint { color: var(--muted); font-size: 12px; margin: 0 0 8px; }
.help ul { color: var(--ink-2); font-size: 12.5px; padding-left: 18px; margin: 6px 0 0; }
.help li::marker { color: var(--neon-pink); }
table.top { width: 100%; border-collapse: collapse; font-size: 12.5px; }
table.top td { padding: 4px; border-top: 1px solid var(--grid); vertical-align: top; color: var(--ink); }
table.top tr { cursor: pointer; }
table.top tr:hover td { background: var(--surface-2); }
table.top .tok { text-align: right; color: var(--ink-2); font-variant-numeric: tabular-nums; white-space: nowrap; }
table.top .sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
```
Split the long panel title: h2 "LARGEST ITEMS", and put "Request #114" in the `.hint` line (display font titles must stay short). Update the help text for the reversed cache ramp: "**read** (cheap, dark), **written** (extra cost, mid), **not cached** (full price, bright)".
Make `table.top tr` focusable (`tabIndex=0`, Enter opens), like `.items li`. Show the category visibly (touch has no hover title): add `<span class="cat">` with the category name under the item name, `font-size: 11px; color: var(--muted)`, and set the row `aria-label` to "name, category, tokens".

### 6.8 Drawer

```css
.drawer { position: fixed; top: 0; right: 0; bottom: 0; width: min(720px, 100vw); z-index: 40;
  background: var(--surface); border-left: 1px solid var(--border-ui);
  box-shadow: -24px 0 64px rgba(0, 0, 0, .6);
  transform: translateX(100%); transition: transform .18s ease; display: flex; flex-direction: column; }
:root[data-fx="on"] .drawer { box-shadow: -1px 0 0 var(--neon-pink), -12px 0 40px rgba(255, 46, 151, .16), -24px 0 64px rgba(0, 0, 0, .6); }
.drawer.open { transform: none; }
.drawer-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; padding: 14px 16px; position: relative; background: var(--surface); }
.drawer-head::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 1px; background: var(--sunset); opacity: .8; }
#drawer-title { font-size: 15px; font-weight: 650; color: var(--ink); min-width: 0; }
#drawer-title .sub { font-weight: 400; font-size: 12px; color: var(--ink-2); margin-top: 2px; }
.drawer-body { overflow: auto; padding: 12px 16px 40px; flex: 1; }
.drawer-body h3 { font: 600 10.5px var(--font-display); letter-spacing: .14em; text-transform: uppercase; color: var(--ink-2); margin: 18px 0 6px; }
.drawer-body h3::before { content: ""; display: inline-block; width: 10px; height: 2px; background: var(--neon-pink); vertical-align: middle; margin-right: 8px; }
pre.content { white-space: pre-wrap; word-break: break-word; margin: 6px 0 0; padding: 12px;
  background: var(--page); border: 1px solid var(--border); border-radius: var(--radius-sm);
  font: 12.5px/1.5 var(--font-mono); color: #e6e0f5; /* 15.8:1 */ tab-size: 2; }
table.kv { border-collapse: collapse; width: 100%; font-size: 13px; }
table.kv td { padding: 5px 6px; border-top: 1px solid var(--grid); color: var(--ink); }
table.kv td:first-child { color: var(--ink-2); white-space: pre; }
table.kv td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
table.kv tr[role="button"]:hover td { background: var(--surface-2); }
.note { color: var(--warn); font-size: 12px; margin: 6px 0; }
.icon-btn#drawer-close { width: 32px; height: 32px; display: grid; place-items: center; padding: 0; }
```
Keyboard: set `drawer.inert = true` when closed and `false` when open (in `openDrawer`/`closeDrawer`, app.js:653–670), so off-screen controls are not tabbable. No scrim / no modal: the page behind stays usable (people click other bars while the drawer is open).

### 6.9 Item lists

```css
.items { list-style: none; margin: 0; padding: 0; }
.items li { display: grid; grid-template-columns: 12px minmax(0, 1fr) auto; gap: 8px; padding: 6px 8px; border-radius: var(--radius-sm); cursor: pointer; align-items: baseline; }
.items li:hover { background: var(--surface-2); }
.items li.sel { background: var(--row-focus); box-shadow: inset 2px 0 0 var(--neon-cyan); }
.items .sw { width: 10px; height: 10px; border-radius: 2px; }
.items .nm { font-size: 13px; color: var(--ink); word-break: break-word; }
.items .tk { font-size: 12px; color: var(--ink-2); font-variant-numeric: tabular-nums; white-space: nowrap; }
.new { font: 700 10px/1.5 var(--font-ui); text-transform: uppercase; letter-spacing: .06em; color: var(--ink);
  background: rgba(63, 240, 255, .14); border: 1px solid rgba(63, 240, 255, .7); border-radius: 999px; padding: 0 6px; margin-left: 6px; }
```

### 6.10 Tooltip

```css
.tooltip { position: fixed; z-index: 50; pointer-events: none; display: none; max-width: 360px;
  background: rgba(16, 9, 34, .97); color: var(--ink); border: 1px solid var(--border-ui); border-radius: var(--radius-sm);
  box-shadow: var(--shadow-pop); padding: 8px 10px; font-size: 12.5px; }
:root[data-fx="on"] .tooltip { box-shadow: 0 0 0 1px rgba(255, 46, 151, .25), var(--shadow-pop); }
.tooltip .h { display: flex; align-items: center; gap: 6px; font-weight: 650; }
.tooltip .sw { width: 10px; height: 10px; border-radius: 2px; }
.tooltip .d { color: var(--ink-2); margin-top: 2px; }
.tooltip .d:last-child { color: var(--muted); }  /* "Click to see the content" */
```

### 6.11 Buttons, scrollbars, focus, selection

```css
.icon-btn { background: var(--surface-2); color: var(--ink); border: 1px solid var(--border-ui); border-radius: var(--radius-sm); padding: 5px 10px; cursor: pointer; }
.icon-btn:hover { border-color: var(--neon-pink); }
:root[data-fx="on"] .icon-btn:hover { box-shadow: var(--glow-pink); }

:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
:root[data-fx="on"] :focus-visible { box-shadow: 0 0 0 5px var(--focus-halo); }
::selection { background: rgba(255, 46, 151, .38); color: var(--ink); }

html { scrollbar-color: var(--axis) var(--page); }
* { scrollbar-width: thin; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--page); }
::-webkit-scrollbar-thumb { background: var(--axis); border-radius: 6px; border: 2px solid var(--page); }
::-webkit-scrollbar-thumb:hover { background: var(--border-ui); }
```

### 6.12 Motion and accessibility switches

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}
/* prefers-contrast: more / forced-colors: handled in JS, not CSS. In init():
   const hc = matchMedia("(prefers-contrast: more), (forced-colors: active)");
   fx = hc.matches ? false : store.get("fx", true) && params.get("fx") !== "0";
   → sets data-fx="off" (so EVERY FX rule is off, incl. blur, glows, pulse) and aria-pressed="false" on the button.
   Listen to hc "change" and re-apply. */
@media (forced-colors: active) { .chip .sw, .items .sw, table.top .sw { forced-color-adjust: none; } }
```

### 6.13 Responsive

- ≥ 1440px: `main { max-width: 1760px }`, sidebar 330px, label column 210px, KPI one row.
- 1280–1439px: sidebar 300px, KPI one row.
- 1024–1279px: sidebar 280px, label column 190px, KPI 4 columns (hero spans 2), sun hidden below 1100px.
- 640–1023px: KPI 4 columns (hero spans 2); board one column, sidebar below the rows and not sticky; key bar still sticky.
- < 640px: topbar wraps to two lines (brand + live + FX, then the select full width); `--topbar-h` is measured by JS, never hard-coded; hero padding 12px, scene height capped (`.ground` hidden, keep sky gradient only); KPI 2 columns; row label stacks above the bar (existing rule); legend single scrolling line; drawer full width.

---

## 7. Canvas (`drawRow`) changes

### 7.1 Read colours from CSS

```js
function readColors() {
  const css = getComputedStyle(document.documentElement);
  const v = (n) => css.getPropertyValue("--" + n).trim();
  const cols = {};
  for (const c of ["tools","system","instructions","skills","reminders","user","assistant","thinking",
                   "tool_use","tool_result","compaction","unattributed"]) cols[c] = v("c-" + c);
  for (const n of ["plot","ink","ink-2","muted","hatch","mark","mark-edge","cache-read","cache-write","cache-none","grid","font-ui"]) cols[n] = v(n);
  S.colors = cols;
}
```
Colours no longer depend on theme or FX, so `readColors()` is needed once at init (keep the call in `render()`, it is cheap). Delete the prefers-color-scheme listener.

### 7.2 Drawing rules

- **Background / gap colour:** keep `clearRect` and a transparent canvas. The 2px gap between segments shows the row background (`--plot`, `--row-hover` or `--row-focus`), all dark, so the gap always reads as a dark seam. Do not fill a canvas background (it would break hover/focus row tints).
- **Segments:** flat fills, no `shadowBlur`, no gradients, no strokes. Keep gap 2px when the segment is ≥ 5px, keep the 4px rounded end on the last segment.
- **Highlight dimming:** keep `globalAlpha = 0.22` for non-highlighted categories (on the dark plot this dims well).
- **Unattributed hatch:** `hatch(ctx, col.hatch, col.unattributed)`; also move `hatchCache = {}` out of `drawRow` (reset it only in `readColors`), it is rebuilt for every row today.
- **"New content" marker:** `ctx.fillStyle = col.mark;` 2px tall at y = 0 over the new segments (as now). White on dark is 17:1 and is neutral (no hue clash).
- **Cache-breakpoint triangles (payload order):** move this block AFTER the cache-strip block (today the strip, drawn later from y = 23, paints over the triangle tip at y = 24). Fill `col.mark`, then `ctx.lineWidth = 1; ctx.strokeStyle = col["mark-edge"]; ctx.stroke();` so a triangle stays visible over the bright "not cached" part. Size unchanged (6 × 4 px).
- **Cache strip:** colours from the new ramp (`cache-read` dark, `cache-write` mid, `cache-none` bright). Keep the 1px gap between parts.
- **"Waiting for response…":** `ctx.font = "italic 11px " + col["font-ui"]; ctx.fillStyle = col.muted;` (7:1 on plot). No placeholder outline (when there are no segments, `x` is 0).
- **Scale guides (UX #5):** before drawing segments, draw 1px vertical lines in `col.grid` at "nice" token steps (50k below 400k peak, 100k up to 1M, 250k above) from y = barY to stripY + stripH. They sit behind the bars and are only visible in empty space. In "context window" scale also draw this row's own window limit at `x = r.contextWindow * per` in `col.muted` (only when `r.contextWindow` is set and `x <= w`). Do not draw it at `w - 1`: `scaleMax()` returns `max(window, peak)`, so the right edge is not always 100%, and rows can have different windows.

### 7.3 Cache ramp meaning

The ramp is now reversed on purpose: cache **read** (cheap, usually 90%+) is the quietest, **not cached** (full price) is the brightest, cache **write** sits in the middle. Rows that missed the cache (e.g. #18 with 69% cache in the current session) now light up in the strip. Update the help panel, the legend tooltips, and the `README` if it describes strip colours.

---

## 8. UX improvements (ranked, max 5)

1. **One hero number.** "Current context" becomes the hero KPI with a window gauge (warn colour above 80%), and tiles are reordered so the context story reads left to right (current → peak → requests → total read → cache → output → cost). Today all 7 tiles have the same weight, so nothing draws the eye.
2. **Sticky key bar.** Controls + legend become one sticky bar under the header. With 100+ rows the legend scrolls away today, and at 1500px the legend wraps to two lines above the board. Sticky keeps the colour key visible exactly where the bars are read.
3. **Make cost visible in the cache strip.** Reverse the cache ramp (cheap = dark, full price = bright) and colour the "% cache" text in the row label `--warn` with a "!" when it is below 80%. Cache misses are the main cost lever in the workshop; today they are the darkest, least visible part of the strip.
4. **Leaner row labels.** Lead with `#n · size` (bold), move time + cache + cost to line 2, and show the model only when it changes (today "Opus 5.5" repeats on every row). The label column shrinks from 240px to 210/190px, giving the bars more width.
5. **Scale guides.** Faint vertical guide lines every 50k/100k tokens (and the 100% window line in window scale) so people can compare bar lengths across many rows without hovering. A small sticky tick header row (`0 · 100k · 200k …`, 11px `--muted`) at the top of `.rows` is a cheap follow-up.

---

## 9. Implementation checklist (app.js touch points)

- `init()`: replace `applyTheme`/theme button with FX (`dataset.fx`, `aria-pressed`, `store "fx"`, `?fx=0`); remove the color-scheme listener.
- `readColors()`: new token list (7.1).
- `drawRow()`: 7.2 (hatch tokens, mark colours, triangle outline, waiting text, guides).
- `renderKpis()`: new order, `hero` class + gauge on Current context.
- `makeRow()`: new label content, `lowcache` class, model only on change.
- `renderLegend()`: `aria-pressed` on chips, "Cache" group label; `setSeg()`: set `aria-pressed`.
- New `measureLayout()`: sets `--topbar-h` (topbar height), `--keybar-h` (key bar height) on `:root` and `--horizon` (`kpis.offsetTop - 10`) on `.scene`. Call it at the end of `render()`, from a new ResizeObserver on `.topbar`, `.keybar` and `.meta` (the existing one on `#rows` only redraws canvases), and after `document.fonts.ready`.
- `renderMeta()`: `path` class + `title` on the path span.
- `openDrawer()` / `closeDrawer()`: toggle `inert`.
- `renderTop()`: shorter h2, request name in hint, focusable rows.
- `index.html`: hero wrapper + scene markup, key bar wrapper, FX button, group labels, optional font link.

---

## 10. Risks and trade-offs

- **Dark-only on projectors.** In a bright room a weak projector lifts the blacks, so `--plot`, `--surface` and `--page` may merge. Data survives (all fills ≥ 3.25:1, most ≥ 6:1, text ≥ 5.8:1), but panel edges will fade. Dropping the light theme removes the fallback; FX off is the only switch. If this is a real risk for the venue, keep a hidden `?theme=light` with the old light tokens rather than designing a new light theme.
- **Neon fatigue.** Large areas of bright yellow/aqua/green can halo on projectors. Mitigation already in the spec: no glow on data, 2px dark seams, chroma kept below the gamut edge. If bars feel loud, lower the L of user and skills by ~0.04 and re-validate.
- **Accent/data hue overlap.** Pink and cyan chrome share hues with tool_result and skills. Kept safe by the rule "accents are lines and glows, never words, never inside `.rows`" (except the cyan focus bar on a focused row, which is a 3px edge, not a fill).
- **Weak CVD pairs outside the required list** (instructions–tool_use 4.2, skills–assistant 5.1, tools–compaction 6.5, tools–tool_use 7.3) look alike for colour-blind viewers. They rarely touch in a bar but can (absent categories, payload order). Mitigation is the dark seam, tooltip names and legend highlight; for a stronger fix use the tool_use alternate #2fb84f (raises instructions–tool_use only a little) or add a texture to one of the pair.
- **Font fallback changes widths.** Orbitron is wide; Bahnschrift/DIN is narrow. `clamp()` sizes, `nowrap` + ellipsis on KPI values, and a test with the webfont blocked are required.
- **Effect cost.** `backdrop-filter` on the sticky header and tiles plus the grid animation cost GPU on old laptops; all of it sits behind FX and reduced-motion. The canvas cost does not change.
- **Reversed cache ramp** is a meaning change for anyone who used the current build; the help text and legend tooltips must say it.

---

## Implementation notes (done 2026-10-15)

Status: implemented as specified. Checked in headless Chrome via the DevTools protocol at 1500 px and
1100 px, FX on and off, drawer open; opened in Chrome for the user. 19 unit tests pass.

Changes against the spec:
- Request #1 never gets the "!" low-cache flag (it cannot reuse this session's cache yet).
- Topbar `min-height` is a fixed 56px; `--topbar-h` is only the measured value for sticky offsets
  (otherwise the header can grow but never shrink — buddy review).
- In forced-colors mode the bar canvas keeps a fixed dark background (canvas colours are not remapped).
- Bug found while testing: a typed prompt is logged as a string but sent as one text block, so all
  requests after it stayed "pending". The parser now also hashes the list form (test added).
- Not done: hidden `?theme=light` fallback for bright rooms (spec risk 1). FX off is the only switch.
