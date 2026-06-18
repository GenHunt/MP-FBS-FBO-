"""
BUILD.md - Guide to build standalone .exe executable
"""

# 🔨 Руководство по сборке .exe

Это руководство описывает, как упаковать приложение в самостоятельный файл .exe, который можно распространять без установки Python.

## 📋 Требования

- **Python 3.10+** на компьютере сборки
- **Windows** (для сборки Windows приложения)
- **Место на диске:** ~500 МБ для процесса сборки
- Все зависимости установлены: `pip install -r requirements.txt`

## 🚀 Быстрая сборка (5 минут)

### Способ 1: Автоматическая сборка (Рекомендуется)

```bash
# 1. Откройте командную строку в папке проекта
cd MP-FBS-FBO-

# 2. Убедитесь, что зависимости установлены
pip install -r requirements.txt

# 3. Запустите скрипт сборки
python build_exe.py
```

Готово! Файл `Ozon-FBS-Label-Printer.exe` появится в папке `dist/`

### Способ 2: Ручная сборка через PyInstaller

```bash
# Установите PyInstaller если еще не установлен
pip install pyinstaller

# Выполните команду сборки
pyinstaller main.py ^
    --name=Ozon-FBS-Label-Printer ^
    --windowed ^
    --onefile ^
    --add-data "data:data" ^
    --add-data "logs:logs" ^
    --hidden-import=PyQt6 ^
    --hidden-import=requests ^
    --hidden-import=PIL ^
    --collect-all=PyQt6
```

## 📦 Структура после сборки

```
dist/
├── Ozon-FBS-Label-Printer.exe    # ← Готовый файл для распространения!
└── ... другие файлы
```

## 🎯 Распространение .exe

### Для одного пользователя:

1. Скопируйте файл `Ozon-FBS-Label-Printer.exe` на компьютер
2. Запустите файл двойным кликом
3. При первом запуске Windows может показать предупреждение - это нормально

### Для команды / развертывания:

1. Создайте папку `Ozon-FBS-Label-Printer`
2. Скопируйте в папку:
   - `Ozon-FBS-Label-Printer.exe`
   - `.env` (с настройками)
   - `README.md` (инструкции)

3. Запакуйте в ZIP и распределите

## ⚙️ Кастомизация сборки

### Изменить иконку приложения

1. Создайте или найдите файл иконки `icon.ico` (256x256 или больше)
2. Поместите в корень проекта
3. При сборке иконка будет автоматически добавлена

### Изменить название в диспетчере задач

Отредактируйте `build_exe.py`:

```python
'--name=Ваше-Название-Приложения',
```

### Включить консоль для отладки

Измените `--windowed` на `--console` в `build_exe.py`

## 🐛 Решение проблем при сборке

### Ошибка: "No module named 'PyQt6'"

```bash
# Переустановите PyQt6
pip install --upgrade PyQt6
```

### Ошибка: "pyinstaller is not recognized"

```bash
# Убедитесь, что PyInstaller установлен
pip install pyinstaller
```

### .exe очень большой (300+ МБ)

Это нормально! PyInstaller включает весь Python интерпретатор и библиотеки.

Для оптимизации:

```bash
# Используйте UPX упаковщик (опционально)
# Скачайте с https://upx.github.io/ и поместите в PATH
pyinstaller main.py --upx-dir=. ...
```

### Приложение не запускается из .exe

1. Запустите из командной строки для просмотра ошибки:
   ```bash
   Ozon-FBS-Label-Printer.exe
   ```

2. Проверьте логи в папке `logs/`

3. Убедитесь, что `.env` файл присутствует в той же папке

## 🔐 Безопасность при распространении

⚠️ **ВАЖНО:** Никогда не делитесь:
- API ключами в `.env` файле
- Лог-файлами с личной информацией

Для каждого пользователя:
1. Отправьте только `.exe` файл
2. Попросите их создать свой `.env` с их ключами
3. Или используйте защищенное хранилище ключей

## 📝 Версионирование сборок

Создавайте разные версии:

```bash
# Для версии 1.1.0
pyinstaller main.py --name=Ozon-FBS-Label-Printer-v1.1.0 --onefile --windowed
```

## 🔄 Автоматическая сборка (CI/CD)

Для GitHub Actions добавьте `.github/workflows/build.yml`:

```yaml
name: Build EXE

on:
  push:
    branches: [main]
  release:
    types: [created]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python build_exe.py
      - uses: actions/upload-artifact@v2
        with:
          name: Ozon-FBS-Label-Printer
          path: dist/Ozon-FBS-Label-Printer.exe
```

## ✅ Чек-лист перед распространением

- [ ] Приложение работает корректно в режиме разработки
- [ ] Все тесты пройдены
- [ ] `.exe` файл создан без ошибок
- [ ] `.exe` запускается и работает на чистом компьютере
- [ ] API ключи НЕ включены в дистрибутив
- [ ] Документация обновлена
- [ ] Версия обновлена в коде

## 📊 Типичные размеры

| Конфигурация | Размер |
|-------------|--------|
| Только основное приложение | ~150 МБ |
| С PyQt6 | ~250 МБ |
| С UPX сжатием | ~100 МБ |

## 🎉 Готово!

Теперь вы можете распространять приложение как самостоятельный .exe файл!

---

**Версия:** 1.1.0  
**Последнее обновление:** 2026-06-18
