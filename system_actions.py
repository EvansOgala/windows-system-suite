from __future__ import annotations

import ctypes
import os
import subprocess
from pathlib import Path


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001
        return False


def relaunch_as_admin() -> bool:
    try:
        import sys

        executable = sys.executable
        script = Path(sys.argv[0]).resolve()
        params = "" if getattr(sys, "frozen", False) else f'"{script}"'
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        return int(result) > 32
    except Exception:  # noqa: BLE001
        return False


def run_command(cmd: list[str], timeout: int = 180) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    output = ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    return p.returncode == 0, output


def run_powershell(command: str, timeout: int = 180) -> tuple[bool, str]:
    return run_command(["powershell", "-NoProfile", "-Command", command], timeout=timeout)


def network_actions() -> dict[str, list[str]]:
    return {
        "Ping 1.1.1.1": ["ping", "1.1.1.1", "-n", "4"],
        "IP Config (/all)": ["ipconfig", "/all"],
        "Flush DNS": ["ipconfig", "/flushdns"],
        "Winsock Reset": ["netsh", "winsock", "reset"],
        "IP Release": ["ipconfig", "/release"],
        "IP Renew": ["ipconfig", "/renew"],
    }


def repair_actions() -> dict[str, list[str]]:
    return {
        "SFC Scan": ["sfc", "/scannow"],
        "DISM ScanHealth": ["dism", "/online", "/cleanup-image", "/scanhealth"],
        "DISM RestoreHealth": ["dism", "/online", "/cleanup-image", "/restorehealth"],
    }


def privacy_actions() -> dict[str, list[str]]:
    return {
        "Disable Telemetry": [
            "reg",
            "add",
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "/v",
            "AllowTelemetry",
            "/t",
            "REG_DWORD",
            "/d",
            "0",
            "/f",
        ],
        "Enable Telemetry (Default)": [
            "reg",
            "delete",
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "/v",
            "AllowTelemetry",
            "/f",
        ],
        "Disable Advertising ID": [
            "reg",
            "add",
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
            "/v",
            "Enabled",
            "/t",
            "REG_DWORD",
            "/d",
            "0",
            "/f",
        ],
        "Enable Advertising ID": [
            "reg",
            "add",
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
            "/v",
            "Enabled",
            "/t",
            "REG_DWORD",
            "/d",
            "1",
            "/f",
        ],
    }


def startup_actions() -> dict[str, list[str]]:
    return {
        "Open Startup Apps Settings": ["cmd", "/c", "start", "", "ms-settings:startupapps"],
        "Open Startup Tab (Task Manager)": ["cmd", "/c", "start", "", "taskmgr", "/7"],
    }


def list_startup_entries() -> tuple[bool, str]:
    ps = (
        "Get-CimInstance Win32_StartupCommand | "
        "Select-Object Name, Command, Location, User | "
        "Format-Table -AutoSize | Out-String -Width 4096"
    )
    return run_powershell(ps, timeout=120)


def inspect_drivers_and_services() -> tuple[bool, str]:
    ps = (
        "$badDrv = Get-PnpDevice -PresentOnly | Where-Object {$_.Status -ne 'OK'} | "
        "Select-Object Class, FriendlyName, Status, Problem; "
        "$badSvc = Get-CimInstance Win32_Service | Where-Object {$_.StartMode -eq 'Auto' -and $_.State -ne 'Running'} | "
        "Select-Object Name, DisplayName, State, StartMode; "
        "'=== Drivers (non-OK) ==='; "
        "if($badDrv){$badDrv | Format-Table -AutoSize}else{'None'}; "
        "'`n=== Auto Services Not Running ==='; "
        "if($badSvc){$badSvc | Format-Table -AutoSize}else{'None'}"
    )
    return run_powershell(ps, timeout=150)


def power_profile_actions() -> dict[str, list[str]]:
    return {
        "List Power Schemes": ["powercfg", "/list"],
        "Set High Performance": ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
        "Set Balanced": ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
        "Set Power Saver": ["powercfg", "/setactive", "a1841308-3541-4fab-bc81-f71556f20b4a"],
    }


def gaming_preset_actions() -> dict[str, list[list[str]]]:
    return {
        "Apply Balanced Gaming Preset": [
            ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
            ["cmd", "/c", "reg", "add", r"HKCU\Software\Microsoft\GameBar", "/v", "AutoGameModeEnabled", "/t", "REG_DWORD", "/d", "1", "/f"],
        ],
        "Apply Quiet Preset": [
            ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
        ],
    }


def rollback_preset_actions() -> dict[str, list[list[str]]]:
    return {
        "Restore Balanced Defaults": [
            ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
            ["cmd", "/c", "reg", "add", r"HKCU\Software\Microsoft\GameBar", "/v", "AutoGameModeEnabled", "/t", "REG_DWORD", "/d", "0", "/f"],
        ],
        "Restore Privacy Defaults": [
            ["reg", "delete", r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection", "/v", "AllowTelemetry", "/f"],
            ["reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "/v", "Enabled", "/t", "REG_DWORD", "/d", "1", "/f"],
        ],
    }


def create_restore_point(description: str = "WindowsSystemSuite") -> tuple[bool, str]:
    safe = (description or "WindowsSystemSuite").replace("'", "")
    ps = (
        "$ErrorActionPreference='Stop'; "
        f"Checkpoint-Computer -Description '{safe}' -RestorePointType MODIFY_SETTINGS | Out-String"
    )
    ok, out = run_powershell(ps, timeout=300)
    if ok:
        return True, out or "Restore point created."
    return False, out or "Restore point creation failed. Ensure System Protection is enabled."


def open_system_restore_ui() -> tuple[bool, str]:
    return run_command(["cmd", "/c", "start", "", "rstrui.exe"])


def storage_rescue_report(root: Path, limit: int = 60) -> tuple[bool, str]:
    root = root.expanduser()
    if not root.exists() or not root.is_dir():
        return False, f"Invalid path: {root}"
    items: list[tuple[int, Path]] = []
    for dirpath, _dirnames, filenames in os.walk(root, topdown=True, onerror=lambda _e: None):
        base = Path(dirpath)
        for name in filenames:
            fp = base / name
            try:
                size = fp.stat().st_size
            except Exception:  # noqa: BLE001
                continue
            items.append((size, fp))
    items.sort(key=lambda t: t[0], reverse=True)
    lines = [f"Scanned: {root}", f"Files seen: {len(items)}", ""]
    for size, path in items[: max(10, min(500, limit))]:
        lines.append(f"{size:>12} bytes  {path}")
    return True, "\n".join(lines)
