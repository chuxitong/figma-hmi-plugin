# Неделя 7. Редактирование по инструкции и сравнение контекстов (**figma_plugin** vs служебный synthetic)

## Два разных блока недели — не смешивать при формулировках текста Диплома

**A.** Четыре последовательных `/edit` на панели `04-operator-panel` (**mockup PNG** + **искусственные** переменные и CSS через `synthetic_context()` в скрипте). Это демонстрирует *реакцию модели на инструкцию* и возможные побочные эффекты — как просили в переписке с научным руководителем (см. столбцы qualitative в MANIFEST).

**B.** Одно попарное сравнение **реально выгруженных из плагина** тел `*.image_only.payload.json` и `*.with_variables_css.payload.json` (**--context-mode from-json**). Именно здесь переменные теперь берутся с привязок из дерева слоя после обновления плагина (Libraries → Fill поддерживаются). Результат визуализации для защиты: **ДВЕ отдельные широкие диагоны** (`figma_plugin_THESIS_slide_image_only_context.png` и `figma_plugin_THESIS_slide_full_figma_context.png`), а не узкий триптих.

## Обязательные команды воспроизведения блока B на сервере

```bash
export API_BASE=http://127.0.0.1:8000   # свой эндпоинт из /health ui2coden
python reports/scripts/hmi_week78_eval.py --week 7 \
  --context-mode from-json \
  --figma-context-dir reports/deliverables_week7/figma_native
```

## Где искать приложения после прогона

| Путь | Содержание |
|------|------------|
| `reports/deliverables_week7/context_compare/figma_native_context/` | Slides THESIS_slide_*.png + дубликаты входных payload + JSON ответов |
| `reports/deliverables_week7/WEEK7_MANIFEST.json` | SSIM каждого режима, тайминги, указатель qualitative |
| `reports/deliverables_week7/edits/` | Последовательность из четырёх /edit после первого базового генерирования операторской |
| `reports/deliverables_week7/reproducibility_complete/` | Полная цепочка POST в gzip |

## То, что **специально вынесено** из главного рассказа ВКР

Массовый одновременный сравнительный режим **`--week 7 --context-mode synthetic`**, который когда-то дублировал картину Б на поддельных variables, считается **чистым инструментарием пайплайна** и занесён в README как инженерный флаг без требования приводить его в основной главе после того, как готов блок **figma_native**.
