"""Draw.io exporter for UML diagrams."""

from pathlib import Path

from drawpyo import File, Page
from drawpyo.diagram import Object as DrawObject, Edge

from whiteprint.model import RelationshipType, UmlClass, UmlRelationship


class DrawIoExporter:
    """Export UML classes to draw.io format."""

    MIN_WIDTH = 180
    DEFAULT_HEIGHT = 120
    CELL_SPACING = 50
    COLUMNS = 3
    CHAR_WIDTH = 8
    LINE_HEIGHT = 20
    HEADER_HEIGHT = 30

    def export(
        self,
        classes: list[UmlClass],
        relationships: list[UmlRelationship],
        output_path: Path,
    ) -> None:
        """Export UML diagram to draw.io file."""
        file = File()
        page = Page(file=file)

        class_sizes = self._calculate_class_sizes(classes)
        positions = self._calculate_positions(classes, class_sizes)

        for cls in classes:
            width, height = class_sizes[cls.name]
            self._add_class_shape(page, cls, *positions[cls.name], width, height)

        class_lookup = {cls.name: cls for cls in classes}

        for rel in relationships:
            source_cls = class_lookup.get(rel.source)
            target_cls = class_lookup.get(rel.target)
            if source_cls and target_cls and rel.source in positions and rel.target in positions:
                self._add_relationship_edge(
                    page, rel, positions[rel.source], positions[rel.target], class_sizes
                )

        file.write(file_path=str(output_path.parent), file_name=output_path.name)

    def _calculate_class_sizes(self, classes: list[UmlClass]) -> dict[str, tuple[int, int]]:
        """Calculate dynamic width and height for each class based on content."""
        sizes = {}
        for cls in classes:
            max_width = self.MIN_WIDTH

            class_name = cls.name
            if cls.is_interface:
                class_name = f"<<interface>>\n{class_name}"
            if cls.is_abstract:
                class_name = f"<<abstract>>\n{class_name}"

            lines = class_name.split("\n")
            for line in lines:
                max_width = max(max_width, len(line) * self.CHAR_WIDTH + 20)

            for attr in cls.attributes:
                attr_str = str(attr)
                max_width = max(max_width, len(attr_str) * self.CHAR_WIDTH + 20)

            for method in cls.methods:
                method_str = str(method)
                max_width = max(max_width, len(method_str) * self.CHAR_WIDTH + 20)

            header_height = self.HEADER_HEIGHT
            attr_height = max(len(cls.attributes) * self.LINE_HEIGHT, 20)
            method_height = len(cls.methods) * self.LINE_HEIGHT if cls.methods else 0

            total_height = header_height + attr_height + method_height
            sizes[cls.name] = (max_width, total_height)

        return sizes

    def _calculate_positions(
        self, classes: list[UmlClass], class_sizes: dict[str, tuple[int, int]]
    ) -> dict[str, tuple[int, int]]:
        """Calculate positions for class boxes in a grid layout."""
        positions = {}
        max_col_widths = {}

        for i, cls in enumerate(classes):
            col = i % self.COLUMNS
            width, _ = class_sizes[cls.name]
            max_col_widths[col] = max(max_col_widths.get(col, 0), width)

        x_offsets = [0] * self.COLUMNS
        for col in range(1, self.COLUMNS):
            prev_width = max_col_widths.get(col - 1, self.MIN_WIDTH)
            x_offsets[col] = x_offsets[col - 1] + prev_width + self.CELL_SPACING

        for i, cls in enumerate(classes):
            col = i % self.COLUMNS
            row = i // self.COLUMNS
            width, height = class_sizes[cls.name]
            x = 50 + x_offsets[col]
            y = 50 + row * (self.DEFAULT_HEIGHT + self.CELL_SPACING)
            positions[cls.name] = (x, y)

        return positions

    def _add_class_shape(
        self, page: Page, cls: "UmlClass", x: int, y: int, width: int, height: int
    ) -> None:
        """Add a UML class shape to the page."""
        header_height = self.HEADER_HEIGHT
        attr_height = max(len(cls.attributes) * self.LINE_HEIGHT, 20)
        method_height = len(cls.methods) * self.LINE_HEIGHT if cls.methods else 0

        total_height = max(height, header_height + attr_height + method_height)

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
            width=width,
            height=total_height,
            style=f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill_color};strokeColor={border_color};",
        )

        DrawObject(
            page=page,
            value=class_name,
            position=(x, y),
            width=width,
            height=header_height,
            style=f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill_color};strokeColor={border_color};fontStyle=1;",
        )

        DrawObject(
            page=page,
            value=attr_text,
            position=(x, y + header_height),
            width=width,
            height=attr_height,
            style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=4;spacingRight=4;overflow=hidden;",
        )

        if cls.methods:
            DrawObject(
                page=page,
                value=method_text,
                position=(x, y + header_height + attr_height),
                width=width,
                height=method_height,
                style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=4;spacingRight=4;overflow=hidden;",
            )

    def _add_relationship_edge(
        self,
        page: Page,
        rel: UmlRelationship,
        source_pos: tuple[int, int],
        target_pos: tuple[int, int],
        class_sizes: dict[str, tuple[int, int]],
    ) -> None:
        """Add a relationship edge to the page."""
        source_x, source_y = source_pos
        target_x, target_y = target_pos

        source_width, source_height = class_sizes.get(
            rel.source, (self.MIN_WIDTH, self.DEFAULT_HEIGHT)
        )
        target_width, target_height = class_sizes.get(
            rel.target, (self.MIN_WIDTH, self.DEFAULT_HEIGHT)
        )

        source_center_x = source_x + source_width // 2
        source_center_y = source_y + source_height // 2
        target_center_x = target_x + target_width // 2
        target_center_y = target_y + target_height // 2

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
        edge.strokeWidth = 1

        if rel_type == RelationshipType.INHERITANCE:
            edge.line_end_target = "block"
        elif rel_type == RelationshipType.IMPLEMENTATION:
            edge.line_end_target = "block"
            edge.pattern = "dashed_medium"
        elif rel_type == RelationshipType.COMPOSITION:
            edge.line_end_target = "diamond"
            edge.endFill_target = True
        elif rel_type == RelationshipType.AGGREGATION:
            edge.line_end_target = "diamond"
            edge.endFill_target = False
        elif rel_type == RelationshipType.ASSOCIATION:
            edge.line_end_target = "classic"


def export_uml(
    classes: list[UmlClass],
    relationships: list[UmlRelationship],
    output_path: Path,
) -> None:
    """Export UML diagram to draw.io format."""
    exporter = DrawIoExporter()
    exporter.export(classes, relationships, output_path)
