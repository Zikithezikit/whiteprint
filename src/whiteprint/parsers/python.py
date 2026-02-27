"""Python source code parser."""

import ast
from pathlib import Path
from typing import Optional

from whiteprint.model import UmlAttribute, UmlClass, UmlMethod, Visibility
from whiteprint.parsers.base import Parser


class PythonParser(Parser):
    """Parser for Python source code using AST."""

    def get_language(self) -> str:
        return "python"

    def _get_source_files(self, path: Path, include_tests: bool) -> list[Path]:
        """Get list of Python source files."""
        if path.is_file():
            return [path] if path.suffix == ".py" else []

        pattern = "test_*.py" if include_tests else "[!test]*.py"
        return sorted(path.rglob(pattern))

    def parse(self, path: Path) -> list[UmlClass]:
        """Parse a Python file and extract UML classes."""
        if not path.exists():
            return []

        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return []

        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            return []

        module_name = path.stem
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls = self._parse_class(node, module_name, str(path))
                if cls:
                    classes.append(cls)

        for cls in classes:
            cls.base_classes = self._resolve_bases(cls.base_classes, classes)

        return classes

    def _parse_class(
        self, node: ast.ClassDef, module: str, file_path: str
    ) -> Optional[UmlClass]:
        base_names = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.append(self._get_attr_name(base))

        is_interface = self._is_interface(node)
        is_abstract = self._is_abstract(node)

        attributes = []
        methods = []

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                attr = self._parse_attribute(item)
                if attr:
                    attributes.append(attr)
            elif isinstance(item, ast.FunctionDef):
                method = self._parse_method(item)
                methods.append(method)

        return UmlClass(
            name=node.name,
            attributes=attributes,
            methods=methods,
            module=module,
            file_path=file_path,
            is_interface=is_interface,
            is_abstract=is_abstract,
            base_classes=base_names,
        )

    def _parse_attribute(self, node: ast.AnnAssign) -> Optional[UmlAttribute]:
        if not isinstance(node.target, ast.Name):
            return None
        name = node.target.id
        type_str = self._get_type_annotation(node.annotation)

        visibility = Visibility.PUBLIC
        if name.startswith("__"):
            visibility = Visibility.PRIVATE
        elif name.startswith("_"):
            visibility = Visibility.PROTECTED

        return UmlAttribute(name=name, type=type_str, visibility=visibility)

    def _parse_method(self, node: ast.FunctionDef) -> UmlMethod:
        params = []
        args = node.args
        all_args = list(args.posonlyargs) + list(args.args)
        
        annotations = getattr(args, 'annotations', []) or []
        
        for i, arg in enumerate(all_args):
            param_type = "Any"
            if annotations and i < len(annotations):
                annotation = annotations[i]
                if annotation:
                    param_type = self._get_type_annotation(annotation)
            params.append((arg.arg, param_type))

        return_type = ""
        if node.returns:
            return_type = self._get_type_annotation(node.returns)

        visibility = Visibility.PUBLIC
        if node.name.startswith("__"):
            visibility = Visibility.PRIVATE
        elif node.name.startswith("_"):
            visibility = Visibility.PROTECTED

        is_abstract = False

        return UmlMethod(
            name=node.name,
            parameters=params,
            return_type=return_type,
            visibility=visibility,
            is_abstract=is_abstract,
        )

    def _get_type_annotation(self, node: ast.AST) -> str:
        if node is None:
            return "Any"

        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            return str(node.value)
        if isinstance(node, ast.Subscript):
            base = self._get_type_annotation(node.value)
            if isinstance(node.slice, ast.Tuple):
                args = ", ".join(self._get_type_annotation(e) for e in node.slice.elts)
                return f"{base}[{args}]"
            if isinstance(node.slice, ast.Constant):
                return f"{base}[{node.slice.value}]"
            return f"{base}[...]"
        if isinstance(node, ast.BinOp):
            left = self._get_type_annotation(node.left)
            right = self._get_type_annotation(node.right)
            return f"{left} | {right}"
        if isinstance(node, ast.Attribute):
            return self._get_attr_name(node)
        return "Any"

    def _get_attr_name(self, node: ast.Attribute) -> str:
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _is_interface(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in ("Protocol", "Interface", "ABC"):
                    return True
        return False

    def _is_abstract(self, node: ast.ClassDef) -> bool:
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if getattr(item, "abstract", False):
                    return True
        return False

    def _resolve_bases(
        self, base_names: list[str], all_classes: list[UmlClass]
    ) -> list[str]:
        resolved = []
        class_names = {c.name for c in all_classes}
        for base in base_names:
            if base in class_names:
                resolved.append(base)
            elif base in ("object", "ABC", "Protocol"):
                continue
            else:
                resolved.append(base)
        return resolved
