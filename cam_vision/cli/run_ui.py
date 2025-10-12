#!/usr/bin/env python3
"""Run SecureVision Streamlit dashboard."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run Streamlit dashboard."""
    ui_path = Path(__file__).parent.parent / "ui" / "app.py"

    if not ui_path.exists():
        print(f"Error: Dashboard app not found at {ui_path}", file=sys.stderr)
        sys.exit(1)

    # Run Streamlit
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ui_path),
            "--server.port",
            "8501",
            "--server.address",
            "localhost",
            "--browser.gatherUsageStats",
            "false",
        ]
    )


if __name__ == "__main__":
    main()
