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


def test_cloud_requirements_include_default_chroma_runtime_dependency():
    requirements = PROJECT_ROOT / "requirements.txt"
    pyproject = PROJECT_ROOT / "pyproject.toml"
    requirements_text = requirements.read_text(encoding="utf-8").lower()
    pyproject_text = pyproject.read_text(encoding="utf-8").lower()

    assert "chromadb" in requirements_text
    assert "kubernetes==35.0.0" in requirements_text
    assert "pyyaml==6.0.2" in requirements_text
    assert '"chromadb>=' in pyproject_text
    assert '"kubernetes==35.0.0"' in pyproject_text
    assert '"pyyaml==6.0.2"' in pyproject_text


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


def test_streamlit_ui_exposes_memory_management_controls():
    ui_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "ui" / "streamlit_app.py"
    contents = ui_file.read_text(encoding="utf-8")

    assert "delete_memory" in contents
    assert "clear_memories" in contents
    assert "prune_memories" in contents
    assert "dedupe_memories" in contents


def test_env_example_documents_vector_search_settings():
    env_file = PROJECT_ROOT / ".env.example"
    contents = env_file.read_text(encoding="utf-8")

    assert "AI_GLASSES_SEARCH_PROVIDER=chroma" in contents
    assert "AI_GLASSES_VECTOR_DB_PATH=data/vector_memory.sqlite3" in contents
    assert "AI_GLASSES_CHROMA_PATH=data/chroma" in contents
    assert "AI_GLASSES_CHROMA_COLLECTION=visual_memory" in contents
    assert "AI_GLASSES_EMBEDDING_PROVIDER=hash" in contents
    assert "AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5" in contents
    assert "AI_GLASSES_EMBEDDING_DIMENSIONS=384" in contents


def test_embedding_extra_includes_torchvision_for_transformers_image_processors():
    pyproject = PROJECT_ROOT / "pyproject.toml"
    contents = pyproject.read_text(encoding="utf-8")

    assert '"sentence-transformers>=' in contents
    assert '"torchvision==0.27.0"' in contents


def test_rag_extra_documents_chroma_dependency():
    pyproject = PROJECT_ROOT / "pyproject.toml"
    contents = pyproject.read_text(encoding="utf-8")

    assert '"chromadb>=' in contents


def test_api_and_streamlit_wire_search_provider_factory():
    api_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "api" / "routes.py"
    ui_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "ui" / "streamlit_app.py"
    factory_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "services" / "factory.py"

    assert "create_pipeline" in api_file.read_text(encoding="utf-8")
    assert "create_pipeline" in ui_file.read_text(encoding="utf-8")
    assert "create_search_provider" in factory_file.read_text(encoding="utf-8")


def test_streamlit_ui_reports_search_and_embedding_provider():
    ui_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "ui" / "streamlit_app.py"
    contents = ui_file.read_text(encoding="utf-8")

    assert "当前检索模式" in contents
    assert "当前 Embedding 模式" in contents
    assert "Hash embedding 只用于验证向量检索架构" in contents


def test_streamlit_ui_exposes_asr_audio_question_controls():
    ui_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "ui" / "streamlit_app.py"
    contents = ui_file.read_text(encoding="utf-8")

    assert "当前 ASR 模式" in contents
    assert "语音提问" in contents
    assert "上传语音问题" in contents
    assert "transcribe_audio" in contents


def test_streamlit_ui_exposes_rag_memory_answer_controls():
    ui_file = PROJECT_ROOT / "src" / "ai_glasses_memory" / "ui" / "streamlit_app.py"
    contents = ui_file.read_text(encoding="utf-8")

    assert "历史记忆问答" in contents
    assert "基于记忆回答" in contents
    assert "answer_from_memory" in contents
    assert "RAG 回答" in contents


def test_rag_smoke_script_documents_chroma_rag_flow():
    script = PROJECT_ROOT / "scripts" / "rag_smoke.py"

    assert script.exists()
    contents = script.read_text(encoding="utf-8")
    assert "ChromaSearchProvider" in contents
    assert "answer_from_memory" in contents
    assert "鼠标是什么颜色的" in contents


def test_asr_extra_documents_faster_whisper_dependency():
    pyproject = PROJECT_ROOT / "pyproject.toml"
    contents = pyproject.read_text(encoding="utf-8")

    assert "asr = [" in contents
    assert '"faster-whisper>=' in contents


def test_env_example_documents_asr_provider_settings():
    env_file = PROJECT_ROOT / ".env.example"
    contents = env_file.read_text(encoding="utf-8")

    assert "AI_GLASSES_ASR_PROVIDER=mock" in contents
    assert "AI_GLASSES_ASR_MODEL=base" in contents
    assert "AI_GLASSES_ASR_DEVICE=cpu" in contents
    assert "AI_GLASSES_ASR_COMPUTE_TYPE=int8" in contents
