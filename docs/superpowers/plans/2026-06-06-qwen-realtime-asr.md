# Qwen Realtime ASR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backend-proxied Qwen-ASR-Realtime WebSocket path for browser microphone interaction without exposing the DashScope API key in the frontend.

**Architecture:** The browser connects only to `/live/asr/ws`. The backend validates `DASHSCOPE_API_KEY`, connects to DashScope Qwen-ASR-Realtime, forwards microphone audio chunks, and relays transcription events back to the browser. The existing `/live/transcribe` faster-whisper fallback remains available.

**Tech Stack:** FastAPI WebSocket, websockets, DashScope Qwen-ASR-Realtime, browser MediaRecorder, pytest.

---

## File Map

- Modify `src/ai_glasses_memory/config.py`: add Qwen realtime ASR settings.
- Modify `src/ai_glasses_memory/api/routes.py`: add `/live/asr/ws` and update `/live` JavaScript to use it.
- Modify `.env.example`, `README.md`, `docs/live-input.md`, `docs/phase4-asr.md`: document Qwen realtime ASR setup.
- Modify `docs/debug-log/README.md`: add bug 26.
- Create `docs/debug-log/bug-26-qwen-realtime-asr-key-proxy.md`: record key-proxy decision.
- Modify `tests/test_config.py`, `tests/test_api.py`, `tests/test_deployment.py`: cover config, WebSocket failure without key, and frontend wiring.

## Task 1: Tests

- [ ] Add failing config test for Qwen realtime settings.
- [ ] Add failing WebSocket test that `/live/asr/ws` sends an error when no DashScope API key is configured.
- [ ] Add failing live page test for `/live/asr/ws`, `startRealtimeAsr`, and Qwen realtime UI text.

## Task 2: Backend Proxy

- [ ] Add Qwen settings to `Settings`.
- [ ] Add `/live/asr/ws` route.
- [ ] On missing API key, accept local WebSocket and send JSON error.
- [ ] When API key exists, connect to DashScope endpoint and relay browser audio to upstream.

## Task 3: Frontend

- [ ] Add “实时识别” controls to `/live`.
- [ ] Use MediaRecorder chunks and WebSocket to `/live/asr/ws`.
- [ ] Append transcript messages into the question textarea.
- [ ] Keep existing record-then-transcribe fallback.

## Task 4: Docs And Verification

- [ ] Update docs and debug log.
- [ ] Run tests and pip check.
- [ ] Commit and push.

## Self-Review

- API key stays server-side.
- faster-whisper fallback remains.
- This is a first proxy implementation; full protocol tuning can follow after a real DashScope key test.
