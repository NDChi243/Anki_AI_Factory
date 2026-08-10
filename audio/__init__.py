"""
Japanese audio package.

Exports the TTS router used by the importer.
"""

from .engine import get_audio_multilang

__all__ = ["get_audio_multilang"]
