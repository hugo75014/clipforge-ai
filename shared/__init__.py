"""Shared types, constants, and utilities used across the monorepo.

Anything in this module is **framework-agnostic** — it must not import from
FastAPI, React, Celery, etc. It is the single source of truth for cross-cutting
enums, constants, and small helpers.
"""

__version__ = "0.1.0"
