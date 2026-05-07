"""
Baseline test runner for UI2Code^N model evaluation.

Usage:
    python baseline-tests/run_baseline_tests.py

This script runs 3 generation tests + 1 refinement test and saves:
- Generated HTML/CSS code
- Rendered PNG screenshots
- Comparison images (reference vs generated)
- Full execution log

When the real model is not available, the rule-based stand-in is used;
set USE_REAL_MODEL=1 for UI2Code^N (see DEPLOYMENT.md).
"""

import asyncio
import base64
import json
import logging
import os
import sys
import time
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "outputs", "test-run.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("baseline-test")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "local-service"))

PROMPTS = {
    "generate": {
        "test1": {
            "image": "mockups/png/01-equipment-status.png",
            "prompt": "Generate a complete single-file HTML page with inline CSS that reproduces this industrial equipment status dashboard. Use a dark background, colored status indicator dots, and card-based layout.",
            "frame_name": "Equipment Status Dashboard",
            "width": 1280,
            "height": 720,
        },
        "test2": {
            "image": "mockups/png/02-alarm-event.png",
            "prompt": "Generate a complete single-file HTML page with inline CSS that reproduces this alarm and event monitoring screen. Include a summary bar with severity counts, tab navigation, and a data table with severity badges, timestamps, descriptions, and acknowledge buttons.",
            "frame_name": "Alarm & Event Monitor",
            "width": 1280,
            "height": 720,
        },
        "test3": {
            "image": "mockups/png/04-operator-panel.png",
            "prompt": "Generate a complete single-file HTML page with inline CSS that reproduces this operator control panel. Include start/stop/reset buttons, operating mode selector (Auto/Manual/Service), setpoint input fields, and live readout displays.",
            "frame_name": "Operator Control Panel",
            "width": 1280,
            "height": 720,
        },
    },
    "refine": {
        "test1_refine": {
            "reference_image": "mockups/png/01-equipment-status.png",
            "prompt": "Compare the rendered code screenshot with the original reference image. Improve spacing, font size hierarchy, status indicator styling, and card proportions to make the output closer to the reference mockup.",
            "iterations": 2,
        },
    },
    "edit": {
        "test1_edit": {
            "instruction": "Make the warning card border thicker and add a pulsing animation to the fault status indicator.",
        },
    },
}


async def run_tests():
    from renderer import shutdown_renderer

    base_dir = os.path.join(os.path.dirname(__file__), "..")
    out_dir = os.path.join(os.path.dirname(__file__), "outputs")

    try:
        await _run_tests_body(base_dir, out_dir, logger)
    finally:
        await shutdown_renderer()


async def _run_tests_body(base_dir, out_dir, logger):
    from renderer import render_html_to_png

    logger.info("=" * 60)
    logger.info("UI2Code^N Baseline Test Run")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    sys.path.insert(0, os.path.join(base_dir, "local-service"))
    if os.environ.get("USE_REAL_MODEL") == "1":
        try:
            from model_wrapper import UI2CodeModel
            model = UI2CodeModel()
            logger.info("Loaded real UI2Code^N model.")
        except Exception as exc:
            logger.warning("Real model load failed (%s); falling back to stand-in.", exc)
            from rule_based_model import RuleBasedModel
            model = RuleBasedModel()
    else:
        from rule_based_model import RuleBasedModel
        model = RuleBasedModel()
        logger.info("Using rule-based stand-in model (set USE_REAL_MODEL=1 for real).")

    results_summary = []

    # ── Generation Tests ──
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: Generation Tests")
    logger.info("=" * 60)

    generated_codes = {}

    for test_name, cfg in PROMPTS["generate"].items():
        logger.info(f"\n--- {test_name}: {cfg['frame_name']} ---")
        logger.info(f"Input image: {cfg['image']}")
        logger.info(f"Prompt: {cfg['prompt']}")
        logger.info(f"Viewport: {cfg['width']}x{cfg['height']}")

        img_path = os.path.join(base_dir, cfg["image"])
        with open(img_path, "rb") as f:
            image_bytes = f.read()

        t0 = time.time()
        code = model.generate(
            image_bytes,
            frame_name=cfg["frame_name"],
            width=cfg["width"],
            height=cfg["height"],
        )
        gen_time = time.time() - t0
        generated_codes[test_name] = code

        html_path = os.path.join(out_dir, f"{test_name}-generated.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(code)
        logger.info(f"Generated HTML saved to: {html_path}")
        logger.info(f"Generation time: {gen_time:.2f}s")
        logger.info(f"Output length: {len(code)} chars")

        try:
            png_bytes = await render_html_to_png(code, cfg["width"], cfg["height"])
            png_path = os.path.join(out_dir, f"{test_name}-generated.png")
            with open(png_path, "wb") as f:
                f.write(png_bytes)
            logger.info(f"Rendered screenshot saved to: {png_path}")
        except Exception as e:
            logger.error(f"Rendering failed: {e}")

        results_summary.append({
            "test": test_name,
            "phase": "generate",
            "frame_name": cfg["frame_name"],
            "time_seconds": round(gen_time, 2),
            "output_chars": len(code),
        })

    # ── Refinement Test ──
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: Refinement Test (Polishing)")
    logger.info("=" * 60)

    for test_name, cfg in PROMPTS["refine"].items():
        logger.info(f"\n--- {test_name} ---")
        logger.info(f"Reference: {cfg['reference_image']}")
        logger.info(f"Prompt: {cfg['prompt']}")
        logger.info(f"Iterations: {cfg['iterations']}")

        ref_path = os.path.join(base_dir, cfg["reference_image"])
        with open(ref_path, "rb") as f:
            ref_bytes = f.read()

        current_code = generated_codes.get("test1", "")

        for i in range(1, cfg["iterations"] + 1):
            logger.info(f"\n  Refinement iteration {i}...")
            t0 = time.time()
            current_code = model.refine(ref_bytes, current_code)
            ref_time = time.time() - t0
            logger.info(f"  Iteration {i} time: {ref_time:.2f}s")

            html_path = os.path.join(out_dir, f"test1-refined-iter{i}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(current_code)

            try:
                png_bytes = await render_html_to_png(current_code, 1280, 720)
                png_path = os.path.join(out_dir, f"test1-refined-iter{i}.png")
                with open(png_path, "wb") as f:
                    f.write(png_bytes)
                logger.info(f"  Saved: {png_path}")
            except Exception as e:
                logger.error(f"  Rendering failed: {e}")

    # ── Edit Test ──
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 3: Edit Test (Natural Language)")
    logger.info("=" * 60)

    for test_name, cfg in PROMPTS["edit"].items():
        logger.info(f"\n--- {test_name} ---")
        logger.info(f"Instruction: {cfg['instruction']}")

        current_code = generated_codes.get("test1", "")
        t0 = time.time()
        edited_code = model.edit(current_code, cfg["instruction"])
        edit_time = time.time() - t0
        logger.info(f"Edit time: {edit_time:.2f}s")

        html_path = os.path.join(out_dir, f"test1-edited.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(edited_code)
        logger.info(f"Edited HTML saved to: {html_path}")

        try:
            png_bytes = await render_html_to_png(edited_code, 1280, 720)
            png_path = os.path.join(out_dir, f"test1-edited.png")
            with open(png_path, "wb") as f:
                f.write(png_bytes)
            logger.info(f"Saved: {png_path}")
        except Exception as e:
            logger.error(f"Rendering failed: {e}")

    # ── Save prompts ──
    prompts_path = os.path.join(out_dir, "prompts.json")
    with open(prompts_path, "w", encoding="utf-8") as f:
        json.dump(PROMPTS, f, indent=2, ensure_ascii=False)
    logger.info(f"\nPrompts saved to: {prompts_path}")

    # ── Summary ──
    summary_path = os.path.join(out_dir, "results-summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    logger.info("\n" + "=" * 60)
    logger.info("TEST RUN COMPLETE")
    logger.info(f"Finished at: {datetime.now().isoformat()}")
    logger.info(f"Log saved to: {LOG_FILE}")
    logger.info(f"All outputs in: {out_dir}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_tests())
