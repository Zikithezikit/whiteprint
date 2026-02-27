"""Tests for Rust parser."""

from pathlib import Path

import pytest

from whiteprint.model import UmlClass, Visibility
from whiteprint.parsers.rust import RustParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestRustParser:
    """Tests for RustParser class."""

    def test_parse_structs(self):
        """Test parsing Rust structs."""
        parser = RustParser()
        result = parser.parse(FIXTURES_DIR / "sample.rs")

        class_names = [cls.name for cls in result]
        assert "Animal" in class_names
        assert "Dog" in class_names
        assert "Cat" in class_names

    def test_parse_trait(self):
        """Test parsing Rust trait."""
        parser = RustParser()
        result = parser.parse(FIXTURES_DIR / "sample.rs")

        trait = next((cls for cls in result if cls.name == "MakeSound"), None)
        assert trait is not None
        assert trait.is_interface is True

    def test_parse_struct_fields(self):
        """Test parsing struct fields."""
        parser = RustParser()
        result = parser.parse(FIXTURES_DIR / "sample.rs")

        animal = next(cls for cls in result if cls.name == "Animal")
        assert len(animal.attributes) >= 2
        attr_names = [attr.name for attr in animal.attributes]
        assert "name" in attr_names
        assert "age" in attr_names

    def test_parse_methods(self):
        """Test parsing impl block methods."""
        parser = RustParser()
        result = parser.parse(FIXTURES_DIR / "sample.rs")

        dog = next(cls for cls in result if cls.name == "Dog")
        method_names = [method.name for method in dog.methods]
        assert "make_sound" in method_names

    def test_parse_implementation_relationship(self):
        """Test parsing trait implementation."""
        parser = RustParser()
        result = parser.parse(FIXTURES_DIR / "sample.rs")

        dog = next(cls for cls in result if cls.name == "Dog")
        assert "MakeSound" in dog.base_classes

    def test_parse_visibility(self):
        """Test visibility detection from field naming."""
        parser = RustParser()
        result = parser.parse(FIXTURES_DIR / "sample.rs")

        dog = next(cls for cls in result if cls.name == "Dog")
        public_attrs = [a for a in dog.attributes if a.visibility == Visibility.PUBLIC]
        assert len(public_attrs) >= 1

    def test_parse_nonexistent_file(self):
        """Test parsing a nonexistent file returns empty list."""
        parser = RustParser()
        result = parser.parse(Path("/nonexistent/file.rs"))
        assert result == []

    def test_language(self):
        """Test get_language returns 'rust'."""
        parser = RustParser()
        assert parser.get_language() == "rust"

    def test_parse_enum(self):
        """Test parsing enum creates interface class."""
        code = """
pub enum Status {
    Active,
    Inactive,
}
"""
        parser = RustParser()
        result = parser._parse_with_regex(code, "test", "test.rs")

        status = next((cls for cls in result if cls.name == "Status"), None)
        assert status is not None
        assert status.is_interface is True
