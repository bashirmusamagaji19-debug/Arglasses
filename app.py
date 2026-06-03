"""Streamlit Cloud / Render entrypoint for the Web MVP."""

import sys
from pathlib import Path

# Ensure src/ is on the path (handles installation edge cases)
_src = Path(__file__).parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from ai_glasses_memory.ui.streamlit_app import *  # noqa: F401,F403
