# Week 4 addendum: UI2Code^N offline loading and verification

This note documents one end-to-end run with `USE_REAL_MODEL=1`, local weights, and mitigation for unreachable `huggingface.co`. Pair it with `week-4-delivery.md` and `week-4-demo-request-response.json`.

## Observed behaviour

- First `/generate` can look stuck for minutes if the HF Hub is probed repeatedly while offline.  
- With a full snapshot on disk (`config.json` present), loading should use **`local_files_only=True`** so no Hub traffic runs.

## What was integrated (long-term)

| Item | Behaviour | Main file |
| --- | --- | --- |
| Local snapshot detection | Prefer directory path containing `UI2Code_N` (or env override) when default repo id is used | `local-service/model_wrapper.py` (`_resolve_pretrained_location`) |
| Offline env hints | Startup hook sets HF offline flags once a local snapshot resolves | `local-service/app.py` + `apply_real_model_env_defaults()` |

## Reproduce (example paths)

Adjust paths if your checkout differs:

```bash
cd local-service
export USE_REAL_MODEL=1 UI2CODEN_MODEL_ID=/path/to/UI2Code_N
.venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Then `curl` `/health`, warm up with `/generate` on e.g. `mockups/png/07-energy-dashboard.png`. Structured log metadata for one run lives in `week-4-generate-07-energy-dashboard-run.json` (may be abbreviated).
