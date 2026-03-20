import os

from pyside_ui import WindowsSystemSuiteApp


def main():
    if os.name != "nt":
        raise SystemExit("Windows System Suite is intended for Windows.")
    WindowsSystemSuiteApp.run_app()


if __name__ == "__main__":
    main()
