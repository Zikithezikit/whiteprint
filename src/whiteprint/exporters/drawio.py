"""Draw.io exporter for UML diagrams."""

import heapq
from pathlib import Path

from drawpyo import File, Page
from drawpyo.diagram import Edge
from drawpyo.diagram import Object as DrawObject
from drawpyo.diagram.base_diagram import DiagramBase

from whiteprint.model import RelationshipType, UmlClass, UmlRelationship


class AStarPathfinder:
    """A* pathfinding for obstacle-free edge routing."""

    def __init__(
        self,
        grid_width: int,
        grid_height: int,
        obstacles: list[tuple[int, int, int, int]],
    ):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.obstacles = obstacles

    def find_path(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> list[tuple[int, int]] | None:
        """Find obstacle-free path from start to end using A*."""
        if not self._is_valid_point(start[0], start[1]):
            return None
        if not self._is_valid_point(end[0], end[1]):
            return None

        open_set: list[tuple[int, tuple[int, int]]] = []
        heapq.heappush(open_set, (0, start))

        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], int] = {start: 0}

        visited = set()

        while open_set:
            _, current = heapq.heappop(open_set)

            if current in visited:
                continue
            visited.add(current)

            if current == end:
                return self._reconstruct_path(came_from, start, end)

            for neighbor in self._get_neighbors(current):
                if neighbor in visited:
                    continue
                if not self._is_valid_point(neighbor[0], neighbor[1]):
                    continue

                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score, neighbor))

        return None

    def _get_neighbors(self, point: tuple[int, int]) -> list[tuple[int, int]]:
        """Get valid neighboring cells (4-directional)."""
        x, y = point
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                neighbors.append((nx, ny))
        return neighbors

    def _heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        """Manhattan distance heuristic."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _is_valid_point(self, x: int, y: int) -> bool:
        """Check if point is within bounds and not in an obstacle."""
        if x < 0 or x >= self.grid_width or y < 0 or y >= self.grid_height:
            return False
        for ox, oy, ow, oh in self.obstacles:
            if ox <= x < ox + ow and oy <= y < oy + oh:
                return False
        return True

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int], tuple[int, int]],
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """Reconstruct path from start to end."""
        path = [end]
        current = end
        while current != start:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path


class DrawIoExporter:
    """Export UML classes to draw.io format."""

    MIN_WIDTH = 180
    DEFAULT_HEIGHT = 120
    CELL_SPACING = 50
    COLUMNS = 3
    CHAR_WIDTH = 8
    LINE_HEIGHT = 20
    HEADER_HEIGHT = 30
    CLASS_MARGIN = 30
    MAX_X = 5000
    GRID_CELL_SIZE = 20
    EDGE_MARGIN = 10

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
        margin = self.CLASS_MARGIN

        class_objects: dict[str, DiagramBase] = {}

        for cls in classes:
            width, height = class_sizes[cls.name]
            x, y = positions[cls.name]
            class_obj = self._add_class_shape(page, cls, x + margin, y + margin, width, height)
            class_objects[cls.name] = class_obj

        class_lookup = {cls.name: cls for cls in classes}

        for rel in relationships:
            source_cls = class_lookup.get(rel.source)
            target_cls = class_lookup.get(rel.target)
            if (
                source_cls
                and target_cls
                and rel.source in positions
                and rel.target in positions
                and rel.source in class_objects
                and rel.target in class_objects
            ):
                self._add_relationship_edge(
                    page,
                    rel,
                    class_objects[rel.source],
                    class_objects[rel.target],
                    (positions[rel.source][0] + margin, positions[rel.source][1] + margin),
                    (positions[rel.target][0] + margin, positions[rel.target][1] + margin),
                    class_sizes,
                    positions,
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
        """Calculate positions for class boxes in a grid layout with collision detection."""
        positions = {}
        placed_boxes: list[tuple[int, int, int, int]] = []

        margin = self.CLASS_MARGIN

        for cls in classes:
            width, height = class_sizes[cls.name]
            width += margin * 2
            height += margin * 2

            x, y = self._find_free_position(placed_boxes, width, height)
            positions[cls.name] = (x, y)
            placed_boxes.append((x, y, width, height))

        return positions

    def _find_free_position(
        self, placed_boxes: list[tuple[int, int, int, int]], width: int, height: int
    ) -> tuple[int, int]:
        """Find a position that doesn't overlap with existing boxes."""
        if not placed_boxes:
            return (50, 50)

        max_col_widths = {}
        for bx, _by, bw, _bh in placed_boxes:
            col = bx // 200
            max_col_widths[col] = max(max_col_widths.get(col, 0), bw)

        for row in range(100):
            for col in range(self.COLUMNS):
                x_offset = sum(
                    max_col_widths.get(i, self.MIN_WIDTH) + self.CELL_SPACING for i in range(col)
                )
                x = 50 + x_offset
                y = 50 + row * (self.DEFAULT_HEIGHT + self.CELL_SPACING)

                new_box = (x, y, width, height)
                if not self._boxes_overlap(new_box, placed_boxes):
                    return (x, y)

        base_x = 50 + (placed_boxes[-1][0] if placed_boxes else 0)
        base_y = 50 + (placed_boxes[-1][1] + placed_boxes[-1][3] if placed_boxes else 0)
        test_x, test_y = base_x, base_y
        for _ in range(1000):
            new_box = (test_x, test_y, width, height)
            if not self._boxes_overlap(new_box, placed_boxes):
                return (test_x, test_y)
            test_x += width + self.CELL_SPACING
            if test_x > self.MAX_X:
                test_x = 50
                test_y += height + self.CELL_SPACING

        return (50, 50)

    def _boxes_overlap(
        self, box: tuple[int, int, int, int], boxes: list[tuple[int, int, int, int]]
    ) -> bool:
        """Check if a box overlaps with any box in the list."""
        x1, y1, w1, h1 = box
        for x2, y2, w2, h2 in boxes:
            if not (x1 + w1 <= x2 or x1 >= x2 + w2 or y1 + h1 <= y2 or y1 >= y2 + h2):
                return True
        return False

    def _add_class_shape(
        self, page: Page, cls: "UmlClass", x: int, y: int, width: int, height: int
    ) -> "DiagramBase":
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

        class_obj = DrawObject(
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

        return class_obj

    def _add_relationship_edge(
        self,
        page: Page,
        rel: UmlRelationship,
        source_obj: "DiagramBase",
        target_obj: "DiagramBase",
        source_pos: tuple[int, int],
        target_pos: tuple[int, int],
        class_sizes: dict[str, tuple[int, int]],
        positions: dict[str, tuple[int, int]],
    ) -> None:
        """Add a relationship edge to the page with A* pathfinding."""
        source_x, source_y = source_pos
        target_x, target_y = target_pos

        source_width, source_height = class_sizes.get(
            rel.source, (self.MIN_WIDTH, self.DEFAULT_HEIGHT)
        )
        target_width, target_height = class_sizes.get(
            rel.target, (self.MIN_WIDTH, self.DEFAULT_HEIGHT)
        )

        source_border = self._calculate_edge_points(
            source_x, source_y, source_width, source_height, target_x, target_y
        )
        target_border = self._calculate_edge_points(
            target_x, target_y, target_width, target_height, source_x, source_y
        )

        grid_size = self.GRID_CELL_SIZE
        edge_margin = self.EDGE_MARGIN

        grid_width = self.MAX_X // grid_size
        grid_height = 5000 // grid_size

        obstacles = []
        skip_classes = {rel.source, rel.target}
        for class_name, (cx, cy) in positions.items():
            if class_name in skip_classes:
                continue
            cw, ch = class_sizes.get(class_name, (self.MIN_WIDTH, self.DEFAULT_HEIGHT))
            ox = (cx + edge_margin) // grid_size
            oy = (cy + edge_margin) // grid_size
            ow = (cw + edge_margin * 2) // grid_size + 1
            oh = (ch + edge_margin * 2) // grid_size + 1
            obstacles.append((ox, oy, ow, oh))

        pathfinder = AStarPathfinder(grid_width, grid_height, obstacles)

        start_grid = (source_border[0] // grid_size, source_border[1] // grid_size)
        end_grid = (target_border[0] // grid_size, target_border[1] // grid_size)

        path = pathfinder.find_path(start_grid, end_grid)

        if path:
            vertices = [(x * grid_size, y * grid_size) for x, y in path]
        else:
            vertices = self._calculate_orthogonal_vertices(source_border, target_border)

        edge = Edge(page=page, waypoints=None)
        for vx, vy in vertices:
            edge.geometry.add_point(vx, vy)
        edge.source = source_obj
        edge.target = target_obj

        self._set_edge_style(edge, rel.type)

    def _calculate_edge_points(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        target_x: int,
        target_y: int,
        margin: int = 5,
    ) -> tuple[int, int, str]:
        """Calculate the best edge point on a box border for connecting to another box."""
        center_x = x + width // 2
        center_y = y + height // 2
        target_center_x = target_x + 50
        target_center_y = target_y + 30

        dx = target_center_x - center_x
        dy = target_center_y - center_y

        if abs(dx) > abs(dy):
            if dx > 0:
                return (x + width + margin, center_y, "right")
            return (x - margin, center_y, "left")
        if dy > 0:
            return (center_x, y + height + margin, "bottom")
        return (center_x, y - margin, "top")

    def _calculate_orthogonal_vertices(
        self,
        source: tuple[int, int, str],
        target: tuple[int, int, str],
    ) -> list[tuple[int, int]]:
        """Calculate orthogonal path vertices between two border points."""
        sx, sy, s_side = source
        tx, ty, t_side = target

        if s_side in ("left", "right"):
            if t_side in ("left", "right"):
                mid_x = (sx + tx) // 2
                return [(sx, sy), (mid_x, sy), (mid_x, ty), (tx, ty)]
            return [(sx, sy), (sx, ty), (tx, ty)]
        if t_side in ("top", "bottom"):
            mid_y = (sy + ty) // 2
            return [(sx, sy), (sx, mid_y), (tx, mid_y), (tx, ty)]
        return [(sx, sy), (tx, sy), (tx, ty)]

    def _set_edge_style(self, edge: Edge, rel_type: RelationshipType) -> None:
        """Set edge style based on relationship type."""
        edge.strokeColor = "black"
        edge.strokeWidth = 1
        edge.waypoints = None

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
