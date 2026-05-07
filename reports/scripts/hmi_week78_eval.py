#!/usr/bin/env python3
"""
Automated Week 7 / Week 8 deliverables (real UI2Code^N required).

Week 7:
  • Four sequential /edit examples (mockup + synthetic ctx) + qualitative slots in manifest
  • from-json: TWO THESIS_slide_*.png for thesis (ref | preview) for image-only vs +variables+CSS; gzip reproducibility

Week 8:
  • 8× mockup PNG, three contexts (image only / +variables / +variables+CSS hints); bulk context marked synthetic_script
  • Figures: per-cell indexed lines + strip plots + taxonomy heatmap; per-mockup overlays kept for comparison

Requirements:
  export USE_REAL_MODEL=1 且 POST /health 中 ui2code_n_active=true
  bash: local-service/.venv/bin/python mockups/build_mockups.py

Usage:
  export API_BASE=http://127.0.0.1:8000
  python reports/scripts/hmi_week78_eval.py --week 7
  python reports/scripts/hmi_week78_eval.py --week 7 \
    --context-mode from-json --figma-context-dir path/to/payloads \
    --truncation-fix-mockup-png mockups/png/04-operator-panel.png
  # When plugin JSON still has `<<truncated …>>` for image_base64, the line above injects a real PNG
  # (variables/css from JSON are kept). Prefer full bodies from reproducibility_complete when available.
  python reports/scripts/hmi_week78_eval.py --week 8 --force-refine-rounds 2 --max-refines 2
  python reports/scripts/hmi_week78_eval.py --week 8 --week8-deliver-dir reports/deliverables_week8_extended ...
  # Каждый запуск Week 7/8: заголовок X-Experiment-Trace-Dir → reproducibility_logs/<stamp>/ +
  # reproducibility_complete/*. Полный gzip POST + README автоматически (override: --trace-dir под корень репо или /tmp).
  # Week 7 «figma_plugin»: два широких THESIS_slide_* (эталон | превью), не трёхколоночный triptych.
  python reports/scripts/hmi_week78_eval.py --week 8 --trace-dir /tmp/hmi_exp_traces
  # After killing a partial Week 8 run: reuse the same --week8-deliver-dir and (ideally)
  # --trace-dir, append --week8-resume — completed per_screen/*/metrics.json are kept.

Redraw charts + SUMMARY.md (needs metrics_full.json):
  python reports/scripts/hmi_week78_eval.py --replay-week8-figures
  python reports/scripts/hmi_week78_eval.py --replay-week8-figures --week8-deliver-dir reports/deliverables_week8_prompt_baseline
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import shutil
import statistics
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


from reproducibility_bundle import ReproducibilityRecorder, wipe_and_create_bundle, week8_bundle_recorder_loaded


def configure_matplotlib_week8_style() -> None:
    """Default sans-serif fonts; Week 8 figures use English-only labels."""
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False


# Fallback when replaying legacy JSON missing taxonomy_descriptions_en
_TAXONOMY_LABELS_EN_FALLBACK = {
    "spacing_suspected": "Spacing / padding signal weak",
    "typography_suspected": "Typography not explicit in HTML",
    "alignment_weak": "Little flex/grid layout semantics",
    "hierarchy_weak": "Heading hierarchy weak",
    "button_semantics_ambiguous": "Primary/secondary button semantics unclear",
    "missing_title_or_header": "Semantic header keywords sparse",
    "chart_or_trend_reproduction_weak": "Charts/synoptic may be simplified",
}


def _week8_ordered_rows(bundle: dict[str, Any], configs: list[str]) -> list[dict[str, Any]]:
    """Stable order: screen name then context — one point per experimental cell."""
    rows = list(bundle.get("per_row_csv") or [])
    rank = {c: i for i, c in enumerate(configs)}
    rows.sort(key=lambda r: (str(r["screen"]), rank.get(str(r["config"]), 99)))
    return rows


def _week8_taxonomy_matrix(
    DEL8: Path,
    rows_ordered: list[dict[str, Any]],
    ordered_keys: list[str],
) -> Any:
    """Shape (n_cells, n_keys); 0/1 flags per cell from on-disk metrics.json."""

    mat: list[list[float]] = []
    for r in rows_ordered:
        p = DEL8 / "per_screen" / str(r["screen"]) / str(r["config"]) / "metrics.json"
        if not p.is_file():
            mat.append([0.0] * len(ordered_keys))
            continue
        try:
            blob = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            mat.append([0.0] * len(ordered_keys))
            continue
        tax = blob.get("taxonomy_after_last_snapshot") or {}
        mat.append([float(tax.get(k, 0)) for k in ordered_keys])
    return np.array(mat, dtype=float)


def draw_week8_figure_pngs(DEL8: Path, bundle: dict[str, Any]) -> None:
    """PNG figures from ``metrics_full.json``.

    Primary plots surface **every experimental cell** (indexed line, strip, heatmap).
    Per-mockup overlays (8 points per series) remain for screen-level comparison.
    """
    configure_matplotlib_week8_style()

    configs = ["image_only", "with_variables", "with_variables_css"]
    taxonomy_means = bundle["error_taxonomy_flag_rate_mean"]

    backend = str(bundle.get("model_backend") or "unknown_backend")
    effects = bundle.get("effects") or {}
    desc_en = effects.get("taxonomy_descriptions_en") or {}
    effect_variables = effects.get("mean_delta_ssim_adding_variables") or 0.0
    effect_css_hints = effects.get("mean_delta_ssim_adding_css_on_top_of_variables") or 0.0

    DEL8.mkdir(parents=True, exist_ok=True)

    rows_ordered = _week8_ordered_rows(bundle, configs)
    row_short = [
        "{}\n{}".format(str(r["screen"])[:14], str(r["config"])[:13]) for r in rows_ordered
    ]

    x_idx = list(range(len(configs)))
    xtick_en = ["image only", "+ variables", "+ variables & CSS"]
    cmap = {"image_only": "#8844aa", "with_variables": "#2266bb", "with_variables_css": "#22aa66"}

    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(10, 5))
    for i_c, c in enumerate(configs):
        sub = [r for r in rows_ordered if str(r["config"]) == c]
        sub.sort(key=lambda r: str(r["screen"]))
        ys = [float(r["seconds_first_generate"]) for r in sub]
        if not ys:
            continue
        jitter = rng.uniform(-0.15, 0.15, size=len(ys))
        ax.scatter(
            i_c + jitter,
            ys,
            color=cmap[c],
            s=52,
            alpha=0.88,
            edgecolors="#111",
            linewidths=0.35,
            label="{} (n={})".format(c, len(ys)),
        )
    ax.set_xticks(x_idx)
    ax.set_xticklabels(xtick_en, fontsize=9)
    ax.set_ylabel("Wall time — first POST /generate (s)")
    ax.set_title(
        "Week 8: every single run — scatter by context regime ({} cells); dashed = mean ref. only".format(
            len(rows_ordered)
        )
    )
    for i_c, c in enumerate(configs):
        sub = [float(r["seconds_first_generate"]) for r in rows_ordered if str(r["config"]) == c]
        if sub:
            ax.hlines(
                statistics.mean(sub),
                i_c - 0.28,
                i_c + 0.28,
                colors="#333",
                linestyles="--",
                linewidth=1.0,
                alpha=0.55,
            )
    ax.grid(axis="y", alpha=0.35)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(DEL8 / "figure_timing_first_generate.png", dpi=140)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    for i_c, c in enumerate(configs):
        sub = [r for r in rows_ordered if str(r["config"]) == c]
        sub.sort(key=lambda r: str(r["screen"]))
        ys = [float(r["seconds_to_acceptable"]) for r in sub]
        if not ys:
            continue
        jitter = rng.uniform(-0.15, 0.15, size=len(ys))
        ax2.scatter(
            i_c + jitter,
            ys,
            color=cmap[c],
            s=52,
            alpha=0.88,
            edgecolors="#111",
            linewidths=0.35,
            label="{} (n={})".format(c, len(ys)),
        )
    ax2.set_xticks(x_idx)
    ax2.set_xticklabels(xtick_en, fontsize=9)
    ax2.set_ylabel("Wall time — pipeline finished (s)")
    ax2.set_title(
        "Week 8: every single run — time until accept rule done ({} cells); dashed = mean ref. only".format(
            len(rows_ordered)
        )
    )
    for i_c, c in enumerate(configs):
        sub = [float(r["seconds_to_acceptable"]) for r in rows_ordered if str(r["config"]) == c]
        if sub:
            ax2.hlines(
                statistics.mean(sub),
                i_c - 0.28,
                i_c + 0.28,
                colors="#333",
                linestyles="--",
                linewidth=1.0,
                alpha=0.55,
            )
    ax2.grid(axis="y", alpha=0.35)
    ax2.legend(fontsize=7, loc="upper left")
    fig2.tight_layout()
    fig2.savefig(DEL8 / "figure_timing_to_accept.png", dpi=140)
    plt.close(fig2)

    ordered_keys = [k for k in _TAXONOMY_LABELS_EN_FALLBACK if k in taxonomy_means]
    for k in taxonomy_means:
        if k not in ordered_keys:
            ordered_keys.append(k)
    labels_en = [
        (desc_en.get(k) or _TAXONOMY_LABELS_EN_FALLBACK.get(k) or k) for k in ordered_keys
    ]

    if rows_ordered:
        tax_mat = _week8_taxonomy_matrix(DEL8, rows_ordered, ordered_keys)
        fig3, ax3 = plt.subplots(figsize=(max(12.0, len(rows_ordered) * 0.28), 5.5))
        im = ax3.imshow(
            tax_mat.T, aspect="auto", cmap="YlOrRd", vmin=0, vmax=1, interpolation="nearest"
        )
        ax3.set_xticks(np.arange(len(rows_ordered)))
        ax3.set_xticklabels(row_short, fontsize=5, rotation=90)
        ax3.set_yticks(np.arange(len(ordered_keys)))
        ax3.set_yticklabels(labels_en, fontsize=7)
        ax3.set_xlabel("Experimental cell (mockup x context), sorted")
        ax3.set_title(
            "Week 8: heuristic flags per single run ({}) — besides SSIM".format(backend)
        )
        fig3.colorbar(im, ax=ax3, fraction=0.025, pad=0.02, label="flag (0/1)")
        fig3.tight_layout()
        fig3.savefig(DEL8 / "figure_error_taxonomy_rates.png", dpi=150)
        plt.close(fig3)

    rows_all = bundle.get("per_row_csv") or []
    screens_graph = sorted({str(r["screen"]) for r in rows_all})
    mats_ssim_marg: dict[str, dict[str, float]] = {}
    for r in rows_all:
        mats_ssim_marg.setdefault(str(r["screen"]), {})[str(r["config"])] = float(r["final_ssim"])
    if screens_graph and all(len(mats_ssim_marg.get(s, {})) >= 3 for s in screens_graph):
        d_var = [
            mats_ssim_marg[s]["with_variables"] - mats_ssim_marg[s]["image_only"]
            for s in screens_graph
        ]
        d_css = [
            mats_ssim_marg[s]["with_variables_css"] - mats_ssim_marg[s]["with_variables"]
            for s in screens_graph
        ]
        xi_m = np.arange(len(screens_graph))
        fig4, ax4 = plt.subplots(figsize=(11, 4.2))
        ax4.plot(
            xi_m,
            d_var,
            "o-",
            color="#8844aa",
            lw=1.4,
            ms=6,
            label="d SSIM: +variables vs image-only (each mockup)",
        )
        ax4.plot(
            xi_m,
            d_css,
            "s-",
            color="#22aa66",
            lw=1.4,
            ms=5,
            label="d SSIM: +CSS vs +variables (each mockup)",
        )
        ax4.axhline(0, color="#666666", linestyle="--", lw=0.9)
        ax4.set_xticks(xi_m)
        ax4.set_xticklabels([s.replace("-", "\n") for s in screens_graph], fontsize=8)
        ax4.set_ylabel("Delta final SSIM")
        ax4.set_title(
            "Week 8: per-mockup marginal SSIM (n={}); pooled means: d_var={:+.4f}, d_css={:+.4f}".format(
                len(screens_graph), effect_variables, effect_css_hints
            )
        )
        ax4.grid(axis="y", alpha=0.3)
        ax4.legend(fontsize=8, loc="best")
        fig4.tight_layout()
        fig4.savefig(DEL8 / "figure_context_effect_ssim_delta.png", dpi=150)
        plt.close(fig4)

    if rows_ordered:
        n = len(rows_ordered)
        x_all = np.arange(n)
        w_in = max(14.0, min(28.0, 0.35 * n + 6))
        idx_specs = (
            (
                "figure_all_runs_indexed_first_generate.png",
                "seconds_first_generate",
                "First /generate wall time (s)",
                "All runs indexed — first /generate",
            ),
            (
                "figure_all_runs_indexed_time_to_accept.png",
                "seconds_to_acceptable",
                "Time until pipeline end (s)",
                "All runs indexed — time to accept / forced refine done",
            ),
            (
                "figure_all_runs_indexed_final_ssim.png",
                "final_ssim",
                "Final preview SSIM",
                "All runs indexed — final SSIM vs mockup",
            ),
            (
                "figure_all_runs_indexed_refine_iters.png",
                "refine_iterations",
                "POST /refine count",
                "All runs indexed — refine iterations",
            ),
        )
        for fname, ykey, ylab, ttl in idx_specs:
            fy, ay = plt.subplots(figsize=(w_in, 4.6))
            yy = [float(r[ykey]) for r in rows_ordered]
            ay.plot(
                x_all,
                yy,
                "o-",
                color="#1f3c88",
                lw=1.1,
                ms=3.5,
                mfc="#62a0ea",
                mec="#0b1f4d",
                mew=0.4,
            )
            ay.set_xticks(x_all)
            ay.set_xticklabels(row_short, fontsize=5, rotation=90)
            ay.set_ylabel(ylab)
            ay.set_title("{} — n={} backend={}".format(ttl, n, backend))
            if ykey == "final_ssim":
                ay.axhline(
                    bundle.get("SSIM_goal", 0.38),
                    color="#999",
                    ls="--",
                    lw=0.9,
                    label="SSIM goal",
                )
                ay.legend(fontsize=7, loc="lower right")
            ay.grid(axis="y", alpha=0.35)
            fy.tight_layout()
            fy.savefig(DEL8 / fname, dpi=150)
            plt.close(fy)

    # Per-screen “sawtooth” profiles (shows spread hidden by aggregates).
    rows = bundle.get("per_row_csv") or []
    screens = sorted({str(r["screen"]) for r in rows})
    if screens:
        x_lab = [s.replace("-", "\n") for s in screens]
        xi = np.arange(len(screens))
        mats: dict[str, dict[str, float]] = {}
        for r in rows:
            sc = str(r["screen"])
            cf = str(r["config"])
            mats.setdefault(sc, {})[cf] = float(r["seconds_first_generate"])
        ys_by_cfg_gen: dict[str, list[float]] = {c: [] for c in configs}
        for s in screens:
            for c in configs:
                ys_by_cfg_gen[c].append(mats[s][c])
        fg, ag = plt.subplots(figsize=(12.5, 5.2))
        for c in configs:
            ag.plot(xi, ys_by_cfg_gen[c], marker="o", linewidth=2.0, markersize=5, label=c, color=cmap[c])
        ag.set_xticks(xi)
        ag.set_xticklabels(x_lab, fontsize=8)
        ag.set_ylabel("Seconds")
        ag.set_title(
            "Week 8: per-mockup — first /generate ({} pts/series); see figure_all_runs_indexed_* for all cells".format(
                len(screens)
            )
        )
        ag.grid(axis="y", alpha=0.35)
        ag.legend(fontsize=8, loc="upper left")
        fg.tight_layout()
        fg.savefig(DEL8 / "figure_timing_first_generate_per_screen_lines.png", dpi=150)
        plt.close(fg)

        mats_accept: dict[str, dict[str, float]] = {}
        for r in rows:
            mats_accept.setdefault(str(r["screen"]), {})[str(r["config"])] = float(
                r["seconds_to_acceptable"]
            )
        fa, aa = plt.subplots(figsize=(12.5, 5.2))
        for c in configs:
            yy = [mats_accept[s][c] for s in screens]
            aa.plot(xi, yy, marker="s", linewidth=2.0, markersize=4, label=c, color=cmap[c])
        aa.set_xticks(xi)
        aa.set_xticklabels(x_lab, fontsize=8)
        aa.set_ylabel("Seconds")
        aa.set_title(
            "Week 8: per-mockup wall time — until acceptance rule finished ({})".format(backend)
        )
        aa.grid(axis="y", alpha=0.35)
        aa.legend(fontsize=8, loc="upper left")
        fa.tight_layout()
        fa.savefig(DEL8 / "figure_timing_to_accept_per_screen_lines.png", dpi=150)
        plt.close(fa)

        mats_ssim: dict[str, dict[str, float]] = {}
        for r in rows:
            mats_ssim.setdefault(str(r["screen"]), {})[str(r["config"])] = float(r["final_ssim"])
        fsim, asim = plt.subplots(figsize=(12.5, 5.0))
        for c in configs:
            yy = [mats_ssim[s][c] for s in screens]
            asim.plot(xi, yy, marker="d", linewidth=2.2, markersize=4, label=c, color=cmap[c])
        asim.set_xticks(xi)
        asim.set_xticklabels(x_lab, fontsize=8)
        asim.set_ylabel("Final preview SSIM vs mockup PNG")
        asim.set_title("Week 8: per-mockup SSIM traces (configs overlaid)")
        asim.axhline(bundle.get("SSIM_goal", 0.38), color="#aaaaaa", linestyle="--", label="accept goal")
        asim.legend(fontsize=7, ncol=4, loc="lower right")
        asim.grid(axis="y", alpha=0.35)
        fsim.tight_layout()
        fsim.savefig(DEL8 / "figure_final_ssim_per_screen_lines.png", dpi=150)
        plt.close(fsim)

        mats_ri: dict[str, dict[str, float]] = {}
        for r in rows:
            mats_ri.setdefault(str(r["screen"]), {})[str(r["config"])] = float(r["refine_iterations"])
        fri, ari = plt.subplots(figsize=(12.5, 4))
        width = 0.25
        for i_c, c in enumerate(configs):
            offs = xi + (i_c - 1) * width
            yy = [mats_ri[s][c] for s in screens]
            ari.bar(offs, yy, width=width * 0.95, label=c, color=cmap[c], edgecolor="#222")
        ari.set_xticks(xi)
        ari.set_xticklabels(x_lab, fontsize=8)
        ari.set_ylabel("POST /refine count")
        ari.set_title("Week 8: per-mockup refine iterations — grouped bars (digits, not pooled mean)")
        ari.legend(fontsize=8)
        ari.grid(axis="y", alpha=0.35)
        fri.tight_layout()
        fri.savefig(DEL8 / "figure_refine_iterations_per_screen_bars.png", dpi=150)
        plt.close(fri)

        # Single stacked PNG for appendix
        fk, aks = plt.subplots(3, 1, figsize=(12.5, 11.4), sharex=True)
        for c in configs:
            aks[0].plot(
                xi,
                ys_by_cfg_gen[c],
                marker="o",
                lw=2.0,
                ms=5,
                label=c,
                color=cmap[c],
            )
            aks[1].plot(
                xi,
                [mats_ssim[s][c] for s in screens],
                marker="d",
                lw=2.0,
                ms=4,
                label=c,
                color=cmap[c],
            )
            aks[2].step(
                xi,
                [mats_ri[s][c] for s in screens],
                where="mid",
                linewidth=2.5,
                label=c,
                color=cmap[c],
            )
            aks[2].scatter(xi, [mats_ri[s][c] for s in screens], s=38, color=cmap[c])
        aks[2].set_ylim(-0.1, float(bundle.get("max_refines_budget") or 2) + 0.6)
        aks[2].set_ylabel("/refine count")
        aks[2].legend(fontsize=7, ncol=3, loc="upper right")
        aks[2].grid(axis="y", alpha=0.3)
        aks[1].axhline(bundle.get("SSIM_goal", 0.38), color="#aaa", ls="--", lw=1)
        aks[1].set_ylabel("Final SSIM")
        aks[1].legend(fontsize=7, ncol=3, loc="lower right")
        aks[1].grid(axis="y", alpha=0.3)
        aks[0].set_ylabel("First generate (s)")
        aks[0].legend(fontsize=7, ncol=3, loc="upper left")
        aks[0].grid(axis="y", alpha=0.35)
        aks[0].set_title(
            "Week 8: stacked per-mockup — {}; context={}. Dense per-cell: figure_all_runs_indexed_*.png".format(
                backend,
                bundle.get("context_source_bulk"),
            )
        )
        aks[2].set_xticks(xi)
        aks[2].set_xticklabels(x_lab, fontsize=8)
        plt.setp(aks[2].get_xticklabels(), rotation=0)
        fk.tight_layout()
        fk.savefig(DEL8 / "figure_per_screen_profiles_stacked.png", dpi=150)
        plt.close(fk)

    plt.close("all")


def write_week8_summary_md(DEL8: Path, bundle: dict[str, Any]) -> None:
    """Write ``SUMMARY.md`` from a Week 8 ``metrics_full`` bundle (matches figure semantics)."""
    eff = bundle.get("effects") or {}
    effect_variables = float(eff.get("mean_delta_ssim_adding_variables") or 0)
    effect_css_hints = float(eff.get("mean_delta_ssim_adding_css_on_top_of_variables") or 0)
    force_note = str(bundle.get("acceptability_definition_en") or "")
    resume_note = ""
    if bundle.get("week8_resume"):
        resume_note = (
            "- **`--week8-resume`** was used: skipped cells reused on-disk timings/HTML; taxonomy flags were "
            "replayed from `refine_trace/step*.html` so pooled means stay consistent.\n\n"
        )
    (DEL8 / "SUMMARY.md").write_text(
        "\n".join(
            [
                "## Week 8 experimental evaluation (auto-generated)",
                "",
                resume_note,
                f"- API: `{bundle['api_base']}` · viewport matches each `mockups/png/*.png` (here 1440×900) · three context regimes",
                (
                    f"- Server `GET /health` → **`ui2coden_prompt_profile` = "
                    f"`{bundle.get('ui2coden_prompt_profile_observed')!r}`** "
                    "(must match intentional `UI2CODEN_PROMPT_PROFILE` restart for baseline vs extended)."
                ),
                "",
                "### Metric mapping (planned study items)",
                "",
                "| Metric | Source in this run |",
                "|--------|---------------------|",
                "| Time to first generated result | CSV `seconds_first_generate` · **every run**: `figure_timing_first_generate.png` (strip) + `figure_all_runs_indexed_first_generate.png` |",
                "| Time to acceptable result | CSV `seconds_to_acceptable_result` · strip `figure_timing_to_accept.png` + `figure_all_runs_indexed_time_to_accept.png` |",
                "| Number of refine iterations | CSV `refine_iterations` · indexed `figure_all_runs_indexed_refine_iters.png` |",
                "| Typical error categories | **per-cell heatmap** `figure_error_taxonomy_rates.png` + `metrics_full.json` `error_taxonomy_flag_rate_mean` |",
                "| Effect of enabling variables / CSS | **per-mockup** deltas `figure_context_effect_ssim_delta.png` (pooled means printed in title only) |",
                "| Final SSIM (preview vs reference) | CSV `final_ssim` · `figure_all_runs_indexed_final_ssim.png` + per-mockup lines `figure_final_ssim_per_screen_lines.png` |",
                "| Spread / all singles | `figure_all_runs_indexed_*.png` (dense), `figure_*_per_screen_lines.png` (8 mockups × 3) |",
                "",
                "### Notes",
                "",
                "Heuristic flags are derived from generated HTML; they are not a substitute for human visual audit.",
                "",
                "**Refine policy:**",
                "",
                f"`{force_note}`",
                "",
                f"- Image-only vs adding variables: `{effect_variables:+.5f}`.",
                f"- Adding CSS on top of variables: `{effect_css_hints:+.5f}`.",
                "",
                "---",
                "Authoritative tables: `metrics.csv`, `metrics_full.json`, `per_screen/*/`.",
            ]
        ),
        encoding="utf-8",
    )


from PIL import Image, ImageDraw, ImageFont
from skimage.metrics import structural_similarity as ski_ssim

ROOT = Path(__file__).resolve().parents[2]
MOCKUP_DIR = ROOT / "mockups" / "png"
REP = ROOT / "reports"
DEL7 = REP / "deliverables_week7"
DEL8 = REP / "deliverables_week8"
# `--week8-deliver-dir` may replace DEL8 inside main() before a Week 8 run.
REQUEST_TIMEOUT = 7200

_DEFAULT_SSIM_ACCEPT = float(os.environ.get("SSIM_ACCEPT", "0.38"))
MAX_REFINES = 2

_TRACE_DIR: Optional[Path] = None
_REPRO_RECORDER: Optional[ReproducibilityRecorder] = None
_MODEL_HTTP_RECORD_PATHS = frozenset({"/generate", "/refine", "/edit"})


def parse_force_refine_rounds_env() -> Optional[int]:
    raw = os.environ.get("FORCE_REFINE_ROUNDS")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        n = int(raw)
    except ValueError:
        raise SystemExit(f"FORCE_REFINE_ROUNDS must be int, got {raw!r}") from None
    if n < 0:
        raise SystemExit("FORCE_REFINE_ROUNDS must be >= 0")
    return n


def allowed_client_trace_dir(raw: Optional[str]) -> Optional[Path]:
    """Match server policy: traces only under repo root or /tmp."""
    if raw is None or not str(raw).strip():
        return None
    p = Path(str(raw).strip()).expanduser().resolve()
    for base in (ROOT, Path("/tmp").resolve()):
        try:
            p.relative_to(base)
            return p
        except ValueError:
            continue
    raise SystemExit(f"--trace-dir must resolve under repo root or /tmp; got {p}")


def ensure_experiment_trace_dir(
    *, week: int, context_mode: str, trace_dir_override: Optional[str]
) -> Path:
    """
    Every full Week 7/8 run sends X-Experiment-Trace-Dir so the service always
    writes effective_prompt.txt + request.json (audit). Override with --trace-dir.
    """
    manual = allowed_client_trace_dir(trace_dir_override)
    if manual is not None:
        return manual

    stamp = time.strftime("%Y%m%d_%H%M%S")
    base = (DEL7 if week == 7 else DEL8) / "reproducibility_logs"
    sub = f"week7_{context_mode}_{stamp}" if week == 7 else f"week8_{stamp}"
    base.mkdir(parents=True, exist_ok=True)
    chosen = (base / sub).resolve()
    try:
        chosen.mkdir(parents=False, exist_ok=False)
    except FileExistsError:
        chosen = (base / f"{sub}_{time.time_ns()}").resolve()
        chosen.mkdir(parents=False, exist_ok=False)
    (chosen / "README_API_TRACES.zh.txt").write_text(
        "本目录 = 每次跑 Week 7/8 时**自动**传给服务端的 X-Experiment-Trace-Dir 根路径；"
        "服务在每次成功的 POST /generate|/refine|/edit 下写入子文件夹（含 effective_prompt.txt；"
        "request_meta.json 与 request.json 内容相同，大块 base64 为长度+哈希摘要）。\n\n"
        "【完整、未删 base64 的请求体】由评估脚本自动写入同级上一层的：\n"
        "  ../reproducibility_complete/\n"
        "请打开其中的 README_REPRODUCIBILITY.zh.md 与 INDEX.json。\n\n"
        "若需自定义追溯根目录，请使用命令行 --trace-dir（须落在仓库根或 /tmp 下）。\n",
        encoding="utf-8",
    )
    return chosen


def ref_png_bytes_from_b64(image_b64: str) -> bytes:
    return base64.standard_b64decode(image_b64)


def write_refine_trace_step(
    trace_dir: Path,
    step_name: str,
    html_code: str,
    preview_b64: str | None,
    width: int,
    height: int,
    ref_png_path: Path,
) -> tuple[float | None, bool]:
    """Writes HTML, preview PNG, SSIM sidecar; returns (ssim, preview_used_render_fallback)."""
    trace_dir.mkdir(parents=True, exist_ok=True)
    (trace_dir / f"{step_name}.html").write_text(html_code, encoding="utf-8")
    raw, fb = write_preview_png(
        html_code,
        preview_b64,
        width,
        height,
        trace_dir / f"{step_name}.preview.png",
    )
    ssim = ssim_png_bytes(ref_png_path, raw)
    (trace_dir / f"{step_name}.ssim.json").write_text(
        json.dumps({"ssim_vs_mockup_reference": ssim}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return ssim, fb


def qualitative_dimensions_template() -> dict[str, Any]:
    """Advisor-facing scaffold: SSIM is not sufficient; pair with categorical notes."""
    return {
        "dimensions_en": [
            "alignment_and_padding_vs_reference",
            "typographic_hierarchy",
            "missing_or_extraneous_widgets",
            "charts_trends_synoptic_quality",
            "edit_side_effects_when_using_post_edit",
        ],
        "note_zh_student": (
            "与 SSIM 并列填写；允许「SSIM 几乎不变但布局更合理」或「SSIM 上升但语义变差」。"
        ),
    }


def model_backend() -> str:
    return str(health().get("model_kind") or "unknown")


def _unwrap_generate_json(obj: dict[str, Any], source_name: str) -> dict[str, Any]:
    inner = obj.get("body") if isinstance(obj.get("body"), dict) else obj
    if not isinstance(inner, dict):
        raise SystemExit(f"{source_name}: expected JSON object or envelope with `.body` object")
    return dict(inner)


def _image_base64_is_truncation_placeholder(raw: Any) -> bool:
    return isinstance(raw, str) and (raw.startswith("<<") or "<<truncated" in raw)


def _finalize_week7_generate_payload(
    inner: dict[str, Any],
    *,
    label: str,
    truncation_fixup_png: Optional[Path],
) -> tuple[dict[str, Any], bool]:
    """
    Validates required keys. If clipboard export used `<<truncated …>>` for ``image_base64``,
    replace it with PNG bytes encoded as standard base64 (``truncation_fixup_png`` required).

    Width/height are aligned to that PNG viewport after repair so decoding stays consistent.

    Returns (payload, truncation_repaired).
    """
    out = dict(inner)
    keys = ("image_base64", "frame_name", "width", "height")
    missing = [k for k in keys if k not in out]
    if missing:
        raise SystemExit(f"{label}: missing keys {missing}")

    b64 = out.get("image_base64")
    if not isinstance(b64, str) or not b64.strip():
        raise SystemExit(f"{label}: `image_base64` must be a non-empty string")

    repaired = False
    if _image_base64_is_truncation_placeholder(b64):
        if truncation_fixup_png is None:
            raise SystemExit(
                f"{label}: `image_base64` is a truncation placeholder ({b64[:72]}…). "
                "Re-save full JSON without truncation from `Last API request snapshot`, use "
                "`reproducibility_complete/http_request_bodies/*.full.json.gz`, or rerun with:\n"
                "  `--truncation-fix-mockup-png mockups/png/04-operator-panel.png`\n"
                "(injects reference image only; variables/css stay from this JSON). "
                "See `help/毕业论文实验-Git与Figma真实上下文.zh.md`."
            )
        p = truncation_fixup_png.expanduser().resolve()
        if not p.is_file():
            raise SystemExit(f"{label}: --truncation-fix-mockup-png not found: {p}")
        ww, hh = png_viewport(p)
        out["image_base64"] = b64file(p)
        out["width"], out["height"] = ww, hh
        repaired = True
    elif "<<" in b64[:200]:
        raise SystemExit(
            f"{label}: `image_base64` looks like a placeholder but is not the known truncation pattern; "
            "replace with a full standard base64 string."
        )

    return out, repaired


def load_week7_figma_context_pair(
    directory: Path,
    *,
    truncation_fixup_png: Optional[Path] = None,
) -> tuple[dict[str, Any], dict[str, Any], Path, Path, dict[str, Any]]:
    """Two POST /generate JSON bodies + source paths + import metadata for the manifest."""
    if not directory.is_dir():
        raise SystemExit(f"--figma-context-dir is not a directory: {directory}")
    lone = sorted(directory.glob("*.image_only.payload.json"))
    lfull = sorted(directory.glob("*.with_variables_css.payload.json"))
    if not lone or not lfull:
        raise SystemExit(
            f"{directory} must contain two files matching "
            "*.image_only.payload.json and *.with_variables_css.payload.json"
        )
    path_a, path_b = lone[0], lfull[0]

    def _loads(path: Path) -> dict[str, Any]:
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            raise SystemExit(
                f"{path.name}: file is empty on disk — save/sync the JSON from your machine or decompress "
                "from reproducibility_complete. If you see JSON only in your editor tab, Ctrl+S to write it "
                "to disk on this server."
            )
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise SystemExit(f"{path.name}: invalid JSON ({e})") from e

    ua = _unwrap_generate_json(_loads(path_a), path_a.name)
    ub = _unwrap_generate_json(_loads(path_b), path_b.name)
    a, rep_a = _finalize_week7_generate_payload(ua, label=path_a.name, truncation_fixup_png=truncation_fixup_png)
    b, rep_b = _finalize_week7_generate_payload(ub, label=path_b.name, truncation_fixup_png=truncation_fixup_png)

    repaired = [n for n, r in ((path_a.name, rep_a), (path_b.name, rep_b)) if r]
    fix_rel: str | None = None
    if truncation_fixup_png is not None and repaired:
        fix_rel = str(truncation_fixup_png.expanduser().resolve().relative_to(ROOT))
    meta: dict[str, Any] = {
        "clipboard_truncation_repair_applied": bool(repaired),
        "repaired_payload_files": repaired,
        "mockup_png_used_repo_relative": fix_rel,
        "repair_note_zh": (
            "`image_base64` 曾因插件导出被替换为占位符：已改用列表中的 mockup PNG；"
            "variables / css_hints / variables 仍以 JSON（Figma 导出）为准。论文与答辩须明确写出本条。"
            if repaired
            else ""
        ),
    }

    return a, b, path_a, path_b, meta


def png_viewport(p: Path) -> tuple[int, int]:
    with Image.open(p) as im:
        return im.width, im.height


def synthetic_context(
    screen: str, fw: int, fh: int
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Figma‑like variables and Inspect‑like CSS; frame size matches PNG from layered-svg/screens."""
    wf, hf = f"{fw}px", f"{fh}px"
    v: dict[str, str]
    css: dict[str, dict[str, str]]
    # Light industrial canvas (matches layered SVG: #f3f5f8 page, #13314f header strips in many screens)
    page_bg = "#f3f5f8"
    if screen == "01-equipment-status":
        v = {
            "--surface-0": page_bg,
            "--surface-card": "#ffffff",
            "--text-primary": "#1b2630",
            "--text-secondary": "#5a6675",
            "--accent-running": "#2e7d32",
            "--accent-warning": "#f9a825",
            "--accent-fault": "#c62828",
            "--radius-md": "6px",
            "--header-bar": "#13314f",
        }
        css = {
            "Frame": {
                "width": wf,
                "height": hf,
                "background-color": page_bg,
            },
            "StatusCard": {
                "background-color": "#ffffff",
                "border-radius": "6px",
                "border-left-width": "6px",
                "border-left-style": "solid",
            },
            "Pump P-101": {"border-left-color": "#2e7d32"},
            "Valve V-102": {"border-left-color": "#c62828"},
        }
        return v, css
    if screen == "02-alarm-event":
        v = {
            "--surface-bg": page_bg,
            "--header-bar": "#13314f",
            "--sev-critical": "#c62828",
            "--sev-high": "#ef6c00",
            "--accent-tab": "#1976d2",
        }
        css = {
            "Frame": {"width": wf, "height": hf, "background-color": page_bg},
            "TableRow": {"min-height": "40px"},
        }
        return v, css
    if screen == "03-trend-monitor":
        v = {"--surface-bg": page_bg, "--plot-grid": "#dde3ea", "--plot-line": "#1976d2", "--header-bar": "#13314f"}
        css = {
            "TrendCard": {"min-height": "320px"},
            "ChartArea": {"background-color": "#ffffff"},
        }
        return v, css
    if screen == "04-operator-panel":
        v = {
            "--surface-0": page_bg,
            "--header-bar": "#13314f",
            "--btn-primary": "#1976d2",
            "--btn-danger": "#c62828",
            "--accent-warn-text": "#ef6c00",
        }
        css = {
            "Frame": {"width": wf, "height": hf, "background-color": page_bg},
            "PrimaryAction": {"background-color": "#1976d2"},
        }
        return v, css
    if screen == "05-production-overview":
        v = {
            "--surface-0": page_bg,
            "--header-bar": "#13314f",
            "--good": "#2e7d32",
            "--attention": "#f9a825",
        }
        css = {
            "Frame": {"width": wf, "height": hf},
            "KPI_Block": {"min-width": "160px"},
        }
        return v, css
    if screen == "06-tank-synoptic":
        v = {"--pipe-stroke": "#3a4756", "--tank-fill": "#eaeef3", "--highlight": "#1976d2", "--surface-0": page_bg}
        css = {"Synoptic": {"width": wf, "height": hf}}
        return v, css
    if screen == "07-energy-dashboard":
        v = {"--surface-0": page_bg, "--bar-good": "#2e7d32", "--bar-use": "#1976d2", "--header-bar": "#13314f"}
        css = {"EnergyBar": {"height": "22px"}, "Frame": {"width": wf, "height": hf}}
        return v, css
    v = {"--surface-0": page_bg, "--header-bar": "#13314f", "--step-active": "#1976d2", "--step-done": "#2e7d32"}
    css = {"StepList": {}, "Frame": {"width": wf, "height": hf}}
    return v, css


def api_base() -> str:
    return (os.environ.get("API_BASE") or "http://127.0.0.1:8000").rstrip("/")


def post_json(path: str, body: object) -> dict[str, Any]:
    global _REPRO_RECORDER
    if (
        _REPRO_RECORDER is not None
        and isinstance(body, dict)
        and path in _MODEL_HTTP_RECORD_PATHS
    ):
        _REPRO_RECORDER.record_post(path, body)
    url = api_base() + path
    data = json.dumps(body).encode("utf-8")
    hdrs: dict[str, str] = {"Content-Type": "application/json; charset=utf-8"}
    if _TRACE_DIR is not None:
        hdrs["X-Experiment-Trace-Dir"] = str(_TRACE_DIR)
    req = urllib.request.Request(
        url,
        data=data,
        headers=hdrs,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def health() -> dict[str, Any]:
    from urllib.request import urlopen

    with urlopen(api_base() + "/health", timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def assert_real() -> None:
    h = health()
    if not h.get("ui2code_n_active"):
        raise SystemExit(
            "Refusing to run deliverables while ui2code_n_active=false. Start uvicorn USE_REAL_MODEL=1."
        )
    if str(h.get("model_kind") or "") != "ui2coden":
        raise SystemExit(
            f"model_kind={h.get('model_kind')!r}; this harness expects real UI2Code^N only "
            "(no rule-based stand-in for experiment labelling)."
        )


def b64file(p: Path) -> str:
    return base64.standard_b64encode(p.read_bytes()).decode("ascii")


def ssim_b64_refs(ref_png: Path, cand_b64: str | None) -> float | None:
    if not cand_b64:
        return None
    r = np.array(Image.open(ref_png).convert("L"))
    cand = Image.open(BytesIO(base64.standard_b64decode(cand_b64))).convert("L")
    c = np.array(cand)
    if r.shape != c.shape:
        c = np.array(cand.resize((r.shape[1], r.shape[0]), Image.Resampling.LANCZOS))
    return float(ski_ssim(r, c, data_range=255))


def png_gray_std(png_bytes: bytes) -> float:
    arr = np.asarray(Image.open(BytesIO(png_bytes)).convert("L"), dtype=np.float64)
    return float(arr.std())


# Near-uniform captures “blank page background” previews (CDN/React mount races).
BLANK_PREVIEW_GRAY_STD_THRESHOLD = 12.0


def write_preview_png(
    html_code: str,
    preview_b64: str | None,
    width: int,
    height: int,
    dest: Path,
) -> tuple[bytes, bool]:
    """Decode API preview PNG or fall back to ``POST /render`` if missing / nearly blank."""
    raw: bytes | None = None
    if preview_b64:
        try:
            raw = base64.standard_b64decode(preview_b64)
        except (ValueError, OSError):
            raw = None
    used_fallback = False
    if raw is None or png_gray_std(raw) < BLANK_PREVIEW_GRAY_STD_THRESHOLD:
        rr = post_json(
            "/render",
            {"html_code": html_code, "width": width, "height": height},
        )
        raw = base64.standard_b64decode(rr["image_base64"])
        used_fallback = True
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    return raw, used_fallback


def generated_html_likely_truncated(html_code: str) -> bool:
    """UI2Code^N occasionally hits ``max_new_tokens`` mid-tag — breaks Babel/CDN previews."""
    s = (html_code or "").strip()
    if len(s) < 200:
        return True
    tail = s[-800:].lower()
    return "</html>" not in tail


def post_generate_expect_complete(body: dict[str, Any], *, label: str, max_tries: int = 3) -> dict[str, Any]:
    last: dict[str, Any] | None = None
    for i in range(max_tries):
        last = post_json("/generate", body)
        code = last.get("code") or ""
        if not generated_html_likely_truncated(code):
            return last
        print(
            f"Warning: {label} /generate looks truncated (try {i + 1}/{max_tries}); "
            "retrying. Restart uvicorn after updating UI2CODEN_MAX_NEW_TOKENS if this persists.",
            file=sys.stderr,
        )
    assert last is not None
    return last


def ssim_png_bytes(ref_png: Path, png_bytes: bytes) -> float | None:
    r = np.array(Image.open(ref_png).convert("L"))
    cand = Image.open(BytesIO(png_bytes)).convert("L")
    c = np.array(cand)
    if r.shape != c.shape:
        c = np.array(cand.resize((r.shape[1], r.shape[0]), Image.Resampling.LANCZOS))
    return float(ski_ssim(r, c, data_range=255))


def error_taxonomy(screen: str, html: str) -> dict[str, int]:
    """One-hot heuristic flags aggregated as counts."""
    low = html.lower()
    scores: dict[str, int] = {
        "spacing_suspected": 0,
        "typography_suspected": 0,
        "alignment_weak": 0,
        "hierarchy_weak": 0,
        "button_semantics_ambiguous": 0,
        "missing_title_or_header": 0,
        "chart_or_trend_reproduction_weak": 0,
    }
    if low.count("padding") + low.count("margin") < 6:
        scores["spacing_suspected"] = 1
    if "<h1" not in low and "font-size" not in low and "fontsize" not in low:
        scores["typography_suspected"] = 1
    if "display:flex" not in low.replace(" ", "") and "display:grid" not in low.replace(
        " ", ""
    ):
        scores["alignment_weak"] = 1
    if "<h1" not in low or low.count("<h") < 2:
        scores["hierarchy_weak"] = 1
    if "button" in low and ("primary" not in low and "outline" not in low):
        scores["button_semantics_ambiguous"] = 1
    if "equipment" in screen or "alarm" in screen:
        keywords = {"dashboard", "alarm", "equipment", "trend", "batch", "operator"}
        hit = sum(1 for kw in keywords if kw in low)
        if hit < 1:
            scores["missing_title_or_header"] = 1
    if screen.startswith("03-trend"):
        scores["chart_or_trend_reproduction_weak"] = 1 - min(
            1, ("svg" in low) + ("canvas" in low)
        )
    if screen.startswith("06-tank") and "polygon" not in low and "<svg" not in low:
        scores["chart_or_trend_reproduction_weak"] = 1
    return scores


def label_strip_draw(img: Image.Image, text: str, *, fill: tuple[int, int, int]) -> Image.Image:
    w, h = img.size
    band = Image.new("RGB", (w, 88), fill)
    d = ImageDraw.Draw(band)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
    d.text((20, 20), text[:80], fill=(255, 255, 255), font=font)
    out = Image.new("RGB", (w, h + band.size[1]))
    out.paste(band, (0, 0))
    out.paste(img, (0, band.size[1]))
    return out


def two_column_report_slide(
    *,
    title: str,
    left_img: Image.Image,
    right_img: Image.Image,
    left_label: str,
    right_label: str,
) -> Image.Image:
    """Two-pane slide sized for projector: reference | model preview (not a 3‑column triptych)."""
    lt = label_strip_draw(left_img.convert("RGB"), left_label, fill=(55, 71, 120))
    rt = label_strip_draw(right_img.convert("RGB"), right_label, fill=(18, 120, 80))
    col_w = max(lt.width, rt.width)
    col_h = max(lt.height, rt.height)
    gap = 32
    title_h = 96
    margin = 20
    total_w = col_w * 2 + gap + margin * 2
    total_h = title_h + col_h + margin * 2
    canvas = Image.new("RGB", (total_w, total_h), "#141414")
    tb = Image.new("RGB", (total_w - margin * 2, title_h - margin), "#2d3d6b")
    d = ImageDraw.Draw(tb)
    try:
        tf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except OSError:
        tf = ImageFont.load_default()
    d.text((20, 22), title[:140], fill=(250, 250, 250), font=tf)
    canvas.paste(tb, (margin, margin))
    lt2 = lt.resize((col_w, col_h), Image.Resampling.LANCZOS)
    rt2 = rt.resize((col_w, col_h), Image.Resampling.LANCZOS)
    y_paste = margin + title_h - margin // 2
    canvas.paste(lt2, (margin, y_paste))
    canvas.paste(rt2, (margin + col_w + gap, y_paste))
    return canvas


def run_week7(
    *,
    context_mode: str,
    figma_context_dir: Optional[Path],
    truncation_fixup_mockup: Optional[Path] = None,
) -> None:
    global _REPRO_RECORDER

    assert_real()

    if not MOCKUP_DIR.is_dir():
        raise SystemExit(f"Missing {MOCKUP_DIR}; run mockups/build_mockups.py first.")

    png_op = MOCKUP_DIR / "04-operator-panel.png"
    if not png_op.is_file():
        raise SystemExit("04-operator-panel.png missing.")

    DEL7.mkdir(parents=True, exist_ok=True)
    (DEL7 / "edits").mkdir(exist_ok=True)
    (DEL7 / "context_compare").mkdir(parents=True, exist_ok=True)

    if context_mode == "synthetic":
        cmp_dir = DEL7 / "context_compare" / "synthetic_context_ablation"
        ctx_source = "synthetic_script"
        pfx = "synthetic_"
    else:
        cmp_dir = DEL7 / "context_compare" / "figma_native_context"
        ctx_source = "figma_plugin"
        pfx = "figma_plugin_"
    cmp_dir.mkdir(parents=True, exist_ok=True)

    png_dense_week7: Optional[Path] = None
    figma_pair_cache: Optional[tuple[dict[str, Any], dict[str, Any], Path, Path]] = None
    pair_meta: dict[str, Any] = {}
    if context_mode == "synthetic":
        png_dense_week7 = MOCKUP_DIR / "05-production-overview.png"
        if not png_dense_week7.is_file():
            raise SystemExit("05-production-overview.png missing.")
    else:
        assert figma_context_dir is not None
        lone_payload, full_payload, _p_lo, _p_fu, pair_meta = load_week7_figma_context_pair(
            figma_context_dir,
            truncation_fixup_png=truncation_fixup_mockup,
        )
        figma_pair_cache = (lone_payload, full_payload, _p_lo, _p_fu)
    rb = wipe_and_create_bundle(DEL7)
    _REPRO_RECORDER = ReproducibilityRecorder(rb, week=7, deliver_name=str(DEL7.name))
    _REPRO_RECORDER.set_health(health())

    slug = png_op.stem
    fw_op, fh_op = png_viewport(png_op)
    vw, cs = synthetic_context(slug, fw_op, fh_op)

    manifest: dict[str, Any] = {
        "api_base": api_base(),
        "model_backend": model_backend(),
        "operator_panel_png": str(png_op.relative_to(ROOT)),
        "viewport_from_png": {"width": fw_op, "height": fh_op},
        "context_compare_mode": context_mode,
        "context_source": ctx_source,
        "context_compare_subdir": str(cmp_dir.relative_to(ROOT)),
        "sequential_edits_context_source": "synthetic_script",
        "sequential_edits_note_zh": (
            "四步 /edit 链路仍使用 mockup PNG + 脚本合成 variables/css，"
            "与 context 对照段来源可能不同；以本 manifest 字段为准。"
        ),
        "qualitative_dimensions_template": qualitative_dimensions_template(),
        **(
            {"figma_payload_import_meta": pair_meta}
            if context_mode == "from-json"
            else {}
        ),
    }

    t0 = time.perf_counter()
    gen_body = {
        "image_base64": b64file(png_op),
        "frame_name": "Operator Control Panel — HMI",
        "width": fw_op,
        "height": fh_op,
        "css_hints": cs,
        "variables": vw,
    }
    gen = post_json("/generate", gen_body)
    gen_elapsed = round(time.perf_counter() - t0, 2)
    code = gen["code"]
    manifest["baseline_generate_seconds"] = gen_elapsed
    (DEL7 / "edits" / "00_after_generate.html").write_text(code, encoding="utf-8")
    _, fb0 = write_preview_png(
        code,
        gen.get("preview_base64"),
        fw_op,
        fh_op,
        DEL7 / "edits" / "00_after_generate.preview.png",
    )

    edits = [
        "Change the most prominent primary action button to a secondary style "
        "(flatter, neutral gray, less visually dominant).",
        "Increase the main page title font size so the title reads as the clearest headline.",
        "Make the alarm/summary strip in the top area more visually prominent "
        "(e.g. stronger background contrast).",
        "Slightly reduce horizontal padding or margins in the main content so controls feel tighter.",
    ]

    manifest["instructions_en"] = edits
    manifest["edit_qualitative_template_for_thesis_zh"] = {
        "advisor_requirement": (
            "对四条 /edit 分别填写：成功 / 部分成功 / 明显连带改写；"
            "配合 edits/*/after_edit.preview.png 与 instruction.txt，不得只写 SSIM。"
        ),
        "columns_suggested": ["步骤", "指令(英)", "分档", "主观观察(中)", "副作用(中)"],
    }
    manifest["baseline_preview_used_render_fallback"] = fb0
    manifest["runs"] = []
    prev_code = code
    for idx, instr in enumerate(edits, start=1):
        t_edit = time.perf_counter()
        ed = post_json(
            "/edit",
            {
                "current_code": prev_code,
                "instruction": instr,
                "width": fw_op,
                "height": fh_op,
                "css_hints": cs,
                "variables": vw,
            },
        )
        el = round(time.perf_counter() - t_edit, 2)
        prev_code = ed["code"]
        sub = DEL7 / "edits" / f"{idx:02d}_edit"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / "instruction.txt").write_text(instr + "\n", encoding="utf-8")
        (sub / "response.json").write_text(
            json.dumps(ed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (sub / "after_edit.html").write_text(ed["code"], encoding="utf-8")
        fb_prev = False
        if ed.get("code"):
            _, fb_prev = write_preview_png(
                ed["code"],
                ed.get("preview_base64"),
                fw_op,
                fh_op,
                sub / "after_edit.preview.png",
            )
        manifest["runs"].append(
            {
                "index": idx,
                "instruction": instr,
                "seconds": el,
                "code_len": len(ed["code"]),
                "preview_used_render_fallback": fb_prev,
            }
        )

    # Context comparison: synthetic mockups vs exported Figma plugin payloads
    if context_mode == "synthetic":
        assert png_dense_week7 is not None
        png_dense = png_dense_week7
        dw, dh = png_viewport(png_dense)
        dv, dcss = synthetic_context(png_dense.stem, dw, dh)
        ref_path = png_dense
        only_body = {
            "image_base64": b64file(png_dense),
            "frame_name": "Production Line Overview — HMI",
            "width": dw,
            "height": dh,
        }
        full_body = {
            "image_base64": b64file(png_dense),
            "frame_name": "Production Line Overview — HMI",
            "width": dw,
            "height": dh,
            "css_hints": dcss,
            "variables": dv,
        }
    else:
        assert figma_pair_cache is not None
        lone_payload, full_payload, p_lone, p_full = figma_pair_cache
        ib64 = lone_payload["image_base64"]
        tmp_ref = cmp_dir / f"{pfx}reference_from_payload.png"
        tmp_ref.write_bytes(ref_png_bytes_from_b64(ib64))
        ref_path = tmp_ref
        dw = int(lone_payload["width"])
        dh = int(lone_payload["height"])
        only_body = dict(lone_payload)
        full_body = dict(full_payload)
        shutil.copy2(p_lone, cmp_dir / f"{pfx}input_image_only.payload.json")
        shutil.copy2(p_full, cmp_dir / f"{pfx}input_with_variables_css.payload.json")

    t_a = time.perf_counter()
    only_img = post_generate_expect_complete(only_body, label="context:image_only")
    only_elapsed = round(time.perf_counter() - t_a, 2)

    t_b = time.perf_counter()
    full_ctx = post_generate_expect_complete(full_body, label="context:with_vars_css_hints")
    full_elapsed = round(time.perf_counter() - t_b, 2)

    (cmp_dir / f"{pfx}generate_image_only.response.json").write_text(
        json.dumps({**only_img, "preview_base64": "<<omitted>>"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (cmp_dir / f"{pfx}generate_with_vars_css.response.json").write_text(
        json.dumps({**full_ctx, "preview_base64": "<<omitted>>"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    ia = cmp_dir / f"{pfx}preview_image_only.png"
    ib = cmp_dir / f"{pfx}preview_with_variables_and_css_hints.png"
    b_only, fb_only = write_preview_png(
        only_img["code"],
        only_img.get("preview_base64"),
        dw,
        dh,
        ia,
    )
    b_full, fb_full = write_preview_png(
        full_ctx["code"],
        full_ctx.get("preview_base64"),
        dw,
        dh,
        ib,
    )
    ssim_only = ssim_png_bytes(ref_path, b_only)
    ssim_full = ssim_png_bytes(ref_path, b_full)

    thesis_img_only_name = f"{pfx}THESIS_slide_image_only_context.png"
    thesis_full_ctx_name = f"{pfx}THESIS_slide_full_figma_context.png"
    if context_mode == "from-json":
        ctx_bar = "Week 7 — Figma plugin payloads (variables CSS from bindings, not synthetic script)"
    else:
        ctx_bar = "Week 7 — SCRIPT synthetic_context() ablation ONLY (engineering; not VKR Fig. evidence)"

    if ref_path.is_file() and ia.is_file():
        rim = Image.open(ref_path).convert("RGB")
        im_ia = Image.open(ia).convert("RGB")
        slip1 = two_column_report_slide(
            title=ctx_bar + " | screen A: IMAGE ONLY (/generate)",
            left_img=rim,
            right_img=im_ia,
            left_label=(
                "REFERENCE (из payload / mockup)"
                if context_mode == "from-json"
                else "REFERENCE (mockups/png)"
            ),
            right_label=(
                "PREVIEW после /generate\nSSIM vs ref="
                + (f"{ssim_only:.3f}" if ssim_only is not None else "n/a")
            ),
        )
        slip1.save(cmp_dir / thesis_img_only_name, optimize=True)

    if ref_path.is_file() and ib.is_file():
        rim = Image.open(ref_path).convert("RGB")
        im_ib = Image.open(ib).convert("RGB")
        slip2 = two_column_report_slide(
            title=ctx_bar + " | screen B: +variables +CSS hints (/generate)",
            left_img=rim,
            right_img=im_ib,
            left_label=(
                "REFERENCE (из payload / mockup)"
                if context_mode == "from-json"
                else "REFERENCE (mockups/png)"
            ),
            right_label=(
                "PREVIEW после /generate\nSSIM vs ref="
                + (f"{ssim_full:.3f}" if ssim_full is not None else "n/a")
            ),
        )
        slip2.save(cmp_dir / thesis_full_ctx_name, optimize=True)
    inp_note = (
        "from-json：已把插件导出的两份 `*.payload.json` 复制进本目录，便于与 PNG 一齐打包进答辩材料。"
        if context_mode == "from-json"
        else (
            "synthetic：`variables`/`css_hints` 来自脚本 synthetic_context()+mockups/png，"
            "非 Figma Inspect 真提取；须在文中诚实表述。"
        )
    )
    snap_rel = None
    if context_mode == "from-json":
        snap_rel = [
            str((cmp_dir / f"{pfx}input_image_only.payload.json").relative_to(ROOT)),
            str((cmp_dir / f"{pfx}input_with_variables_css.payload.json").relative_to(ROOT)),
        ]

    manifest["context_compare"] = {
        "reference_png": str(ref_path.relative_to(ROOT)),
        "timings_seconds": {"image_only_generate": only_elapsed, "full_context_generate": full_elapsed},
        "ssim_vs_reference": {"image_only": ssim_only, "variables_css": ssim_full},
        "preview_used_render_fallback": {"image_only": fb_only, "variables_css": fb_full},
        "png_for_report_thesis_slide_image_only_relative": str((cmp_dir / thesis_img_only_name).relative_to(ROOT))
        if (cmp_dir / thesis_img_only_name).is_file()
        else None,
        "png_for_report_thesis_slide_full_context_relative": str((cmp_dir / thesis_full_ctx_name).relative_to(ROOT))
        if (cmp_dir / thesis_full_ctx_name).is_file()
        else None,
        "input_payload_snapshots_relative": snap_rel,
        "input_note_zh": inp_note,
        "artifact_prefix": pfx.rstrip("_"),
        "recommended_for_thesis_zh": (
            "答辩/ВКР：**两张独立**全宽投影片 `THESIS_slide_*`（各为「参考帧 | 生成预览」），"
            "不要使用三栏拼图以免字号过小；仅在方法学附录中可提及旧版 triptych。"
        ),
    }

    manifest["experiment_api_trace_dir_relative"] = (
        str(_TRACE_DIR.relative_to(ROOT)) if _TRACE_DIR is not None else None
    )

    manifest["purpose_en"] = (
        "Week 7 deliverables: four sequential natural-language edits (mockup+synthetic ctx) "
        "plus side-by-side of image-only vs image with variables/CSS; "
        f"context slice labelled `{ctx_source}`."
    )
    rb_rel = str((DEL7 / "reproducibility_complete").relative_to(ROOT))
    manifest["reproducibility_bundle_relative"] = rb_rel
    manifest["reproducibility_readme_zh_relative"] = (
        f"{rb_rel}/README_REPRODUCIBILITY.zh.md"
    )
    rec = _REPRO_RECORDER
    _REPRO_RECORDER = None
    if rec is None:
        raise RuntimeError("internal: reproducibility recorder missing")
    rec.finalize(
        repo_root=ROOT,
        api_base=api_base(),
        trace_dir_relative=str(_TRACE_DIR.relative_to(ROOT)) if _TRACE_DIR else None,
        week_extra={
            "week7_context_mode": context_mode,
            "week7_context_source": ctx_source,
        },
        bundle_repo_relative=rb_rel,
    )

    (DEL7 / "WEEK7_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Week 7 artefacts →", DEL7)


@dataclass
class Row:
    screen: str
    config: str
    seconds_first_generate: float
    seconds_to_acceptable: float | None
    refine_iterations_for_acceptance: int
    ssims: list[float] = field(default_factory=list)


def _week8_cell_complete_disk(out_dir: Path, slug: str, cfg_name: str) -> bool:
    metrics_p = out_dir / "metrics.json"
    html_p = out_dir / "final_code.html"
    if not metrics_p.is_file() or not html_p.is_file():
        return False
    try:
        j = json.loads(metrics_p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    for k in (
        "slug",
        "config",
        "seconds_first_generate",
        "seconds_to_acceptable",
        "refine_iters_actual",
        "ssim_trace",
    ):
        if k not in j:
            return False
    if j.get("slug") != slug or j.get("config") != cfg_name:
        return False
    return True


def _week8_aggregate_taxonomy_from_refine_trace(
    agg_flags: dict[str, list[int]], slug: str, trace_root: Path
) -> None:
    """Replay ``error_taxonomy`` on each dumped HTML step — matches non‑skipped live loop."""
    if not trace_root.is_dir():
        return
    for hp in sorted(trace_root.glob("step*.html")):
        try:
            code = hp.read_text(encoding="utf-8")
        except OSError:
            continue
        for kk, vv in error_taxonomy(slug, code).items():
            agg_flags.setdefault(kk, []).append(vv)


def _week8_accumulate_row_from_disk(
    *,
    agg_flags: dict[str, list[int]],
    timings_by_cfg: dict[str, list[float]],
    time_accept_by_cfg: dict[str, list[float]],
    ssim_tail_by_screen: dict[str, dict[str, float]],
    rows: list[dict[str, Any]],
    slug: str,
    cfg_name: str,
    out_dir: Path,
) -> None:
    j = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    _week8_aggregate_taxonomy_from_refine_trace(agg_flags, slug, out_dir / "refine_trace")
    timings_by_cfg[cfg_name].append(float(j["seconds_first_generate"]))
    time_accept_by_cfg[cfg_name].append(float(j["seconds_to_acceptable"]))
    tail_ssim = float(j["ssim_trace"][-1]) if j.get("ssim_trace") else 0.0
    ssim_tail_by_screen[slug][cfg_name] = tail_ssim
    rows.append(
        {
            "screen": slug,
            "config": cfg_name,
            "seconds_first_generate": float(j["seconds_first_generate"]),
            "seconds_to_acceptable": float(j["seconds_to_acceptable"]),
            "refine_iterations": int(j["refine_iters_actual"]),
            "final_ssim": round(tail_ssim, 4),
        }
    )


def run_week8(
    *,
    ssim_goal: float,
    force_refine_rounds: Optional[int],
    max_refines: int,
    resume: bool,
) -> None:
    global _REPRO_RECORDER

    assert_real()
    if force_refine_rounds is not None and force_refine_rounds < 0:
        raise SystemExit("--force-refine-rounds must be >= 0")
    backend = model_backend()

    if not MOCKUP_DIR.is_dir():
        raise SystemExit(f"Missing {MOCKUP_DIR}; run mockups/build_mockups.py first.")

    DEL8.mkdir(parents=True, exist_ok=True)

    rb = wipe_and_create_bundle(DEL8, resume=resume)
    _REPRO_RECORDER = week8_bundle_recorder_loaded(
        rb,
        week=8,
        deliver_name=str(DEL8.name),
        resume=resume,
    )
    _REPRO_RECORDER.set_health(health())

    png_files = sorted(MOCKUP_DIR.glob("*.png"))
    configs = ["image_only", "with_variables", "with_variables_css"]

    rows: list[dict[str, Any]] = []
    agg_flags: dict[str, list[int]] = {}
    timings_by_cfg: dict[str, list[float]] = {k: [] for k in configs}
    time_accept_by_cfg: dict[str, list[float]] = {k: [] for k in configs}
    ssim_tail_by_screen: dict[str, dict[str, float]] = {}

    for png in png_files:
        slug = png.stem
        fw, fh = png_viewport(png)
        v, css = synthetic_context(slug, fw, fh)
        ssim_tail_by_screen[slug] = {}
        frame_name_en = slug.replace("-", " ").title() + " — HMI"
        body_map = {
            "image_only": {
                "image_base64": b64file(png),
                "frame_name": frame_name_en,
                "width": fw,
                "height": fh,
            },
            "with_variables": {
                "image_base64": b64file(png),
                "frame_name": frame_name_en,
                "width": fw,
                "height": fh,
                "variables": v,
                "css_hints": {},
            },
            "with_variables_css": {
                "image_base64": b64file(png),
                "frame_name": frame_name_en,
                "width": fw,
                "height": fh,
                "variables": v,
                "css_hints": css,
            },
        }

        for cfg_name in configs:
            out_dir = DEL8 / "per_screen" / slug / cfg_name
            out_dir.mkdir(parents=True, exist_ok=True)
            if resume and _week8_cell_complete_disk(out_dir, slug, cfg_name):
                _week8_accumulate_row_from_disk(
                    agg_flags=agg_flags,
                    timings_by_cfg=timings_by_cfg,
                    time_accept_by_cfg=time_accept_by_cfg,
                    ssim_tail_by_screen=ssim_tail_by_screen,
                    rows=rows,
                    slug=slug,
                    cfg_name=cfg_name,
                    out_dir=out_dir,
                )
                continue

            body = body_map[cfg_name]
            wall_start = time.perf_counter()
            t_gen0 = time.perf_counter()
            gen = post_generate_expect_complete(body, label=f"week8:{slug}:{cfg_name}")
            t_gen_elapsed = time.perf_counter() - t_gen0
            timings_by_cfg[cfg_name].append(t_gen_elapsed)
            refined = gen["code"]
            ref_b64 = b64file(png)

            out_dir = DEL8 / "per_screen" / slug / cfg_name
            out_dir.mkdir(parents=True, exist_ok=True)
            trace_root = out_dir / "refine_trace"

            s0_trace, _ = write_refine_trace_step(
                trace_root,
                "step00_generate",
                refined,
                gen.get("preview_base64"),
                fw,
                fh,
                png,
            )
            ssims_track: list[float] = [float(s0_trace if s0_trace is not None else 0.0)]

            taxonomy_last = error_taxonomy(slug, refined)
            for kk, vv in taxonomy_last.items():
                agg_flags.setdefault(kk, []).append(vv)

            refine_iters = 0
            if force_refine_rounds is not None:
                for ri in range(force_refine_rounds):
                    rf_body = {
                        "reference_image_base64": ref_b64,
                        "current_code": refined,
                        "width": fw,
                        "height": fh,
                        "variables": {} if cfg_name == "image_only" else v,
                        "css_hints": css if cfg_name == "with_variables_css" else {},
                    }
                    rf = post_json("/refine", rf_body)
                    refined = rf["code"]
                    step_nm = f"step{ri + 1:02d}_refine"
                    sv, _ = write_refine_trace_step(
                        trace_root,
                        step_nm,
                        refined,
                        rf.get("preview_base64"),
                        fw,
                        fh,
                        png,
                    )
                    ssims_track.append(float(sv if sv is not None else 0.0))
                    taxonomy_last = error_taxonomy(slug, refined)
                    for kk, vv in taxonomy_last.items():
                        agg_flags.setdefault(kk, []).append(vv)
                    refine_iters = ri + 1
            elif ssims_track[0] < ssim_goal:
                for ri in range(max_refines):
                    rf_body = {
                        "reference_image_base64": ref_b64,
                        "current_code": refined,
                        "width": fw,
                        "height": fh,
                        "variables": {} if cfg_name == "image_only" else v,
                        "css_hints": css if cfg_name == "with_variables_css" else {},
                    }
                    rf = post_json("/refine", rf_body)
                    refined = rf["code"]
                    step_nm = f"step{ri + 1:02d}_refine"
                    sv, _ = write_refine_trace_step(
                        trace_root,
                        step_nm,
                        refined,
                        rf.get("preview_base64"),
                        fw,
                        fh,
                        png,
                    )
                    ssim_v = float(sv if sv is not None else 0.0)
                    ssims_track.append(ssim_v)
                    taxonomy_last = error_taxonomy(slug, refined)
                    for kk, vv in taxonomy_last.items():
                        agg_flags.setdefault(kk, []).append(vv)
                    refine_iters = ri + 1
                    if ssim_v >= ssim_goal:
                        break

            elapsed_accept = time.perf_counter() - wall_start
            time_accept_by_cfg[cfg_name].append(elapsed_accept)
            tail_ssim = ssims_track[-1] if ssims_track else 0.0
            ssim_tail_by_screen[slug][cfg_name] = tail_ssim

            row = Row(
                screen=slug,
                config=cfg_name,
                seconds_first_generate=round(t_gen_elapsed, 2),
                seconds_to_acceptable=round(elapsed_accept, 2),
                refine_iterations_for_acceptance=refine_iters,
                ssims=ssims_track,
            )
            (out_dir / "metrics.json").write_text(
                json.dumps(
                    {
                        "slug": slug,
                        "config": cfg_name,
                        "model_backend": backend,
                        "context_source_bulk": "synthetic_script",
                        "seconds_first_generate": row.seconds_first_generate,
                        "seconds_to_acceptable": row.seconds_to_acceptable,
                        "refine_iters_actual": row.refine_iterations_for_acceptance,
                        "refine_mode": (
                            f"forced_{force_refine_rounds}_rounds"
                            if force_refine_rounds is not None
                            else "until_ssim_goal_or_budget"
                        ),
                        "ssim_trace": ssims_track,
                        "taxonomy_after_last_snapshot": taxonomy_last,
                        "SSIM_goal": ssim_goal,
                        "max_refines_budget": max_refines,
                        "force_refine_rounds": force_refine_rounds,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (out_dir / "final_code.html").write_text(refined, encoding="utf-8")

            rows.append(
                {
                    "screen": slug,
                    "config": cfg_name,
                    "seconds_first_generate": row.seconds_first_generate,
                    "seconds_to_acceptable": row.seconds_to_acceptable,
                    "refine_iterations": row.refine_iterations_for_acceptance,
                    "final_ssim": round(tail_ssim, 4),
                }
            )

    need_rows = len(png_files) * len(configs)
    if len(rows) != need_rows:
        raise SystemExit(
            f"Incomplete Week 8 run: aggregated {len(rows)}/{need_rows} rows "
            "(expected one finished cell per mockup × config). "
            "Keep `per_screen/` and `reproducibility_complete/` untouched. "
            "After the API is up again, re-run with the **same** "
            "`--week8-deliver-dir` plus `--week8-resume`; pass the same `--trace-dir` "
            "as the interrupted run so server-side traces stay comparable."
        )

    # Means for effect of variables vs css
    avg = {c: statistics.mean(timings_by_cfg[c]) if timings_by_cfg[c] else 0 for c in configs}
    avg_accept = {
        c: statistics.mean(time_accept_by_cfg[c]) if time_accept_by_cfg[c] else 0 for c in configs
    }
    taxonomy_means = {k: round(statistics.mean(v), 4) if v else 0 for k, v in agg_flags.items()}

    gains_vars = []
    gains_css_extra = []
    for slug, dct in ssim_tail_by_screen.items():
        gains_vars.append(dct["with_variables"] - dct["image_only"])
        gains_css_extra.append(dct["with_variables_css"] - dct["with_variables"])

    effect_variables = statistics.mean(gains_vars) if gains_vars else 0
    effect_css_hints = statistics.mean(gains_css_extra) if gains_css_extra else 0

    rb_rel = str((DEL8 / "reproducibility_complete").relative_to(ROOT))
    rec_fin = _REPRO_RECORDER
    _REPRO_RECORDER = None
    if rec_fin is None:
        raise RuntimeError("internal: reproducibility recorder missing")
    rec_fin.finalize(
        repo_root=ROOT,
        api_base=api_base(),
        trace_dir_relative=str(_TRACE_DIR.relative_to(ROOT)) if _TRACE_DIR else None,
        week_extra={
            "ssim_goal": ssim_goal,
            "force_refine_rounds": force_refine_rounds,
            "max_refines": max_refines,
            "screens": len(png_files),
            "week8_resume": resume,
            "resume_note_zh": (
                "本 RUN_META 产生于带 `--week8-resume` 的续跑；历史 gzip POST 已从 INDEX 或文件系统恢复序号。"
                if resume
                else ""
            ),
        },
        bundle_repo_relative=rb_rel,
    )

    force_note = (
        f"Forced refine mode: exactly {force_refine_rounds} POST /refine call(s) after each /generate, "
        "regardless of first-preview SSIM."
        if force_refine_rounds is not None
        else (
            f"If the SSIM of step00_generate preview vs reference is >= {ssim_goal}, no /refine runs. "
            f"Otherwise repeat /refine until SSIM >= goal or {max_refines} refines, whichever comes first."
        )
    )
    bundle = {
        "api_base": api_base(),
        "model_backend": backend,
        "ui2coden_prompt_profile_observed": health().get("ui2coden_prompt_profile"),
        "context_source_bulk": "synthetic_script",
        "qualitative_dimensions_template": qualitative_dimensions_template(),
        "experiment_api_trace_dir_relative": (
            str(_TRACE_DIR.relative_to(ROOT)) if _TRACE_DIR is not None else None
        ),
        "reproducibility_bundle_relative": rb_rel,
        "reproducibility_readme_zh_relative": f"{rb_rel}/README_REPRODUCIBILITY.zh.md",
        "reference_mockups": [str(x.relative_to(ROOT)) for x in png_files],
        "SSIM_goal": ssim_goal,
        "max_refines_budget": max_refines,
        "force_refine_rounds": force_refine_rounds,
        "acceptability_definition_en": force_note,
        "per_row_csv": rows,
        "timing_means_generate_sec": avg,
        "timing_means_to_accept_sec": avg_accept,
        "error_taxonomy_flag_rate_mean": taxonomy_means,
        "effects": {
            "mean_delta_ssim_adding_variables": round(effect_variables, 5),
            "mean_delta_ssim_adding_css_on_top_of_variables": round(effect_css_hints, 5),
            "taxonomy_descriptions_en": {
                "spacing_suspected": "Spacing / padding heuristic flag",
                "typography_suspected": "Typography may be implicit in HTML",
                "alignment_weak": "Little flex/grid semantics",
                "hierarchy_weak": "Weak heading hierarchy",
                "button_semantics_ambiguous": "Primary/secondary button cues unclear",
                "missing_title_or_header": "Few semantic header keywords",
                "chart_or_trend_reproduction_weak": "Charts/synoptic simplified",
            },
        },
        "week8_resume": resume,
    }

    csv_path = DEL8 / "metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(
            [
                "screen",
                "config",
                "seconds_first_generate",
                "seconds_to_acceptable_result",
                "refine_iterations",
                "final_ssim",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r["screen"],
                    r["config"],
                    r["seconds_first_generate"],
                    r["seconds_to_acceptable"],
                    r["refine_iterations"],
                    r["final_ssim"],
                ]
            )

    (DEL8 / "metrics_full.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    draw_week8_figure_pngs(DEL8, bundle)

    write_week8_summary_md(DEL8, bundle)

    print("Week 8 artefacts →", DEL8)


def main() -> int:
    global _TRACE_DIR, DEL8

    ap = argparse.ArgumentParser(description="Week 7/8 automated deliverables")
    mx = ap.add_mutually_exclusive_group(required=True)
    mx.add_argument("--week", type=int, choices=(7, 8), help="Full pipeline for week 7 or 8")
    mx.add_argument(
        "--replay-week8-figures",
        action="store_true",
        help="Redraw Week 8 PNG charts and SUMMARY.md from metrics_full.json (English labels)",
    )
    ap.add_argument(
        "--context-mode",
        choices=("synthetic", "from-json"),
        default="synthetic",
        help="Week 7 context-compare payloads: mockup+synthetic vs Figma-exported *.payload.json pairs",
    )
    ap.add_argument(
        "--figma-context-dir",
        type=Path,
        default=None,
        help="Directory with *.image_only.payload.json and *.with_variables_css.payload.json (from-json)",
    )
    ap.add_argument(
        "--ssim-accept",
        type=float,
        default=None,
        metavar="FLOAT",
        help=f"SSIM goal for adaptive refine (default env SSIM_ACCEPT or {_DEFAULT_SSIM_ACCEPT:g})",
    )
    ap.add_argument(
        "--force-refine-rounds",
        type=int,
        default=None,
        help="If set (or env FORCE_REFINE_ROUNDS), always run exactly this many /refine after each generate",
    )
    ap.add_argument(
        "--max-refines",
        type=int,
        default=MAX_REFINES,
        metavar="N",
        help="Max adaptive refines before giving up when not forcing (default %(default)s)",
    )
    ap.add_argument(
        "--trace-dir",
        type=str,
        default=None,
        help=(
            "Override X-Experiment-Trace-Dir (repo root or /tmp only). "
            "Default: auto-create under reports/deliverables_weekN/reproducibility_logs/"
        ),
    )
    ap.add_argument(
        "--truncation-fix-mockup-png",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Week 7 from-json only: when `image_base64` is a `<<truncated …>>` placeholder, "
            "replace it with standard base64 of this PNG; variables/CSS from JSON unchanged."
        ),
    )
    ap.add_argument(
        "--week8-deliver-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Write Week 8 outputs here instead of reports/deliverables_week8 (e.g. separate prompt-profile runs).",
    )
    ap.add_argument(
        "--week8-resume",
        action="store_true",
        help=(
            "Week 8 only: preserve reproducibility_complete/; skip cells that already have "
            "metrics.json + final_code.html; continue gzip numbering from INDEX or existing .gz files."
        ),
    )
    args = ap.parse_args()

    if (
        getattr(args, "truncation_fix_mockup_png", None) is not None
        and (args.week != 7 or args.context_mode != "from-json")
    ):
        print(
            "--truncation-fix-mockup-png applies only with --week 7 --context-mode from-json.",
            file=sys.stderr,
        )
        return 1
    _wk = getattr(args, "week", None)
    if args.week8_deliver_dir is not None and _wk != 8 and not args.replay_week8_figures:
        print("--week8-deliver-dir requires --week 8 (or use with --replay-week8-figures).", file=sys.stderr)
        return 1
    if getattr(args, "week8_resume", False) and _wk != 8:
        print("--week8-resume applies only with --week 8.", file=sys.stderr)
        return 1
    if args.week == 8 and args.week8_deliver_dir is not None:
        DEL8 = args.week8_deliver_dir.expanduser().resolve()

    if args.replay_week8_figures:
        deliver = (
            args.week8_deliver_dir.expanduser().resolve()
            if args.week8_deliver_dir is not None
            else (REP / "deliverables_week8")
        )
        mj = deliver / "metrics_full.json"
        if not mj.is_file():
            print(f"Missing {mj}; run --week 8 first or fix --week8-deliver-dir.", file=sys.stderr)
            return 1
        bundle = json.loads(mj.read_text(encoding="utf-8"))
        draw_week8_figure_pngs(deliver, bundle)
        write_week8_summary_md(deliver, bundle)
        print("Redrawn PNG figures + SUMMARY.md →", deliver)
        return 0

    _TRACE_DIR = ensure_experiment_trace_dir(
        week=args.week,
        context_mode=args.context_mode,
        trace_dir_override=args.trace_dir,
    )
    print("X-Experiment-Trace-Dir (fixed every run) →", _TRACE_DIR, file=sys.stderr)

    ssim_goal = (
        args.ssim_accept if args.ssim_accept is not None else _DEFAULT_SSIM_ACCEPT
    )
    force_ref = args.force_refine_rounds
    if force_ref is None:
        force_ref = parse_force_refine_rounds_env()

    if args.week == 7:
        if args.context_mode == "from-json" and args.figma_context_dir is None:
            print(
                "--figma-context-dir is required when --context-mode from-json",
                file=sys.stderr,
            )
            return 1
        run_week7(
            context_mode=args.context_mode,
            figma_context_dir=args.figma_context_dir,
            truncation_fixup_mockup=args.truncation_fix_mockup_png,
        )
    else:
        if args.context_mode != "synthetic":
            print(
                "Note: Week 8 bulk sweep uses synthetic_context only; "
                "context_source_bulk stays synthetic_script.",
                file=sys.stderr,
            )
        run_week8(
            ssim_goal=ssim_goal,
            force_refine_rounds=force_ref,
            max_refines=args.max_refines,
            resume=bool(args.week8_resume),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
