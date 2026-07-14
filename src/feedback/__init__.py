"""Feedback Loop (Phase 11, Module 9).

Feedback never edits production directly — it produces candidate
improvements (clusters -> backlog ticket -> new prompt/data/retrieval
candidate) that must still pass through PromptOps + Evaluation Engine +
Quality Gate like every other change in this project.
"""
