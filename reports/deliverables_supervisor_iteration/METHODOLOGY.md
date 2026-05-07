# Методология экспериментов и честная маркировка артефактов (RU)

Параллельный документ к китайскому [`METHODOLOGY.zh.md`](./METHODOLOGY.zh.md). Пошаговые инструкции для оператора — только в `help/` (на китайском); этот файл фиксирует **смысл** требований научного руководителя и соответствие коду.

## Бэкенд модели

Скрипт `reports/scripts/hmi_week78_eval.py` перед запуском проверяет `GET /health`: нужны `ui2code_n_active=true` и **`model_kind == "ui2coden"`**. Иначе выполнение прерывается. В тексте ВКР нельзя смешивать **UI2Code^N** и **rule_based** («заглушку на правилах») под одним названием «реальный baseline».

## Источник контекста (variables / CSS hints)

| Артефакт | Поле / смысл |
|----------|----------------|
| PNG макета + функция `synthetic_context()` в Python | **`synthetic_script`** (режим по умолчанию для массового Week 8) |
| Пара JSON из плагина Figma `*.payload.json` | **`figma_plugin`** (Week 7, `--context-mode from-json`) |

Цепочка из **четырёх вызовов `/edit` в Week 7** по-прежнему использует макет и **синтетический** контекст; источник может отличаться от блока сравнения контекстов — см. `reports/deliverables_week7/WEEK7_MANIFEST.json` (`sequential_edits_context_source` и пояснение `sequential_edits_note_zh`).

В `metrics_full.json` для Week 8 указано `context_source_bulk: synthetic_script`.

**Формулировка для ВКР**: в главе с результатами Week 8 variables/CSS hints следует описывать как **искусственный контекст, имитирующий design tokens и CSS-подобные подсказки**, а не как полноценное извлечение живых переменных Figma; последнее только в неделе 7 режим `figma_plugin`.


- **SSIM** — только метрика пиксельного сходства; выводы требуют **визуального** и качественного сопровождения.
- **Адаптивный refine**: если SSIM первого превью ≥ порога `--ssim-accept` / `SSIM_ACCEPT`, цикл `/refine` не запускается; иначе — до `--max-refines` итераций, пока не достигнут порог или не исчерпан бюджет.
- **Принудительный режим**: `--force-refine-rounds` / `FORCE_REFINE_ROUNDS` задаёт фиксированное число вызовов `/refine` после каждого `/generate`, **независимо** от SSIM первого кадра (для сравнительного анализа). Значение не может превышать `--max-refines` и не может быть отрицательным.
- **Трассировка**: для Week 8 в `per_screen/<slug>/<config>/refine_trace/` сохраняются HTML, PNG превью и JSON с SSIM на каждом шаге.
- **Шаблон качественных измерений** (`qualitative_dimensions_template` в `metrics_full.json`) напоминает фиксировать категории (выравнивание, типографическая иерархия, пропуски элементов, графики, побочный эффект правок).

## PNG для отчёта (Week 7, сравнение контекста)

Иллюстрации Week 7 в ВКР: два отдельных файла `figma_plugin_THESIS_slide_*` (в каждом две большие колонки: референс | превью модели для режима image-only и для режима с variables+CSS из плагина). Рядом — `*_input_*.payload.json` и архив **`reproducibility_complete/`** для полных тел POST. Абляцию `synthetic_script` смешивать с реальными `figma_plugin` в тексте выпускной работы недопустимо.

## Воспроизводимость (автоматически)

- **Полные тела POST** (как у клиента скрипта, с полным base64): `reports/deliverables_week7|8/reproducibility_complete/http_request_bodies/*.full.json.gz`, плюс `INDEX.json` и авто-**`README_REPRODUCIBILITY.zh.md`** (честные ограничения и запрет на «сценарный» `prompts.json`).  
- **Серверный audit-trace (всегда при полном Week 7/8)**: скрипт каждый раз отправляет `X-Experiment-Trace-Dir` (по умолчанию `reports/deliverables_weekN/reproducibility_logs/<timestamp>/`; переопределение — `--trace-dir` в пределах корня репозитория или `/tmp`) → `effective_prompt.txt` + идентичные `request_meta.json` / `request.json` с усечёнными base64.  
- **`POST /render`** в gzip не включается.

## Профиль промпта

Переменная окружения `UI2CODEN_PROMPT_PROFILE=baseline|extended` управляет дополнительным англоязычным блоком ограничений для HMI в `local-service/model_wrapper.py`; в trace сохраняется поле `prompt_profile_env`.