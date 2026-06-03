"""Streamlit Cloud / Render entrypoint for the Web MVP."""

import runpy
import sys
from pathlib import Path

_root = Path(__file__).parent
_src = _root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

runpy.run_path(str(_src / "ai_glasses_memory" / "ui" / "streamlit_app.py"))
