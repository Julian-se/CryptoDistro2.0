# CryptoDistro 2.0 — Visual Redesign Spec
**Date:** 2026-03-16
**Status:** Approved by user
**Scope:** Full frontend visual overhaul — layout, design tokens, components

---

## Design Direction: Supabase × xAI Hybrid

Supabase's structural discipline (left sidebar, card/table layout, green accent) fused with xAI's dark density and minimal chrome. `#3ECF8E` Supabase green on near-black. The serious operator's tool — data-forward, no decoration that doesn't carry information.

**Inspirations:**
- Supabase dashboard: left sidebar, table-driven data, `#3ECF8E` brand green, clean card borders, breadcrumb topbar
- xAI/Grok: near-black backgrounds, no glow effects, dense tables, Inter + monospace hierarchy, restrained decoration

---

## Design Tokens

### Colors (replaces current palette)

```css
/* Backgrounds */
--bg-base:     #0a0a0a   /* page background */
--bg-surface:  #0d0d0d   /* topbar, sidebar */
--bg-card:     #141414   /* cards, table shells */
--bg-border:   #242424   /* primary borders */
--bg-sub:      #1a1a1a   /* table row dividers, subtle borders */

/* Accent — Supabase green (replaces neon #00ff88) */
--accent-green:        #3ECF8E
--accent-green-dim:    rgba(62, 207, 142, 0.08)
--accent-green-border: rgba(62, 207, 142, 0.20)
--accent-green-glow:   rgba(62, 207, 142, 0.25)   /* live dot only */

/* State colors */
--accent-orange: #F5A623   /* WATCH signal */
--accent-red:    #FF4757   /* AVOID signal */
--accent-blue:   #3B82F6   /* informational */

/* Text */
--text-primary:  #f0f0f0
--text-muted:    #505050
--text-dim:      #333333
```

### Typography

- **UI labels, headings, body:** Inter (already imported)
- **Numeric data, monospace values, badges, timestamps:** JetBrains Mono
- **Rule:** Use Inter everywhere by default. Swap to mono only for numbers, codes, prices, percentages displayed as data values.
- **Remove:** The current heavy mono-everywhere pattern (all labels in monospace). Uppercase tracking labels stay (`text-xs uppercase tracking-wider`) but in Inter.

### Spacing & Shape

- Card border-radius: `6px` (down from `8px` — tighter, more Supabase)
- Border width: `1px solid var(--bg-border)`
- Sidebar width: `220px`
- Topbar height: `44px`
- Content max-width: `100%` within `flex: 1` (no more `max-w-screen-xl` centering — sidebar takes that role)

---

## Layout Structure

### Before (current)
```
┌──────────────────────────────────┐
│  Navbar (top, sticky, full-width)│
├──────────────────────────────────┤
│  max-w-screen-xl centered content│
└──────────────────────────────────┘
```

### After (new)
```
┌─────────────────────────────────────────────┐
│  Topbar (44px): Logo │ Breadcrumb │ Status   │
├────────────┬────────────────────────────────┤
│  Sidebar   │  Main content (flex: 1)        │
│  220px     │  padding: 20px                 │
│  sticky    │                                │
│  full-h    │                                │
└────────────┴────────────────────────────────┘
```

### `layout.tsx` target shell structure

```tsx
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-bg-base text-text-primary h-screen flex flex-col overflow-hidden">
        {/* Topbar — fixed height row */}
        <Topbar />  {/* or inline — see Sidebar.tsx note */}

        {/* Below topbar: sidebar + scrollable content */}
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />   {/* 220px, sticky, full-height, overflow-y-auto */}
          <main className="flex-1 overflow-y-auto p-5">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
```

`Topbar` and `Sidebar` are both exported from `Sidebar.tsx` (one file, two named exports). The `<body>` is `flex flex-col h-screen overflow-hidden`. The inner `<div>` is `flex flex-1 overflow-hidden`. `<main>` is `flex-1 overflow-y-auto` so only the content area scrolls — sidebar stays fixed.

### Topbar
- Left: Logo zone (220px, matches sidebar width, right-bordered) — `₿` icon + "CryptoDistro" wordmark
- Centre: Breadcrumb — `Page / Subpage` in muted → active text
- Right: Live status dot + "LIVE"/"OFFLINE" label

### Sidebar (220px, sticky)
- Section label: "OPERATOR" (7px uppercase, dim)
- Nav items: Lucide icon (16px) + label + optional badge
- Active state: `bg-accent-green-dim`, `border: 1px solid accent-green-border`, label in accent green
- Divider then **Capital block**: "NOONES CAPITAL" label → big `$XXX` value → BTC sub → progress bar

#### Lucide icon mapping
| Page | Icon |
|---|---|
| Overview | `LayoutDashboard` |
| Analytics | `TrendingUp` |
| Refill | `Zap` |
| Simulation | `FlaskConical` |
| System | `Activity` |

#### Badge
Active `ACT_NOW` market count shown as a small green pill on Overview nav item.

---

## Component Designs

### MetricTile
```
┌─────────────────┐
│ AVG PREMIUM      │  ← 7px Inter uppercase, --text-muted
│ +10.8%           │  ← 14px JetBrains Mono bold, accent-green
│ 30-day average   │  ← 7px Inter, --text-muted  (optional)
└─────────────────┘
bg: --bg-card, border: 1px --bg-border, radius: 6px, padding: 10px
```

### Market Table (Dashboard main content)
```
┌─────────────────────────────────────────────────────────┐
│ Market Signals                              3 active    │  ← table header row
├─────────┬──────────┬────────┬────────┬─────────┬───────┤
│ Market  │ Premium  │ Margin │ FX Rate│ Methods │ Signal│  ← th: 7px uppercase
├─────────┼──────────┼────────┼────────┼─────────┼───────┤
│🇳🇬 NGN  │ +8.4%   │  7.2%  │  1,587 │ [pills] │ ACT   │
│🇦🇷 ARS  │ +11.2%  │  9.0%  │    934 │ [pills] │ ACT   │
│ ...     │          │        │        │         │       │
└─────────┴──────────┴────────┴────────┴─────────┴───────┘
```
- Wrapper: `bg-card`, `border`, `radius: 6px`, overflow hidden
- Header row: `padding: 9px 12px`, border-bottom
- `th`: 7px Inter uppercase, `--text-muted`
- `td`: 8–9px, row hover `rgba(255,255,255,0.015)`, row divider `--bg-sub`
- Premium column: `--accent-green` for positive, `--text-muted` for low/negative
- Signal badge: `ACT NOW` (green), `WATCH` (orange), `AVOID` (red)
- Payment method pills: small, `accent-green-dim` bg, accent border

### Analytics Page Layout
```
Page title + period tabs (7d / 30d / 90d)
5-tile metric row
2×2 chart card grid:
  [Capital Growth area chart]  [Daily P&L bar chart    ]
  [Premium by Market h-bars ]  [90-Day Forecast area   ]
```
- Chart cards: `bg-card`, border, radius 6px, padding 10px
- Chart header: metric name (8px uppercase muted) + current value (12px mono bold)
- Area fill: `rgba(62,207,142,0.15)` under line, `#3ECF8E` stroke 1.5px
- Bar charts: `#3ECF8E` with `opacity` varied by value
- Axes: `--bg-sub` lines, `--text-dim` labels

### Refill Page
- Keep the `MethodCard` structure but reskin to new tokens
- `PipelineFlow` steps: token colors align to new palette (orange fiat, purple LN, green Noones)
- Remove neon glows from step nodes

### Sidebar Capital Block
```
NOONES CAPITAL          ← 7px uppercase dim
$500                    ← 19px mono bold, accent-green
0.00594 BTC · noones    ← 7px mono, muted
████░░░░░░░░            ← 2px progress bar, accent-green fill
```

---

## Removed Elements

- **3D FlowViz** (React Three Fiber `FlowViz` component): Remove from Dashboard. Adds heavy JS bundle, conflicts with data-forward aesthetic. Can be retained as a hidden easter egg or fully deleted.
- **Neon glow effects** (`.glow-green`, `.glow-orange`, `.text-glow-green`): Remove from globals.css. Replace with Supabase-style subtle box-shadow on focus states only.
- **Badge utility classes** (`.badge-act-now`, `.badge-watch`, `.badge-avoid`, `.badge-data-issue`): Rewrite in globals.css to use `var(--accent-green)` etc. instead of raw hex strings (`#00ff88`, `#ff8c00`, `#ff3366`). Otherwise these classes will not pick up the new palette.
- **Grid pattern background** (`.bg-grid`): Remove. Replace with flat `--bg-base`.
- **All-monospace labels**: Labels revert to Inter. Mono reserved for values only.
- **`animate-pulse-slow` on decorative elements**: Keep only on the live status dot.
- **`accent-green: #00ff88`**: Replaced by `#3ECF8E`.

---

## Files to Create / Modify

### New files
- `frontend/components/layout/Sidebar.tsx` — replaces `Navbar.tsx`
  - **Must be `'use client'`** — uses `usePathname()` for active nav state and `useWebSocket()` for the live status dot. Export two named components: `Topbar` and `Sidebar`.

### Modified files
| File | Change |
|---|---|
| `frontend/tailwind.config.js` | New color tokens |
| `frontend/app/globals.css` | New CSS variables, remove glow/grid |
| `frontend/app/layout.tsx` | Sidebar layout replacing top-nav layout |
| `frontend/components/layout/Navbar.tsx` | Delete or keep as dead code |
| `frontend/components/shared/Card.tsx` | Updated border-radius, tokens |
| `frontend/app/page.tsx` | Remove FlowViz, add `MarketTable` |
| `frontend/components/dashboard/MarketCard.tsx` | Delete (replaced by table) |
| `frontend/components/dashboard/BalancePanel.tsx` | Move capital into sidebar; delete or repurpose |
| `frontend/app/analytics/page.tsx` | 2×2 chart grid, period tabs |
| `frontend/app/refill/page.tsx` | Reskin tokens only |
| `frontend/app/simulation/page.tsx` | Reskin tokens only |
| `frontend/app/observability/page.tsx` | Reskin tokens only |
| `frontend/components/dashboard/ControllerPanel.tsx` | Reskin tokens only (uses accent-orange/red/blue) |
| `frontend/components/dashboard/IntelligenceChat.tsx` | Reskin tokens only |

### New component
- `frontend/components/dashboard/MarketTable.tsx` — table-based market display

---

## Migration Notes

### Token synchronisation — both files must be updated together
The project uses **two parallel token systems**: CSS variables in `globals.css` and Tailwind color keys in `tailwind.config.js`. Components use Tailwind utilities (`text-text-muted`, `bg-bg-card`) not raw CSS variables, so the Tailwind config is the ground truth for utilities. Both must be kept in sync.

Full `tailwind.config.js` color block after migration:
```js
colors: {
  bg: {
    base:    '#0a0a0a',
    surface: '#0d0d0d',
    card:    '#141414',
    border:  '#242424',
    sub:     '#1a1a1a',   // NEW — table row dividers
    hover:   '#1c1c1c',   // keep for interactive hover states
  },
  accent: {
    green:          '#3ECF8E',               // was #00ff88
    'green-dim':    'rgba(62,207,142,0.08)', // sidebar active bg, pill bg
    'green-border': 'rgba(62,207,142,0.20)', // sidebar active border, pill border
    'green-glow':   'rgba(62,207,142,0.25)', // live status dot only
    orange:         '#F5A623',               // was #ff8c00
    red:            '#FF4757',               // was #ff3366
    blue:           '#3B82F6',               // was #0088ff
    purple:         '#8844ff',               // unchanged
  },
  text: {
    primary:   '#f0f0f0',
    secondary: '#8888aa',  // keep for legacy uses
    muted:     '#505050',  // was #555577
    dim:       '#333333',  // NEW
  },
}
```

### Other notes
- `lucide-react` is already in `package.json` — no install needed.
- `FlowViz` can be deleted — only caller is `app/page.tsx`. Remove `@react-three/fiber`, `@react-three/drei`, `three` from `package.json` at the same time to save ~500 KB bundle.
- `accent-green` rename from `#00ff88` → `#3ECF8E` flows automatically to all Tailwind utilities. No per-component find/replace needed for green — only for orange/red if any component hardcodes old hex values.
