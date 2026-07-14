"""Optimization/Routing (Phase 11, Module 8).

Semantic cache, extractive context compression, dynamic top-k and
complexity-based model routing. Every feature here is opt-in (constructor
flags on RagService, default off) so existing eval baselines and API
behavior stay reproducible unless explicitly enabled — see
docs/system/experiments/results_optimization_o1_o8.md for the measured
trade-offs.
"""
