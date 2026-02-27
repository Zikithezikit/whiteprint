"""Tests for draw.io exporter."""

import tempfile
from pathlib import Path

import pytest

from whiteprint.exporters.drawio import DrawIoExporter
from whiteprint.model import (
    RelationshipDetector,
    RelationshipType,
    UmlAttribute,
    UmlClass,
    UmlMethod,
    UmlRelationship,
    Visibility,
)


class TestDrawIoExporter:
    """Tests for DrawIoExporter class."""

    def test_export_creates_file(self):
        """Test that export creates a draw.io file."""
        classes = [
            UmlClass(
                name="TestClass",
                attributes=[UmlAttribute(name="field", type="str", visibility=Visibility.PUBLIC)],
                methods=[],
            )
        ]
        relationships = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.drawio"
            exporter = DrawIoExporter()
            exporter.export(classes, relationships, output_path)

            assert output_path.exists()

    def test_export_multiple_classes(self):
        """Test exporting multiple classes."""
        classes = [
            UmlClass(name="ClassA", attributes=[], methods=[]),
            UmlClass(name="ClassB", attributes=[], methods=[]),
            UmlClass(name="ClassC", attributes=[], methods=[]),
        ]
        relationships = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.drawio"
            exporter = DrawIoExporter()
            exporter.export(classes, relationships, output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "ClassA" in content
            assert "ClassB" in content
            assert "ClassC" in content

    def test_export_with_inheritance_relationship(self):
        """Test exporting with inheritance relationship."""
        classes = [
            UmlClass(name="Parent", attributes=[], methods=[]),
            UmlClass(name="Child", attributes=[], base_classes=["Parent"]),
        ]
        detector = RelationshipDetector(language="python")
        relationships = detector.detect(classes)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.drawio"
            exporter = DrawIoExporter()
            exporter.export(classes, relationships, output_path)

            assert output_path.exists()

    def test_calculate_positions(self):
        """Test position calculation for grid layout."""
        exporter = DrawIoExporter()
        classes = [
            UmlClass(name="A", attributes=[], methods=[]),
            UmlClass(name="B", attributes=[], methods=[]),
            UmlClass(name="C", attributes=[], methods=[]),
            UmlClass(name="D", attributes=[], methods=[]),
        ]
        class_sizes = exporter._calculate_class_sizes(classes)
        positions = exporter._calculate_positions(classes, class_sizes)

        assert positions["A"] == (50, 50)
        assert positions["B"] == (280, 50)
        assert positions["C"] == (510, 50)
        assert positions["D"] == (50, 220)

    def test_export_interface(self):
        """Test exporting interface class."""
        classes = [
            UmlClass(
                name="MyInterface",
                attributes=[],
                methods=[UmlMethod(name="do_something", parameters=[], return_type="void")],
                is_interface=True,
            )
        ]
        relationships = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.drawio"
            exporter = DrawIoExporter()
            exporter.export(classes, relationships, output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "&lt;&lt;interface&gt;&gt;" in content


class TestRelationshipDetector:
    """Tests for RelationshipDetector class."""

    def test_detect_inheritance(self):
        """Test detecting inheritance relationship."""
        classes = [
            UmlClass(name="Animal", attributes=[], methods=[]),
            UmlClass(name="Dog", attributes=[], methods=[], base_classes=["Animal"]),
        ]
        detector = RelationshipDetector(language="python")
        relationships = detector.detect(classes)

        assert len(relationships) >= 1
        inheritance = next(
            (r for r in relationships if r.type == RelationshipType.INHERITANCE), None
        )
        assert inheritance is not None
        assert inheritance.source == "Dog"
        assert inheritance.target == "Animal"

    def test_detect_implementation(self):
        """Test detecting implementation relationship."""
        classes = [
            UmlClass(name="MakeSound", attributes=[], methods=[], is_interface=True),
            UmlClass(name="Dog", attributes=[], methods=[], base_classes=["MakeSound"]),
        ]
        detector = RelationshipDetector(language="rust")
        relationships = detector.detect(classes)

        impl = next((r for r in relationships if r.type == RelationshipType.IMPLEMENTATION), None)
        assert impl is not None

    def test_detect_composition(self):
        """Test detecting composition relationship."""
        classes = [
            UmlClass(name="Engine", attributes=[], methods=[]),
            UmlClass(
                name="Car",
                attributes=[
                    UmlAttribute(name="engine", type="Engine", visibility=Visibility.PUBLIC)
                ],
                methods=[],
            ),
        ]
        detector = RelationshipDetector(language="python")
        relationships = detector.detect(classes)

        comp = next((r for r in relationships if r.type == RelationshipType.COMPOSITION), None)
        assert comp is not None

    def test_detect_aggregation(self):
        """Test detecting aggregation relationship."""
        classes = [
            UmlClass(name="Child", attributes=[], methods=[]),
            UmlClass(
                name="Parent",
                attributes=[UmlAttribute(name="child", type="Child", visibility=Visibility.PUBLIC)],
                methods=[],
            ),
        ]
        detector = RelationshipDetector(language="python")
        relationships = detector.detect(classes)

        comp = next((r for r in relationships if r.type == RelationshipType.COMPOSITION), None)
        assert comp is not None

    def test_detect_association(self):
        """Test detecting association from method parameters."""
        classes = [
            UmlClass(name="Trainer", attributes=[], methods=[]),
            UmlClass(
                name="Pet",
                attributes=[],
                methods=[
                    UmlMethod(name="train", parameters=[("trainer", "Trainer")], return_type="")
                ],
            ),
        ]
        detector = RelationshipDetector(language="python")
        relationships = detector.detect(classes)

        assoc = next((r for r in relationships if r.type == RelationshipType.ASSOCIATION), None)
        assert assoc is not None

    def test_detect_optional_type(self):
        """Test detecting aggregation from Optional[T] type."""
        classes = [
            UmlClass(name="Animal", attributes=[], methods=[]),
            UmlClass(
                name="Owner",
                attributes=[
                    UmlAttribute(name="pet", type="Optional[Animal]", visibility=Visibility.PUBLIC)
                ],
                methods=[],
            ),
        ]
        detector = RelationshipDetector(language="python")
        relationships = detector.detect(classes)

        agg = next((r for r in relationships if r.type == RelationshipType.AGGREGATION), None)
        assert agg is not None
        assert agg.source == "Owner"
        assert agg.target == "Animal"

    def test_detect_list_type(self):
        """Test detecting composition from List[T] type."""
        classes = [
            UmlClass(name="Item", attributes=[], methods=[]),
            UmlClass(
                name="Inventory",
                attributes=[
                    UmlAttribute(name="items", type="List[Item]", visibility=Visibility.PUBLIC)
                ],
                methods=[],
            ),
        ]
        detector = RelationshipDetector(language="python")
        relationships = detector.detect(classes)

        comp = next((r for r in relationships if r.type == RelationshipType.COMPOSITION), None)
        assert comp is not None
        assert comp.source == "Inventory"
        assert comp.target == "Item"

    def test_detect_dict_type(self):
        """Test detecting composition from Dict[K,V] type."""
        classes = [
            UmlClass(name="Value", attributes=[], methods=[]),
            UmlClass(
                name="Cache",
                attributes=[
                    UmlAttribute(name="data", type="Dict[str, Value]", visibility=Visibility.PUBLIC)
                ],
                methods=[],
            ),
        ]
        detector = RelationshipDetector(language="python")
        relationships = detector.detect(classes)

        comp = next((r for r in relationships if r.type == RelationshipType.COMPOSITION), None)
        assert comp is not None
        assert comp.target == "Value"

    def test_detect_generic_method_param(self):
        """Test detecting association from method parameters with generic types."""
        classes = [
            UmlClass(name="Handler", attributes=[], methods=[]),
            UmlClass(
                name="Service",
                attributes=[],
                methods=[
                    UmlMethod(
                        name="process",
                        parameters=[("handler", "Optional[Handler]")],
                        return_type="",
                    )
                ],
            ),
        ]
        detector = RelationshipDetector(language="python")
        relationships = detector.detect(classes)

        assoc = next((r for r in relationships if r.type == RelationshipType.ASSOCIATION), None)
        assert assoc is not None
        assert assoc.target == "Handler"
