# HMI Code Generator — Intelligent Figma Plugin

An intelligent Figma plugin for generating and iteratively refining HTML/CSS code of industrial Human–Machine Interfaces (HMI) from graphical mockups.

## Project Overview

This project implements a prototype Figma plugin that assists engineers in converting industrial interface designs (operator panels, monitoring dashboards, alarm screens, equipment status pages, supervisory control interfaces) into working HTML/CSS code. The system leverages the UI2Code^N visual language model as its baseline.

### Key Features

- **Generate Code** — export a selected Figma frame and receive generated HTML/CSS
- **Make It Closer to the Mockup** — iteratively refine generated code to match the reference design
- **Edit by Request** — modify code via natural-language instructions

## Repository Structure

```
hmi-code-gen/
├── figma-plugin/          # Figma plugin source code
│   ├── manifest.json      # Plugin manifest
│   └── src/
│       ├── code.ts        # Plugin backend (sandbox)
│       └── ui.html        # Plugin UI (iframe)
├── local-service/         # Local AI inference HTTP service
│   ├── app.py             # FastAPI application
│   ├── renderer.py        # HTML-to-screenshot rendering module
│   └── requirements.txt   # Python dependencies
├── mockups/               # Industrial HMI mockup set
│   ├── png/               # Exported PNG images
│   └── mockup-index.md    # Description table for each mockup
├── baseline-tests/        # Baseline model test results
│   ├── outputs/           # Generated code and screenshots
│   └── baseline-report.md # Evaluation report
├── reports/               # Weekly progress reports
│   ├── week-1.md
│   ├── week-2.md
│   ├── week-3.md
│   └── week-4.md
└── docs/                  # Technical documentation
    └── figma-data-extraction.md
```

## Prerequisites

- Node.js ≥ 18 (for Figma plugin development)
- Python ≥ 3.10 (for local service)
- Figma Desktop App (for plugin testing)
- CUDA-capable GPU recommended (for model inference)

## Quick Start

### 1. Figma Plugin

```bash
cd figma-plugin
npm install
npm run build
```

Load the plugin in Figma via *Plugins → Development → Import plugin from manifest…* and select `figma-plugin/manifest.json`.

### 2. Local Service

```bash
cd local-service
pip install -r requirements.txt
python app.py
```

The service starts at `http://localhost:8000`. The Figma plugin communicates with this endpoint.

## Thesis

**Title (RU):** Разработка интеллектуального программного модуля генерации и итеративной корректировки кода человеко-машинных интерфейсов по графическим макетам

**Title (EN):** Development of an Intelligent Software Module for the Generation and Iterative Refinement of Human-Machine Interface Code from Graphical Mockups
