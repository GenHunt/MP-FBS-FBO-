# Автоматическая сборка Windows EXE через GitHub Actions

Этот документ описывает, как использовать встроенный workflow GitHub Actions для автоматической сборки `OzonFbsLabelPrinter.exe` на облачном Windows-раннере без необходимости иметь локальную машину Windows.

---

## Содержание

- [Как это работает](#как-это-работает)
- [Шаг 1 — Создать GitHub-репозиторий](#шаг-1--создать-github-репозиторий)
- [Шаг 2 — Загрузить код в репозиторий](#шаг-2--загрузить-код-в-репозиторий)
- [Шаг 3 — Перейти в Actions и запустить сборку вручную](#шаг-3--перейти-в-actions-и-запустить-сборку-вручную)
- [Шаг 4 — Скачать артефакт](#шаг-4--скачать-артефакт)
- [Сборка по тегу и автоматический GitHub Release](#сборка-по-тегу-и-автоматический-github-release)
- [Секреты Ozon и безопасность](#секреты-ozon-и-безопасность)
- [Что происходит внутри workflow](#что-происходит-внутри-workflow)
- [Решение проблем](#решение-проблем)

---

## Как это работает

Файл `.github/workflows/build-windows-exe.yml` описывает pipeline, который:

1. Запускает виртуальную машину **Windows Latest** (Windows Server 2022) в облаке GitHub.
2. Устанавливает Python 3.11, все зависимости проекта, PyInstaller и pywin32.
3. Выполняет проверки: синтаксис Python, headless-запуск, тесты.
4. Собирает `OzonFbsLabelPrinter.exe` через PyInstaller.
5. Упаковывает папку `dist/OzonFbsLabelPrinter` в zip-архив.
6. Загружает архив как артефакт (доступен 30 дней).
7. Если сборка запущена по тегу `v*` — создаёт GitHub Release и прикладывает zip.

---

## Шаг 1 — Создать GitHub-репозиторий

1. Войдите на [github.com](https://github.com).
2. Нажмите кнопку **«+»** → **«New repository»**.
3. Введите имя репозитория, например `ozon-fbs-label-app`.
4. Выберите **Private** (рекомендуется — ключи Ozon не нужны для сборки, но лучше хранить код приватно).
5. **Не** инициализируйте репозиторий через GitHub (не добавляйте README, .gitignore — они уже есть в проекте).
6. Нажмите **«Create repository»**.
7. Скопируйте URL репозитория вида `https://github.com/ВАШ_ЛОГИН/ozon-fbs-label-app.git`.

---

## Шаг 2 — Загрузить код в репозиторий

Откройте терминал (Windows: PowerShell или Git Bash, Linux/macOS: bash) в папке проекта `ozon_fbs_label_app/`:

```bash
# 1. Инициализировать git (если ещё не сделано)
git init

# 2. Добавить все файлы в коммит
git add .

# 3. Проверить, что settings.json не добавлен (должен быть в .gitignore)
git status

# 4. Создать первый коммит
git commit -m "Initial commit"

# 5. Переименовать ветку в main (если нужно)
git branch -M main

# 6. Добавить удалённый репозиторий
git remote add origin https://github.com/ВАШ_ЛОГИН/ozon-fbs-label-app.git

# 7. Отправить код
git push -u origin main
```

> **Проверьте перед отправкой:** убедитесь, что файл `settings.json` с вашими API-ключами **не** входит в коммит (`git status` должен его не показывать — он в `.gitignore`).

---

## Шаг 3 — Перейти в Actions и запустить сборку вручную

1. Откройте ваш репозиторий на GitHub.
2. Перейдите на вкладку **«Actions»** (верхнее меню).
3. В левой панели найдите workflow **«Build Windows EXE»**.
4. Нажмите **«Run workflow»** → **«Run workflow»** (зелёная кнопка).
5. Workflow запустится. Прогресс можно отследить в реальном времени, кликнув на запуск.

Сборка занимает **3–7 минут** (большая часть времени — установка PySide6).

### Когда ещё запускается workflow автоматически

- **При push в ветку `main` или `master`** — каждый раз, когда вы отправляете изменения.
- **При создании тега `v*`** — например `v1.0.0`, `v1.2.3` (см. ниже).

---

## Шаг 4 — Скачать артефакт

1. После успешного завершения workflow перейдите на страницу запуска (кликните на его название в списке).
2. Прокрутите вниз до раздела **«Artifacts»**.
3. Нажмите на **«OzonFbsLabelPrinter-windows»** — начнётся скачивание zip-архива.
4. Распакуйте архив. Внутри будет папка `OzonFbsLabelPrinter/`.
5. Запустите `OzonFbsLabelPrinter.exe`.

> **Важно:** не перемещайте только `.exe` — запускайте всю папку `OzonFbsLabelPrinter/` целиком. Все вспомогательные файлы (runtime Python, Qt, шаблоны) находятся рядом с exe.

---

## Сборка по тегу и автоматический GitHub Release

При создании тега вида `v1.0.0` GitHub Actions автоматически:

1. Собирает EXE.
2. Создаёт **GitHub Release** с именем тега.
3. Прикладывает `OzonFbsLabelPrinter-windows.zip` к релизу.

### Как создать тег и Release

```bash
# Локально — создать и отправить тег
git tag v1.0.0
git push origin v1.0.0
```

Или через GitHub UI:
1. Перейдите **Releases** → **«Draft a new release»**.
2. В поле **«Choose a tag»** введите `v1.0.0` и нажмите **«+ Create new tag: v1.0.0 on publish»**.
3. Нажмите **«Publish release»**.

После публикации workflow запустится автоматически, соберёт EXE и прикрепит zip к релизу. Через 5–7 минут zip появится на странице Release в разделе **«Assets»** — его можно скачать напрямую без входа в GitHub.

### Именование версий

Используйте семантическое версионирование: `v<MAJOR>.<MINOR>.<PATCH>` (например `v1.0.0`, `v1.1.0`, `v2.0.0`).

---

## Секреты Ozon и безопасность

**Для сборки EXE секреты Ozon не нужны.**

Workflow использует `--no-gui` / mock-режим для проверок — никаких реальных запросов к API Ozon не делается. Ваши ключи (`Client-Id`, `Api-Key`) хранятся только в локальном `settings.json`, который:

- добавлен в `.gitignore` и **не попадает в репозиторий**,
- не нужен при сборке EXE,
- вводится пользователем вручную в интерфейсе уже готового приложения на его Windows-машине.

> **Никогда не добавляйте ключи Ozon в переменные окружения GitHub Actions** — в этом нет необходимости, и это создаёт угрозу безопасности.

Единственный токен, который используется — стандартный `GITHUB_TOKEN`, автоматически выдаваемый GitHub для создания Release. Он не требует настройки.

---

## Что происходит внутри workflow

| Шаг | Описание |
|---|---|
| Checkout | Скачивает код вашего репозитория |
| Set up Python 3.11 | Устанавливает Python 3.11 на Windows-раннер |
| Cache pip | Кэширует скачанные пакеты по хэшу `requirements.txt` |
| Install dependencies | `pip install -r requirements.txt`, `pyinstaller`, `pywin32` |
| Check syntax | `python -m compileall app run.py -q` — проверяет синтаксис |
| Headless smoke test | `python run.py --no-gui` — mock-запуск без GUI |
| Run tests | `pytest tests/ -q` — запускает все тесты |
| Build with PyInstaller | `pyinstaller --noconfirm --clean OzonFbsLabelPrinter.spec` |
| Pack dist into zip | Упаковывает `dist\OzonFbsLabelPrinter` → `OzonFbsLabelPrinter-windows.zip` |
| Upload artifact | Загружает zip как артефакт Actions (хранится 30 дней) |
| Create GitHub Release | Только при теге `v*` — создаёт Release и прикладывает zip |

---

## Решение проблем

**Тест не проходит — ошибка в headless-режиме**

Убедитесь, что `python run.py --no-gui` успешно работает локально на Linux или Windows. Mock-режим не требует ключей Ozon.

**PyInstaller не находит модуль**

Добавьте модуль в список `hiddenimports` в файле `OzonFbsLabelPrinter.spec` и пересоберите.

**Release не создался**

Проверьте, что тег начинается с `v` (например `v1.0.0`, не `1.0.0`). Убедитесь, что в настройках репозитория Actions имеют право записи: **Settings → Actions → General → Workflow permissions → Read and write permissions**.

**Артефакт не появился**

Если шаг «Build with PyInstaller» упал — zip не создаётся. Смотрите логи шагов «Check syntax», «Headless smoke test», «Run tests» и «Build with PyInstaller».

---

## Ссылки

- [Файл workflow](.github/workflows/build-windows-exe.yml)
- [PyInstaller spec](OzonFbsLabelPrinter.spec)
- [Инструкция по сборке локально на Windows](README_EXE.md)
- [GitHub Actions документация](https://docs.github.com/en/actions)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)
