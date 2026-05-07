# API локального сервиса

Base URL: `http://localhost:8000`. Сервис поднимается из `local-service/app.py` через uvicorn. Поверх всех эндпоинтов включён CORS, чтобы плагин Figma ходил без боли. Ниже описание каждого эндпоинта с телом запроса, телом ответа и примерами вызова.

## Галки в UI плагина (опциональные поля)

**Запрос:** включение `task_description`, `variables`, `css_hints`, а также отправка `current_code` / `instruction` на **`/refine`** и **`/edit`**, задаётся чекбоксами **Include …** в **`figma-plugin/src/ui.html`** (см. **`help/docs/figma-data-extraction.md`**).

**Ответ:** сервер по-прежнему отдаёт **`explanation`**, **`metadata`**, **`preview_base64`**. Показ в панели переключается галками **Show explanation / Show metadata / Show preview image**.

## POST `/generate`

Вход: `image_base64` (PNG in base64), `frame_name`, optional `task_description` (user prompt for generation), `width`/`height`, optional `css_hints` / `variables` (Figma checkboxes in the plugin). Preview `preview_base64` is always **PNG** (headless Chromium), locally or on a remote server.

Пример запроса:

```json
{
  "image_base64": "<base64-PNG>",
  "frame_name": "Equipment Status Dashboard",
  "task_description": "Emphasize alarm cards; dark header bar.",
  "width": 1280,
  "height": 720,
  "css_hints": {
    "StatusCard": { "width": "280px", "background": "#2a2a3e", "border-radius": "8px" }
  },
  "variables": {
    "--color-primary": "#1A73E8",
    "--spacing-md": "16px"
  }
}
```

Ответ: `code`, `preview_base64` (PNG in base64 or `null` on render failure), `explanation`, `metadata` (model kind, viewport, context flags, suggested next HTTP endpoints).

## POST `/refine`

Итеративно улучшает уже сгенерированный код так, чтобы он был ближе к оригиналу. На вход подаётся референс-изображение (`reference_image_base64`) и текущий код (`current_code`). По желанию — тот же опциональный контекст (`css_hints`, `variables`).

Пример запроса:

```json
{
  "reference_image_base64": "<base64-PNG>",
  "current_code": "<!DOCTYPE html>...",
  "css_hints": {},
  "variables": {}
}
```

Ответ той же формы, что и у `/generate`.

## POST `/edit`

Применяет короткую инструкцию на естественном языке к текущему коду. Типовые инструкции: «сделай кнопку вторичной», «увеличь заголовок», «выдели блок аварий поярче».

Пример запроса:

```json
{
  "current_code": "<!DOCTYPE html>...",
  "instruction": "Выдели блок аварий поярче"
}
```

Ответ той же формы, что и у `/generate`.

## POST `/render`

Служебный эндпоинт. Принимает HTML-код и viewport, возвращает PNG. Используется и внутри сервиса (для формирования `preview_base64` в других ответах), и извне — экспериментальными скриптами, чтобы рендерить любой HTML в PNG одинаковым способом.

```json
{
  "html_code": "<!DOCTYPE html>...",
  "width": 1280,
  "height": 720
}
```

Ответ: `image_base64` (PNG), `explanation`, `metadata` (format, viewport, etc.).

## GET `/health`

Типично: `status`, `model_loaded`, `model_kind` (`ui2coden` / `rule_based` / `stub`), `ui2code_n_active` (true only for real UI2Code^N).

## Пример вызова через curl

Генерация:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "iVBORw0...", "frame_name": "Equipment Status Dashboard"}'
```

Правка по запросу:

```bash
curl -X POST http://localhost:8000/edit \
  -H "Content-Type: application/json" \
  -d '{"current_code": "<!DOCTYPE html>...", "instruction": "Make the card background lighter"}'
```

## Про модель внутри сервиса

Сервис лениво грузит модель при первом запросе. Он сначала пробует импортировать `model_wrapper.UI2CodeModel` (настоящая UI2Code^N), и если что-то не получилось (например, нет весов или нет GPU), откатывается на детерминированный заместитель `rule_based_model.RuleBasedModel`. Обе модели предоставляют один и тот же интерфейс `generate`/`refine`/`edit`, поэтому остальной код ничего об этом не знает.
