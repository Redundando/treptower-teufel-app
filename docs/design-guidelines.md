# Design Guidelines (for FastAPI + Svelte apps)

This document translates the active WordPress theme `klohn-kit` design system into concrete, reusable UI rules (optics + UX + design principles).
Use it as the source of truth for tokens (colors, borders, radius, typography, spacing) and for component "recipes" so your new club-management app visually matches the website.

## 1) Brand / Design Intent

The site should feel:
- Classic, practical, "old-site" in the good sense: direct, readable, structured, not decorative.
- Information-dense, but always scannable via consistent hierarchy (headings, lists, predictable actions).
- Flat by default: borders + subtle tints. No "modern card UI" aesthetics.

Non-negotiable: styling must increase clarity or speed of navigation.

## 2) Non-Negotiable Principles

1. Content + functionality first. Styling must increase clarity or speed of navigation.
2. Whitespace must justify itself (grouping + readability). Avoid empty decorative bands.
3. Consistency: the same thing must look the same everywhere (buttons, cards, lists, headings).
4. Color communicates meaning; avoid decorative color noise.
5. Shadows are basically off (only allowed if they communicate layering, e.g. dropdown over page). If you use shadows, keep them extremely subtle and consistent.
6. Red usage rule: brand red is primarily for navigation and actions. Do not use brand red for long body text.

## 3) Global Tokens (Use everywhere)

### 3.1 Typography

Base typography:
- Font family: `Arial` with `system-ui` sans-serif fallback.
- Body text: `16px`, line-height `1.6`, normal weight (not bold).

Heading hierarchy (scannable, not decorative):
- H1: ~`23-27px` with line-height about `1.15`, weight "bold-ish" (~`600-700`)
- H2: ~`20-25px` with line-height about `1.2`, weight ~`600-700`
- H3: ~`18-21px` with line-height about `1.25`, weight `600`

Structure rule:
- Keep H4-H6 as structural only (no special "styles" that create inconsistent hierarchy).

Heading spacing:
- Headings use a consistent top/bottom rhythm (theme sets `margin: 12px 0 16px 0` for `h1-h6`).

Meta / secondary text:
- Muted/meta: `14px`, line-height `1.4`, muted gray.

### 3.2 Links

Link optics:
- Links look like links immediately (theme uses the site link color).
- Underline on hover and on focus is mandatory.
- Underline uses an offset (~`2px`).

### 3.3 Spacing Rhythm

Use a fixed rhythm for vertical and component spacing (avoid one-off gaps):
- `4px` (XS)
- `8px` (S)
- `14px` (M) default vertical rhythm between blocks
- `18px` (L)
- `24-28px` (XL / major sections)

Example mapping (common):
- Default block-to-block gap: `14px`
- Major section spacing: `24-28px`

### 3.4 Borders and Dividers

Use consistent border thickness:
- Default border: `1px solid` border color
- Dividers: same `1px` thickness as default border
- Meta bars/separators: `1px dotted` border color

Corners (radius):
- Recommended/minimal rounding: `3px` everywhere for panels/cards/inputs/buttons.

### 3.5 Focus State

Make focus obvious and consistent:
- Use a clear focus ring color from the accent red family.
- Theme focus ring uses `outline: 2px solid` and an `outline-offset` approach.

## 4) Color Palette (Concrete Hex Values)

The theme uses one coherent palette with semantic roles.

### 4.1 Neutrals

- Surface (background): `#FFFFFF`
- Page text (default): `#0E0E0E`
- Muted/meta text: `#888888`
- Border / dividers: `#BEBEBE`
- Surface tint (subtle light gray): `#F3F3F3`

### 4.2 Brand Red (actions + navigation)

Use brand red for:
- Header/nav backgrounds
- Primary actions/buttons
- Links

- Primary darkest (brand/action): `#B51A2C`
- Hover/darker secondary: `#D83A4D`
- Focus ring: `#F88492`
- Light surfaces (for callouts / tints): `#FBB0B9` and/or `#F88492` depending on desired intensity

### 4.3 Positive / Success (green family)

Use for positive callouts and success messages:
- Tertiary darkest (border): `#2D6126`
- Tertiary lightest (background): `#F1FEEF`

### 4.4 Semantic Role Mapping (Recommended)

Map your app's design tokens like this:
- `surface` -> `#FFFFFF`
- `surfaceTint` -> `#F3F3F3`
- `text` -> `#0E0E0E`
- `muted` -> `#888888`
- `border` -> `#BEBEBE`
- `brand` -> `#B51A2C`
- `brandHover` -> `#D83A4D`
- `focus` -> `#F88492`
- `successBg` -> `#F1FEEF`
- `successBorder` -> `#2D6126`

Rule of thumb:
- Red communicates interaction/brand accent, not "text paint" for explanations.

## 5) Layout Rules

### 5.1 Container + Prose Width

The theme aligns content to one container:
- Desktop max width: `1200px`
- Side padding: `18px`

- Text-heavy content uses a prose width constraint:
- Target reading width: "comfortable reading width", ~`45-60 characters per line`
- Implement via a max width around `75ch` / `800px` for main prose.

### 5.2 Header Navigation (optics)

Header is compact and uses the brand red only in the header area:
- Brand row background: `#B51A2C`
- Nav links: white text
- Nav link hover background: `#D83A4D`
- Header border below nav: uses the same red family (theme uses a border color derived from the hover red)
- Nav item padding uses the small spacing unit (`8px` vertically and horizontally in the theme CSS)
- Border radius for nav items: `3px`

### 5.3 Footer Navigation

Footer is dense but structured:
- Footer widgets background: `#F3F3F3`
- Footer nav background: `#0E0E0E`
- Footer nav hover background: `#4B4B4B`
- Footer link border radius: `6px` (note: slightly larger than global `3px` to feel consistent in footer tiles)

## 6) Component "Recipes" (What things should look like)

The theme intentionally avoids special effects; components are flat boxes with borders and consistent padding.

### 6.1 Section Headings (H2)

For every major section:
- Use H2 for the section title (dark text, not red).
- Spacing: XL above, L below (follow the rhythm values).
- Optional lead line:
  - 1-2 short lines max
  - bold only for the key phrase

### 6.2 Panels (hero, notes, framed blocks)

Panel look:
- Flat box
- Border: `1px solid #BEBEBE`
- Radius: `3px`
- Background: typically `#FFFFFF`
- Padding: theme's "panel pad" is `8px` (use `8px` as default; increase only if needed for readability)
- No shadows

Panel tint variant ("prose box" / highlighted info):
- Background: `#F3F3F3`

### 6.3 Cards (lists/grids of items)

Card look:
- Same as panel, but used inside lists/grids.
- Title uses the H3 rules.
- Keep internal structure consistent:
  - Meta -> Title -> descriptor/excerpt -> action

### 6.4 Meta Bars (compact meta rows)

Meta bar look:
- Muted text: `14px`, line-height `1.4`, muted gray
- Dotted top + bottom borders (`1px dotted #BEBEBE`)
- Padding: ~`8px` vertically
- Layout: flex-like row that wraps on small screens

### 6.5 Lists (must read as lists)

List UX rule:
- Do not render "lists of things" as a paragraph wall.
- Each item should have a consistent internal layout (title + optional meta + optional short line + optional action).
- Use thin dividers between items when the list has multiple entries.
- Item spacing uses S or M spacing values; never random.

### 6.6 Text Actions (lightweight interactive elements)

Text action style:
- Looks like an action but stays lightweight (not a big button).
- Uses link/brand red color.
- Underline on hover/focus is mandatory.
- Place consistently inside cards/lists (typically bottom-left of the item).

### 6.7 Buttons (primary + secondary)

General rules (from theme intent):
- Flat, consistent height
- Radius: `3px`
- No decorative shadows
- Exactly one primary CTA per major section (usually only in the hero)

Primary button:
- Filled with brand red background (`#B51A2C`)
- Text contrast: white

Secondary button:
- Outline style: `1px solid brand red`, neutral background (`#FFFFFF`)
- Use as the secondary choice so it does not compete with the primary CTA.

Button sizing (feel):
- Height around `36-40px`
- Horizontal padding around `12-14px`

### 6.8 Forms (inputs)

Form optics:
- Flat controls: border + white background
- Minimal rounding: `3px`
- Control height should feel similar to buttons (`36-40px`).

Validation:
- Errors must be explicit (use an error text + optionally border change).
- Do not rely on red color alone for error communication.

### 6.9 Tables (compact)

Compact table look:
- Flat framed table container:
  - background: `#FFFFFF`
  - border: `1px solid #BEBEBE`
  - radius: `3px`
  - overflow-x auto for narrow screens
- Cell padding:
  - ~`4px 8px` (XS/S)
  - line-height around `1.45`
- Header row:
  - background: `#F3F3F3`
  - border lines follow meta/divider rules

### 6.10 Callouts / Alerts (tinted panels)

Callouts are flat bordered panels that keep the information dense (no shadow, no big ornaments):
- Base panel:
  - background: `#FFFFFF` (or use `#F3F3F3` when you need a tinted info box)
  - border: `1px solid` border color
  - radius: `3px`

Variants:
- Neutral / info:
  - background: `#F3F3F3`
  - border: `#BEBEBE`
- Warning / attention (brand-red family):
  - background: `#FBB0B9`
  - border: `#B51A2C`
  - text: default `#0E0E0E`
  - links: use link red `#B51A2C` (underline on hover/focus)
- Positive / success (green family):
  - background: `#F1FEEF`
  - border: `#2D6126`
  - text: default `#0E0E0E`

UX rule:
- Start with a short bold label when needed (e.g. "Achtung:" / "Hinweis:") and keep the content to a few lines.

### 6.11 Pagination (for list views)

Pagination controls should look like compact framed buttons:
- Button/link height: `36px`
- Padding: horizontal `8px`
- Border: `1px solid #BEBEBE`
- Radius: `3px`
- Background: `#FFFFFF`
- Text color: `#0E0E0E`

States:
- Current page:
  - background: `#F3F3F3`
  - border color: `#0E0E0E`
  - font-weight: `700`
- Hover/focus:
  - background: `#F3F3F3`
  - border color: `#0E0E0E`
  - underline (matches link rule)

Ellipsis/dots (if used):
- Render as text with no visible framing (borderless), colored muted `#888888`.

### 6.12 Modals & Overlays (app UI)

When you need dialogs (confirmations, edit forms):
- Modal surface: `#FFFFFF`
- Border: `1px solid #BEBEBE`
- Radius: `3px`
- Shadows: avoid (theme is flat); layering should come from border + backdrop opacity.

## 7) UX Rules for the App (FastAPI + Svelte)

Even if your backend/UI differs from WordPress blocks, the UX patterns should stay aligned:

- One primary CTA per section: avoid competing primary actions.
- Dense but scannable: use headings + lists + consistent actions; avoid decorative separators.
- Make state changes obvious:
  - hover/focus states visible
  - active navigation item obvious and consistent
  - focus ring uses the red-family focus color (`#F88492`)
- Keep consistent hierarchy:
  - headings are dark
  - red is for interaction/navigation/actions

## 8) Token Setup Suggestion for Your Other Project

In the other FastAPI + Svelte project, implement design tokens as CSS variables (or a design-token module) using these names/values:
- `--kk-surface: #FFFFFF`
- `--kk-surface-tint: #F3F3F3`
- `--kk-text: #0E0E0E`
- `--kk-muted: #888888`
- `--kk-border: #BEBEBE`
- `--kk-brand: #B51A2C`
- `--kk-brand-hover: #D83A4D`
- `--kk-focus: #F88492`
- `--kk-success-bg: #F1FEEF`
- `--kk-success-border: #2D6126`
- `--kk-radius: 3px`
- `--kk-space-xs: 4px`
- `--kk-space-s: 8px`
- `--kk-space-m: 14px`
- `--kk-space-l: 18px`
- `--kk-space-xl: 24px (or 28px for major sections)`

## 9) Quick "Definition of Done" Checks

Before you call the app "on design":
- Panels/cards share the exact border, radius, and padding logic.
- Headings are consistently dark; red is reserved for nav/actions/links.
- Lists read like lists (consistent item layout + dividers).
- Spacing follows the fixed rhythm (4 / 8 / 14 / 18 / 24-28), not random.
- Hover/focus states are obvious and consistent for links/buttons.

