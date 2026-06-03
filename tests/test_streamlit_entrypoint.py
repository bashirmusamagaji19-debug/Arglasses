from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_entrypoint_executes_ui_file_directly():
    entrypoint = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")

    assert "runpy.run_path" in entrypoint
    assert '"ai_glasses_memory" / "ui" / "streamlit_app.py"' in entrypoint
    assert "from ai_glasses_memory.ui.streamlit_app import *" not in entrypoint
