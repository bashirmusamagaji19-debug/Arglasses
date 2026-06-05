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


def test_cloud_requirements_include_runtime_http_client():
    requirements = PROJECT_ROOT / "requirements.txt"
    pyproject = PROJECT_ROOT / "pyproject.toml"

    assert "httpx" in requirements.read_text(encoding="utf-8")
    assert '"httpx>=' in pyproject.read_text(encoding="utf-8")


def test_cloud_requirements_include_runtime_image_library():
    requirements = PROJECT_ROOT / "requirements.txt"
    pyproject = PROJECT_ROOT / "pyproject.toml"

    assert "pillow" in requirements.read_text(encoding="utf-8").lower()
    assert '"pillow>=' in pyproject.read_text(encoding="utf-8").lower()


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


def test_streamlit_ui_reports_ocr_provider_and_uses_supported_image_width():
    ui_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "ui" / "streamlit_app.py"
    contents = ui_file.read_text(encoding="utf-8")

    assert "当前 OCR 模式" in contents
    assert "PaddleOCR 首次识别会加载模型" in contents
    assert 'width="stretch"' in contents
    assert "use_container_width" not in contents


def test_streamlit_ui_reports_vlm_provider_and_cost_warning():
    ui_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "ui" / "streamlit_app.py"
    contents = ui_file.read_text(encoding="utf-8")

    assert "当前 VLM 模式" in contents
    assert "真实 VLM 每次提交都会产生一次模型调用" in contents


def test_env_example_documents_vlm_provider_settings():
    env_file = PROJECT_ROOT / ".env.example"
    contents = env_file.read_text(encoding="utf-8")

    assert "AI_GLASSES_VLM_PROVIDER=mock" in contents
    assert "AI_GLASSES_VLM_BASE_URL=" in contents
    assert "AI_GLASSES_VLM_API_KEY=" in contents
    assert "AI_GLASSES_VLM_MODEL=" in contents
    assert "AI_GLASSES_VLM_MAX_TOKENS=512" in contents
    assert "AI_GLASSES_VLM_MAX_IMAGE_WIDTH=1024" in contents
