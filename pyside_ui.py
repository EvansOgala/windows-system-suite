from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from suite_settings import append_history, clear_history, load_settings, read_history, save_settings
from system_actions import (
    create_restore_point,
    open_system_restore_ui,
    inspect_drivers_and_services,
    is_admin,
    list_startup_entries,
    startup_actions,
    gaming_preset_actions,
    rollback_preset_actions,
    network_actions,
    power_profile_actions,
    privacy_actions,
    relaunch_as_admin,
    repair_actions,
    run_command,
    storage_rescue_report,
)


class SystemSuiteWindow(QtWidgets.QMainWindow):
    command_done = QtCore.Signal(bool, str)
    status_msg = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.active_jobs = 0
        self.setWindowTitle("Windows System Suite")
        self.resize(1360, 900)
        self.command_done.connect(self._on_command_done)
        self.status_msg.connect(self._set_status)
        self._build_ui()
        self._apply_theme(self.settings.get("theme", "dark"))
        self.tabs.setCurrentIndex(int(self.settings.get("last_tab", 0)))
        self._set_status("Ready")

    def _build_ui(self):
        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        outer = QtWidgets.QVBoxLayout(root)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        header = QtWidgets.QHBoxLayout()
        outer.addLayout(header)
        title = QtWidgets.QLabel("Windows System Suite")
        title.setStyleSheet("font-size: 30px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch(1)
        self.admin_label = QtWidgets.QLabel("Admin: Yes" if is_admin() else "Admin: No")
        header.addWidget(self.admin_label)
        self.admin_btn = QtWidgets.QPushButton("Run As Admin")
        self.admin_btn.clicked.connect(self._relaunch_admin)
        header.addWidget(self.admin_btn)
        self.history_btn = QtWidgets.QPushButton("History")
        self.history_btn.clicked.connect(self._show_history)
        header.addWidget(self.history_btn)
        header.addWidget(QtWidgets.QLabel("Theme"))
        self.theme_box = QtWidgets.QComboBox()
        self.theme_box.addItems(["dark", "light"])
        self.theme_box.setCurrentText(self.settings.get("theme", "dark"))
        self.theme_box.currentTextChanged.connect(self._on_theme_change)
        header.addWidget(self.theme_box)
        self.history_toggle = QtWidgets.QCheckBox("Log Actions")
        self.history_toggle.setChecked(bool(self.settings.get("history_enabled", True)))
        self.history_toggle.toggled.connect(self._on_history_toggled)
        header.addWidget(self.history_toggle)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.setMinimumHeight(210)
        self.tabs.setMaximumHeight(340)

        self.tabs.addTab(self._tab_network_doctor(), "Network Doctor")
        self.tabs.addTab(self._tab_driver_service_inspector(), "Driver + Services")
        self.tabs.addTab(self._tab_startup_optimizer(), "Startup Optimizer")
        self.tabs.addTab(self._tab_storage_rescue(), "Storage Rescue")
        self.tabs.addTab(self._tab_permission_fix(), "Permission Fix")
        self.tabs.addTab(self._tab_repair_runner(), "Repair Runner")
        self.tabs.addTab(self._tab_gaming_tune(), "Gaming Tune")
        self.tabs.addTab(self._tab_privacy_board(), "Privacy Board")
        self.tabs.addTab(self._tab_safety_rollback(), "Safety + Rollback")

        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(260)

        self.main_split = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        self.main_split.addWidget(self.tabs)
        self.main_split.addWidget(self.output)
        self.main_split.setCollapsible(0, False)
        self.main_split.setCollapsible(1, False)
        self.main_split.setSizes([270, 520])
        outer.addWidget(self.main_split, 1)

        output_tools = QtWidgets.QHBoxLayout()
        outer.addLayout(output_tools)
        self.copy_btn = QtWidgets.QPushButton("Copy Output")
        self.copy_btn.clicked.connect(self._copy_output)
        output_tools.addWidget(self.copy_btn)
        self.export_btn = QtWidgets.QPushButton("Export Report")
        self.export_btn.clicked.connect(self._export_output)
        output_tools.addWidget(self.export_btn)
        output_tools.addStretch(1)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        output_tools.addWidget(self.progress, 1)

        self.status = QtWidgets.QLabel("Ready")
        outer.addWidget(self.status)

    def _tab_network_doctor(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        l.addLayout(row)
        for label, cmd in network_actions().items():
            b = QtWidgets.QPushButton(label)
            b.clicked.connect(lambda _=False, c=cmd, n=label: self._run_async(n, c))
            row.addWidget(b)
        row.addStretch(1)
        return w

    def _tab_driver_service_inspector(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout(w)
        b = QtWidgets.QPushButton("Run Inspector")
        b.clicked.connect(self._run_driver_inspector)
        l.addWidget(b)
        l.addWidget(QtWidgets.QLabel("Shows non-OK drivers + auto services not running."))
        l.addStretch(1)
        return w

    def _tab_startup_optimizer(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout(w)
        b = QtWidgets.QPushButton("List Startup Entries")
        b.clicked.connect(self._run_startup_listing)
        l.addWidget(b)
        row = QtWidgets.QHBoxLayout()
        l.addLayout(row)
        for label, cmd in startup_actions().items():
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(lambda _=False, c=cmd, n=label: self._run_async(n, c))
            row.addWidget(btn)
        row.addStretch(1)
        l.addWidget(QtWidgets.QLabel("Review startup load and disable unnecessary items in Task Manager/Settings."))
        l.addStretch(1)
        return w

    def _tab_storage_rescue(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        l.addLayout(row)
        row.addWidget(QtWidgets.QLabel("Path"))
        self.storage_path = QtWidgets.QLineEdit(str(Path.home()))
        row.addWidget(self.storage_path, 1)
        row.addWidget(QtWidgets.QLabel("Top N"))
        self.storage_limit = QtWidgets.QSpinBox()
        self.storage_limit.setRange(10, 500)
        self.storage_limit.setValue(80)
        row.addWidget(self.storage_limit)
        b = QtWidgets.QPushButton("Scan Largest Files")
        b.clicked.connect(self._run_storage_scan)
        row.addWidget(b)
        return w

    def _tab_permission_fix(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        l.addLayout(row)
        row.addWidget(QtWidgets.QLabel("Folder"))
        self.permission_path = QtWidgets.QLineEdit(str(Path.home()))
        row.addWidget(self.permission_path, 1)
        b = QtWidgets.QPushButton("Reset ACLs (icacls /reset /T /C)")
        b.clicked.connect(self._run_permission_fix)
        row.addWidget(b)
        l.addWidget(QtWidgets.QLabel("Use carefully on your own folders, not system roots."))
        l.addStretch(1)
        return w

    def _tab_repair_runner(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        l.addLayout(row)
        for label, cmd in repair_actions().items():
            b = QtWidgets.QPushButton(label)
            b.clicked.connect(lambda _=False, c=cmd, n=label: self._run_async(n, c, timeout=3600))
            row.addWidget(b)
        row.addStretch(1)
        return w

    def _tab_gaming_tune(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        l.addLayout(row)
        for label, cmd in power_profile_actions().items():
            b = QtWidgets.QPushButton(label)
            b.clicked.connect(lambda _=False, c=cmd, n=label: self._run_async(n, c))
            row.addWidget(b)
        row.addStretch(1)
        preset_row = QtWidgets.QHBoxLayout()
        l.addLayout(preset_row)
        for label, commands in gaming_preset_actions().items():
            b = QtWidgets.QPushButton(label)
            b.clicked.connect(lambda _=False, n=label, cmds=commands: self._run_batch_async(n, cmds))
            preset_row.addWidget(b)
        preset_row.addStretch(1)
        l.addWidget(QtWidgets.QLabel("Tip: High Performance profile may increase heat and power usage."))
        return w

    def _tab_privacy_board(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QGridLayout()
        l.addLayout(row)
        actions = list(privacy_actions().items())
        for i, (label, cmd) in enumerate(actions):
            b = QtWidgets.QPushButton(label)
            b.clicked.connect(lambda _=False, c=cmd, n=label: self._run_async(n, c))
            row.addWidget(b, i // 2, i % 2)
        l.addWidget(QtWidgets.QLabel("These toggles edit registry values. Run as Admin for system-wide changes."))
        return w

    def _tab_safety_rollback(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        l.addLayout(row)
        create_btn = QtWidgets.QPushButton("Create Restore Point")
        create_btn.clicked.connect(self._run_restore_point)
        row.addWidget(create_btn)
        open_btn = QtWidgets.QPushButton("Open System Restore")
        open_btn.clicked.connect(self._open_restore_ui)
        row.addWidget(open_btn)
        row.addStretch(1)

        rollback_row = QtWidgets.QHBoxLayout()
        l.addLayout(rollback_row)
        for label, commands in rollback_preset_actions().items():
            b = QtWidgets.QPushButton(label)
            b.clicked.connect(lambda _=False, n=label, cmds=commands: self._run_batch_async(n, cmds))
            rollback_row.addWidget(b)
        rollback_row.addStretch(1)

        tools_row = QtWidgets.QHBoxLayout()
        l.addLayout(tools_row)
        view_history = QtWidgets.QPushButton("View Action History")
        view_history.clicked.connect(self._show_history)
        tools_row.addWidget(view_history)
        clear_hist = QtWidgets.QPushButton("Clear History")
        clear_hist.clicked.connect(self._clear_history_clicked)
        tools_row.addWidget(clear_hist)
        tools_row.addStretch(1)

        l.addWidget(QtWidgets.QLabel("Use restore points before high-impact fixes."))
        l.addStretch(1)
        return w

    def _on_theme_change(self, theme: str):
        self.settings["theme"] = theme
        save_settings(self.settings)
        self._apply_theme(theme)

    def _on_tab_changed(self, idx: int):
        self.settings["last_tab"] = max(0, int(idx))
        save_settings(self.settings)

    def _on_history_toggled(self, checked: bool):
        self.settings["history_enabled"] = bool(checked)
        save_settings(self.settings)

    def _apply_theme(self, theme: str):
        if theme == "light":
            self.setStyleSheet("")
            return
        self.setStyleSheet(
            """
            QMainWindow { background-color: #0b1220; }
            QWidget { color: #f8fafc; }
            QLineEdit, QPlainTextEdit, QTabWidget::pane, QSpinBox, QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 6px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: 0;
                border-radius: 10px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2563eb; }
            QTabBar::tab {
                background: #334155;
                color: #e2e8f0;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 11px;
                margin-right: 4px;
            }
            QTabBar::tab:selected { background: #3b82f6; color: white; }
            """
        )

    def _set_status(self, text: str):
        self.status.setText(text)

    def _on_command_done(self, ok: bool, text: str):
        self._job_finished()
        self.output.setPlainText(text or ("Done." if ok else "Failed."))
        self._set_status("Done" if ok else "Failed")

    def _run_async(self, name: str, cmd: list[str], timeout: int = 180):
        self._job_started()
        self._set_status(f"Running: {name}...")

        def task():
            ok, out = run_command(cmd, timeout=timeout)
            self._log_action(name, cmd, ok, out)
            self.command_done.emit(ok, out)

        threading.Thread(target=task, daemon=True).start()

    def _run_batch_async(self, name: str, commands: list[list[str]], timeout: int = 240):
        self._job_started()
        self._set_status(f"Running preset: {name}...")

        def task():
            all_ok = True
            lines = [f"Preset: {name}", ""]
            for i, cmd in enumerate(commands, start=1):
                ok, out = run_command(cmd, timeout=timeout)
                all_ok = all_ok and ok
                lines.append(f"[{i}] {' '.join(cmd)}")
                if out:
                    lines.append(out)
                lines.append("")
                if not ok:
                    break
            self._log_action(name, ["(batch preset)"], all_ok, "\n".join(lines))
            self.command_done.emit(all_ok, "\n".join(lines))

        threading.Thread(target=task, daemon=True).start()

    def _run_driver_inspector(self):
        self._job_started()
        self._set_status("Running driver/service inspector...")

        def task():
            ok, out = inspect_drivers_and_services()
            self._log_action("Driver + Service Inspector", ["powershell", "Get-PnpDevice/Get-CimInstance"], ok, out)
            self.command_done.emit(ok, out)

        threading.Thread(target=task, daemon=True).start()

    def _run_startup_listing(self):
        self._job_started()
        self._set_status("Listing startup entries...")

        def task():
            ok, out = list_startup_entries()
            self._log_action("List Startup Entries", ["powershell", "Get-CimInstance Win32_StartupCommand"], ok, out)
            self.command_done.emit(ok, out)

        threading.Thread(target=task, daemon=True).start()

    def _run_storage_scan(self):
        self._job_started()
        path = self.storage_path.text().strip()
        limit = int(self.storage_limit.value())
        self._set_status(f"Scanning storage: {path}")

        def task():
            ok, out = storage_rescue_report(Path(path), limit=limit)
            self._log_action("Storage Rescue Scan", [path, f"limit={limit}"], ok, out)
            self.command_done.emit(ok, out)

        threading.Thread(target=task, daemon=True).start()

    def _run_permission_fix(self):
        target = self.permission_path.text().strip()
        if not target:
            self._set_status("Enter a folder path first.")
            return
        self._run_async("Permission Reset", ["icacls", target, "/reset", "/T", "/C"])

    def _run_restore_point(self):
        self._job_started()
        self._set_status("Creating restore point...")

        def task():
            ok, out = create_restore_point("WindowsSystemSuite")
            self._log_action("Create Restore Point", ["Checkpoint-Computer"], ok, out)
            self.command_done.emit(ok, out)

        threading.Thread(target=task, daemon=True).start()

    def _open_restore_ui(self):
        self._job_started()
        self._set_status("Opening System Restore...")

        def task():
            ok, out = open_system_restore_ui()
            self._log_action("Open System Restore", ["rstrui.exe"], ok, out)
            self.command_done.emit(ok, out)

        threading.Thread(target=task, daemon=True).start()

    def _job_started(self):
        self.active_jobs += 1
        self.progress.setRange(0, 0)

    def _job_finished(self):
        self.active_jobs = max(0, self.active_jobs - 1)
        if self.active_jobs == 0:
            self.progress.setRange(0, 1)
            self.progress.setValue(0)

    def _copy_output(self):
        text = self.output.toPlainText().strip()
        if not text:
            self._set_status("No output to copy.")
            return
        QtWidgets.QApplication.clipboard().setText(text)
        self._set_status("Output copied to clipboard.")

    def _show_history(self):
        rows = read_history(limit=300)
        if not rows:
            self.output.setPlainText("No action history yet.")
            self._set_status("History is empty.")
            return
        lines: list[str] = []
        for row in rows:
            ts = str(row.get("ts", ""))
            name = str(row.get("name", ""))
            ok = bool(row.get("ok", False))
            cmd = row.get("cmd", [])
            cmd_text = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            lines.append(f"[{ts}] {'OK' if ok else 'FAIL'} | {name}")
            lines.append(f"  {cmd_text}")
        self.output.setPlainText("\n".join(lines))
        self._set_status(f"Loaded {len(rows)} history entries.")

    def _clear_history_clicked(self):
        clear_history()
        self._set_status("Action history cleared.")

    def _log_action(self, name: str, cmd: list[str], ok: bool, out: str):
        if not bool(self.settings.get("history_enabled", True)):
            return
        append_history(
            {
                "name": name,
                "cmd": cmd,
                "ok": ok,
                "output_preview": (out or "")[:500],
            }
        )

    def _export_output(self):
        text = self.output.toPlainText().strip()
        if not text:
            self._set_status("No output to export.")
            return
        reports_dir = Path.home() / "Documents" / "WindowsSystemSuiteReports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = reports_dir / f"report-{stamp}.txt"
        path.write_text(text, encoding="utf-8")
        self._set_status(f"Saved report: {path}")

    def _relaunch_admin(self):
        if is_admin():
            self._set_status("Already running as administrator.")
            self.admin_label.setText("Admin: Yes")
            return
        started = relaunch_as_admin()
        if started:
            QtWidgets.QApplication.quit()
        else:
            self._set_status("Admin relaunch failed.")


class WindowsSystemSuiteApp:
    @staticmethod
    def run_app():
        app = QtWidgets.QApplication([])
        app.setStyle("Fusion")
        win = SystemSuiteWindow()
        win.show()
        app.exec()
