"""Source code parsers."""

from whiteprint.parsers.base import Parser, detect_language_from_extension, get_parser_for_language
from whiteprint.parsers.python import PythonParser
from whiteprint.parsers.rust import RustParser

__all__ = [
    "Parser",
    "PythonParser",
    "RustParser",
    "detect_language_from_extension",
    "get_parser_for_language",
]
