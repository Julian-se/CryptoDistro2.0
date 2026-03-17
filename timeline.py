"""
CryptoDistro 2.0 — Build Timeline
Scientific visualization using matplotlib + numpy
Reconstructed from file system timestamps (no git repo available)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.gridspec as gridspec
import numpy as np
from datetime import datetime, timedelta

# ── Design tokens (matches the app's Supabase × xAI palette) ──────────────────
BG_BASE    = '#0a0a0a'
BG_CARD    = '#141414'
BG_BORDER  = '#242424'
BG_SUB     = '#1a1a1a'
GREEN      = '#3ECF8E'
GREEN_DIM  = '#1a4a35'
ORANGE     = '#F5A623'
RED        = '#FF4757'
BLUE       = '#3B82F6'
PURPLE     = '#8844ff'
TEXT_PRI   = '#f0f0f0'
TEXT_MUT   = '#505050'
TEXT_DIM   = '#333333'
TEXT_SEC   = '#8888aa'

# ── Timeline data ──────────────────────────────────────────────────────────────
# Each phase: (label, start_datetime, end_datetime, color, description)
PHASES = [
    (
        "Research & PDF\nAnalysis",
        datetime(2026, 3, 13, 11, 0),
        datetime(2026, 3, 13, 14, 0),
        BLUE,
        "Grok AI report\nP2P trading overview\nFirst BTC simulator HTML"
    ),
    (
        "Architecture v1\n& Scripts",
        datetime(2026, 3, 13, 14, 0),
        datetime(2026, 3, 13, 20, 30),
        PURPLE,
        "src/ scaffold\nLightning connectors (lnd, boltz)\nOrchestrator, spread scanner\nstart.sh"
    ),
    (
        "Business Model\nPivot → P2P On/Off-Ramp",
        datetime(2026, 3, 14, 15, 0),
        datetime(2026, 3, 14, 17, 45),
        ORANGE,
        "Emerging markets simulators\nbluepring.md architecture\nBinance + FX connectors\npremium_monitor, market_discovery"
    ),
    (
        "Backend API\n+ Frontend v1",
        datetime(2026, 3, 15, 15, 0),
        datetime(2026, 3, 15, 18, 0),
        GREEN,
        "FastAPI backend scaffold\nNext.js 14 frontend\nWebSocket hooks\nAll 5 pages built"
    ),
    (
        "Refill Page\n+ Bug Fixes",
        datetime(2026, 3, 16, 7, 0),
        datetime(2026, 3, 16, 9, 5),
        RED,
        "refill/page.tsx\nNoones connector\nSchema fixes\nAPI key integration"
    ),
    (
        "Visual Redesign\n(Supabase × xAI)",
        datetime(2026, 3, 16, 9, 5),
        datetime(2026, 3, 16, 11, 45),
        GREEN,
        "Brainstorm → spec → plan\nTailwind tokens\nSidebar layout\nAll 9 tasks in 65 min"
    ),
    (
        "Live — DB Active",
        datetime(2026, 3, 17, 0, 0),
        datetime(2026, 3, 17, 20, 0),
        GREEN,
        "Backend running :8000\nSQLite DB writes\nLive market scanning"
    ),
]

# ── Key milestones ─────────────────────────────────────────────────────────────
MILESTONES = [
    (datetime(2026, 3, 13, 11, 19), "btc_p2p_arbitrage_simulator.html\ncreated — project genesis", BLUE),
    (datetime(2026, 3, 13, 14, 24), "src/ directory\nscaffolded", PURPLE),
    (datetime(2026, 3, 14, 15, 59), "blueprint.md written\n(full architecture)", ORANGE),
    (datetime(2026, 3, 15, 16, 51), "backend/ created\n(FastAPI)", GREEN),
    (datetime(2026, 3, 15, 17, 16), "Next.js frontend\ninitialized", GREEN),
    (datetime(2026, 3, 16, 7, 59), "refill page\n+ noones.py", RED),
    (datetime(2026, 3, 16, 10, 38), "Design spec\ncommitted", ORANGE),
    (datetime(2026, 3, 16, 11, 43), "Visual redesign\ncomplete ✓", GREEN),
    (datetime(2026, 3, 17, 19, 58), "DB live, trades\nbeing tracked", GREEN),
]

# ── Setup figure ───────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 13), facecolor=BG_BASE)
gs = gridspec.GridSpec(
    3, 1,
    height_ratios=[0.08, 0.72, 0.20],
    hspace=0.04,
    figure=fig,
)

# ─ Title panel ────────────────────────────────────────────────────────────────
ax_title = fig.add_subplot(gs[0])
ax_title.set_facecolor(BG_BASE)
ax_title.axis('off')
ax_title.text(
    0.02, 0.55, 'CryptoDistro 2.0',
    transform=ax_title.transAxes,
    fontsize=22, fontweight='bold', color=TEXT_PRI,
    fontfamily='monospace', va='center'
)
ax_title.text(
    0.02, 0.05, 'Build Timeline  ·  Mar 13 → Mar 17, 2026  ·  Reconstructed from filesystem timestamps',
    transform=ax_title.transAxes,
    fontsize=10, color=TEXT_SEC, va='center'
)
# Stats in header right side
stats = [
    ("5 days", "Elapsed calendar time"),
    ("~9.5 hrs", "Active build time"),
    ("7 phases", "Dev phases"),
    ("65 min", "Full redesign sprint"),
]
for i, (val, lbl) in enumerate(stats):
    x = 0.55 + i * 0.115
    ax_title.text(x, 0.72, val, transform=ax_title.transAxes,
                  fontsize=14, fontweight='bold', color=GREEN, fontfamily='monospace')
    ax_title.text(x, 0.18, lbl, transform=ax_title.transAxes,
                  fontsize=8, color=TEXT_MUT)

# ─ Gantt chart ────────────────────────────────────────────────────────────────
ax = fig.add_subplot(gs[1])
ax.set_facecolor(BG_CARD)
for spine in ax.spines.values():
    spine.set_color(BG_BORDER)

# Time axis bounds
t_start = datetime(2026, 3, 13, 10, 0)
t_end   = datetime(2026, 3, 17, 22, 0)

def to_hours(dt):
    return (dt - t_start).total_seconds() / 3600

total_hours = to_hours(t_end)

# Day separators
day_boundaries = [
    datetime(2026, 3, 14, 0, 0),
    datetime(2026, 3, 15, 0, 0),
    datetime(2026, 3, 16, 0, 0),
    datetime(2026, 3, 17, 0, 0),
]
for db in day_boundaries:
    ax.axvline(to_hours(db), color=BG_BORDER, lw=1.2, zorder=1)

# Day labels at top
day_labels = [
    (datetime(2026, 3, 13, 10, 0), "Mar 13"),
    (datetime(2026, 3, 14, 0, 0),  "Mar 14"),
    (datetime(2026, 3, 15, 0, 0),  "Mar 15"),
    (datetime(2026, 3, 16, 0, 0),  "Mar 16"),
    (datetime(2026, 3, 17, 0, 0),  "Mar 17"),
]
for dt, lbl in day_labels:
    ax.text(to_hours(dt) + 0.3, len(PHASES) + 0.1, lbl,
            fontsize=9, color=TEXT_SEC, fontfamily='monospace', va='bottom')

# Phase bars
bar_height  = 0.62
bar_gap     = 0.38
y_positions = list(range(len(PHASES)))

for i, (label, start, end, color, desc) in enumerate(PHASES):
    y    = i
    x0   = to_hours(start)
    dur  = to_hours(end) - x0

    # Glow / shadow behind main bar
    shadow = FancyBboxPatch(
        (x0 - 0.05, y - bar_height/2 - 0.05),
        dur + 0.10, bar_height + 0.10,
        boxstyle="round,pad=0.0",
        linewidth=0, facecolor=color, alpha=0.12,
        zorder=2,
    )
    ax.add_patch(shadow)

    # Main bar
    bar = FancyBboxPatch(
        (x0, y - bar_height/2),
        dur, bar_height,
        boxstyle="round,pad=0.0",
        linewidth=1.2, edgecolor=color,
        facecolor=BG_SUB, alpha=1.0,
        zorder=3,
    )
    ax.add_patch(bar)

    # Left accent stripe
    stripe = FancyBboxPatch(
        (x0, y - bar_height/2),
        min(0.25, dur * 0.08), bar_height,
        boxstyle="round,pad=0.0",
        linewidth=0, facecolor=color, alpha=0.85,
        zorder=4,
    )
    ax.add_patch(stripe)

    # Duration label inside bar (if wide enough)
    duration_hrs = (end - start).total_seconds() / 3600
    if duration_hrs >= 1.0:
        dur_text = f"{duration_hrs:.1f}h" if duration_hrs < 24 else f"{duration_hrs/24:.1f}d"
        ax.text(x0 + dur - 0.2, y, dur_text,
                fontsize=8, color=color, fontfamily='monospace',
                ha='right', va='center', zorder=5, alpha=0.9)

    # Phase label (left of bar — y-axis labels)
    ax.text(-0.5, y, label,
            fontsize=9, color=TEXT_PRI, ha='right', va='center',
            fontweight='bold', multialignment='right')

    # Description text (below bar — subtle)
    ax.text(x0 + 0.25 + min(0.3, dur * 0.10), y - bar_height/2 - 0.05, desc,
            fontsize=7.2, color=TEXT_SEC, va='top', ha='left',
            multialignment='left', zorder=5,
            style='italic')

# Milestone markers
milestone_y = len(PHASES) + 0.7
for dt, label, color in MILESTONES:
    x = to_hours(dt)
    # Diamond marker
    ax.plot(x, milestone_y, marker='D', markersize=7,
            color=color, zorder=8, markeredgecolor=BG_BASE, markeredgewidth=1)
    # Drop line
    ax.plot([x, x], [0 - bar_height/2 - 0.05, milestone_y - 0.25],
            color=color, lw=0.6, alpha=0.35, zorder=6, linestyle='--')
    # Label alternating above/below to avoid overlap
    ax.text(x, milestone_y + 0.25, label,
            fontsize=7, color=color, ha='center', va='bottom',
            multialignment='center', rotation=0, zorder=9)

# "NOW" marker
now_x = to_hours(datetime(2026, 3, 17, 20, 0))
ax.axvline(now_x, color=GREEN, lw=1.5, linestyle=':', alpha=0.6, zorder=7)
ax.text(now_x + 0.1, -0.55, 'NOW\nMar 17', fontsize=7.5,
        color=GREEN, fontfamily='monospace', va='top')

# Axis formatting
ax.set_xlim(-12, total_hours + 1)
ax.set_ylim(-0.85, len(PHASES) + 1.8)
ax.set_yticks([])
ax.set_xticks([])
ax.tick_params(colors=TEXT_MUT)

# Hour ticks along bottom
tick_interval = 6  # every 6 hours
for h in range(0, int(total_hours) + 1, tick_interval):
    t = t_start + timedelta(hours=h)
    ax.axvline(h, color=BG_BORDER, lw=0.4, alpha=0.4, zorder=1)
    ax.text(h, -0.75, t.strftime('%H:%M'), fontsize=6.5,
            color=TEXT_DIM, ha='center', fontfamily='monospace')

# ─ Stats bar ──────────────────────────────────────────────────────────────────
ax_stats = fig.add_subplot(gs[2])
ax_stats.set_facecolor(BG_BASE)
ax_stats.axis('off')

# Horizontal timeline summary bar
phases_summary = [
    ("Research\n& PDFs", 3.0,  BLUE),
    ("Scripts v1\n& Scaffold", 6.5, PURPLE),
    ("Business\nModel Pivot", 2.75, ORANGE),
    ("Backend +\nFrontend v1", 3.0, GREEN),
    ("Refill +\nBug Fixes", 2.08, RED),
    ("Visual\nRedesign", 2.67, GREEN),
    ("Live\nTrading", 20.0, GREEN),
]

total_w = sum(w for _, w, _ in phases_summary)
x_cursor = 0.0

for name, w, color in phases_summary:
    frac = w / total_w
    rect = FancyBboxPatch(
        (x_cursor + 0.003, 0.38), frac - 0.006, 0.38,
        boxstyle="round,pad=0.0",
        linewidth=1, edgecolor=color,
        facecolor=color + '22',
        transform=ax_stats.transAxes, zorder=3
    )
    ax_stats.add_patch(rect)
    ax_stats.text(
        x_cursor + frac / 2, 0.57, name,
        transform=ax_stats.transAxes,
        fontsize=7.5, color=color, ha='center', va='center',
        fontweight='bold', multialignment='center'
    )
    # Width label
    hrs_lbl = f"{w:.0f}h" if w >= 1 else f"{w*60:.0f}m"
    ax_stats.text(
        x_cursor + frac / 2, 0.32, hrs_lbl,
        transform=ax_stats.transAxes,
        fontsize=7, color=TEXT_MUT, ha='center', va='top',
        fontfamily='monospace'
    )
    x_cursor += frac

# Bottom credits
ax_stats.text(
    0.5, 0.05,
    'CryptoDistro 2.0  ·  P2P Bitcoin on/off-ramp operator dashboard  ·  '
    'Reconstructed from filesystem timestamps  ·  No git history available',
    transform=ax_stats.transAxes, fontsize=7.5, color=TEXT_DIM,
    ha='center', va='bottom'
)

# ─ Save ───────────────────────────────────────────────────────────────────────
output = '/home/ironman/CryptoDistro2.0/build_timeline.png'
plt.savefig(output, dpi=180, bbox_inches='tight',
            facecolor=BG_BASE, edgecolor='none')
print(f"Saved → {output}")
