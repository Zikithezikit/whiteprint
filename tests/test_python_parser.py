"""Tests for Python parser."""

from pathlib import Path

import pytest

from whiteprint.model import UmlClass, Visibility
from whiteprint.parsers.python import PythonParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestPythonParser:
    """Tests for PythonParser class."""

    def test_parse_simple_class(self):
        """Test parsing a simple Python class."""
        parser = PythonParser()
        result = parser.parse(FIXTURES_DIR / "sample.py")

        assert len(result) == 4
        class_names = [cls.name for cls in result]
        assert "Animal" in class_names
        assert "Dog" in class_names
        assert "Cat" in class_names
        assert "Owner" in class_names

    def test_parse_inheritance(self):
        """Test parsing class inheritance."""
        parser = PythonParser()
        result = parser.parse(FIXTURES_DIR / "sample.py")

        dog = next(cls for cls in result if cls.name == "Dog")
        assert "Animal" in dog.base_classes

        cat = next(cls for cls in result if cls.name == "Cat")
        assert "Animal" in cat.base_classes

    def test_parse_attributes(self):
        """Test parsing class attributes."""
        parser = PythonParser()
        result = parser.parse(FIXTURES_DIR / "sample.py")

        animal = next(cls for cls in result if cls.name == "Animal")
        assert len(animal.attributes) >= 2
        attr_names = [attr.name for attr in animal.attributes]
        assert "name" in attr_names
        assert "age" in attr_names

    def test_parse_methods(self):
        """Test parsing class methods."""
        parser = PythonParser()
        result = parser.parse(FIXTURES_DIR / "sample.py")

        animal = next(cls for cls in result if cls.name == "Animal")
        method_names = [method.name for method in animal.methods]
        assert "__init__" in method_names
        assert "speak" in method_names

    def test_parse_visibility(self):
        """Test visibility detection from naming convention."""
        parser = PythonParser()
        result = parser.parse(FIXTURES_DIR / "sample.py")

        animal = next(cls for cls in result if cls.name == "Animal")
        public_attrs = [a for a in animal.attributes if a.visibility == Visibility.PUBLIC]
        assert len(public_attrs) >= 2

    def test_parse_nonexistent_file(self):
        """Test parsing a nonexistent file returns empty list."""
        parser = PythonParser()
        result = parser.parse(Path("/nonexistent/file.py"))
        assert result == []

    def test_language(self):
        """Test get_language returns 'python'."""
        parser = PythonParser()
        assert parser.get_language() == "python"

    def test_optional_type_attribute(self):
        """Test Optional type is detected."""
        parser = PythonParser()
        result = parser.parse(FIXTURES_DIR / "sample.py")

        owner = next(cls for cls in result if cls.name == "Owner")
        pet_attr = next((a for a in owner.attributes if a.name == "pet"), None)
        assert pet_attr is not None
        assert "Optional" in pet_attr.type
