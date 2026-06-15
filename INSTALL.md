"""
INSTALL.md - Detailed installation and setup guide
"""

# Подробное руководство по установке

## 1. Системные требования

- **Windows 7, 8, 10, 11** (64-bit рекомендуется)
- **Python 3.10 или выше** (загрузить с https://www.python.org/)
- **Принтер Xprinter XP-365B** или совместимый
- **Минимум 200 МБ свободного места**

## 2. Установка Python

### Способ A: Прямая загрузка

1. Перейдите на https://www.python.org/downloads/
2. Загрузите Python 3.10+ для Windows
3. Запустите установщик
4. **ВАЖНО:** Отметьте "Add Python to PATH"
5. Нажмите "Install Now"

### Способ B: Через Microsoft Store

1. Откройте Microsoft Store
2. Поищите "Python"
3. Нажмите "Get" для установки

### Проверка установки

Откройте командную строку и выполните:

```bash
python --version
```

Должна показать Python 3.10 или выше.

## 3. Клонирование репозитория

### Способ A: Через Git

```bash
git clone https://github.com/GenHunt/MP-FBS-FBO-.git
cd MP-FBS-FBO-
```

### Способ B: Загрузка ZIP

1. Перейдите на https://github.com/GenHunt/MP-FBS-FBO-
2. Нажмите "Code" → "Download ZIP"
3. Распакуйте архив
4. Откройте папку в командной строке

## 4. Установка зависимостей

Откройте командную строку в папке проекта:

```bash
pip install -r requirements.txt
```

Процесс установки может занять 2-5 минут.

## 5. Конфигурация

### Шаг 1: Копирование примера конфигурации

```bash
copy .env.example .env
```

### Шаг 2: Получение Ozon API ключей

1. Откройте https://seller.ozon.ru/
2. Войдите в личный кабинет
3. Перейдите в **Настройки** → **Доступ к API**
4. Скопируйте:
   - **Client ID**
   - **API Key**

### Шаг 3: Редактирование .env файла

Откройте файл `.env` в блокноте:

```env
# Ozon API Configuration
OZON_CLIENT_ID=your_client_id_here
OZON_API_KEY=your_api_key_here

# Printer Settings
PRINTER_NAME=Xprinter XP-365B
DEFAULT_PRINTER_DPI=203
```

Замените `your_client_id_here` и `your_api_key_here` на ваши данные.

### Шаг 4: Проверка названия принтера

Узнайте точное название вашего принтера:

```bash
powershell -Command "Get-Printer | Select-Object -ExpandProperty Name"
```

Скопируйте название принтера и обновите `.env`.

## 6. Первый запуск

```bash
python main.py
```

Приложение должно открыться окно с интерфейсом.

## 7. Первичная настройка в приложении

1. В верхней части окна введите **Client ID** и **API Key**
2. Нажмите **"✓ Подключиться"**
3. Дождитесь сообщения **"✅ Подключено к Ozon"**

## Решение проблем установки

### Ошибка: "python is not recognized"

**Решение:** Python не добавлен в PATH. Переустановите Python и отметьте "Add Python to PATH".

### Ошибка: "No module named 'PyQt6'"

**Решение:** Зависимости не установлены. Выполните:

```bash
pip install -r requirements.txt
```

### Ошибка: "Failed to connect to Ozon API"

**Решение:** 
- Проверьте правильность Client ID и API Key
- Убедитесь в наличии интернета
- Проверьте, что IP не заблокирован

### Принтер не печатает

**Решение:**
1. Убедитесь, что принтер включен и подключен
2. Проверьте название принтера:
   ```bash
   powershell -Command "Get-Printer | Select-Object -ExpandProperty Name"
   ```
3. Обновите название в `.env` или в Настройках приложения
4. Проверьте логи в вкладке "Логи"

### Ошибка "Permission denied"

**Решение:** Запустите командную строку от администратора.

## Обновление приложения

Для обновления на новую версию:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

## Удаление приложения

Просто удалите папку проекта. Все данные хранятся локально в папке `data/`.

## Антивирус

Приложение может быть заблокировано антивирусом из-за использования PowerShell для печати. Если так произойдет:

1. Добавьте папку проекта в исключения антивируса
2. Или отключите защиту для этого приложения

## Техническая поддержка

Если проблема не решена:

1. Проверьте файл логов: `logs/ozon_label_printer.log`
2. Откройте Issue на GitHub с описанием ошибки
3. Приложите скриншот ошибки и содержимое логов
