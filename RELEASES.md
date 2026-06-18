# 🚀 Автоматические релизы и .exe сборки

Этот документ описывает, как в репозитории работает автоматическая сборка `.exe` и публикация в GitHub Releases.

## Что автоматизировано

Workflow: `.github/workflows/build.yml`

На каждый:
- push в `main`
- push тега (например `v1.2.0`)
- публикацию GitHub Release

выполняется:
1. Сборка `.exe` в Windows (`windows-latest`)
2. Python `3.10`
3. Загрузка артефакта в Actions (хранение **30 дней**)
4. Публикация `.exe` в GitHub Releases (для tag/release событий)

## Как создать новый релиз

### Вариант 1 (рекомендуется): через GitHub UI

1. Откройте вкладку **Releases** в репозитории  
   https://github.com/GenHunt/MP-FBS-FBO-/releases
2. Нажмите **Draft a new release**
3. Укажите тег (например, `v1.2.0`)
4. Нажмите **Publish release**
5. Workflow автоматически соберёт и прикрепит `Ozon-FBS-Label-Printer.exe`

### Вариант 2: через git tag

```bash
git tag v1.2.0
git push origin v1.2.0
```

После пуша тега workflow соберёт `.exe` и опубликует его в релизе по тегу.

## Где скачать готовый .exe

Пользователям нужно:
1. Открыть страницу Releases:  
   https://github.com/GenHunt/MP-FBS-FBO-/releases
2. Выбрать последнюю версию
3. Скачать `Ozon-FBS-Label-Printer.exe` из секции **Assets**

## Диагностика и troubleshooting

### 1) Workflow упал на этапе зависимостей
- Проверьте `requirements.txt`
- Убедитесь, что все зависимости совместимы с Python 3.10

### 2) `.exe` не появился в релизе
- Проверьте, что событие было `tag push` или `release published`
- Убедитесь, что job завершился успешно
- Проверьте шаг `Publish executable to GitHub Release` в логах

### 3) Файл есть в Actions, но не в Releases
- Откройте run в **Actions**
- Скачайте артефакт вручную из секции Artifacts (доступен 30 дней)

## Лучшие практики

- Используйте семантические теги: `vMAJOR.MINOR.PATCH` (например, `v1.3.0`)
- Перед релизом проверяйте `README.md`, `BUILD.md` и этот документ
- Добавляйте release notes с изменениями для пользователей
- Не публикуйте секреты и ключи в релизных артефактах
