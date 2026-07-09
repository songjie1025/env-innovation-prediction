"""Methodology-chapter schematic figures.

Two presentation-oriented figures that visualise the *modeling design* (the data
processing itself is visualised in the Data chapter):

* ``fig_model_pipeline`` -- the end-to-end modeling pipeline, from the final panel
  through the leakage-safe split, the model families, the single test evaluation,
  and the robustness / fair-test layer.
* ``fig_eval_timeline``  -- the chronological 80/10/10 split and the six-fold
  expanding-window rolling-origin backtest, on a real 1999–2023 year axis.

All numbers are taken from the fixed modeling configuration and the committed
rolling-origin summary (``linear_model_rolling_origin_summary.csv``).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

C_BG = "#FAFAFA"
C_INK = "#2D3748"
C_MUTED = "#718096"

# stage palette
C_PANEL = "#2D6A9F"   # blue   -- data
C_SPLIT = "#5F7FA5"   # slate  -- split
C_MODEL = "#5F9C6B"   # green  -- model families
C_TEST = "#C87D2A"    # amber  -- refit + test
C_ROBUST = "#9E4F3F"  # rust   -- robustness / fair test

# split-block palette (shared by both figures)
C_TRAIN = "#3C6E9C"
C_VAL = "#D69E2E"
C_TEST_BLK = "#38795B"


def _save(fig, out_dir: Path, stem: str) -> dict[str, str]:
    paths: dict[str, str] = {}
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        p = out_dir / f"{stem}.{ext}"
        fig.savefig(p, dpi=200, bbox_inches="tight", facecolor=C_BG)
        paths[ext] = str(p)
    plt.close(fig)
    return paths


# ── Figure 1: modeling pipeline ───────────────────────────────────────────────
STAGES = [
    (C_PANEL, "1  Final panel",
     ["174 countries $\\times$ 1999–2023",
      "8 main features + 3 submodels",
      "3-year lagged predictors (Ch. 2)"]),
    (C_SPLIT, "2  Chronological split",
     ["Train 1999–2018  (80%)",
      "Val 2019–2020  (10%)",
      "Test 2021–2023  (10%)",
      "impute + scale fit on train only"]),
    (C_MODEL, "3  Model families",
     ["Linear: OLS $\\cdot$ Ridge",
      "Lasso $\\cdot$ ElasticNet",
      "Trees: Random Forest $\\cdot$ XGBoost",
      "select by validation MAE"]),
    (C_TEST, "4  Refit & test once",
     ["refit on train + val",
      "one held-out test evaluation",
      "vs persistence baselines",
      "(global / mean / last)"]),
    (C_ROBUST, "5  Robustness & fair test",
     ["6-fold rolling origin",
      "same-sample nested $\\cdot$ 25-seed RF",
      "$\\Delta$-target + Clark–West",
      "change-space significance"]),
]


def _stage_box(ax, x0, y0, box_w, box_h, color, title, lines,
               title_fs=11.0, line_fs=9.2):
    """Draw a single rounded stage box with a coloured header strip."""
    cx = x0 + box_w / 2
    ax.add_patch(FancyBboxPatch(
        (x0, y0), box_w, box_h, boxstyle="round,pad=0.6",
        linewidth=1.6, edgecolor=color, facecolor=color + "14", zorder=2))
    hdr_h = box_h * 0.22
    ax.add_patch(FancyBboxPatch(
        (x0, y0 + box_h - hdr_h), box_w, hdr_h, boxstyle="round,pad=0.4",
        linewidth=0, facecolor=color + "30", zorder=2))
    ax.text(cx, y0 + box_h - hdr_h / 2, title, ha="center", va="center",
            fontsize=title_fs, fontweight="bold", color=color, zorder=3)
    # evenly distribute body lines in the space below the header
    body_top = y0 + box_h - hdr_h - 3
    body_bot = y0 + 3
    step = (body_top - body_bot) / max(len(lines), 1)
    ty = body_top - step / 2
    for ln in lines:
        ax.text(cx, ty, ln, ha="center", va="center",
                fontsize=line_fs, color=C_INK, zorder=3)
        ty -= step


def make_pipeline_figure(out_dir: str | Path, stem: str = "fig_model_pipeline") -> dict[str, str]:
    """Two-row (3 + 2) layout. A full-width leakage-control band sits on top,
    spanning the whole pipeline to signal that it holds at every stage."""
    fig, ax = plt.subplots(figsize=(11.8, 6.4), facecolor=C_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    fig.text(0.5, 0.985, "Modeling pipeline: from final panel to the change-based fair test",
             ha="center", va="top", fontsize=14, fontweight="bold", color=C_INK)

    # ── full-width leakage-control band (applies across the whole pipeline) ────
    band_y, band_h = 85, 8.0
    ax.add_patch(FancyBboxPatch(
        (2, band_y), 96, band_h, boxstyle="round,pad=0.4",
        linewidth=1.3, edgecolor=C_MUTED, facecolor="#E7EDF3", zorder=2))
    ax.text(50, band_y + band_h / 2,
            "Leakage control, held at every stage:   every learned transform is fit "
            "on the training fold only   ·   time-ordered blocks   ·   "
            "one selection, one evaluation",
            ha="center", va="center", fontsize=8.4, color=C_INK, zorder=3)
    # faint droplines tying the band to each column below
    mx, gx = 2.0, 4.0
    box_w = (100 - 2 * mx - 2 * gx) / 3
    cols = [mx, mx + box_w + gx, mx + 2 * (box_w + gx)]
    for c in cols:
        ax.plot([c + box_w / 2, c + box_w / 2], [band_y, 79.3],
                color=C_MUTED, lw=0.8, ls=(0, (2, 2)), zorder=1)

    # ── stage boxes: top row 1-3, bottom row 4-5 (centred) ────────────────────
    box_h = 32
    top_y = 47
    bot_y = 4
    for j in range(3):
        color, title, lines = STAGES[j]
        _stage_box(ax, cols[j], top_y, box_w, box_h, color, title, lines)

    bottom_total = 2 * box_w + gx
    bstart = (100 - bottom_total) / 2
    bcols = [bstart, bstart + box_w + gx]
    for j in range(2):
        color, title, lines = STAGES[3 + j]
        _stage_box(ax, bcols[j], bot_y, box_w, box_h, color, title, lines)

    def cxt(j):
        return cols[j] + box_w / 2

    def cxb(j):
        return bcols[j] + box_w / 2

    # horizontal arrows within each row
    for a, b in [(0, 1), (1, 2)]:
        ax.add_patch(FancyArrowPatch(
            (cols[a] + box_w + 0.1, top_y + box_h / 2), (cols[b] - 0.1, top_y + box_h / 2),
            arrowstyle="-|>", mutation_scale=16, color=C_MUTED, lw=1.8, zorder=1))
    ax.add_patch(FancyArrowPatch(
        (bcols[0] + box_w + 0.1, bot_y + box_h / 2), (bcols[1] - 0.1, bot_y + box_h / 2),
        arrowstyle="-|>", mutation_scale=16, color=C_MUTED, lw=1.8, zorder=1))

    # wrap connector: box 3 (top-right) -> down -> left -> box 4 (bottom-left)
    y_mid = (top_y + bot_y + box_h) / 2
    ax.plot([cxt(2), cxt(2)], [top_y, y_mid], color=C_MUTED, lw=1.8, zorder=1)
    ax.plot([cxt(2), cxb(0)], [y_mid, y_mid], color=C_MUTED, lw=1.8, zorder=1)
    ax.add_patch(FancyArrowPatch(
        (cxb(0), y_mid), (cxb(0), bot_y + box_h + 0.1),
        arrowstyle="-|>", mutation_scale=16, color=C_MUTED, lw=1.8, zorder=1))

    return _save(fig, Path(out_dir), stem)


# ── Figure 2: evaluation timeline ─────────────────────────────────────────────
# (train_start, train_end, val_start, val_end, test_start, test_end) per fold,
# from linear_model_rolling_origin_summary.csv
FOLDS = [
    (1999, 2004, 2005, 2006, 2007, 2009),
    (1999, 2007, 2008, 2009, 2010, 2012),
    (1999, 2010, 2011, 2012, 2013, 2015),
    (1999, 2013, 2014, 2015, 2016, 2018),
    (1999, 2016, 2017, 2018, 2019, 2021),
    (1999, 2019, 2020, 2021, 2022, 2023),
]
Y0, Y1 = 1999, 2023


def _span(ax, y, x_start, x_end, color, h=0.72):
    ax.add_patch(Rectangle((x_start - 0.5, y - h / 2), (x_end - x_start + 1), h,
                           facecolor=color + "D0", edgecolor=color, linewidth=0.8, zorder=2))


def make_timeline_figure(out_dir: str | Path, stem: str = "fig_eval_timeline") -> dict[str, str]:
    fig, ax = plt.subplots(figsize=(13.5, 5.6), facecolor=C_BG)
    n_fold = len(FOLDS)

    # rows: primary split on top (y = n_fold+1), then folds n_fold..1
    y_primary = n_fold + 1.2
    _span(ax, y_primary, 1999, 2018, C_TRAIN)
    _span(ax, y_primary, 2019, 2020, C_VAL)
    _span(ax, y_primary, 2021, 2023, C_TEST_BLK)
    ax.text(1998.4, y_primary, "Primary split", ha="right", va="center",
            fontsize=9.5, fontweight="bold", color=C_INK)
    ax.text((1999 + 2018) / 2, y_primary, "Train  1999–2018", ha="center", va="center",
            fontsize=8.2, color="white", fontweight="bold")
    ax.text(2019.5, y_primary + 0.62, "Val", ha="center", va="bottom", fontsize=7.6, color=C_VAL)
    ax.text(2022, y_primary + 0.62, "Test", ha="center", va="bottom", fontsize=7.6, color=C_TEST_BLK)

    for k, (ts, te, vs, ve, tes, tee) in enumerate(FOLDS):
        y = n_fold - k
        _span(ax, y, ts, te, C_TRAIN)
        _span(ax, y, vs, ve, C_VAL)
        _span(ax, y, tes, tee, C_TEST_BLK)
        ax.text(1998.4, y, f"Fold {k + 1}", ha="right", va="center",
                fontsize=8.8, color=C_INK)

    # divider between primary and folds
    ax.axhline(y_primary - 0.7, color="#CBD5E0", lw=0.8, zorder=1)
    ax.text(1998.4, y_primary + 1.05, "", ha="right")
    fig.text(0.5, 0.965,
             "Leakage-safe evaluation: one chronological split + six expanding-window folds",
             ha="center", va="top", fontsize=13.5, fontweight="bold", color=C_INK)
    ax.text((Y0 + Y1) / 2, n_fold + 2.15,
            "Rolling-origin backtest (each fold trains on earlier years, then scores the next block)",
            ha="center", va="center", fontsize=8.6, color=C_MUTED, style="italic")

    ax.set_xlim(1996.5, Y1 + 0.8)
    ax.set_ylim(0.2, y_primary + 1.6)
    ax.set_yticks([])
    ax.set_xticks(range(2000, 2024, 2))
    ax.tick_params(axis="x", labelsize=8.5, colors=C_INK)
    for s in ("top", "left", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#CBD5E0")

    # legend
    handles = [Rectangle((0, 0), 1, 1, facecolor=c + "D0", edgecolor=c) for c in
               (C_TRAIN, C_VAL, C_TEST_BLK)]
    ax.legend(handles, ["Train", "Validation", "Test"], loc="lower center",
              ncols=3, fontsize=8.5, frameon=True, edgecolor="#CBD5E0",
              bbox_to_anchor=(0.5, -0.13))

    fig.subplots_adjust(left=0.09, right=0.98, top=0.9, bottom=0.12)
    return _save(fig, Path(out_dir), stem)


if __name__ == "__main__":
    here = Path(__file__).resolve().parents[2]
    concept = here / "4_analysis" / "figures" / "model_panels" / "paper_concept"
    print(make_pipeline_figure(concept))
    print(make_timeline_figure(concept))
