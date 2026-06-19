#Requires -Version 5.0
<#
.SYNOPSIS
    Сборка и запуск OzonFbsLabelPrinter.exe — один клик!

.DESCRIPTION
    Скрипт автоматически:
      1. Находит Python (предпочтение: 3.12, 3.11, 3.10, py -3, python)
      2. Проверяет совместимость: версия 3.10-3.13, 64-bit, CPython
      3. Создаёт виртуальное окружение .venv
      4. Устанавливает зависимости (requirements.txt + pyinstaller + pywin32)
      5. Запускает быструю проверку кода и тесты
      6. Собирает OzonFbsLabelPrinter.exe через PyInstaller
      7. Открывает папку с результатом и предлагает запустить приложение

.EXAMPLE
    # Запустить из PowerShell в папке проекта:
    .\START_WINDOWS.ps1

    # Если скрипты отключены — запустить в обход политики:
    powershell -ExecutionPolicy Bypass -File START_WINDOWS.ps1

.NOTES
    Если PowerShell выдаёт ошибку "Выполнение скриптов отключено",
    выполните один раз в PowerShell (от администратора):
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

    Требования к Python для PySide6:
      - Python 3.10, 3.11, 3.12 или 3.13 (64-bit)
      - CPython (с python.org)
      - Рекомендуется: Python 3.11 или 3.12 64-bit
#>

[CmdletBinding()]
param()

# Принудительно UTF-8 в выводе
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$Host.UI.RawUI.WindowTitle = "OzonFbsLabelPrinter — Сборка и запуск"
$ErrorActionPreference = "Stop"

# Переходим в папку проекта (там, где лежит этот скрипт)
Set-Location -Path $PSScriptRoot

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

function Write-Header([string]$Message) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Blue
    Write-Host "  $Message" -ForegroundColor White
    Write-Host "============================================================" -ForegroundColor Blue
    Write-Host ""
}

function Write-Step([int]$Num, [int]$Total, [string]$Message) {
    Write-Host ""
    Write-Host "[$Num/$Total] $Message" -ForegroundColor Cyan
}

function Write-OK([string]$Message) {
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Warn([string]$Message) {
    Write-Host "  [ПРЕДУПРЕЖДЕНИЕ] $Message" -ForegroundColor Yellow
}

function Write-Fail([string]$Message) {
    Write-Host ""
    Write-Host "  [ОШИБКА] $Message" -ForegroundColor Red
}

function Exit-WithPause([string]$Message) {
    Write-Fail $Message
    Write-Host ""
    Write-Host "Нажмите Enter для закрытия окна..." -ForegroundColor Gray
    Read-Host | Out-Null
    exit 1
}

function Invoke-SafeCommand {
    param(
        [scriptblock]$Command,
        [string]$ErrorMessage,
        [switch]$WarnOnly
    )
    try {
        & $Command
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
            if ($WarnOnly) {
                Write-Warn $ErrorMessage
                return $false
            }
            Exit-WithPause $ErrorMessage
        }
    } catch {
        if ($WarnOnly) {
            Write-Warn "$ErrorMessage ($($_.Exception.Message))"
            return $false
        }
        Exit-WithPause "$ErrorMessage`n$($_.Exception.Message)"
    }
    return $true
}

# ---------------------------------------------------------------------------
# Функция проверки Python на совместимость с PySide6
# ---------------------------------------------------------------------------

function Test-PythonCompatibility {
    param([string]$Cmd, [string[]]$CmdArgs = @())

    # Inline-скрипт проверки
    $checkCode = @"
import sys
v = sys.version_info
arch = '64bit' if sys.maxsize > 2**32 else '32bit'
impl = sys.implementation.name
ok = (v >= (3, 10) and v < (3, 14) and arch == '64bit' and impl == 'cpython')
print('PYCHECK_VERSION=' + '.'.join(str(x) for x in v[:3]))
print('PYCHECK_ARCH=' + arch)
print('PYCHECK_IMPL=' + impl)
print('PYCHECK_PATH=' + sys.executable)
print('PYCHECK_OK=' + ('1' if ok else '0'))
"@

    try {
        $result = & $Cmd @CmdArgs -c $checkCode 2>&1
        if ($LASTEXITCODE -ne 0) { return $null }

        $info = @{}
        foreach ($line in $result) {
            if ($line -match '^([^=]+)=(.*)$') {
                $info[$Matches[1]] = $Matches[2]
            }
        }
        return $info
    } catch {
        return $null
    }
}

# ---------------------------------------------------------------------------
# Заголовок
# ---------------------------------------------------------------------------

Write-Header "Ozon FBS Label Printer — Сборка и запуск (один клик!)"

# Подсказка по ExecutionPolicy
$policy = Get-ExecutionPolicy -Scope CurrentUser -ErrorAction SilentlyContinue
if ($policy -eq "Restricted" -or $policy -eq "Undefined") {
    Write-Warn "ExecutionPolicy = $policy. Если возникают проблемы с запуском скриптов, выполните:"
    Write-Host "    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Write-Host "  Или запустите напрямую:" -ForegroundColor Yellow
    Write-Host "    powershell -ExecutionPolicy Bypass -File START_WINDOWS.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# ---------------------------------------------------------------------------
# ШАГ 0: Поиск Python (предпочтение: 3.12 > 3.11 > 3.10 > py -3 > python)
# ---------------------------------------------------------------------------

Write-Step 0 6 "Поиск Python (3.10-3.13, 64-bit, CPython)..."

$pythonCmd = $null
$pythonArgs = @()
$pyInfo = $null

# Список кандидатов в порядке предпочтения
$candidates = @(
    @{ Cmd = "py"; Args = @("-3.12"); Label = "py -3.12" },
    @{ Cmd = "py"; Args = @("-3.11"); Label = "py -3.11" },
    @{ Cmd = "py"; Args = @("-3.10"); Label = "py -3.10" },
    @{ Cmd = "py"; Args = @("-3");    Label = "py -3"    },
    @{ Cmd = "python"; Args = @();   Label = "python"    }
)

foreach ($candidate in $candidates) {
    $cmdName = $candidate.Cmd
    $cmdArgs = $candidate.Args
    $label   = $candidate.Label

    # Проверить, доступна ли команда
    $found = Get-Command $cmdName -ErrorAction SilentlyContinue
    if (-not $found) { continue }

    # Пробуем запустить с аргументами
    & $cmdName @cmdArgs --version 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { continue }

    Write-Host "  Найден: $label" -ForegroundColor Gray

    # Проверяем совместимость
    $info = Test-PythonCompatibility -Cmd $cmdName -CmdArgs $cmdArgs
    if ($null -eq $info) { continue }

    Write-Host "    Версия      : $($info['PYCHECK_VERSION'])" -ForegroundColor Gray
    Write-Host "    Архитектура : $($info['PYCHECK_ARCH'])" -ForegroundColor Gray
    Write-Host "    Реализация  : $($info['PYCHECK_IMPL'])" -ForegroundColor Gray
    Write-Host "    Путь        : $($info['PYCHECK_PATH'])" -ForegroundColor Gray

    if ($info['PYCHECK_OK'] -eq '1') {
        Write-OK "Совместим с PySide6: $label (Python $($info['PYCHECK_VERSION']), $($info['PYCHECK_ARCH']))"
        $pythonCmd  = $cmdName
        $pythonArgs = $cmdArgs
        $pyInfo     = $info
        break
    } else {
        Write-Warn "$label не совместим с PySide6 (нужен Python 3.10-3.13, 64-bit, CPython)"
    }
}

if (-not $pythonCmd) {
    Exit-WithPause @"
Не найден совместимый Python для PySide6!

Требования:
  - Python 3.10, 3.11, 3.12 или 3.13
  - 64-bit (x64)
  - CPython (с python.org)

Рекомендуется: Python 3.11 или 3.12 (64-bit).

Что сделать:
  1. Скачайте Python 3.11 или 3.12 (64-bit) с https://www.python.org/downloads/windows/
  2. При установке отметьте: Add python.exe to PATH
  3. Удалите папку .venv (если есть)
  4. Запустите этот скрипт снова.

Для детальной диагностики запустите: CHECK_PYTHON_WINDOWS.bat
"@
}

# ---------------------------------------------------------------------------
# ШАГ 1: Виртуальное окружение
# ---------------------------------------------------------------------------

Write-Step 1 6 "Подготовка виртуального окружения .venv..."

# Проверить существующий .venv
if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "  .venv уже существует. Проверяем его совместимость..." -ForegroundColor Gray

    $venvInfo = Test-PythonCompatibility -Cmd ".venv\Scripts\python.exe"

    if ($null -ne $venvInfo -and $venvInfo['PYCHECK_OK'] -eq '1') {
        Write-OK "Существующий .venv совместим (Python $($venvInfo['PYCHECK_VERSION']), $($venvInfo['PYCHECK_ARCH']))."
    } else {
        $venvVer  = if ($null -ne $venvInfo) { $venvInfo['PYCHECK_VERSION'] } else { "неизвестна" }
        $venvArch = if ($null -ne $venvInfo) { $venvInfo['PYCHECK_ARCH'] }    else { "неизвестна" }

        Write-Host ""
        Write-Host "  [ПРЕДУПРЕЖДЕНИЕ] Существующий .venv создан несовместимым Python:" -ForegroundColor Yellow
        Write-Host "    Версия: $venvVer, Архитектура: $venvArch" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Удалите папку .venv и запустите скрипт снова." -ForegroundColor Yellow
        Write-Host "  Новый .venv будет создан с правильным Python ($($pyInfo['PYCHECK_VERSION']) $($pyInfo['PYCHECK_ARCH']))." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Нажмите Enter для закрытия..." -ForegroundColor Gray
        Read-Host | Out-Null
        exit 1
    }
} elseif (Test-Path ".venv") {
    Write-Host "  .venv существует, но python.exe не найден внутри. Создаём заново..." -ForegroundColor Gray
    & $pythonCmd @pythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Exit-WithPause "Не удалось создать виртуальное окружение."
    }
    Write-OK "Виртуальное окружение пересоздано."
} else {
    Write-Host "  Создаём .venv с Python $($pyInfo['PYCHECK_VERSION']) ($($pyInfo['PYCHECK_ARCH']))..." -ForegroundColor Gray
    & $pythonCmd @pythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Exit-WithPause "Не удалось создать виртуальное окружение.`nУбедитесь, что Python установлен корректно."
    }
    Write-OK "Виртуальное окружение создано."
}

# Пути к исполняемым файлам внутри venv
$venvPython = ".\.venv\Scripts\python.exe"
$venvPip    = ".\.venv\Scripts\pip.exe"

if (-not (Test-Path $venvPython)) {
    Exit-WithPause "Python не найден в .venv: $venvPython`nПопробуйте удалить папку .venv и запустить снова."
}

Write-OK "Виртуальное окружение готово."

# ---------------------------------------------------------------------------
# ШАГ 2: Установка зависимостей
# ---------------------------------------------------------------------------

Write-Step 2 6 "Установка зависимостей (может занять 2-5 минут при первом запуске)..."
Write-Host "  Python  : $($pyInfo['PYCHECK_VERSION']) ($($pyInfo['PYCHECK_ARCH']))" -ForegroundColor Gray
Write-Host "  Команда : $pythonCmd $($pythonArgs -join ' ')" -ForegroundColor Gray

# Обновить pip
Write-Host "  Обновление pip..." -ForegroundColor Gray
& $venvPython -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Не удалось обновить pip — продолжаем..."
}

# requirements.txt
Write-Host "  Установка requirements.txt..." -ForegroundColor Gray
& $venvPip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  [ОШИБКА] Не удалось установить зависимости из requirements.txt." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Если ошибка касается PySide6 (No matching distribution found):" -ForegroundColor Yellow
    Write-Host "    Причина: несовместимый Python (32-bit или неподдерживаемая версия)." -ForegroundColor Yellow
    Write-Host "    Решение: установите Python 3.11 или 3.12 (64-bit) с https://www.python.org/" -ForegroundColor Yellow
    Write-Host "             удалите папку .venv и запустите скрипт снова." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Для диагностики запустите: CHECK_PYTHON_WINDOWS.bat" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Нажмите Enter для закрытия..." -ForegroundColor Gray
    Read-Host | Out-Null
    exit 1
}

# pytest
Write-Host "  Установка pytest (для проверки)..." -ForegroundColor Gray
& $venvPip install pytest --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Не удалось установить pytest — тесты будут пропущены."
}

# PyInstaller + pywin32
Write-Host "  Установка PyInstaller и pywin32 (для сборки EXE)..." -ForegroundColor Gray
& $venvPip install pyinstaller pywin32 --quiet
if ($LASTEXITCODE -ne 0) {
    Exit-WithPause @"
Не удалось установить PyInstaller или pywin32.
Возможно, антивирус блокирует установку — добавьте папку проекта в исключения.
"@
}

Write-OK "Все зависимости установлены."

# ---------------------------------------------------------------------------
# ШАГ 3: Проверка кода
# ---------------------------------------------------------------------------

Write-Step 3 6 "Быстрая проверка кода..."

# Компиляция
Write-Host "  Компиляция модулей..." -ForegroundColor Gray
& $venvPython -m compileall app run.py -q
if ($LASTEXITCODE -ne 0) {
    Exit-WithPause "Найдены синтаксические ошибки в коде!`nПроверьте файлы в папке app\ и run.py."
}
Write-OK "Компиляция прошла успешно."

# Headless-проверка
Write-Host "  Headless-проверка приложения (без GUI)..." -ForegroundColor Gray
& $venvPython run.py --no-gui
if ($LASTEXITCODE -ne 0) {
    Exit-WithPause "Headless-проверка завершилась с ошибкой.`nСмотрите детали выше."
}
Write-OK "Headless-проверка прошла успешно."

# Тесты (опционально)
if (Test-Path "tests") {
    $pytestPath = ".\.venv\Scripts\pytest.exe"
    if (Test-Path $pytestPath) {
        Write-Host "  Запуск тестов..." -ForegroundColor Gray
        & $pytestPath tests -q --tb=short
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "Некоторые тесты не прошли. Сборка продолжается."
        } else {
            Write-OK "Все тесты прошли."
        }
    } else {
        Write-Warn "pytest не найден в .venv — пропускаем тесты."
    }
} else {
    Write-OK "Папка tests не найдена — тесты пропущены."
}

# ---------------------------------------------------------------------------
# ШАГ 4: Сборка EXE
# ---------------------------------------------------------------------------

Write-Step 4 6 "Сборка OzonFbsLabelPrinter.exe через PyInstaller..."
Write-Host "  (Это может занять 2-5 минут — пожалуйста, подождите...)" -ForegroundColor Gray
Write-Host ""

$pyinstallerExe = ".\.venv\Scripts\pyinstaller.exe"

if (-not (Test-Path $pyinstallerExe)) {
    Exit-WithPause "PyInstaller не найден в .venv: $pyinstallerExe"
}

& $pyinstallerExe --noconfirm --clean OzonFbsLabelPrinter.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  [ОШИБКА] Сборка завершилась с ошибкой!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Возможные причины:" -ForegroundColor Yellow
    Write-Host "    1. Антивирус блокирует PyInstaller." -ForegroundColor Yellow
    Write-Host "       Добавьте папку проекта в исключения и запустите снова." -ForegroundColor Yellow
    Write-Host "    2. Недостаточно прав." -ForegroundColor Yellow
    Write-Host "       Запустите PowerShell от имени администратора." -ForegroundColor Yellow
    Write-Host "    3. Конфликт зависимостей." -ForegroundColor Yellow
    Write-Host "       Удалите папку .venv и запустите этот скрипт снова." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Подробный лог: build\OzonFbsLabelPrinter\" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Нажмите Enter для закрытия..." -ForegroundColor Gray
    Read-Host | Out-Null
    exit 1
}

# ---------------------------------------------------------------------------
# ШАГ 5: Проверка результата
# ---------------------------------------------------------------------------

Write-Step 5 6 "Проверка результата..."

$exeRelPath = "dist\OzonFbsLabelPrinter\OzonFbsLabelPrinter.exe"

if (-not (Test-Path $exeRelPath)) {
    Exit-WithPause "EXE-файл не найден после сборки: $exeRelPath`nПроверьте лог выше."
}

$exeItem   = Get-Item $exeRelPath
$exeSizeMB = [math]::Round($exeItem.Length / 1MB, 1)
$exeFullPath  = $exeItem.FullName
$distFolderFull = (Get-Item "dist\OzonFbsLabelPrinter").FullName

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ГОТОВО! Приложение собрано успешно!" -ForegroundColor Green
Write-Host ""
Write-Host "  Исполняемый файл:" -ForegroundColor White
Write-Host "    $exeFullPath" -ForegroundColor Cyan
Write-Host "    Размер: $exeSizeMB МБ" -ForegroundColor Gray
Write-Host ""
Write-Host "  Папка с приложением (можно скопировать куда угодно):" -ForegroundColor White
Write-Host "    $distFolderFull" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# ---------------------------------------------------------------------------
# ШАГ 6: Открыть папку и предложить запустить
# ---------------------------------------------------------------------------

Write-Step 6 6 "Открываем папку с приложением..."

Start-Process explorer.exe -ArgumentList $distFolderFull

Write-Host ""
$launch = Read-Host "Запустить приложение сейчас? [Y/N]"

if ($launch -eq "Y" -or $launch -eq "y" -or $launch -eq "д" -or $launch -eq "Д") {
    Write-Host ""
    Write-Host "  Запускаем OzonFbsLabelPrinter.exe..." -ForegroundColor Cyan
    Start-Process -FilePath $exeFullPath
    Write-OK "Приложение запущено."
} else {
    Write-Host ""
    Write-Host "  Чтобы запустить позже — откройте:" -ForegroundColor Gray
    Write-Host "  $exeFullPath" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "  Для повторной сборки запустите START_WINDOWS.ps1 снова." -ForegroundColor Gray
Write-Host ""
Write-Host "Нажмите Enter для закрытия окна..." -ForegroundColor Gray
Read-Host | Out-Null
