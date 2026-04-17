# Публикация на GitHub

Каноническое имя репозитория: **figma-hmi-plugin**.  
Целевой URL: https://github.com/chuxitong/figma-hmi-plugin

Пока репозиторий на GitHub ещё называется `hmi-code-gen`, выгрузка идёт в него:

```bash
git remote set-url origin https://github.com/chuxitong/hmi-code-gen.git
git push origin master
```

## Переименование с hmi-code-gen в figma-hmi-plugin

1. На GitHub: **Settings** → **General** → **Repository name** → ввести `figma-hmi-plugin` → **Rename**. Старая ссылка обычно перенаправляется на новое имя.
2. Локально обновить remote:

```bash
git remote set-url origin https://github.com/chuxitong/figma-hmi-plugin.git
git remote -v
```

## Полная выгрузка текущего состояния

Из корня репозитория:

```bash
git add -A
git status
git commit -m "Figma HMI Plugin: полное обновление прототипа и материалов ВКР"
git push origin master
```

Если история на сервере расходится и нужно заменить содержимое ветки текущим деревом (осторожно):

```bash
git push origin master --force
```

Требуются учётные данные GitHub (Personal Access Token или SSH).

Файл `REPOSITORY.txt` в корне содержит только канонический URL репозитория.
