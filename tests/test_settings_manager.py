"""
Тесты SettingsManager.
"""
import pytest
import sys
import os
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.settings_manager import SettingsManager, DEFAULTS


class TestSettingsManager:
    def _make_manager(self, initial: dict = None) -> SettingsManager:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            if initial:
                json.dump(initial, f)
            path = f.name
        mgr = SettingsManager(Path(path))
        return mgr, path

    def test_defaults_on_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        os.unlink(path)
        mgr = SettingsManager(Path(path))
        assert mgr.mock_mode is True
        assert mgr.client_id == ""
        os.unlink(path)

    def test_load_existing(self):
        mgr, path = self._make_manager({"client_id": "12345", "mock_mode": False})
        assert mgr.client_id == "12345"
        assert mgr.mock_mode is False
        os.unlink(path)

    def test_set_and_get(self):
        mgr, path = self._make_manager()
        mgr.set("client_id", "TEST-ID")
        assert mgr.get("client_id") == "TEST-ID"
        os.unlink(path)

    def test_save_and_reload(self):
        mgr, path = self._make_manager()
        mgr.set("client_id", "SAVED-ID")
        mgr.save()

        mgr2 = SettingsManager(Path(path))
        assert mgr2.client_id == "SAVED-ID"
        os.unlink(path)

    def test_update_and_save(self):
        mgr, path = self._make_manager()
        mgr.update_and_save({"client_id": "X", "api_key": "Y", "mock_mode": False})

        with open(path) as f:
            data = json.load(f)
        assert data["client_id"] == "X"
        assert data["mock_mode"] is False
        os.unlink(path)

    def test_property_shortcuts(self):
        mgr, path = self._make_manager({"mock_mode": False, "printer_inner": "MyPrinter"})
        assert mgr.mock_mode is False
        assert mgr.printer_inner == "MyPrinter"
        os.unlink(path)

    def test_corrupted_json_uses_defaults(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("{corrupted")
            path = f.name
        mgr = SettingsManager(Path(path))
        assert mgr.mock_mode is True  # default
        os.unlink(path)

    def test_unknown_key_returns_none(self):
        mgr, path = self._make_manager()
        assert mgr.get("totally_unknown_key_xyz") is None
        os.unlink(path)

    def test_new_keys_merged_with_defaults(self):
        """Если в файле есть доп. ключи — они сохраняются."""
        mgr, path = self._make_manager({"custom_field": "custom_value"})
        assert mgr.get("custom_field") == "custom_value"
        os.unlink(path)
