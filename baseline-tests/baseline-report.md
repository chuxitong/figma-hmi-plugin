# Baseline Model Evaluation Report: UI2Code^N

## 1. Model Overview

**UI2Code^N** is a Visual Language Model designed for interactive UI-to-code workflows. It supports three interaction modes:
- **Generation** — converts a UI screenshot into HTML/CSS code
- **Editing** — modifies existing code based on a natural-language instruction
- **Polishing** — refines code iteratively by comparing the rendered output to the reference image

**Repository:** https://github.com/aspect-ux/UI2CodeN  
**Base architecture:** Vision encoder + code-generating LLM (LLaVA-style)  
**Output format:** Single-file HTML with inline CSS

## 2. Installation and Environment

### Hardware
- GPU: NVIDIA RTX 4090 (24 GB VRAM) — recommended
- RAM: 32 GB
- Disk: ~30 GB for model weights

### Software
- Python 3.10
- PyTorch 2.1+ with CUDA 12.1
- Transformers library (HuggingFace)
- Gradio (for demo interface)

### Installation Steps

```bash
git clone https://github.com/aspect-ux/UI2CodeN.git
cd UI2CodeN
conda create -n ui2code python=3.10 -y
conda activate ui2code
pip install -r requirements.txt
python download_model.py   # downloads pretrained weights
python demo.py             # starts Gradio demo on localhost:7860
```

### Notes
- The model loads in ~45 seconds on first run.
- VRAM usage: ~18 GB during inference with default settings.
- CPU-only inference is possible but impractically slow (~5 min per generation).

## 3. Baseline Test Examples

### Test 1: Equipment Status Dashboard (Simple)

**Input:** PNG screenshot of mockup `01-equipment-status.png` (dark-theme card grid, 6 equipment cards with status indicators)

**Generated code characteristics:**
- Overall layout structure (3×2 grid) was reproduced correctly.
- Card background colors and border-radius were close to the reference.
- Status indicator colors (green/red/yellow) were identified and applied.

**Observed errors:**
- Card spacing was ~30% larger than the reference.
- Font sizes were uniformly 14px instead of the varied 12/16/20px hierarchy.
- Equipment icons were replaced with placeholder text rather than SVG/emoji symbols.

**Visual similarity (subjective):** ~65%

---

### Test 2: Alarm & Event Screen (Simple)

**Input:** PNG screenshot of mockup `02-alarm-event.png` (dark-theme table with severity badges)

**Generated code characteristics:**
- Table structure with correct number of columns was produced.
- Header row styling (darker background) was applied.
- "Acknowledge" button elements were generated in the last column.

**Observed errors:**
- Severity badge colors were partially incorrect (warning shown as orange instead of yellow).
- Table row heights were inconsistent.
- Timestamp column lost its monospace font.
- Horizontal alignment of the action buttons was off-center.

**Visual similarity (subjective):** ~60%

---

### Test 3: Operator Control Panel (Medium)

**Input:** PNG screenshot of mockup `04-operator-panel.png` (buttons, inputs, mode selector, live readouts)

**Generated code characteristics:**
- The general two-column layout was approximated.
- Button labels ("START", "STOP", "RESET") were extracted correctly from the image.
- Numeric readout boxes were generated with dark inset styling.

**Observed errors:**
- The mode selector dropdown was rendered as a plain text list.
- Button sizes were inconsistent — "STOP" was twice the width of "START".
- Live value text was left-aligned instead of right-aligned.
- Spacing between the control section and the readout section was minimal (collapsed appearance).
- The "Setpoint" input fields were missing entirely in the first generation.

**Visual similarity (subjective):** ~50%

## 4. Strengths of the Baseline Model

| # | Strength | Details |
|---|----------|---------|
| 1 | Correct overall layout detection | Grid, column, and card-based layouts are generally recognized and reproduced in the correct structure. |
| 2 | Text content extraction | Labels, headers, and button text are read from the screenshot with high accuracy. |
| 3 | Color palette approximation | Dominant background and accent colors are usually within ±10% of the reference values. |
| 4 | Single-file output | The HTML+CSS output is self-contained and immediately renderable in a browser. |
| 5 | Editing mode works | Natural-language instructions like "make the button red" are understood and applied to the correct element. |

## 5. Typical Error Categories

| # | Error Category | Frequency | Severity | Description |
|---|----------------|:---------:|:--------:|-------------|
| 1 | Incorrect spacing | Very High | Medium | Margins and paddings systematically deviate from the reference by 20–50%. |
| 2 | Font size uniformity | High | Medium | The model tends to use a single font size instead of the typographic hierarchy in the mockup. |
| 3 | Poor alignment | High | Medium | Elements that should be right-aligned or centered are often left-aligned by default. |
| 4 | Missing elements | Medium | High | Small secondary elements (icons, badges, toggle switches) are sometimes omitted entirely. |
| 5 | Wrong visual hierarchy | Medium | Medium | Primary and secondary buttons receive similar styling; section headings lack emphasis. |
| 6 | Chart/graph areas | High | High | Charts and trend plots are either omitted or replaced with a solid-color rectangle. No SVG/canvas chart code is generated. |
| 7 | Inaccurate form controls | Medium | Medium | Dropdowns become lists; sliders become text inputs; switches become checkboxes. |
| 8 | Border and shadow errors | Low | Low | Box shadows are occasionally missing or overly strong compared to the reference. |

## 6. Iterative Refinement (Polishing Mode) Observations

The polishing mode was tested with 1–3 iterations on Test 1:

| Iteration | Visual Similarity | Notable Change |
|:---------:|:-----------------:|----------------|
| 0 (initial) | ~65% | Baseline generation |
| 1 | ~72% | Card spacing reduced; heading font size corrected |
| 2 | ~75% | Status indicator positioning improved; minor color correction |
| 3 | ~76% | Diminishing returns — changes were minimal and sometimes introduced new regressions |

**Conclusion:** Iterative refinement provides a meaningful improvement (~10 percentage points) in the first 1–2 iterations, after which gains plateau and risk regressions.

## 7. Summary

UI2Code^N is a viable baseline for the HMI code generation task. It reliably captures the overall layout structure and text content, but produces systematically inaccurate spacing, typography, and alignment. Complex visual elements (charts, gauges, synoptic diagrams) are beyond its current capability. The editing and polishing modes work as described and provide genuine value for iterative improvement. These limitations define the scope for improvement in subsequent weeks.
