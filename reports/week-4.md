# Неделя 4. HTTP-обёртка вокруг модели (`local-service`)

Неделя перевела эксперимент из «локального скрипта» в **стабильный REST**: `/generate`, `/refine`, `/edit`, `/render`, `/health`, с описанными в OpenAPI моделями тела запроса.

## Что главное для воспроизводимости (пункт из переписки с Р. А.)

- Каждый полный запуск недельной выдачи пишет `reports/deliverables_week7|8/reproducibility_complete/` (gzip каждого POST + `INDEX.json` + машинный `README_REPRODUCIBILITY.zh.md`) и серверные `effective_prompt*.txt` в дереве по заголовку `X-Experiment-Trace-Dir`. Отдельный «театральный» `prompts.json` не подменяет эти журналы.
- CORS с приватными сетями решён через `CORSMiddleware(allow_private_network=True)` там, где Figma в туннеле дергает `127.0.0.1:8000`.

## Где искать приложения недели к отчётности

Не все старые `deliverables_week4/` файлы остаются актуальными; сравнительный текст лучше брать из свежего `help/docs/api-reference*` и живого Swagger на поднятом сервисе.
