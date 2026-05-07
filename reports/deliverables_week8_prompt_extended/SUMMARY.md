## Week 8 experimental evaluation (auto-generated)

- **`--week8-resume`** was used: skipped cells reused on-disk timings/HTML; taxonomy flags were replayed from `refine_trace/step*.html` so pooled means stay consistent.


- API: `http://127.0.0.1:8000` · viewport matches each `mockups/png/*.png` (here 1440×900) · three context regimes
- Server `GET /health` → **`ui2coden_prompt_profile` = `'extended'`** (must match intentional `UI2CODEN_PROMPT_PROFILE` restart for baseline vs extended).

### Metric mapping (planned study items)

| Metric | Source in this run |
|--------|---------------------|
| Time to first generated result | CSV `seconds_first_generate` · **every run**: `figure_timing_first_generate.png` (strip) + `figure_all_runs_indexed_first_generate.png` |
| Time to acceptable result | CSV `seconds_to_acceptable_result` · strip `figure_timing_to_accept.png` + `figure_all_runs_indexed_time_to_accept.png` |
| Number of refine iterations | CSV `refine_iterations` · indexed `figure_all_runs_indexed_refine_iters.png` |
| Typical error categories | **per-cell heatmap** `figure_error_taxonomy_rates.png` + `metrics_full.json` `error_taxonomy_flag_rate_mean` |
| Effect of enabling variables / CSS | **per-mockup** deltas `figure_context_effect_ssim_delta.png` (pooled means printed in title only) |
| Final SSIM (preview vs reference) | CSV `final_ssim` · `figure_all_runs_indexed_final_ssim.png` + per-mockup lines `figure_final_ssim_per_screen_lines.png` |
| Spread / all singles | `figure_all_runs_indexed_*.png` (dense), `figure_*_per_screen_lines.png` (8 mockups × 3) |

### Notes

Heuristic flags are derived from generated HTML; they are not a substitute for human visual audit.

**Refine policy:**

`Forced refine mode: exactly 2 POST /refine call(s) after each /generate, regardless of first-preview SSIM.`

- Image-only vs adding variables: `+0.00637`.
- Adding CSS on top of variables: `-0.02265`.

---
Authoritative tables: `metrics.csv`, `metrics_full.json`, `per_screen/*/`.