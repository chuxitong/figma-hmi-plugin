# Figma HMI Plugin

Учебный проект в рамках выпускной квалификационной работы. Плагин Figma переводит макет промышленного человеко-машинного интерфейса в HTML/CSS-код с помощью открытой визуально-языковой модели UI2Code^N. Сценариев три: получить начальную версию кода, итеративно подтянуть рендер под референс, точечно отредактировать результат текстовой инструкцией.

## Состав репозитория

- `figma-plugin/` — сам плагин: песочница `src/code.ts`, интерфейс `src/ui.html`, манифест, собранный `dist/code.js`.
- `local-service/` — HTTP-сервис на FastAPI с эндпоинтами `/generate`, `/refine`, `/edit`, `/render`. Обёртка модели в `model_wrapper.py`. Для отладки без GPU есть детерминированный заместитель `rule_based_model.py` с тем же интерфейсом.
- `mockups/` — восемь мокапов промышленного HMI (PNG-экспорты в `png/`, описание в `mockup-index.md`) и библиотека SCADA-символов в `layered-svg/symbols/`. Облачный файл Figma: `https://www.figma.com/design/HrkgKx1ITbIIlwsqDJ2Esv/Industrial-HMI-Mockups?node-id=3-3080&t=x7BBRPlaCsHxhTPK-1`.
- `baseline-tests/` — скрипты экспериментов и их выходы (HTML, PNG, JSON-сводки) в `outputs/`.
- `reports/` — еженедельные отчёты по проекту.
- `help/` — руководства по неделям и API (`help/docs/`).
- `REPOSITORY.txt` — канонический URL репозитория на GitHub.

## Клонирование и зависимости

```bash
git clone https://github.com/chuxitong/figma-hmi-plugin.git
cd figma-hmi-plugin
```

Сервис (Python 3.12+):

```bash
cd local-service
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Плагин (сборка `dist/code.js` для Figma):

```bash
cd ../figma-plugin
npm ci
npx tsc
```

Подробнее про модель и AutoDL: [`help/docs/DEPLOYMENT_AUTODL.zh.md`](help/docs/DEPLOYMENT_AUTODL.zh.md). Растеризация мокапов из SVG: [`mockups/build_mockups.py`](mockups/build_mockups.py).

## Запуск

В одном терминале поднимаем сервис:

```
cd local-service
python -m uvicorn app:app --port 8000
```

Если хочется работать с настоящей моделью UI2Code^N, перед запуском выставляем `USE_REAL_MODEL=1` и убеждаемся, что веса лежат в локальном кэше (`zai-org/UI2Code_N`). Без этой переменной автоматически подключается заместитель.

В Figma Desktop импортируем плагин: *Plugins → Development → Import plugin from manifest* и выбираем `figma-plugin/manifest.json`. После этого плагин открывается как панель и работает с выбранным фреймом.

## Тема ВКР

«Разработка интеллектуального программного модуля генерации и итеративной корректировки кода человеко-машинных интерфейсов по графическим макетам».
