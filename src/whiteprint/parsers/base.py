"""Parser base interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from whiteprint.model import UmlClass


class Parser(ABC):
    """Base class for all language parsers."""

    @abstractmethod
    def parse(self, path: Path) -> list[UmlClass]:
        """Parse source code and extract UML classes."""
        pass

    @abstractmethod
    def get_language(self) -> str:
        """Return the language identifier."""
        pass

    def parse_directory(self, path: Path, include_tests: bool = False) -> list[UmlClass]:
        """Parse all source files in a directory."""
        classes = []
        for file_path in self._get_source_files(path, include_tests):
            classes.extend(self.parse(file_path))
        return classes

    def _get_source_files(self, path: Path, include_tests: bool) -> list[Path]:
        """Get list of source files to parse."""
        raise NotImplementedError


def detect_language_from_extension(path: Path) -> Optional[str]:
    """Detect language from file extension."""
    ext_map = {
        ".py": "python",
        ".rs": "rust",
    }
    return ext_map.get(path.suffix.lower())


def get_parser_for_language(language: str) -> type[Parser]:
    """Get the parser class for a given language."""
    from whiteprint.parsers.python import PythonParser
    from whiteprint.parsers.rust import RustParser

    parsers = {
        "python": PythonParser,
        "rust": RustParser,
    }
    if language not in parsers:
        raise ValueError(f"Unsupported language: {language}")
    return parsers[language]
