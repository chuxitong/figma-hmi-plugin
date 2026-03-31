# Еженедельный отчёт — Неделя 4

**Тема:** Преобразование базовой модели в локальный HTTP-сервис  
**Дата:** Неделя 4  
**Автор:** Чжан Сычэн

---

## Выполненные задачи

### 1. Архитектура сервиса

Модель обёрнута в локальный HTTP-сервис на базе **FastAPI**. Плагин Figma не запускает модель внутри себя, а отправляет HTTP-запросы к отдельному процессу.

**Архитектура взаимодействия:**
```
Figma Plugin (ui.html)
       │
       │  fetch() — HTTP POST
       ▼
Local Service (localhost:8000)
       │
       ├── /generate  — генерация кода из скриншота
       ├── /refine    — итеративное улучшение кода
       ├── /edit      — редактирование по текстовой инструкции
       ├── /render    — рендер HTML в PNG (утилита)
       └── /health    — проверка состояния
```

### 2. Реализованные эндпоинты

#### POST `/generate`
**Принимает:**
- `image_base64` (обязательно) — скриншот фрейма в base64
- `frame_name`, `width`, `height` — метаданные фрейма
- `css_hints` (опционально) — CSS-подсказки от Figma
- `variables` (опционально) — дизайн-переменные Figma

**Возвращает:**
- `code` — сгенерированный HTML/CSS
- `preview_base64` — скриншот отрендеренного результата
- `explanation` — краткое описание

#### POST `/refine`
**Принимает:**
- `reference_image_base64` — исходный скриншот из Figma
- `current_code` — текущий HTML/CSS код
- `css_hints`, `variables` (опционально)

**Возвращает:** обновлённый код, предварительный просмотр, описание.

#### POST `/edit`
**Принимает:**
- `current_code` — текущий код
- `instruction` — инструкция на естественном языке

**Возвращает:** изменённый код, предварительный просмотр, описание.

#### POST `/render`
**Принимает:** `html_code`, `width`, `height`  
**Возвращает:** `image_base64` — PNG-скриншот отрендеренной страницы.

### 3. Модуль рендеринга

Реализован модуль рендеринга на базе **Playwright** (headless Chromium):
- Принимает HTML-строку
- Сохраняет во временный файл
- Открывает в headless-браузере с заданным viewport
- Делает скриншот
- Возвращает PNG-байты

### 4. Режим разработки (Stub Model)

Для тестирования без GPU реализована заглушка `StubModel`, которая возвращает фиксированный HTML-код. Она автоматически используется, если модуль `model_wrapper` не найден.

### 5. Демонстрация

**Демо-запрос (генерация):**
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "<base64_png>",
    "frame_name": "Equipment Status Dashboard",
    "width": 1280,
    "height": 720
  }'
```

**Демо-ответ:**
```json
{
  "code": "<!DOCTYPE html><html>...<div class=\"card\">Pump A — Running</div>...</html>",
  "preview_base64": "iVBORw0KGgo...",
  "explanation": "Initial code generated from screenshot."
}
```

Скриншот Swagger UI интерфейса: см. `reports/screenshots/w4-swagger-api.png`

---

## Текущие проблемы

- Для полноценной работы эндпоинтов `/generate`, `/refine`, `/edit` требуется подключение реальной модели через `model_wrapper.py` — будет реализовано на следующей неделе.
- Playwright требует предварительной установки браузеров (`playwright install chromium`).

## Следующие шаги (Неделя 5)

- Реализовать модуль рендеринга и проверить end-to-end pipeline.
- Собрать первую рабочую оболочку плагина Figma с интеграцией сервиса.
- Подготовить демо-видео.

---

## Приложение: файлы交付物

| # | 交付物 | Расположение в репозитории |
|---|--------|---------------------------|
| 1 | Код сервиса (FastAPI) | `local-service/app.py` |
| 2 | Модуль рендеринга HTML→PNG | `local-service/renderer.py` |
| 3 | Зависимости Python | `local-service/requirements.txt` |
| 4 | Документация API (с примерами запросов/ответов) | `docs/api-reference.md` |
| 5 | Скриншот Swagger UI | `reports/screenshots/w4-swagger-api.png` |
