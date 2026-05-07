# Release notes. Замороженный снимок прототипа

Дата снимка: 2026-04-17.

К концу девятой недели я зафиксировал прототип как «замороженный» для защиты: новые фичи не добавляю, дальше только текст ВКР. В git есть тег `v2026.04.17-prototype-freeze`.

В снимке есть: плагин с тремя кнопками (Generate / Refine по макету / Edit по тексту), галки для переменных и CSS, собранный `dist/code.js`; локальный сервис с `/generate`, `/refine`, `/edit`, `/render`; рендер через Playwright; обёртка UI2Code^N в `model_wrapper.py`; для отладки без GPU — `rule_based_model.py`; постобработка в `postprocess.py`. Скрипты в `baseline-tests/` (полный прогон — `run_all_experiments.py`, проверка файлов — `verify_deliverables.py`). Иллюстрации для отчётов можно пересобрать в `reports/screenshots/` через `build_report_screenshots.py`.

Поднять у себя: зависимости в `local-service`, `uvicorn app:app --port 8000`. Без скачанной UI2Code^N можно не ставить `USE_REAL_MODEL` — тогда подставится rule-based модель. С весами — `snapshot_download` с Hugging Face (у меня путь `d:/hf_models/UI2Code_N`, при медленном канале зеркало `HF_ENDPOINT=https://hf-mirror.com`) и `USE_REAL_MODEL=1`.
