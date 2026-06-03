from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_deployment_entrypoint_exists():
    entrypoint = PROJECT_ROOT / "app.py"
    contents = entrypoint.read_text(encoding="utf-8")

    assert entrypoint.exists()
    assert "streamlit_app.py" in contents
    assert "runpy.run_path" in contents


def test_requirements_installs_local_package():
    requirements = PROJECT_ROOT / "requirements.txt"

    assert requirements.exists()
    assert "-e ." in requirements.read_text(encoding="utf-8").splitlines()


def test_python_runtime_preference_is_documented():
    runtime = PROJECT_ROOT / "runtime.txt"

    assert runtime.exists()
    assert runtime.read_text(encoding="utf-8").strip() == "python-3.11"


def test_render_blueprint_uses_streamlit_port_from_environment():
    render_yaml = PROJECT_ROOT / "render.yaml"

    assert render_yaml.exists()
    contents = render_yaml.read_text(encoding="utf-8")
    assert "streamlit run app.py" in contents
    assert "--server.address 0.0.0.0" in contents
    assert "--server.port $PORT" in contents


def test_streamlit_ui_exposes_camera_and_upload_inputs():
    ui_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "ui" / "streamlit_app.py"
    contents = ui_file.read_text(encoding="utf-8")

    assert "st.camera_input" in contents
    assert "st.file_uploader" in contents
    assert "save_input_image(selected_image)" in contents
