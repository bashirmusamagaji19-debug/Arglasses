# ASR Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first ASR stage so the AI glasses memory assistant can accept voice questions through audio upload while keeping the default demo lightweight.

**Architecture:** Add an `ASRProvider` boundary with a mock default and optional `faster_whisper` provider. Wire ASR through settings, factory, pipeline latency tracking, Streamlit audio upload, and a FastAPI transcription endpoint without changing the existing visual QA flow.

**Tech Stack:** Python 3.11, FastAPI, Streamlit, pytest, optional faster-whisper.

---

## File Map

- Create `src/ai_glasses_memory/services/asr.py`: ASR provider protocol, mock provider, optional faster-whisper provider, factory.
- Modify `src/ai_glasses_memory/config.py`: ASR provider, model, device, compute type settings.
- Modify `src/ai_glasses_memory/services/factory.py`: create and inject ASR provider.
- Modify `src/ai_glasses_memory/services/pipeline.py`: add `transcribe_audio()` and ASR latency tracking.
- Modify `src/ai_glasses_memory/api/routes.py`: add `/transcribe` endpoint.
- Modify `src/ai_glasses_memory/ui/streamlit_app.py`: add audio upload and ASR question text handoff.
- Modify `.env.example`, `pyproject.toml`, `README.md`: document ASR configuration and optional dependency.
- Create `docs/phase4-asr.md`: explain non-streaming ASR design.
- Create `docs/debug-log/bug-22-asr-non-streaming-first.md`: record why first ASR version is file upload.
- Modify `docs/debug-log/README.md`: add bug 22 index entry.
- Add tests in `tests/test_asr_provider.py`, update config/factory/pipeline/api/deployment tests.

## Task 1: ASR Provider Boundary

- [ ] Write failing tests for mock ASR, unsupported provider, and missing faster-whisper dependency.
- [ ] Implement `services/asr.py`.
- [ ] Run ASR provider tests.

## Task 2: Settings, Factory, Pipeline

- [ ] Write failing tests for ASR settings, factory wiring, and `MemoryPipeline.transcribe_audio()`.
- [ ] Add ASR settings and inject ASR provider from the factory.
- [ ] Add pipeline transcription method with `asr` latency.
- [ ] Run targeted tests.

## Task 3: API And Streamlit UI

- [ ] Write failing tests for `/transcribe` and Streamlit ASR controls.
- [ ] Add FastAPI audio transcription endpoint.
- [ ] Add Streamlit audio uploader and question handoff.
- [ ] Run API and deployment tests.

## Task 4: Docs, Verification, Git

- [ ] Update env, README, phase docs, and debug log.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest -q`.
- [ ] Run `.\.venv\Scripts\python.exe -m pip check`.
- [ ] Commit with message `新增: ASR 语音提问入口`.
- [ ] Push to `origin main`.

## Self-Review

- Spec coverage: The plan covers provider boundary, configuration, pipeline integration, UI/API entrypoints, docs, tests, and git.
- Placeholder scan: No TBD/TODO placeholders are used.
- Scope check: The first ASR version is intentionally non-streaming and does not add WebRTC or live microphone capture.
