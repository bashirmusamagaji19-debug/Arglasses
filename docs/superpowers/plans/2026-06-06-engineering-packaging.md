# Engineering Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the project documentation with the current Chroma RAG implementation and add interview-ready project materials.

**Architecture:** This is a documentation packaging pass. It does not change runtime behavior; it updates stale search/RAG docs, adds resume and interview artifacts, and records the documentation drift as a debug log for interview reuse.

**Tech Stack:** Markdown, pytest smoke verification, Git.

---

## File Map

- Modify `docs/phase3-search.md`: update the search phase from lightweight-only history to the current provider stack and Chroma RAG status.
- Modify `docs/vector-search.md`: clarify that Chroma is now the default RAG retrieval backend, while SQLite vector search remains a local provider.
- Create `docs/interview/resume-bullets.md`: concise resume bullet material.
- Create `docs/interview/interview-qa.md`: interview questions and answers.
- Create `docs/interview/demo-script-2min.md`: longer demo narrative.
- Modify `docs/debug-log/README.md`: add bug 21 to the index.
- Create `docs/debug-log/bug-21-engineering-packaging-gap.md`: document why packaging materials lagged behind implementation.

## Task 1: Align Search And RAG Docs

- [ ] Update `docs/phase3-search.md` to describe the progression from keyword search to lightweight semantic search, SQLite vector search, and default Chroma RAG.
- [ ] Update `docs/vector-search.md` to separate SQLite vector search from Chroma retrieval.
- [ ] Ensure both docs explain that SQLite stores full memory events and Chroma stores retrieval documents plus metadata.

## Task 2: Add Interview Materials

- [ ] Create `docs/interview/resume-bullets.md` with Chinese resume bullets and a short project summary.
- [ ] Create `docs/interview/interview-qa.md` with likely interview questions about architecture, provider boundaries, RAG, OCR, VLM, Chroma, and trade-offs.
- [ ] Create `docs/interview/demo-script-2min.md` with a practical two-minute demo script.

## Task 3: Add Debug Log

- [ ] Create `docs/debug-log/bug-21-engineering-packaging-gap.md`.
- [ ] Update `docs/debug-log/README.md` with the new entry.

## Task 4: Verification And Git

- [ ] Run `.\.venv\Scripts\python.exe -m pytest -q`.
- [ ] Review `git diff --stat`.
- [ ] Commit with message `文档: 补齐工程包装和面试材料`.
- [ ] Push to `origin main`.

## Self-Review

- Spec coverage: The plan covers documentation alignment, interview artifacts, debug logging, verification, commit, and push.
- Placeholder scan: No TBD/TODO placeholders are used.
- Scope check: This package does not change runtime code and can be completed as one documentation-focused change.
