"""
CryptoDistro 2.0 — Build Timeline
Scientific visualization using matplotlib + numpy
Reconstructed from file system timestamps (no git repo available)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import numpy as np
from datetime import datetime, timedelta

# ── Design tokens ──────────────────────────────────────────────────────────────
BG_BASE  = '#0a0a0a'
BG_CARD  = '#141414'
BG_BORDER= '#242424'
BG_SUB   = '#1a1a1a'
GREEN    = '#3ECF8E'
ORANGE   = '#F5A623'
RED      = '#FF4757'
BLUE     = '#3B82F6'
PURPLE   = '#8844ff'
TEXT_PRI = '#f0f0f0'
TEXT_MUT = '#505050'
TEXT_DIM = '#333333'
TEXT_SEC = '#8888aa'

# ── Phase data ─────────────────────────────────────────────────────────────────
PHASES = [
    ("Research & PDF Analysis",        datetime(2026,3,13,11, 0), datetime(2026,3,13,14, 0), BLUE,   "Grok AI report · P2P trading overview · First simulator HTML"),
    ("Architecture v1 & Scripts",      datetime(2026,3,13,14, 0), datetime(2026,3,13,20,30), PURPLE, "Lightning node · swap connector · orchestrator · spread scanner"),
    ("Business Model Pivot",           datetime(2026,3,14,15, 0), datetime(2026,3,14,17,45), ORANGE, "Emerging markets research · blueprint.md · Binance + FX connectors"),
    ("Backend API + Frontend v1",      datetime(2026,3,15,15, 0), datetime(2026,3,15,18, 0), GREEN,  "FastAPI · Next.js 14 · WebSocket hooks · All 5 pages built"),
    ("Refill Page + Bug Fixes",        datetime(2026,3,16, 7, 0), datetime(2026,3,16, 9, 5), RED,    "refill/page.tsx · Noones connector · Schema fixes"),
    ("Visual Redesign (Supabase×xAI)", datetime(2026,3,16, 9, 5), datetime(2026,3,16,11,45), GREEN,  "Brainstorm → spec → plan → 9 tasks executed in 65 min"),
    ("Live — DB Active",               datetime(2026,3,17, 0, 0), datetime(2026,3,17,20, 0), GREEN,  "FastAPI :8000 · SQLite active · scanner on"),
]

# ── Milestone data ─────────────────────────────────────────────────────────────
MILESTONES = [
    (datetime(2026,3,13,11,19), "Project genesis\nbtc_p2p simulator.html",  BLUE),
    (datetime(2026,3,13,14,24), "src/ scaffolded\nLightning connectors",    PURPLE),
    (datetime(2026,3,14,15,59), "blueprint.md written\nFull architecture",  ORANGE),
    (datetime(2026,3,15,16,51), "backend/ created\nFastAPI scaffold",       GREEN),
    (datetime(2026,3,15,17,16), "Next.js frontend\ninitialized",            GREEN),
    (datetime(2026,3,16, 7,59), "Refill page\n+ noones.py",                 RED),
    (datetime(2026,3,16,10,38), "Design spec\ncommitted",                   ORANGE),
    (datetime(2026,3,16,11,43), "Visual redesign\ncomplete ✓",              GREEN),
    (datetime(2026,3,17,19,58), "DB live\ntrades tracked",                  GREEN),
]

# ── Time helpers ───────────────────────────────────────────────────────────────
T_START = datetime(2026,3,13,10,0)
T_END   = datetime(2026,3,17,22,0)

def hrs(dt):
    return (dt - T_START).total_seconds() / 3600

TOTAL_HRS = hrs(T_END)

# ── Stagger algorithm — assign each milestone to least-recently-used level ─────
N_LEVELS  = 3
MIN_GAP   = 4.0   # minimum hours before reusing same level

def assign_stagger_levels(milestones):
    last_x = [-999.0] * N_LEVELS
    levels = []
    for dt, *_ in milestones:
        x = hrs(dt)
        # pick level with greatest x-distance from current position
        best = max(range(N_LEVELS), key=lambda l: x - last_x[l])
        levels.append(best)
        last_x[best] = x
    return levels

STAGGER_LEVELS = assign_stagger_levels(MILESTONES)
LEVEL_OFFSETS  = [0.55, 1.35, 2.15]   # y-offsets above milestone_base_y

# ── Figure layout ──────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(22, 16), facecolor=BG_BASE)
gs  = gridspec.GridSpec(3, 1, height_ratios=[0.07, 0.75, 0.18],
                        hspace=0.03, figure=fig)

# ─ Title ──────────────────────────────────────────────────────────────────────
ax_title = fig.add_subplot(gs[0])
ax_title.set_facecolor(BG_BASE)
ax_title.axis('off')
ax_title.text(0.02, 0.60, 'CryptoDistro 2.0',
              transform=ax_title.transAxes,
              fontsize=22, fontweight='bold', color=TEXT_PRI, fontfamily='monospace')
ax_title.text(0.02, 0.08,
              'Build Timeline  ·  Mar 13 → Mar 17, 2026  ·  Reconstructed from filesystem timestamps',
              transform=ax_title.transAxes, fontsize=10, color=TEXT_SEC)
stats = [("5 days","Elapsed"), ("~9.5 hrs","Active build"), ("7 phases","Dev phases"), ("65 min","Redesign sprint")]
for i,(val,lbl) in enumerate(stats):
    x = 0.56 + i*0.11
    ax_title.text(x, 0.75, val, transform=ax_title.transAxes,
                  fontsize=14, fontweight='bold', color=GREEN, fontfamily='monospace')
    ax_title.text(x, 0.12, lbl, transform=ax_title.transAxes,
                  fontsize=8, color=TEXT_MUT)

# ─ Gantt ──────────────────────────────────────────────────────────────────────
ax = fig.add_subplot(gs[1])
ax.set_facecolor(BG_CARD)
for spine in ax.spines.values():
    spine.set_color(BG_BORDER)

# Day separators + labels
for dt in [datetime(2026,3,d,0,0) for d in [14,15,16,17]]:
    ax.axvline(hrs(dt), color=BG_BORDER, lw=1.2, zorder=1)
for day in [13,14,15,16,17]:
    dt  = datetime(2026,3,day,0,0)
    lbl = f"Mar {day}"
    x   = hrs(dt) if day > 13 else 0
    ax.text(x + 0.4, len(PHASES) + 3.6, lbl,
            fontsize=9, color=TEXT_SEC, fontfamily='monospace')

# ── Phase bars ─────────────────────────────────────────────────────────────────
BAR_H = 0.58

for i, (label, start, end, color, desc) in enumerate(PHASES):
    y  = i
    x0 = hrs(start)
    dw = hrs(end) - x0
    dur_h = (end - start).total_seconds() / 3600

    # Glow halo
    ax.add_patch(FancyBboxPatch((x0-0.08, y-BAR_H/2-0.08), dw+0.16, BAR_H+0.16,
        boxstyle="round,pad=0", linewidth=0, facecolor=color, alpha=0.10, zorder=2))
    # Main bar
    ax.add_patch(FancyBboxPatch((x0, y-BAR_H/2), dw, BAR_H,
        boxstyle="round,pad=0", linewidth=1.2, edgecolor=color,
        facecolor=BG_SUB, alpha=1.0, zorder=3))
    # Left accent stripe
    ax.add_patch(FancyBboxPatch((x0, y-BAR_H/2), min(0.3, dw*0.07), BAR_H,
        boxstyle="round,pad=0", linewidth=0, facecolor=color, alpha=0.85, zorder=4))

    # Duration label — top-right corner of bar, clear of description text
    if dur_h >= 1.0:
        dur_txt = f"{dur_h:.0f}h" if dur_h < 24 else f"{dur_h/24:.0f}d"
        ax.text(x0 + dw - 0.2, y + BAR_H/2 - 0.04, dur_txt,
                fontsize=8, color=color, fontfamily='monospace',
                ha='right', va='top', zorder=6, alpha=0.9)

    # Phase name drawn via ytick labels below — skip inline text

    # One-line description inside bar (only if bar is wide enough)
    if dw > 3.0:
        txt_x = x0 + min(0.5, dw*0.08) + 0.5
        # For the rightmost bar, anchor text from left with hard right clip
        ax.text(txt_x, y, desc,
                fontsize=7.8, color='#b0b0c8', ha='left', va='center',
                style='italic', zorder=5, clip_on=True,
                wrap=False)

# ── Milestones — staggered labels ──────────────────────────────────────────────
base_y = len(PHASES) + 0.5

for idx, ((dt, label, color), level) in enumerate(zip(MILESTONES, STAGGER_LEVELS)):
    x      = hrs(dt)
    lbl_y  = base_y + LEVEL_OFFSETS[level]

    # Vertical connector from bar area up to diamond
    ax.plot([x, x], [BAR_H*0.5, base_y - 0.15],
            color=color, lw=0.5, alpha=0.25, linestyle='--', zorder=5)

    # Connector from diamond up to label
    ax.plot([x, x], [base_y + 0.12, lbl_y - 0.18],
            color=color, lw=0.7, alpha=0.45, zorder=6)

    # Diamond marker
    ax.plot(x, base_y, marker='D', markersize=7,
            color=color, zorder=8, markeredgecolor=BG_BASE, markeredgewidth=1.2)

    # Label background box
    bbox_props = dict(boxstyle='round,pad=0.3', facecolor=BG_CARD,
                      edgecolor=color, alpha=0.92, linewidth=0.8)
    ax.text(x, lbl_y, label,
            fontsize=7.5, color=color, ha='center', va='bottom',
            multialignment='center', zorder=9, bbox=bbox_props)

# NOW marker
now_x = hrs(datetime(2026,3,17,20,0))
ax.axvline(now_x, color=GREEN, lw=1.5, linestyle=':', alpha=0.5, zorder=7)
ax.text(now_x + 0.2, -0.6, 'NOW', fontsize=8, color=GREEN,
        fontfamily='monospace', va='top', fontweight='bold')

# Hour ticks
for h in range(0, int(TOTAL_HRS)+1, 6):
    t = T_START + timedelta(hours=h)
    ax.axvline(h, color=BG_BORDER, lw=0.4, alpha=0.35, zorder=1)
    ax.text(h, -0.75, t.strftime('%H:%M'), fontsize=6.5,
            color=TEXT_DIM, ha='center', fontfamily='monospace')

ax.set_xlim(-1, TOTAL_HRS + 3)
ax.set_ylim(-0.9, len(PHASES) + LEVEL_OFFSETS[-1] + 1.6)
# Y-axis tick labels — proper matplotlib way, sits outside the grey box
ax.set_yticks(range(len(PHASES)))
ax.set_yticklabels([p[0] for p in PHASES],
                   fontsize=9.5, color=TEXT_PRI, fontweight='bold')
ax.tick_params(axis='y', length=0, pad=10, colors=TEXT_PRI)
ax.set_xticks([])

# ─ Summary bar ────────────────────────────────────────────────────────────────
ax_s = fig.add_subplot(gs[2])
ax_s.set_facecolor(BG_BASE)
ax_s.axis('off')

summary = [
    ("Research\n& PDFs",      3.0,  BLUE),
    ("Scripts v1\n& Scaffold",6.5,  PURPLE),
    ("Business\nPivot",       2.75, ORANGE),
    ("Backend +\nFrontend",   3.0,  GREEN),
    ("Refill +\nFixes",       2.08, RED),
    ("Visual\nRedesign",      2.67, GREEN),
    ("Live\nTrading",         20.0, GREEN),
]
total_w = sum(w for _,w,_ in summary)
x_cur   = 0.0
for name, w, color in summary:
    frac = w / total_w
    ax_s.add_patch(FancyBboxPatch(
        (x_cur+0.003, 0.35), frac-0.006, 0.42,
        boxstyle="round,pad=0", linewidth=1, edgecolor=color,
        facecolor=color+'22', transform=ax_s.transAxes, zorder=3))
    ax_s.text(x_cur+frac/2, 0.57, name,
              transform=ax_s.transAxes, fontsize=7.5, color=color,
              ha='center', va='center', fontweight='bold', multialignment='center')
    hrs_lbl = f"{w:.0f}h" if w >= 1 else f"{w*60:.0f}m"
    ax_s.text(x_cur+frac/2, 0.28, hrs_lbl,
              transform=ax_s.transAxes, fontsize=7, color=TEXT_MUT,
              ha='center', va='top', fontfamily='monospace')
    x_cur += frac

ax_s.text(0.5, 0.04,
          'CryptoDistro 2.0  ·  P2P Bitcoin on/off-ramp  ·  Reconstructed from filesystem timestamps',
          transform=ax_s.transAxes, fontsize=7.5, color=TEXT_DIM, ha='center')

# ─ Save ───────────────────────────────────────────────────────────────────────
out = '/home/ironman/CryptoDistro2.0/build_timeline.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=BG_BASE, edgecolor='none')
print(f"Saved → {out}")
