# Fix Report: PySide6 Install Precheck

## Summary

Fixed one-click Windows build scripts to detect incompatible Python before attempting PySide6 installation. Added a dedicated diagnostic tool. Updated all README files.

---

## Changed Files

### 1. `START_WINDOWS.bat` (ASCII + CRLF, updated)

**Changes:**
- Python search order changed: `py -3.12` → `py -3.11` → `py -3.10` → `py -3` → `python`
- After selecting Python, runs a compatibility check:
  - Version must be ≥ 3.9 and < 3.14
  - Architecture must be 64-bit
  - Implementation must be CPython
- If check fails: prints clear ASCII error with instructions (install Python 3.11/3.12 64-bit from python.org, add to PATH), then exits without attempting pip install
- Before `pip install -r requirements.txt`: prints selected Python version and architecture
- If `pip install -r requirements.txt` fails: prints PySide6-specific hint (probable cause: 32-bit Python, fix: install 3.11/3.12 64-bit, delete .venv, rerun)
- If `.venv` already exists: checks its Python for compatibility; if incompatible, prints message asking user to delete `.venv` and rerun (does not auto-delete)
- No Cyrillic characters, ASCII only, CRLF line endings preserved

### 2. `START_WINDOWS.ps1` (UTF-8 + CRLF, updated)

**Changes:**
- Added `Test-PythonCompatibility` function that runs inline Python to check version, arch, implementation
- Python search order changed: `py -3.12` → `py -3.11` → `py -3.10` → `py -3` → `python`
- Each candidate is checked for PySide6 compatibility before selection
- If no compatible Python found: exit with detailed Russian-language instructions
- Step 1: checks existing `.venv` Python compatibility; if incompatible, asks user to delete `.venv` and rerun
- Step 2: prints selected Python version/arch before installing dependencies
- `pip install -r requirements.txt` failure: prints PySide6-specific hint in Russian
- Russian comments and messages; CRLF line endings

### 3. `CHECK_PYTHON_WINDOWS.bat` (ASCII + CRLF, new file)

New standalone diagnostic script. Checks all Python candidates (`py -3.12`, `py -3.11`, `py -3.10`, `py -3`, `python`) and for each found installation shows:
- Version, architecture, implementation, executable path
- PySide6 compatibility: OK or NOT OK

Final summary: "Compatible Python found" or "No compatible Python found" with fix instructions.

### 4. `README_ONE_CLICK.md` (updated)

- Step 0 table entry updated to show new search order and precheck
- New section: **Требования к Python для PySide6** — table showing OS, Python version, architecture, implementation requirements
- **Если Python не найден** section updated to recommend Python 3.11/3.12 64-bit explicitly
- New section: **Ошибка «No matching distribution found for PySide6»** — explains cause and 4-step fix
- Troubleshooting table: added `No matching distribution found for PySide6` row

### 5. `README_EXE.md` (updated)

- Requirements table: Python row updated to show 3.10/3.11/3.12/3.13 (64-bit, CPython), recommended 3.11 or 3.12
- Warning note updated to mention 32-bit Python, Microsoft Store Python, and link to python.org
- New section: **Ошибка «No matching distribution found for PySide6»** — explains cause and fix with CHECK_PYTHON_WINDOWS.bat reference

### 6. `README.md` (updated)

- Requirements section: Python bullet updated to 3.10–3.13 (64-bit CPython), recommended 3.11/3.12, lists unsupported variants
- Added note about PySide6 error with fix hint
- Build files table: added `CHECK_PYTHON_WINDOWS.bat` row
- Project structure: added `CHECK_PYTHON_WINDOWS.bat` entry

---

## Verification Results

```
file START_WINDOWS.bat:
  DOS batch file, ASCII text, with very long lines (391), with CRLF line terminators

file CHECK_PYTHON_WINDOWS.bat:
  DOS batch file, ASCII text, with CRLF line terminators

file START_WINDOWS.ps1:
  Unicode text, UTF-8 text, with CRLF line terminators

ASCII purity (BAT files):
  OK   START_WINDOWS.bat: pure ASCII
  OK   CHECK_PYTHON_WINDOWS.bat: pure ASCII

CRLF check:
  START_WINDOWS.bat:        CRLF=280, LF-only=0
  CHECK_PYTHON_WINDOWS.bat: CRLF=121, LF-only=0
  START_WINDOWS.ps1:        CRLF=477, LF-only=0

python3 -m compileall app run.py -q  →  exit 0
python3 run.py --no-gui              →  exit 0 (3 mock postings OK)
python3 -m pytest tests/ -q          →  57 passed in 0.47s, exit 0
```

---

## No functional code changes

Files in `app/`, `run.py`, `requirements.txt`, `conftest.py`, and `tests/` were not modified.
