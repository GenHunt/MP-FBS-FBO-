@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ============================================================
rem Ozon FBS Label Printer - one click build and run for Windows
rem This file intentionally uses ASCII only to avoid CMD encoding bugs.
rem ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   Ozon FBS Label Printer - Build and Run
echo ============================================================
echo.

rem ---------------------------------------------------------------------------
rem STEP 0: Find a suitable Python (prefer 3.12, then 3.11, 3.10, py -3, python)
rem ---------------------------------------------------------------------------

echo [0/6] Searching for Python (3.10-3.13, 64-bit, CPython)...
set "PYTHON_CMD="

py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.12"
    echo   Found: py -3.12
    goto check_python
)

py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.11"
    echo   Found: py -3.11
    goto check_python
)

py -3.10 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.10"
    echo   Found: py -3.10
    goto check_python
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    echo   Found: py -3
    goto check_python
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    echo   Found: python
    goto check_python
)

echo.
echo ERROR: Python was not found on this computer.
echo.
echo Please install Python 3.11 or 3.12 (64-bit) from:
echo   https://www.python.org/downloads/windows/
echo.
echo During installation enable: Add python.exe to PATH
echo Then run this file again.
echo.
pause
exit /b 1

:check_python
rem --- Run Python compatibility check ---
echo.
echo   Checking Python version and architecture...
%PYTHON_CMD% -c "import sys; v=sys.version_info; arch=('64bit' if sys.maxsize>2**32 else '32bit'); impl=sys.implementation.name; ok=(v>=(3,10) and v<(3,14) and arch=='64bit' and impl=='cpython'); print('PYCHECK_VERSION=' + '.'.join(str(x) for x in v[:3])); print('PYCHECK_ARCH=' + arch); print('PYCHECK_IMPL=' + impl); print('PYCHECK_OK=' + ('1' if ok else '0'))" > "%TEMP%\py_check.txt" 2>&1
if errorlevel 1 goto err_pycheck

rem Read results from temp file
for /f "usebackq tokens=1,2 delims==" %%A in ("%TEMP%\py_check.txt") do (
    if "%%A"=="PYCHECK_VERSION" set "PY_VERSION=%%B"
    if "%%A"=="PYCHECK_ARCH"    set "PY_ARCH=%%B"
    if "%%A"=="PYCHECK_IMPL"    set "PY_IMPL=%%B"
    if "%%A"=="PYCHECK_OK"      set "PY_OK=%%B"
)

echo   Python version : %PY_VERSION%
echo   Architecture   : %PY_ARCH%
echo   Implementation : %PY_IMPL%

if "%PY_OK%"=="1" (
    echo   OK: Python is compatible with PySide6.
    goto python_ok
)

echo.
echo ERROR: This Python is NOT compatible with PySide6.
echo.
echo   Required: Python 3.10-3.13, 64-bit, CPython
echo   Found   : Python %PY_VERSION%, %PY_ARCH%, %PY_IMPL%
echo.
echo   Recommended: Python 3.11 or 3.12 (64-bit) from https://www.python.org/
echo.
echo   Steps to fix:
echo     1. Download Python 3.11 or 3.12 64-bit from https://www.python.org/downloads/windows/
echo     2. During installation enable: Add python.exe to PATH
echo     3. Delete the .venv folder (if it exists)
echo     4. Run this file again.
echo.
echo   Run CHECK_PYTHON_WINDOWS.bat for a detailed compatibility report.
echo.
pause
exit /b 1

:err_pycheck
echo.
echo ERROR: Could not run Python compatibility check.
echo Unexpected error with: %PYTHON_CMD%
echo.
pause
exit /b 1

:python_ok
echo.
echo [1/6] Preparing virtual environment...

rem --- Check existing .venv Python compatibility ---
if exist ".venv\Scripts\python.exe" (
    echo   .venv already exists. Checking its Python compatibility...
    ".venv\Scripts\python.exe" -c "import sys; v=sys.version_info; arch=('64bit' if sys.maxsize>2**32 else '32bit'); impl=sys.implementation.name; ok=(v>=(3,10) and v<(3,14) and arch=='64bit' and impl=='cpython'); print('PYCHECK_OK=' + ('1' if ok else '0')); print('PYCHECK_VERSION=' + '.'.join(str(x) for x in v[:3])); print('PYCHECK_ARCH=' + arch)" > "%TEMP%\venv_check.txt" 2>&1
    set "VENV_OK=0"
    for /f "usebackq tokens=1,2 delims==" %%A in ("%TEMP%\venv_check.txt") do (
        if "%%A"=="PYCHECK_OK" set "VENV_OK=%%B"
        if "%%A"=="PYCHECK_VERSION" set "VENV_VERSION=%%B"
        if "%%A"=="PYCHECK_ARCH" set "VENV_ARCH=%%B"
    )
    if "!VENV_OK!"=="1" (
        echo   OK: .venv Python !VENV_VERSION! !VENV_ARCH! is compatible.
        goto venv_ready
    ) else (
        echo.
        echo   WARNING: Existing .venv was created with an incompatible Python
        echo            (version !VENV_VERSION!, !VENV_ARCH!).
        echo.
        echo   Please delete the .venv folder and run this file again.
        echo   The new .venv will be created with the correct Python.
        echo.
        pause
        exit /b 1
    )
) else (
    echo   Creating .venv with %PYTHON_CMD%...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto err_venv
    echo   OK: .venv created.
)

:venv_ready
set "VENV_PY=%CD%\.venv\Scripts\python.exe"

if not exist "%VENV_PY%" goto err_venv

echo.
echo [2/6] Installing dependencies...
echo   Python  : %PY_VERSION% (%PY_ARCH%)
echo   Command : %PYTHON_CMD%
echo.

"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto err_pip

if exist "requirements.txt" (
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 goto err_deps
) else (
    echo ERROR: requirements.txt not found.
    goto err_deps
)

"%VENV_PY%" -m pip install pytest pyinstaller pywin32
if errorlevel 1 goto err_deps

echo.
echo [3/6] Running quick checks...

"%VENV_PY%" -m compileall app run.py -q
if errorlevel 1 goto err_check

"%VENV_PY%" run.py --no-gui
if errorlevel 1 goto err_check

if exist "tests\" (
    "%VENV_PY%" -m pytest tests -q
    if errorlevel 1 goto err_check
) else (
    echo   Tests folder not found, skipping pytest.
)

echo.
echo [4/6] Building EXE with PyInstaller...

if not exist "OzonFbsLabelPrinter.spec" (
    echo ERROR: OzonFbsLabelPrinter.spec not found.
    goto err_build
)

"%VENV_PY%" -m PyInstaller --noconfirm --clean OzonFbsLabelPrinter.spec
if errorlevel 1 goto err_build

echo.
echo [5/6] Checking build result...

set "EXE_PATH=%CD%\dist\OzonFbsLabelPrinter\OzonFbsLabelPrinter.exe"

if not exist "%EXE_PATH%" (
    echo ERROR: EXE file was not created:
    echo %EXE_PATH%
    goto err_build
)

echo.
echo SUCCESS: EXE was created:
echo %EXE_PATH%
echo.

echo [6/6] Opening output folder...
explorer "%CD%\dist\OzonFbsLabelPrinter"

echo.
set /p RUN_NOW=Run application now? [Y/N]: 
if /I "%RUN_NOW%"=="Y" (
    start "" "%EXE_PATH%"
)

echo.
echo Done.
pause
exit /b 0

:err_venv
echo.
echo ERROR: Failed to create or use .venv.
echo Try deleting the .venv folder and run this file again.
pause
exit /b 1

:err_pip
echo.
echo ERROR: Failed to update pip.
echo Check your internet connection and try again.
pause
exit /b 1

:err_deps
echo.
echo ERROR: Failed to install dependencies.
echo.
echo   If the error mentions PySide6:
echo     Probable cause: unsupported Python version or 32-bit Python.
echo     Fix: Install Python 3.11 or 3.12 (64-bit) from https://www.python.org/
echo          Delete the .venv folder and run this file again.
echo.
echo   Otherwise: check your internet connection and Python installation.
echo   Run CHECK_PYTHON_WINDOWS.bat for a detailed compatibility report.
echo.
pause
exit /b 1

:err_check
echo.
echo ERROR: Project check failed.
echo Please copy the error text above and send it for debugging.
pause
exit /b 1

:err_build
echo.
echo ERROR: PyInstaller build failed.
echo Please copy the error text above and send it for debugging.
pause
exit /b 1
