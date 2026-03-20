# Windows System Suite

Modern Windows troubleshooting and tuning dashboard built with PySide6.

## Modules

- Network Doctor
- Driver + Service Inspector
- Startup Optimizer
- Storage Rescue Center
- Permission Fix Wizard
- Windows Repair Runner
- Gaming Tune Switcher
- Privacy Toggle Board

## Phase 2 Additions

- Busy progress indicator while commands run
- `Copy Output` and `Export Report` tools
- Startup quick-open actions (Startup Apps settings + Task Manager startup tab)
- One-click gaming presets (balanced gaming / quiet)
- Expanded network actions (`ipconfig /all`)

## Phase 3 Additions

- Safety + Rollback tab
- Create Restore Point action (`Checkpoint-Computer`)
- Open System Restore UI action
- Rollback presets:
  - Restore Balanced Defaults
  - Restore Privacy Defaults
- Action history logging (toggleable)
- History viewer and history clear controls

## Dependencies

```powershell
py -m pip install --upgrade pip
py -m pip install PySide6 PySide6-Addons
```

## Run From Source

```powershell
cd C:\Users\your-username\Documents\windows-system-suite
py main.py
```

## Build Windows EXE (PyInstaller)

### Build requirements

```powershell
py -m pip install --upgrade pip pyinstaller
py -m pip install PySide6 PySide6-Addons
```

### Build command

```powershell
cd C:\Users\your-username\Documents\windows-system-suite
build-windows.bat
```

Output:

- `dist\WindowsSystemSuite\WindowsSystemSuite.exe`

Optional icon:

- Add `app_icon.ico` to project root before build.
