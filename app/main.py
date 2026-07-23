from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.error_report import install_exception_hook


def set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Bixers.EpubForge")
    except Exception:
        pass


def main() -> int:
    install_exception_hook()
    if len(sys.argv) > 1 and sys.argv[1] == "--convert":
        from app.cli import main as cli_main

        return cli_main(sys.argv[2:])
    set_windows_app_user_model_id()
    from app.ui.main_window import run_app

    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
