# Какие данные извлекаются из Figma

Документ описывает **текущую реализацию** плагина в репозитории `figma-hmi-plugin`. Источник правды по коду: **`figma-plugin/src/code.ts`** (песочница), **`figma-plugin/src/ui.html`** (UI) и **`local-service/app.py`** (HTTP-сервис).

---

## План недели 4: что сервис **принимает** и что **возвращает**

Формулировки совпадают с **`help/张思成-任务计划（中文翻译）.md`** (неделя 4). **«Опционально»** здесь: **эндпоинт обязан уметь принять поле**; в **конкретном HTTP-запросе** оно может отсутствовать (сценарий: первый `/generate` без `current_code`).

### Сервис должен принимать

| № | По плану | Поле в API | Источник в плагине |
|---|----------|------------|-------------------|
| 1 | PNG интерфейса | `image_base64`, метаданные кадра | Figma `exportAsync` |
| 2 | Описание задачи / prompt | `task_description`; в `/edit` — `instruction` | Поле UI; **`/generate`** шлёт текст только если отмечено **Include task description**; для **`/edit`** — галка **Include edit instruction** |
| 3 | (опц.) текущий код | `current_code` | **`currentCode`**; на **`/refine`** и **`/edit`** код уходит только если включено **Include current HTML in Refine / Edit** (иначе кнопки блокируются) |
| 4 | (опц.) переменные Figma | `variables` | Variables API + **Include design variables** |
| 5 | (опц.) CSS-подсказки | `css_hints` | `getCSSAsync` + **Include CSS hints** |

### Сервис должен возвращать

| № | По плану | Поле | Где видно в UI плагина |
|---|----------|------|-------------------------|
| 1 | HTML/CSS | `code` | блок **Generated Code** |
| 2 | (опц.) краткое пояснение | `explanation` | если **Show explanation in panel** — текст в поле; иначе заглушка (сервер всё равно отдаёт поле) |
| 3 | (опц.) метаданные следующего шага | `metadata` | если **Show metadata (JSON)** — JSON; иначе заглушка |

Дополнительно **`preview_base64`**: отображается при **Show preview image from service**.

### Галки в **`figma-plugin/src/ui.html`**

**Запрос (включается ли поле в JSON в момент нажатия):**

| Галка | Эффект |
|-------|--------|
| Include task description | Вкл: `task_description` из текстового поля (или `null`). Выкл: всегда `null`. |
| Include design variables / Include CSS hints | Как раньше: песочница шлёт словари или `{}`. |
| Include current HTML in Refine / Edit | Вкл: разрешены `/refine` и `/edit` с `current_code`. Выкл: действие отменяется, сообщение в лог. |
| Include edit instruction | Вкл: разрешён `POST /edit` с `instruction`. Выкл: кнопка Edit заблокирована сообщением. |

**Ответ (показывать ли в панели; JSON от сервера не меняется):**

| Галка | Эффект |
|-------|--------|
| Show explanation in panel | Вкл/выкл заполнение поля `explanation`. |
| Show metadata (JSON) in panel | Вкл/выкл форматированный `metadata`. |
| Show preview image from service | Вкл/выкл обновление превью из `preview_base64`. |

PNG для первого **Generate** по-прежнему всегда экспортируется и отправляется (отдельной галки «без картинки» нет).

Дальше документ разбирает **сбор данных из Figma**. Поля ответа задаёт `CodeResponse`; отображение — см. таблицы галок выше.

---

## Как читать остальной документ

- **Обязательный минимум** — без него нет цепочки «выбор → экспорт → HTTP».  
- **Опционально из Figma (галки)** — только `variables` и `css_hints`.  
- **Текущий код** — см. таблицу выше и раздел ниже.

## Обязательные данные

1. **Растровый экспорт выбранного узла**  
   - Допустимые типы: **только** `FRAME`, `COMPONENT` или `INSTANCE` (см. `getSelectedFrame()`). Иначе плагин показывает ошибку выбора.  
   - Экспорт: `node.exportAsync({ format: 'PNG', constraint: { type: 'SCALE', value: 2 } })` → `Uint8Array`, затем `figma.base64Encode(pngBytes)`.  
   - Масштаб **2×** — чтобы стабильнее читались подписи и мелкие элементы.

2. **Метаданные узла (без фона страницы из Figma)**  
   В теле, уходящем в UI и далее на сервис при генерации, сейчас передаются:  
   - `frameName` ← `node.name`  
   - `width`, `height` ← округлённые `node.width`, `node.height`  
   **`node.backgrounds` в payload не сериализуется** — если понадобится фон как сигнал для модели, это отдельное изменение кода.

3. **Канал песочница ↔ UI**  
   - Из песочницы в UI: `figma.ui.postMessage(...)`.  
   - Из UI в песочницу: `parent.postMessage({ pluginMessage: ... }, '*')`.  
   Без этого `fetch` к локальному сервису из UI не сможет получить PNG и контекст из документа.

## Текущий код (состояние UI, не экспорт из Figma)

- В протоколе это поле **`current_code`**; для refine дополнительно **`html_code`** уходит в **`POST /render`**.  
- В **`ui.html`** строка **`currentCode`** хранит последний ответ модели; обновляется после **`/generate`**, **`/refine`**, **`/edit`**.  
- **`POST /generate`** первый раз **не** отправляет предыдущий код (генерация с нуля по картинке). **`/refine`** и **`/edit`** **обязаны** отправить **`current_code`** — иначе нет итерации. Это согласуется с планом: опциональность — **на уровне шага** (первый запрос без кода), а **поддержка в API обязательна**.  
- Модели в **`app.py`**: `RefineRequest`, `EditRequest` содержат **`current_code`** и передают **`css_hints` / `variables`** в обёртку модели.

## Опциональные данные из Figma (только variables и CSS, галки в UI)

В **`ui.html`** две опции: **Include design variables** и **Include CSS hints**.  
Они влияют на **Generate**, **Refine** и **Edit**: в теле запроса оказываются непустые `variables` / `css_hints` **только если галка включена в момент действия** (для Refine/Edit контекст снова собирается через `request-context`, см. ниже).

### Переменные (`includeVariables`)

- **Основное:** обход поддерева экспортируемого **Frame** (DFS), сбор `VARIABLE_ALIAS` из `boundVariables`, заливок/обводок/effect/текстовых сегментов; разрешение через **`getVariableByIdAsync`** и **`resolveForConsumer(корень)`** (в т.ч. переменные из **библиотек**, привязанные к слоям); при сбое — значение из `valuesByMode` для **первого режима** коллекции.  
- **Дополнение:** до **80** локальных переменных файла из **`getLocalVariablesAsync()`**, ещё не попавших в словарь по привязкам.  
- **Лимиты:** до **200** уникальных ID привязок; обход до **~4000** узлов.  
- Ключ: `--` + имя переменной, `/` → `-`.  
- Прежняя реализация **только** `getLocalVariablesAsync()` давала **пустой `variables`**, если переменные брались **только из Libraries** и не были «локальными определениями» в файле — это исправлено (см. `code.ts`, build **2026-05-07-r5-vars-bound-tree**).

### CSS-подсказки (`includeCssHints`)

- Для выбранного узла: `getCSSAsync()` → объект свойств.  
- Для до **10** прямых детей (`node.children.slice(0, 10)`): у кого есть `getCSSAsync`, результат кладётся в тот же словарь по **`child.name`** (ключи — имена узлов; при коллизии имён возможно перезаписывание).  
- Ошибки API глушатся; при недоступности метода словарь может быть пустым.

### Дополнительное поле только для Generate

В UI есть необязательное текстовое поле **task description**: при вызове **`POST /generate`** оно уходит как **`task_description`** (или `null`, если пусто).

## Отдельный поток: контекст без повторного экспорта PNG

Сообщение **`request-context`** (из UI в песочницу) собирает только `cssHints` и `variables` по текущим галкам **без** повторного `exportAsync`.  
Используется для **Refine** и **Edit**, чтобы контекст соответствовал состоянию галок **в момент нажатия кнопки**, а не моменту первой генерации.

Ответ песочницы: **`context-ready`** с `requestId` и `data: { cssHints, variables }`.

## Что уходит на HTTP-сервис (сводка по эндпоинтам)

Базовый URL задаётся в UI (**Service URL**), по умолчанию `http://localhost:8000`, сохраняется в `localStorage`. В текущем репозитории **`manifest.json`** использует `networkAccess` с `allowedDomains: ["*"]`, обязательным `reasoning` и `devAllowedDomains` для localhost, чтобы Figma не падала на валидации manifest при локальной разработке.

| Эндпоинт | Откуда данные |
|----------|----------------|
| **`POST /generate`** | После `frame-exported`: `image_base64`, `frame_name`, `width`, `height`, `task_description` (опц.), `css_hints`, `variables` |
| **`POST /refine`** | Референс — сохранённый при генерации PNG; текущий код; картинка рендера кода через **`POST /render`** (`html_code`, размеры); `css_hints` / `variables` из свежего `request-context` |
| **`POST /edit`** | `current_code`, `instruction`, размеры; `css_hints` / `variables` из `request-context` |
| **`POST /render`** | Только из UI: `html_code`, `width`, `height` (для сравнения макета и HTML при refine) |

Имена полей на wire совпадают с моделями в **`local-service/app.py`** (`GenerateRequest`, `RefineRequest`, и т.д.).

## Поток данных (схема)

```
┌────────────────────────── Figma Desktop ──────────────────────────┐
│                                                                   │
│   code.ts (sandbox)          postMessage           ui.html       │
│   export-frame / request-context  ◄────────────►   pluginMessage   │
│   frame-exported / context-ready                   fetch /generate │
│                                                    /refine /edit   │
│                                                    /render         │
└────────────────────────────────────┬──────────────────────────────┘
                                     │ HTTP (base URL из UI)
                                     ▼
                         сервис (например localhost:8000)
```

## Чего в коде сейчас нет

- **Облегчённое дерево узлов** (рекурсия по `children` на несколько уровней) — **не собирается**; весь структурный сигнал для модели — PNG + опционально variables/CSS.  
- **Передача `backgrounds` фрейма** на сервис — **не реализована**.

## Коротко

**Принимает (план):** пять видов входа + галки **Include …** в **`ui.html`** решают, уйдёт ли поле в конкретный HTTP-запрос. PNG для первого generate по-прежнему обязателен.  

**Возвращает (план):** `CodeResponse`; показ `explanation` / `metadata` / превью в панели — галки **Show …**.  

**Refine/Edit:** контекст variables/CSS через `request-context`; refine дополнительно вызывает `/render`.

*При расхождении этого файла с кодом приоритет у **`figma-plugin/src/code.ts`** и **`figma-plugin/src/ui.html`**.*
