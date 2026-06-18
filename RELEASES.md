"""
RELEASES.md - Guide to automated .exe releases
"""

# 📦 Автоматическая сборка .exe через GitHub Actions

Теперь `.exe` файл **автоматически собирается и публикуется** при каждом релизе! 🎉

## 🚀 Как это работает?

### Автоматическая сборка срабатывает когда:

1. **Вы создаете Release** на GitHub
2. **Вы делаете push с тегом** (например, `v1.1.0`)
3. **Вы вручную запускаете workflow**

## 📝 Как создать релиз с .exe?

### Способ 1: Через интерфейс GitHub (Рекомендуется) ⭐

1. **Перейдите в репозиторий:** https://github.com/GenHunt/MP-FBS-FBO-

2. **Откройте Releases:**
   ```
   Code → Releases → Draft a new release
   ```

3. **Заполните форму:**
   ```
   Tag version: v1.1.0
   Release title: Version 1.1.0 - Fixed bugs
   Description: 
   - ✅ Fixed analytics bug
   - ✅ Improved UI
   - ✅ Better error handling
   ```

4. **Нажмите "Publish release"**

5. **GitHub Actions автоматически:**
   - ✅ Собирает `.exe` файл
   - ✅ Загружает в Release
   - ✅ Создает artifact на 30 дней

### Способ 2: Через командную строку (Git)

```bash
# Убедитесь, что все изменения закоммичены
git add .
git commit -m "Version 1.1.0"

# Создайте тег
git tag -a v1.1.0 -m "Release version 1.1.0"

# Отправьте тег на GitHub
git push origin v1.1.0
```

GitHub Actions автоматически создаст Release и загрузит `.exe`!

## 🔄 Процесс сборки

Когда вы создаете релиз:

```
1. GitHub Actions запускается на Windows
   ↓
2. Скачивает исходный код
   ↓
3. Устанавливает Python 3.10
   ↓
4. Устанавливает зависимости (requirements.txt)
   ↓
5. Запускает build_exe.py
   ↓
6. Создает Ozon-FBS-Label-Printer.exe (~250 МБ)
   ↓
7. Загружает в Release
   ↓
✅ Готово! Файл доступен для скачивания
```

⏱️ **Время сборки:** ~5-10 минут

## 📥 Как скачать .exe?

### Для пользователей:

1. Перейдите в **Releases:** https://github.com/GenHunt/MP-FBS-FBO-/releases

2. Найдите нужную версию (например, v1.1.0)

3. Скачайте **Ozon-FBS-Label-Printer.exe**

4. Запустите и используйте! 🎉

### Для разработчиков (в процессе разработки):

Если нужен последний `.exe` из main ветки:

1. Перейдите в **Actions:** https://github.com/GenHunt/MP-FBS-FBO-/actions

2. Найдите последний успешный run

3. Скачайте artifact `Ozon-FBS-Label-Printer`

## 🏷️ Рекомендуемая схема версий

Используйте **Semantic Versioning**:

```
v1.0.0   - Первый релиз
v1.1.0   - Новые функции
v1.1.1   - Исправление ошибок
v2.0.0   - Крупное обновление
```

### Примеры тегов:

```bash
git tag v1.0.0  # Первый релиз
git tag v1.1.0  # Аналитика добавлена
git tag v1.1.1  # Bugfix
git tag v2.0.0  # Полное переписание
```

## 📋 Типичный workflow разработки

### День 1: Начальный релиз

```bash
git push origin main
# Затем на GitHub создаете Release v1.0.0
# → GitHub Actions собирает .exe
# → Пользователи скачивают и используют
```

### День 5: Исправление ошибки

```bash
# Исправляете ошибку в коде
git commit -am "Fix analytics crash"
git tag v1.0.1
git push origin v1.0.1
# → Автоматически собирается новый .exe
# → Можно раздать пользователям
```

### День 15: Новая функция

```bash
# Добавляете новую функцию
git commit -am "Add export to Excel"
git tag v1.1.0
git push origin v1.1.0
# → Собирается .exe с новой функцией
```

## 🔍 Мониторинг сборки

### Проверить статус сборки:

1. Перейдите в **Actions:** https://github.com/GenHunt/MP-FBS-FBO-/actions/workflows/build.yml

2. Посмотрите последний run

3. Если зелёная галочка ✅ - сборка успешна

### Если сборка упала ❌

1. Нажмите на failed run

2. Посмотрите логи (обычно там видна ошибка)

3. Исправьте проблему в коде

4. Создайте новый тег

## 🛠️ Как GitHub Actions собирает .exe?

Workflow в `.github/workflows/build.yml` делает:

```yaml
1. Checkout - скачивает код
2. Setup Python - устанавливает Python 3.10
3. Install dependencies - pip install -r requirements.txt
4. Build EXE - python build_exe.py
5. Upload artifact - сохраняет для разработчиков
6. Create Release - загружает в Release для пользователей
```

## 📊 Артефакты vs Releases

### Artifacts (временные файлы)
- 📦 Хранятся 30 дней
- 🔗 Доступны в Actions → Run Details
- ✅ Идеально для CI/CD тестирования

### Releases (постоянные файлы)
- 💾 Хранятся навсегда
- 🔗 Доступны в Releases раздела
- ✅ Идеально для пользователей

## 🔐 Безопасность

### ✅ Безопасно:
- GitHub Actions выполняется на официальных серверах Microsoft
- Исходный код остается на GitHub
- Ключи не передаются в workflow

### ⚠️ Важно:
- **НЕ добавляйте** чувствительные данные в `.env`
- **НЕ включайте** API-ключи в git
- Каждый пользователь должен вводить свои ключи

## 🚨 Решение проблем

### Ошибка: "Build failed"

1. Посмотрите логи в Actions
2. Обычно причина: опечатка в коде или отсутствующая зависимость
3. Исправьте в коде
4. Создайте новый тег

### Ошибка: "PyInstaller not found"

Уже добавлена в `requirements.txt`, не должна быть!

### Файл не загружается в Release

Убедитесь, что `build_exe.py` создает файл в `dist/` папке:
```
dist/Ozon-FBS-Label-Printer.exe
```

## 💡 Советы

### Совет 1: Тестируйте локально перед релизом

```bash
python build_exe.py
# Проверьте, что dist/Ozon-FBS-Label-Printer.exe создалась
# Запустите и тестируйте
```

### Совет 2: Пишите информативные Release Notes

```
Version 1.1.0 - Major Update

✨ New Features:
- Added export to PDF
- Improved analytics dashboard

🐛 Bug Fixes:
- Fixed crash on startup
- Fixed printer detection

📚 Documentation:
- Added API reference
- Added troubleshooting guide
```

### Совет 3: Тегируйте стабильные версии

```bash
# ✅ Хорошо - релиз для пользователей
git tag v1.1.0
git tag v1.0.0

# ❌ Плохо - нестабильные версии
git tag nightly-2026-06-18
git tag test-build
```

## 📞 FAQ

**Q: Как часто делать релизы?**
A: При готовности новой функции или исправления. Обычно 1-2 раза в неделю.

**Q: Можно ли пересобрать старый .exe?**
A: Да! Просто создайте новый Release с тем же тегом (GitHub переудалит).

**Q: Что если я ошибся в названии версии?**
A: Удалите тег: `git tag -d v1.1.0` и создайте новый.

**Q: Можно ли запустить сборку вручную?**
A: Да! В Actions есть кнопка "Run workflow" для ручного запуска.

## 📈 Отслеживание версий

Текущая версия хранится в:
- 🏷️ Git tags: `v1.1.0`
- 📝 README.md: "Версия: 1.1.0"
- 🔧 Код: при необходимости в константах

## 🎉 Готово!

Теперь при каждом релизе:
1. Автоматически собирается `.exe`
2. Загружается в Release
3. Готов для распространения пользователям

---

**Версия:** 1.1.0  
**Последнее обновление:** 2026-06-18

## 📚 Дополнительные ссылки

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Releases на GitHub](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Semantic Versioning](https://semver.org/)
- [BUILD.md](BUILD.md) - Ручная сборка
