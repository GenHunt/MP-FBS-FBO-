#Requires -Version 5.0
<#
.SYNOPSIS
    Сборка OzonFbsLabelPrinter.exe для Windows

.DESCRIPTION
    Скрипт создаёт виртуальное окружение, устанавливает зависимости,
    PyInstaller, pywin32 и собирает EXE-приложение.

    Результат: dist\OzonFbsLabelPrinter\OzonFbsLabelPrinter.exe

.EXAMPLE
    # Открыть PowerShell в папке проекта и выполнить:
    .\build_exe.ps1

.NOTES
    Если PowerShell выдаёт ошибку "Выполнение скриптов отключено",
    запустите в PowerShell от имени администратора:
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    Или запустите этот скрипт напрямую:
        powershell -ExecutionPolicy Bypass -File build_exe.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "OzonFbsLabelPrinter — Сборка EXE"

# Принудительно UTF-8 в выводе
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

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

function Exit-WithError([string]$Message) {
    Write-Fail $Message
    Write-Host ""
    Write-Host "Нажмите Enter для выхода..." -ForegroundColor Gray
    Read-Host
    exit 1
}

# ---------------------------------------------------------------------------
# Заголовок
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Blue
Write-Host "  Сборка OzonFbsLabelPrinter.exe" -ForegroundColor White
Write-Host "  Ozon FBS Label — печать этикеток для FBS-отправлений" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Blue
Write-Host ""

# ---------------------------------------------------------------------------
# Подсказка по ExecutionPolicy
# ---------------------------------------------------------------------------

$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq "Restricted" -or $policy -eq "Undefined") {
    Write-Warn "Текущий ExecutionPolicy: $policy"
    Write-Host "  Если скрипт не запускается, выполните в PowerShell (от администратора):" -ForegroundColor Yellow
    Write-Host "    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Write-Host "  Или запустите напрямую:" -ForegroundColor Yellow
    Write-Host "    powershell -ExecutionPolicy Bypass -File build_exe.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# ---------------------------------------------------------------------------
# Шаг 0: Проверка Python
# ---------------------------------------------------------------------------

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Exit-WithError @"
Python не найден.
Скачайте и установите Python 3.11+ с https://python.org/
При установке отметьте "Add Python to PATH"
"@
}

$pyVersion = & python --version 2>&1
Write-OK "Python: $pyVersion"

# ---------------------------------------------------------------------------
# Шаг 1: Виртуальное окружение
# ---------------------------------------------------------------------------

Write-Step 1 5 "Создание виртуального окружения .venv ..."

if (Test-Path ".venv") {
    Write-OK "Виртуальное окружение уже существует, используем его."
} else {
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError "Не удалось создать виртуальное окружение."
    }
    Write-OK "Виртуальное окружение создано."
}

# Пути внутри venv
$venvPython = ".\.venv\Scripts\python.exe"
$venvPip    = ".\.venv\Scripts\pip.exe"

if (-not (Test-Path $venvPython)) {
    Exit-WithError "Python не найден в .venv: $venvPython"
}

Write-OK "Виртуальное окружение готово."

# ---------------------------------------------------------------------------
# Шаг 2: Обновление pip
# ---------------------------------------------------------------------------

Write-Step 2 5 "Обновление pip ..."

& $venvPython -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Не удалось обновить pip, продолжаем..."
} else {
    Write-OK "pip обновлён."
}

# ---------------------------------------------------------------------------
# Шаг 3: Установка зависимостей проекта
# ---------------------------------------------------------------------------

Write-Step 3 5 "Установка зависимостей из requirements.txt ..."

& $venvPip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Exit-WithError @"
Ошибка при установке зависимостей из requirements.txt.
Проверьте подключение к интернету и повторите попытку.
"@
}
Write-OK "Зависимости проекта установлены."

# ---------------------------------------------------------------------------
# Шаг 4: Установка PyInstaller и pywin32
# ---------------------------------------------------------------------------

Write-Step 4 5 "Установка PyInstaller и pywin32 ..."

& $venvPip install pyinstaller pywin32 --quiet
if ($LASTEXITCODE -ne 0) {
    Exit-WithError "Не удалось установить PyInstaller или pywin32."
}
Write-OK "PyInstaller и pywin32 установлены."

# ---------------------------------------------------------------------------
# Шаг 5: Сборка EXE
# ---------------------------------------------------------------------------

Write-Step 5 5 "Сборка приложения через PyInstaller ..."
Write-Host "  (Это может занять 1-3 минуты, пожалуйста подождите...)" -ForegroundColor Gray
Write-Host ""

$pyinstallerCmd = ".\.venv\Scripts\pyinstaller.exe"

& $pyinstallerCmd --clean --noconfirm OzonFbsLabelPrinter.spec
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  [ОШИБКА] Сборка завершилась с ошибкой." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Возможные причины:" -ForegroundColor Yellow
    Write-Host "    1. Антивирус блокирует PyInstaller." -ForegroundColor Yellow
    Write-Host "       Добавьте папку проекта в исключения антивируса." -ForegroundColor Yellow
    Write-Host "    2. Недостаточно прав — запустите PowerShell от администратора." -ForegroundColor Yellow
    Write-Host "    3. Конфликт зависимостей — удалите .venv и запустите снова." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Подробный лог сборки: build\OzonFbsLabelPrinter\" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Нажмите Enter для выхода..." -ForegroundColor Gray
    Read-Host
    exit 1
}

# ---------------------------------------------------------------------------
# Проверка результата
# ---------------------------------------------------------------------------

$exePath = "dist\OzonFbsLabelPrinter\OzonFbsLabelPrinter.exe"

if (Test-Path $exePath) {
    $exeInfo = Get-Item $exePath
    $exeSizeMB = [math]::Round($exeInfo.Length / 1MB, 1)
    $exeFullPath = $exeInfo.FullName

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  СБОРКА УСПЕШНА!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Исполняемый файл:" -ForegroundColor White
    Write-Host "    $exeFullPath" -ForegroundColor Cyan
    Write-Host "    Размер: $exeSizeMB МБ" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Папка с приложением:" -ForegroundColor White
    Write-Host "    $((Get-Item 'dist\OzonFbsLabelPrinter').FullName)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Для запуска: дважды щёлкните по OzonFbsLabelPrinter.exe" -ForegroundColor White
    Write-Host "  или скопируйте всю папку dist\OzonFbsLabelPrinter\ куда угодно." -ForegroundColor Gray
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""

    # Открыть папку с результатом
    Start-Process explorer.exe -ArgumentList "dist\OzonFbsLabelPrinter"
} else {
    Exit-WithError "EXE-файл не найден после сборки: $exePath`nПроверьте лог выше."
}

Write-Host "Нажмите Enter для выхода..." -ForegroundColor Gray
Read-Host
