# Browser Native Live Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a browser-native live input page that uses real-time camera preview and browser recording before submitting a captured frame and question to the existing memory pipeline.

**Architecture:** Keep `MemoryPipeline` unchanged. Add FastAPI routes for `/live`, `/live/ask`, and `/live/transcribe`; the page uses `getUserMedia`, canvas frame capture, and `MediaRecorder` to provide a more realistic first-person interaction than Streamlit camera/audio widgets.

**Tech Stack:** FastAPI, browser JavaScript, HTML/CSS, multipart uploads, pytest.

---

## File Map

- Modify `src/ai_glasses_memory/api/routes.py`: add browser-native live page and live endpoints.
- Modify `tests/test_api.py`: cover `/live`, `/live/ask`, and `/live/transcribe`.
- Modify `README.md`: document `/live` as the preferred input experience.
- Create `docs/live-input.md`: explain live camera preview, frame capture, and voice recording flow.
- Modify `docs/mobile-input.md`: position `/mobile` as fallback and `/live` as preferred.
- Modify `docs/architecture/system-architecture.md`: include browser-native live input.
- Modify `docs/interview/demo-script-2min.md` and `docs/interview/interview-qa.md`: update demo/interview wording.
- Create `docs/debug-log/bug-25-streamlit-input-not-final-live-experience.md`: record why we moved input to browser-native live page.
- Modify `docs/debug-log/README.md`: add bug 25 index entry.

## Task 1: Tests

- [ ] Add failing tests that `/live` serves a page containing `getUserMedia`, `MediaRecorder`, canvas capture, `/live/ask`, and `/live/transcribe`.
- [ ] Add failing tests that `/live/ask` accepts an image frame and question and returns a memory event.
- [ ] Add failing tests that `/live/transcribe` accepts audio and returns transcription.

## Task 2: Live Routes

- [ ] Add `GET /live` HTML response.
- [ ] Add `POST /live/ask` multipart endpoint.
- [ ] Add `POST /live/transcribe` multipart endpoint.
- [ ] Reuse `save_input_image`, `save_input_audio`, and `MemoryPipeline`.

## Task 3: Docs

- [ ] Document `/live` startup and usage.
- [ ] Update architecture and interview docs to call Streamlit a dashboard/debug surface, not the final input surface.
- [ ] Add debug log for the interaction design shift.

## Task 4: Verification And Git

- [ ] Run `.\.venv\Scripts\python.exe -m pytest -q`.
- [ ] Run `.\.venv\Scripts\python.exe -m pip check`.
- [ ] Commit with message `新增: 浏览器原生实时输入页`.
- [ ] Push to `origin main`.

## Self-Review

- Scope is limited to browser-native live page and endpoints.
- No WebSocket/WebRTC token streaming is added in this iteration.
- Existing Streamlit UI remains available as dashboard and fallback.
