"""Compatibility re-exports for the storage boundary.

The neutral definitions live in ``app.storage.models`` so that importing
``app.storage`` never has to initialize ``app.connector`` first.
"""

from app.storage.models import QuestionAnswerPair, QuestionAnswerStore

__all__ = ["QuestionAnswerPair", "QuestionAnswerStore"]
