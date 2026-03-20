from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


def _settings_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    return base / "WindowsSystemSuite"


SETTINGS_PATH = _settings_dir() / "settings.json"
HISTORY_PATH = _settings_dir() / "action-history.jsonl"

DEFAULT_SETTINGS = {
    "theme": "dark",
    "last_tab": 0,
    "history_enabled": True,
}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return DEFAULT_SETTINGS.copy()
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return DEFAULT_SETTINGS.copy()

    merged = DEFAULT_SETTINGS.copy()
    if isinstance(data, dict):
        merged.update(data)
    if merged.get("theme") not in {"dark", "light"}:
        merged["theme"] = DEFAULT_SETTINGS["theme"]
    try:
        merged["last_tab"] = max(0, int(merged.get("last_tab", 0)))
    except Exception:  # noqa: BLE001
        merged["last_tab"] = 0
    return merged


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def append_history(entry: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        **entry,
    }
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_history(limit: int = 200) -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    rows: list[dict] = []
    for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows[-max(1, min(5000, int(limit))):]


def clear_history() -> None:
    if HISTORY_PATH.exists():
        HISTORY_PATH.unlink()
