@echo off
setlocal

py -m pip install --upgrade pip pyinstaller
py -m pip install PySide6 PySide6-Addons

py -m PyInstaller --noconfirm --clean WindowsSystemSuite.spec

echo.
echo Build complete. Output: dist\WindowsSystemSuite\
if exist "app_icon.ico" (
  echo Using icon: app_icon.ico
) else (
  echo Tip: add app_icon.ico in this folder for a custom EXE icon.
)

endlocal
