# Ozon FBS Label App

Локальное Windows-приложение для получения и печати этикеток FBS-отправлений Ozon.

- Загружает список необработанных FBS-отправлений через Ozon Seller API
- Генерирует внутренние этикетки 58×40 мм (и других размеров) по настраиваемым шаблонам
- Получает и печатает маршрутные этикетки от Ozon (PDF, без изменений)
- Работает в **mock-режиме** без реального аккаунта Ozon — для разработки и тестирования
- На Linux/macOS сохраняет файлы вместо отправки на принтер

---

## Содержание

- [Требования](#требования)
- [Установка](#установка)
- [Запуск](#запуск)
- [Настройка API](#настройка-api)
- [Mock-режим](#mock-режим)
- [Шаблоны этикеток](#шаблоны-этикеток)
- [Печать](#печать)
- [Тесты](#тесты)
- [Самый простой вариант — один клик](#самый-простой-вариант--один-клик) — [README_ONE_CLICK.md](README_ONE_CLICK.md)
- [Сборка EXE (Windows)](#сборка-exe-windows) — [README_EXE.md](README_EXE.md)
- [Автоматическая сборка через GitHub Actions](#автоматическая-сборка-через-github-actions) — [README_GITHUB_ACTIONS.md](README_GITHUB_ACTIONS.md)
- [Безопасность](#безопасность)
- [Структура проекта](#структура-проекта)
- [TODO / Roadmap](#todo--roadmap)

---

## Требования

- **Python 3.10, 3.11, 3.12 или 3.13 (64-bit, CPython)**. Рекомендуется **3.11 или 3.12** с [python.org](https://www.python.org/downloads/windows/). Не поддерживаются: 32-bit Python, Python из Microsoft Store, PyPy.
- **Windows 10/11** (для полноценной печати; Linux/macOS работает в режиме сохранения файлов)
- Принтер этикеток 58 мм (например, Xprinter, TSC, Zebra, HPRT) — для реальной печати

> Если видите ошибку `No matching distribution found for PySide6` — удалите папку `.venv`, установите Python 3.11/3.12 (64-bit) и запустите `START_WINDOWS.bat` снова. Для диагностики запустите `CHECK_PYTHON_WINDOWS.bat`.

---

## Установка

```bat
:: Клонировать или скопировать проект
cd ozon_fbs_label_app

:: Создать виртуальное окружение (рекомендуется)
python -m venv .venv
.venv\Scripts\activate

:: Установить зависимости
pip install -r requirements.txt

:: Опционально: Windows-печать через win32api
pip install pywin32
```

**Linux/macOS (разработка, mock-режим):**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Запуск

```bat
:: Запустить GUI (Windows)
python run.py

:: Явный mock-режим
python run.py --mock

:: Headless-проверка (без GUI, для CI/тестов)
python run.py --no-gui

:: Подробный лог
python run.py --log-level DEBUG
```

---

## Настройка API

1. Войдите в [личный кабинет Ozon Seller](https://seller.ozon.ru/).
2. Перейдите в **Настройки → API-ключи**.
3. Создайте ключ с правами: `Заказы`, `Товары`, `Этикетки`.
4. Скопируйте **Client-Id** и **Api-Key**.
5. Введите их в верхней панели приложения и нажмите **«Сохранить настройки»**.
6. Снимите галочку **Mock-режим**.
7. Нажмите **«Обновить список»**.

> **Внимание:** настройки сохраняются в `settings.json` в папке проекта.
> Файл добавлен в `.gitignore` — не коммитьте его в репозиторий.

---

## Mock-режим

Mock-режим включён по умолчанию. В этом режиме:

- Никаких сетевых запросов не делается
- Возвращаются 3 тестовых отправления с разными товарами
- Генерируются реальные PDF-этикетки по шаблону
- Маршрутные этикетки генерируются как stub-PDF
- Файлы сохраняются в `output/print_jobs/`

Чтобы отключить mock-режим — снимите галочку в интерфейсе или передайте реальные ключи.

---

## Шаблоны этикеток

### Формат

Шаблоны хранятся в `templates/templates.json`. Структура шаблона:

```json
{
  "id": "uuid",
  "name": "Стандарт 58×40",
  "width_mm": 58.0,
  "height_mm": 40.0,
  "default": true,
  "elements": [
    {
      "type": "barcode",
      "x_mm": 3.0, "y_mm": 2.0, "w_mm": 52.0, "h_mm": 14.0,
      "variable": "barcode",
      "visible": true
    },
    {
      "type": "text",
      "x_mm": 1.0, "y_mm": 18.0, "w_mm": 56.0, "h_mm": 10.0,
      "variable": "product_name",
      "font_size": 7.0,
      "align": "left"
    }
  ]
}
```

### Переменные

| Переменная | Описание |
|---|---|
| `article` | Артикул карточки Ozon (fallback: `offer_id`) |
| `product_name` | Наименование товара |
| `barcode` | Штрихкод (EAN/GTIN) |
| `manufacturer_part_number` | Партномер производителя (MPN) |
| `offer_id` | Артикул продавца |
| `sku` | SKU (внутренний ID Ozon) |
| `posting_number` | Номер отправления |
| `order_number` | Номер заказа |
| `quantity` | Количество |
| `date` | Дата генерации (ДД.ММ.ГГГГ) |
| `time` | Время генерации (ЧЧ:ММ) |

### Редактор шаблонов

Кнопка **«Редактор шаблонов»** открывает диалог, где можно:

- Создавать, копировать, удалять шаблоны
- Редактировать элементы в таблице (координаты, переменные, шрифты, размеры)
- Просматривать предпросмотр (схематично или PDF→PNG при наличии `pdf2image`)
- Устанавливать шаблон по умолчанию

> **TODO:** Drag-and-drop элементов по предпросмотру будет добавлен в следующей версии.
> Пока координаты вводятся вручную (в мм).

---

## Печать

### Режимы печати

| Режим | Описание |
|---|---|
| **Внутренние** | Ваши этикетки 58×40 мм, сгенерированные по шаблону |
| **Маршрутные (Ozon)** | Готовые PDF от Ozon (не редактируются) |
| **Всё** | Оба типа поочерёдно |

### Выбор принтера

В выпадающем списке **«Принтер»** отображаются доступные принтеры. Если выбрать **«сохранить в файл»** — PDF сохраняется в `output/print_jobs/`.

### Windows (с pywin32)

Используется `win32api.ShellExecute("printto")` — прямая отправка на принтер без диалогов.

### Windows (без pywin32)

Используется `os.startfile(path, "print")` — открывает PDF через системный обработчик.

### Linux/macOS / Sandbox

Все задания сохраняются в `output/print_jobs/` с временными метками. Лог сохраняется в `output/print_jobs/print_log.txt`.

### Кнопка «Повторная печать»

Открывает папку `output/print_jobs/` в проводнике для повторной отправки сохранённых файлов.

---

## Тесты

```bash
# Запустить все тесты
pytest tests/ -v

# Только тесты без зависимостей от reportlab
pytest tests/test_label_context.py tests/test_template.py tests/test_ozon_client.py -v

# С покрытием (если установлен pytest-cov)
pytest tests/ --cov=app --cov-report=term-missing
```

Тесты не требуют реального аккаунта Ozon — все работают в mock-режиме.

---

## Самый простой вариант — один клик

Если вы хотите получить готовый EXE без лишних шагов — используйте **`START_WINDOWS.bat`**:

1. Дважды щёлкните по **`START_WINDOWS.bat`** в папке проекта.
2. Скрипт сам найдёт Python, создаст окружение, установит зависимости, проверит код и соберёт EXE.
3. По окончании сборки откроется папка с приложением.

Подробная инструкция: **[README_ONE_CLICK.md](README_ONE_CLICK.md)**

> **Примечание:** Путь к папке не должен содержать кириллицу и пробелы (например, `C:\Projects\ozon_fbs_label_app`).

---

## Сборка EXE (Windows)

EXE можно собрать **только на Windows** — PyInstaller не поддерживает кросс-компиляцию.
Подробное руководство: **[README_EXE.md](README_EXE.md)**.

### Быстрый старт

```bat
:: 1. Предварительная проверка (опционально)
smoke_test.bat

:: 2. Сборка (создаёт venv, устанавливает зависимости, собирает EXE)
build_exe.bat

:: 3. Результат
dist\OzonFbsLabelPrinter\OzonFbsLabelPrinter.exe
```

Альтернативно через PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

Или вручную:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller pywin32
pyinstaller --clean OzonFbsLabelPrinter.spec
```

### Файлы сборки

| Файл | Назначение |
|---|---|
| `OzonFbsLabelPrinter.spec` | PyInstaller spec с настройками (datas, hiddenimports, console=False) |
| `START_WINDOWS.bat` | **Один клик** — всё включено: venv, проверки, сборка, запуск |
| `START_WINDOWS.ps1` | То же самое через PowerShell (с цветным выводом) |
| `CHECK_PYTHON_WINDOWS.bat` | Диагностика: показывает все Python и совместимость с PySide6 |
| `build_exe.bat` | Автоматическая сборка — одна команда для Windows |
| `build_exe.ps1` | То же через PowerShell с подсказкой по ExecutionPolicy |
| `smoke_test.bat` | Проверка синтаксиса, headless-запуск и тесты перед сборкой |
| `README_EXE.md` | Подробное руководство, настройка Xprinter, советы по антивирусу |
| `README_ONE_CLICK.md` | Инструкция по запуску одним кликом |

> **SmartScreen:** при первом запуске собранного EXE нажмите «Подробнее» → «Выполнить в любом случае».
> Это стандартное поведение для неподписанных приложений.

---

## Автоматическая сборка через GitHub Actions

EXE можно собрать автоматически в облаке через GitHub Actions — без локальной Windows-машины.

- Workflow `.github/workflows/build-windows-exe.yml` запускается вручную, при push в `main`/`master` и при создании тега `v*`.
- Сборка выполняется на `windows-latest` раннере GitHub: установка зависимостей, проверки (compileall, headless-запуск, тесты), сборка EXE через PyInstaller.
- Результат доступен как артефакт Actions (30 дней) или автоматически прикладывается к GitHub Release при теге `v*`.
- **Секреты Ozon не нужны** — проверки работают в mock/no-gui режиме.

Подробная пошаговая инструкция: **[README_GITHUB_ACTIONS.md](README_GITHUB_ACTIONS.md)**

---

## Безопасность

- **API-ключи** хранятся в `settings.json` в папке проекта.
- `settings.json` добавлен в `.gitignore` — не попадёт в репозиторий случайно.
- Никогда не публикуйте `settings.json` и не передавайте ключи третьим лицам.
- Для командного использования рекомендуется шифрование ключей через `keyring` (Python) или Windows Credential Manager.
- Ключи в памяти не логируются. При включённом `DEBUG`-логировании — убедитесь, что лог-файлы не доступны посторонним.

---

## Структура проекта

```
ozon_fbs_label_app/
├── .github/
│   └── workflows/
│       └── build-windows-exe.yml # GitHub Actions: сборка EXE на windows-latest
├── run.py                        # Точка входа
├── requirements.txt
├── conftest.py                   # pytest настройка
├── settings.json                 # Настройки (в .gitignore, не коммитить)
├── .gitignore
├── LICENSE
├── README.md
├── README_EXE.md                 # Инструкция по сборке EXE (Windows)
├── README_GITHUB_ACTIONS.md      # Автоматическая сборка через GitHub Actions
├── OzonFbsLabelPrinter.spec      # PyInstaller spec-файл
├── START_WINDOWS.bat             # Один клик: venv + проверки + сборка + запуск
├── START_WINDOWS.ps1             # То же через PowerShell (цветной вывод)
├── build_exe.bat                 # Сборка EXE одной командой (Windows CMD)
├── build_exe.ps1                 # Сборка EXE через PowerShell
├── smoke_test.bat                # Проверка перед сборкой (compileall + headless + pytest)
├── CHECK_PYTHON_WINDOWS.bat      # Диагностика совместимости Python с PySide6
├── README_ONE_CLICK.md           # Инструкция: запуск одним кликом
│
├── app/
│   ├── api/
│   │   └── ozon_client.py        # Клиент Ozon Seller API + mock
│   ├── models/
│   │   ├── label_context.py      # Модель данных этикетки
│   │   └── template.py           # Шаблоны + сериализация
│   ├── services/
│   │   ├── label_generator.py    # PDF-генератор (reportlab)
│   │   ├── print_service.py      # Сервис печати (win32/shell/файл)
│   │   └── settings_manager.py   # Настройки (settings.json)
│   └── ui/
│       ├── main_window.py        # Главное окно (PySide6)
│       └── template_editor.py    # Редактор шаблонов (PySide6)
│
├── templates/
│   └── templates.json            # Шаблоны этикеток (создаётся автоматически)
│
├── output/
│   └── print_jobs/               # Сохранённые PDF (создаётся автоматически)
│       └── print_log.txt
│
└── tests/
    ├── test_label_context.py
    ├── test_template.py
    ├── test_label_generator.py
    ├── test_ozon_client.py
    └── test_settings_manager.py
```

---

## TODO / Roadmap

- [ ] Drag-and-drop элементов в редакторе шаблонов
- [ ] Поддержка нескольких кабинетов (мультиаккаунт)
- [ ] Асинхронное получение маршрутных этикеток (`/v1/posting/fbs/package-label/create` + get)
- [ ] Пакетная печать нескольких отправлений одним PDF
- [ ] Фильтрация списка отправлений (по статусу, дате, складу)
- [ ] Экспорт таблицы в Excel/CSV
- [ ] Интеграция с keyring для безопасного хранения ключей
- [ ] Авто-обновление списка по таймеру
- [ ] Уведомления о новых отправлениях
- [ ] Поддержка QR-кода в шаблонах

---

## Лицензия

MIT — см. [LICENSE](LICENSE).
