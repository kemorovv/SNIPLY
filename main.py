#!/usr/bin/env python3
"""
SNIPLY — Smart Clipboard Manager for Windows 10 & Windows 11
"Your clipboard. Reimagined."

Application Entry Point.
"""

import sys

from app.application import SniplyApplication
from core.logger import get_logger


def main() -> int:
    logger = get_logger("main")
    try:
        app = SniplyApplication(sys.argv)
        return app.run()
    except Exception as exc:
        logger.critical(f"Unhandled startup error in SNIPLY: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
