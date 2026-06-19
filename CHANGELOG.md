# Changelog

All notable changes to **Ozon FBS Label Printer** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] - 2026-06-19

### Added
- Full application source code created from scratch
- `main.py` — application entry point with logging initialisation
- `config.py` — centralised configuration (reads `.env`)
- `src/api/__init__.py` — `OzonAPIClient` for Ozon Seller API v3 FBS
- `src/models/shipment.py` — `Shipment` and `ShipmentItem` data models
- `src/models/template.py` — added `PrintType` enum
- `src/printing/__init__.py` — `LabelGenerator` (PIL + python-barcode)
- `src/database.py` — SQLite helper (`Database` class)
- `src/order_timing_analytics.py` — `OrderTimingAnalytics` for shipment timing insights
- `src/utils/__init__.py` — common utility helpers
- `src/ui/__init__.py` — UI package init
- `src/ui/tabs/shipments_tab.py` — FBS postings list with checkbox selection
- `src/ui/tabs/template_editor_tab.py` — drag-free template element editor
- `src/ui/tabs/logs_tab.py` — live log viewer with auto-refresh
- `data/` and `logs/` directories tracked via `.gitkeep`
- `.env.example` — environment variable template
- `LICENSE` — MIT licence
- Fixed `build_exe.py`:
  - Removed all emoji from `print()` calls (fixes `UnicodeEncodeError` on Windows)
  - Fixed `--add-data` separator (uses `;` on Windows, `:` elsewhere)
  - Added `win32print`, `win32api`, `pywintypes` to `--hidden-import`
  - Fixed `--buildpath` → `--workpath`
  - Added `PyQt6.QtCharts` hidden import

### Changed
- `requirements.txt` — verified package versions

---

## [1.0.0] - 2026-06-18

### Added
- Initial project structure (documentation, workflow, partial source)
- `build_exe.py` — initial build script
- `requirements.txt` — dependency list
- `.github/workflows/build.yml` — GitHub Actions CI/CD for Windows .exe
- Documentation: `README.md`, `BUILD.md`, `INSTALL.md`, `QUICKSTART.md`,
  `RELEASES.md`, `API_KEYS.md`
