# Week 4 deliverables (task spec → implementation)

## Request / response fields

| Task spec (inputs) | Implemented as | Location |
| --- | --- | --- |
| Frame PNG | `image_base64` | `POST /generate`; refine uses `reference_image_base64` / `rendered_image_base64` |
| Task / prompt | `task_description` (`instruction` on edit) | `GenerateRequest`, `RefineRequest`, `EditRequest` in `local-service/app.py` |
| Optional current HTML | `current_code` | `/refine`, `/edit` flows |
| Optional Figma variables & CSS hints | `variables`, `css_hints` (plugin checkboxes gate sending them) | Same models |
| Return HTML/CSS | `code` | All `CodeResponse` shapes |
| Short explanation | `explanation` | `CodeResponse`; `/render` returns a fixed note |
| “Next stage” metadata | `metadata` (model kind, viewport, flags, suggested endpoints) | `CodeResponse`, `RenderResponse` |
| Multiple vs single endpoints | Separate `/generate`, `/refine`, `/edit`, `/render` | `app.py` |

## Weekly artefacts (three bullets from the translated plan § week 4)

1. Runnable local service → `local-service/app.py` plus `model_wrapper.py`, `rule_based_model.py`, etc.  
2. Short API documentation with examples → `help/docs/api-reference.md`; Chinese mirror stays in repo only where the course expects it (`help/docs/api-reference.zh.md`).  
3. One demo **request + response pair** → `reports/deliverables_week4/week-4-demo-request-response.json` (`request` and `response` in one file; sample base64 may be truncated).

## Offline real-model checklist (additional log)

Summary of a successful `POST /generate` against local weights without Hugging Face HTTP: see `reports/deliverables_week4/week-4-real-model-setup.md`.

Do **not** commit huge JSON payloads; truncate or keep only metadata in-repo.
