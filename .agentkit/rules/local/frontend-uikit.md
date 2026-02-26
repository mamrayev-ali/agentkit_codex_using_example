# Frontend UI Kit Rules (local)

These rules are mandatory for upcoming UI implementation tickets in this repository.

## 1) Colors and design tokens
- Do not use hardcoded colors in components/styles.
- Allowed color sources:
  - `var(--color-...)`
  - `var(--brand-...)`
  - `var(--neutral-...)`
- Avoid `#hex`, `rgb(...)`, `hsl(...)`, and named colors unless mapped to token declarations first.

## 2) Main layout
- Desktop layout must use:
  - sidebar
  - sticky header
- Mobile layout must use:
  - no sidebar
  - filters in a drawer/panel

## 3) Registry view modes
- `default` mode: cards view.
- `alternate` mode: table view.
- A view-mode switcher is required in the registry UI.

## 4) Tool card content (required)
- title
- category / task type badge
- short description
- model / provider
- last updated
- CTA actions:
  - open details
  - edit

## 5) Tool details page structure
- top hero block
- right-side meta panel
- tabs below:
  - `overview`
  - `prompts`
  - `policy`
  - `integrations`
  - `history`

## 6) Dashboard structure
- top: stats cards
- middle: charts inside `chart-card`
- bottom: sections for:
  - recent changes
  - top used tools
  - gaps

## 7) Forms
- label above input
- hint below field
- errors use semantic token color only + short text
- primary CTA aligned to bottom-right of the form

## 8) Tables
- sticky header
- row hover state
- selected-row state
- mobile behavior:
  - horizontal scroll
  - do not auto-convert into cards unless explicitly required
