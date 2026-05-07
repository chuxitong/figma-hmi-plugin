# Week 5 deliverables checklist

Referenced plan section: translator notes “Rendering + First plug-in shell”.

## A. HTML → PNG renderer

| Requirement | Impl | Paths |
| --- | --- | --- |
| Accept HTML snippet | `RenderRequest.html_code` (+ viewport fields) | `local-service/app.py` |
| Headless Chromium capture | Async Playwright screenshot | `local-service/renderer.py` (`render_html_to_png`) |
| Shared with previews | Wrapped by `/generate`, `/refine`, `/edit` | `local-service/app.py` |

Standalone check lives at Swagger `POST /render`.

## B. Minimum Figma plug-in UI

| UI control | Meaning | Approx. DOM ids (`figma-plugin/src/ui.html`) |
| --- | --- | --- |
| Generate Code | Snapshot frame → `/generate` | `#btnGenerate` |
| Refine | Render snippet → `/refine` | `#btnRefine` |
| Edit | Textual instruction `/edit` | `#editInstruction`, `#btnEdit` |
| Generated code | Readable HTML output | `#codeOutput`, copy control |
| Preview | PNG from service | `#previewArea` |
| Diagnostics | Trace log | `#log` |
| Service URL | Overrides default origin | `#serviceUrl` |

Build flow: `cd figma-plugin && npx tsc` → `dist/code.js`, referenced from `manifest.json`.

## C. Artefacts enumerated in syllabus

| Deliverable | In repo |
| --- | --- |
| Working renderer | `renderer.py` + `/render` |
| Minimal talking shell | `figma-plugin/` sources |
| Short demo recording | **`reports/deliverables_week5/week-5-plugin-shell-demo.mp4`** (see `DEMO-VIDEO-README.md`) |

## Boundary with Week 6

Week‑6 wording stresses longer end‑to‑end evidence; nonetheless this milestone already wires **Generate → export frame → `/generate`** for integration testing, which stays inside the Week‑5 boundary.
