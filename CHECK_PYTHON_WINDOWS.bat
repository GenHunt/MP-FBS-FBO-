@echo off
setlocal

rem ============================================================
rem CHECK_PYTHON_WINDOWS.bat
rem Checks all available Python installations for PySide6 compatibility.
rem ASCII only, CRLF line endings.
rem ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   Python Compatibility Check for PySide6
echo   OzonFbsLabelPrinter
echo ============================================================
echo.
echo   PySide6 requires:
echo     - Python 3.10, 3.11, 3.12 or 3.13 (64-bit)
echo     - CPython implementation (from python.org)
echo     - NOT 32-bit, NOT PyPy, NOT Microsoft Store Python
echo.
echo   Recommended: Python 3.11 or 3.12 64-bit from https://www.python.org/
echo.
echo ============================================================

set "ANY_OK=0"

rem Helper script written to temp, used for each candidate
echo import sys > "%TEMP%\pycheck_script.py"
echo v=sys.version_info >> "%TEMP%\pycheck_script.py"
echo arch='64bit' if sys.maxsize^>2**32 else '32bit' >> "%TEMP%\pycheck_script.py"
echo impl=sys.implementation.name >> "%TEMP%\pycheck_script.py"
echo ok=(v^>=(3,10) and v^<(3,14) and arch=='64bit' and impl=='cpython') >> "%TEMP%\pycheck_script.py"
echo status='OK   ' if ok else 'NOT OK'
echo print(f'  Version : {v.major}.{v.minor}.{v.micro}') >> "%TEMP%\pycheck_script.py"
echo print(f'  Arch    : {arch}') >> "%TEMP%\pycheck_script.py"
echo print(f'  Impl    : {impl}') >> "%TEMP%\pycheck_script.py"
echo print(f'  Path    : {sys.executable}') >> "%TEMP%\pycheck_script.py"
echo print(f'  PySide6 : {("OK - compatible" if ok else "NOT OK - incompatible")}') >> "%TEMP%\pycheck_script.py"

rem --- Check each candidate ---

echo.
echo [1] py -3.12
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo   Not found.
) else (
    py -3.12 "%TEMP%\pycheck_script.py"
    rem Check ok flag separately
    py -3.12 -c "import sys; v=sys.version_info; arch='64bit' if sys.maxsize>2**32 else '32bit'; impl=sys.implementation.name; ok=(v>=(3,10) and v<(3,14) and arch=='64bit' and impl=='cpython'); exit(0 if ok else 1)" >nul 2>&1
    if not errorlevel 1 set "ANY_OK=1"
)

echo.
echo [2] py -3.11
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo   Not found.
) else (
    py -3.11 "%TEMP%\pycheck_script.py"
    py -3.11 -c "import sys; v=sys.version_info; arch='64bit' if sys.maxsize>2**32 else '32bit'; impl=sys.implementation.name; ok=(v>=(3,10) and v<(3,14) and arch=='64bit' and impl=='cpython'); exit(0 if ok else 1)" >nul 2>&1
    if not errorlevel 1 set "ANY_OK=1"
)

echo.
echo [3] py -3.10
py -3.10 --version >nul 2>&1
if errorlevel 1 (
    echo   Not found.
) else (
    py -3.10 "%TEMP%\pycheck_script.py"
    py -3.10 -c "import sys; v=sys.version_info; arch='64bit' if sys.maxsize>2**32 else '32bit'; impl=sys.implementation.name; ok=(v>=(3,10) and v<(3,14) and arch=='64bit' and impl=='cpython'); exit(0 if ok else 1)" >nul 2>&1
    if not errorlevel 1 set "ANY_OK=1"
)

echo.
echo [4] py -3 (any installed via Python Launcher)
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo   Not found.
) else (
    py -3 "%TEMP%\pycheck_script.py"
    py -3 -c "import sys; v=sys.version_info; arch='64bit' if sys.maxsize>2**32 else '32bit'; impl=sys.implementation.name; ok=(v>=(3,10) and v<(3,14) and arch=='64bit' and impl=='cpython'); exit(0 if ok else 1)" >nul 2>&1
    if not errorlevel 1 set "ANY_OK=1"
)

echo.
echo [5] python (in PATH)
python --version >nul 2>&1
if errorlevel 1 (
    echo   Not found.
) else (
    python "%TEMP%\pycheck_script.py"
    python -c "import sys; v=sys.version_info; arch='64bit' if sys.maxsize>2**32 else '32bit'; impl=sys.implementation.name; ok=(v>=(3,10) and v<(3,14) and arch=='64bit' and impl=='cpython'); exit(0 if ok else 1)" >nul 2>&1
    if not errorlevel 1 set "ANY_OK=1"
)

echo.
echo ============================================================

if "%ANY_OK%"=="1" (
    echo   RESULT: Compatible Python found - PySide6 should install OK.
    echo   Run START_WINDOWS.bat to build the application.
) else (
    echo   RESULT: No compatible Python found for PySide6!
    echo.
    echo   ACTION REQUIRED:
    echo     1. Download Python 3.11 or 3.12 (64-bit) from:
    echo        https://www.python.org/downloads/windows/
    echo     2. Run the installer.
    echo     3. Enable: Add python.exe to PATH
    echo     4. Delete the .venv folder in the project (if it exists).
    echo     5. Run START_WINDOWS.bat again.
)

echo ============================================================
echo.
pause
exit /b 0
