# Неделя 8 — текст для научрука (RU)

Параллельный текст на китайском: [`week-8.zh.md`](week-8.zh.md).

Соответствие заданию: **время, число итераций, сводка по классам ошибок, переключатели контекста**, плюс **① refine должен быть измеримым, не декларацией; ② synthetic bulk нельзя смешивать с реальным выводом из Figma; ③ SSIM + таксономия + текстовый вывод**.

**Запуск (облако):** `hmi_week78_eval.py --week 8 --force-refine-rounds 2 --max-refines 2` (или `FORCE_REFINE_ROUNDS=2`), чтобы в **`refine_trace`** были шаги `step01_refine`, `step02_refine`. В `/health` должно быть **`model_kind=ui2coden`**.

**Графики:** помимо сводок по трём режимам — **ломаные/столбцы по каждому макету** (`figure_*per_screen*`), плюс индексные кривые на **все 24 прогона** (`figure_all_runs_indexed_*.png`), чтобы среднее не скрывало разброс.

**Честная формулировка:** поля `variables` / `css_hints` в запросах Week 8 собраны скриптом **`synthetic_context`**; в `metrics_full.json` это **`context_source_bulk: synthetic_script`** — в тексте ВКР это **контекст, имитирующий variables/CSS**, отдельно от экспорта плагином Figma (Week 7).

---

## Зачем два прогона: baseline и extended

Оба — на **реальном** UI2Code^N: в `GET /health` — `model_kind: ui2coden`, в `metrics_full.json` — `model_backend: ui2coden`. **Не** меняются веса и **не** два независимых сервера; меняется только **`UI2CODEN_PROMPT_PROFILE`**. Между прогонами в `reports/scripts/run_week8_two_prompt_profiles.sh` перезапускается **`uvicorn`**, чтобы подтянулся нужный шаблон. Остальное совпадает: 8 PNG, три режима входа, в JSON **`context_source_bulk: synthetic_script`**.

## В чём именно два варианта промпта

Управляется переменной окружения **`UI2CODEN_PROMPT_PROFILE`**; по умолчанию (или явно `baseline`) — базовый набор. Реализация: `local-service/model_wrapper.py` (`build_generate_prompt`, `build_refine_prompt`, `build_edit_prompt`, `_prompt_profile_extended()`).

**`baseline`**  
Фиксированные основные инструкции + блок контекста (variables/css и т.д.), **без** дополнительных инженерных суффиксов:

- **generate:** один самодостаточный HTML со встроенным CSS по скриншоту HMI, семантическая разметка, без внешних ресурсов.
- **refine:** сблизить рендер с эталоном (отступы, иерархия типографики, выравнивание, палитра, недостающие крупные элементы), вернуть полный HTML.
- **edit:** применить пользовательскую инструкцию к приложенному HTML, вернуть полный обновлённый HTML.

**`extended`**  
К **тем же** основным шаблонам и контексту добавляются **три** англоязычных блока уточнений:

1. **generate:** отличать аварии/статусы от декоративного chrome, предсказуемая вёрстка (flex/grid), не выкидывать крупные зоны оборудования/трендов, стили кнопок primary/secondary/neutral при их наличии.
2. **refine:** приоритет пиксельного выравнивания и типографики без пересборки несвязанных карточек, если эталон явно не требует иного.
3. **edit:** локальное выполнение инструкции, избегать переписывания несвязанных фрагментов страницы.

Итого: **одна модель и один pipeline; отличие только в том, добавляются ли суффиксы `extended` к тексту на этапах generate / refine / edit.**

---

## Объём

На профиль: **8×3 = 24** ячейки. На каждую: **1×`/generate` + 2×`/refine`** при `force_refine_rounds = 2`, поэтому `refine_iterations` везде 2. Сводка в `metrics_full.json` и `metrics.csv`, детали в `per_screen/.../`.

## Метрики

- **Время:** `seconds_first_generate`, `seconds_to_acceptable` (wall clock). Точечные графики по трём режимам + `figure_all_runs_indexed_*.png` на 24 прогона.
- **SSIM:** `final_ssim`; линии по 24 ячейкам и три линии по восьми макетам (`figure_final_ssim_per_screen_lines.png`).
- **ΔSSIM по контексту:** на макет — прирост к `+variables` от `image_only` и к `+variables_css` от `with_variables`, `figure_context_effect_ssim_delta.png`; сводные числа в `effects` (пример: baseline +0.01333 / −0.01850, extended +0.00637 / −0.02265 — сверять с актуальным JSON).
- **Эвристика HTML:** `taxonomy_after_last_snapshot`, теплокарта `figure_error_taxonomy_rates.png` по ячейкам; использовать вместе с SSIM и визуальной оценкой.

## Где лежит результат

- Baseline: `reports/deliverables_week8_prompt_baseline/` (`figure*.png`, `SUMMARY.md`, `reproducibility_complete/`, trace под `reproducibility_logs/`).
- Extended: `reports/deliverables_week8_prompt_extended/` (аналогично).

С `rule_based` эти выгрузки не смешаны; промпты и тела запросов сшиваются с `reproducibility_complete` и trace.

## Порядок запуска

`USE_REAL_MODEL=1`, проверка `ui2coden` → серия baseline (`--week8-deliver-dir …_baseline`, `--trace-dir`, при обрыве `--week8-resume`) → рестарт → серия extended в `…_extended`. Рисунки и `SUMMARY.md` можно обновить через `--replay-week8-figures`.

Чжан Сычэн
