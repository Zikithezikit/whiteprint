"""Draw.io exporter for UML diagrams."""

from pathlib import Path

from drawpyo import File, Page
from drawpyo.diagram import Object as DrawObject, Edge

from whiteprint.model import RelationshipType, UmlClass, UmlRelationship


class DrawIoExporter:
    """Export UML classes to draw.io format."""

    DEFAULT_WIDTH = 180
    DEFAULT_HEIGHT = 120
    CELL_SPACING = 50
    COLUMNS = 3

    def export(
        self,
        classes: list[UmlClass],
        relationships: list[UmlRelationship],
        output_path: Path,
    ) -> None:
        """Export UML diagram to draw.io file."""
        file = File()
        page = Page(file=file)

        positions = self._calculate_positions(classes)

        for cls in classes:
            self._add_class_shape(page, cls, *positions[cls.name])

        class_lookup = {cls.name: cls for cls in classes}

        for rel in relationships:
            source_cls = class_lookup.get(rel.source)
            target_cls = class_lookup.get(rel.target)
            if source_cls and target_cls and rel.source in positions and rel.target in positions:
                self._add_relationship_edge(page, rel, positions[rel.source], positions[rel.target])

        file.write(file_path=str(output_path.parent), file_name=output_path.name)

    def _calculate_positions(self, classes: list[UmlClass]) -> dict[str, tuple[int, int]]:
        """Calculate positions for class boxes in a grid layout."""
        positions = {}
        for i, cls in enumerate(classes):
            col = i % self.COLUMNS
            row = i // self.COLUMNS
            x = 50 + col * (self.DEFAULT_WIDTH + self.CELL_SPACING)
            y = 50 + row * (self.DEFAULT_HEIGHT + self.CELL_SPACING)
            positions[cls.name] = (x, y)
        return positions

    def _add_class_shape(self, page: Page, cls: "UmlClass", x: int, y: int) -> None:
        """Add a UML class shape to the page."""
        header_height = 30
        attr_height = max(len(cls.attributes) * 20, 20)
        method_height = len(cls.methods) * 20 if cls.methods else 0

        total_height = header_height + attr_height + method_height

        class_name = cls.name
        if cls.is_interface:
            class_name = f"<<interface>>\n{class_name}"
        if cls.is_abstract:
            class_name = f"<<abstract>>\n{class_name}"

        attr_text = "\n".join(str(a) for a in cls.attributes)
        method_text = "\n".join(str(m) for m in cls.methods)

        border_color = "#6c8ebf"
        fill_color = "#dae8fc"

        DrawObject(
            page=page,
            value="",
            position=(x, y),
            width=self.DEFAULT_WIDTH,
            height=total_height,
            style=f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill_color};strokeColor={border_color};",
        )

        DrawObject(
            page=page,
            value=class_name,
            position=(x, y),
            width=self.DEFAULT_WIDTH,
            height=header_height,
            style=f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill_color};strokeColor={border_color};fontStyle=1;",
        )

        DrawObject(
            page=page,
            value=attr_text,
            position=(x, y + header_height),
            width=self.DEFAULT_WIDTH,
            height=attr_height,
            style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=4;spacingRight=4;overflow=hidden;",
        )

        if cls.methods:
            DrawObject(
                page=page,
                value=method_text,
                position=(x, y + header_height + attr_height),
                width=self.DEFAULT_WIDTH,
                height=method_height,
                style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=4;spacingRight=4;overflow=hidden;",
            )

    def _add_relationship_edge(
        self,
        page: Page,
        rel: UmlRelationship,
        source_pos: tuple[int, int],
        target_pos: tuple[int, int],
    ) -> None:
        """Add a relationship edge to the page."""
        source_x, source_y = source_pos
        target_x, target_y = target_pos

        source_center_x = source_x + self.DEFAULT_WIDTH // 2
        source_center_y = source_y + self.DEFAULT_HEIGHT // 2
        target_center_x = target_x + self.DEFAULT_WIDTH // 2
        target_center_y = target_y + self.DEFAULT_HEIGHT // 2

        edge = Edge(
            page=page,
            vertices=[
                (source_center_x, source_center_y),
                (
                    (source_center_x + target_center_x) // 2,
                    (source_center_y + target_center_y) // 2,
                ),
                (target_center_x, target_center_y),
            ],
        )

        self._set_edge_style(edge, rel.type)

    def _set_edge_style(self, edge: Edge, rel_type: RelationshipType) -> None:
        """Set edge style based on relationship type."""
        edge.strokeColor = "black"
        edge.strokeWidth = "1"

        if rel_type == RelationshipType.INHERITANCE:
            edge.endArrow = "block"
        elif rel_type == RelationshipType.IMPLEMENTATION:
            edge.endArrow = "block"
            edge.pattern = "dashed_medium"
        elif rel_type == RelationshipType.COMPOSITION:
            edge.endArrow = "diamond"
            edge.endFill = True
        elif rel_type == RelationshipType.AGGREGATION:
            edge.endArrow = "diamond"
            edge.endFill = False
        elif rel_type == RelationshipType.ASSOCIATION:
            edge.endArrow = "classic"


def export_uml(
    classes: list[UmlClass],
    relationships: list[UmlRelationship],
    output_path: Path,
) -> None:
    """Export UML diagram to draw.io format."""
    exporter = DrawIoExporter()
    exporter.export(classes, relationships, output_path)
