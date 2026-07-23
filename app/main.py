from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.error_report import install_exception_hook


def main() -> int:
    install_exception_hook()
    if len(sys.argv) > 1 and sys.argv[1] == "--convert":
        from app.cli import main as cli_main

        return cli_main(sys.argv[2:])
    from app.ui.main_window import run_app

    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
