"""Rust source code parser using regex."""

import re
from pathlib import Path
from typing import Optional

from whiteprint.model import UmlAttribute, UmlClass, UmlMethod, Visibility
from whiteprint.parsers.base import Parser


class RustParser(Parser):
    """Parser for Rust source code using regex."""

    def get_language(self) -> str:
        return "rust"

    def _get_source_files(self, path: Path, include_tests: bool) -> list[Path]:
        """Get list of Rust source files."""
        if path.is_file():
            return [path] if path.suffix == ".rs" else []

        pattern = "test_*.rs" if include_tests else "[!test]*.rs"
        return sorted(path.rglob(pattern))

    def parse(self, path: Path) -> list[UmlClass]:
        """Parse a Rust file and extract UML classes."""
        if not path.exists():
            return []

        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return []

        return self._parse_with_regex(source, path.stem, str(path))

    def _parse_with_regex(self, source: str, module: str, file_path: str) -> list[UmlClass]:
        classes: dict[str, UmlClass] = {}

        struct_pattern = re.compile(
            r"^\s*(?:pub\s+)?struct\s+(\w+)\s*\{([^}]*)\}",
            re.MULTILINE,
        )
        for match in struct_pattern.finditer(source):
            name = match.group(1)
            body = match.group(2)
            attributes = self._parse_rust_fields(body)
            classes[name] = UmlClass(
                name=name,
                attributes=attributes,
                methods=[],
                module=module,
                file_path=file_path,
                is_interface=False,
                base_classes=[],
            )

        enum_pattern = re.compile(
            r"^\s*(?:pub\s+)?enum\s+(\w+)\s*\{([^}]*)\}",
            re.MULTILINE,
        )
        for match in enum_pattern.finditer(source):
            name = match.group(1)
            classes[name] = UmlClass(
                name=name,
                attributes=[],
                methods=[],
                module=module,
                file_path=file_path,
                is_interface=True,
                base_classes=[],
            )

        trait_pattern = re.compile(
            r"^\s*(?:pub\s+)?trait\s+(\w+)\s*\{",
            re.MULTILINE,
        )
        for match in trait_pattern.finditer(source):
            name = match.group(1)
            if name not in classes:
                classes[name] = UmlClass(
                    name=name,
                    attributes=[],
                    methods=[],
                    module=module,
                    file_path=file_path,
                    is_interface=True,
                    base_classes=[],
                )

        impl_pattern = re.compile(
            r"^\s*impl(?:<[^>]+>)?\s*(?:(\w+)\s+)?for\s+(\w+)\s*\{",
            re.MULTILINE,
        )
        impl_body_pattern = re.compile(
            r"impl\s+(?:(\w+)\s+)?for\s+(\w+)\s*\{(.*?)(?=\n\s*impl\s|\Z)",
            re.DOTALL,
        )
        for match in impl_body_pattern.finditer(source):
            trait_name = match.group(1)
            struct_name = match.group(2)
            body = match.group(3)

            if struct_name in classes:
                methods = self._parse_rust_methods(body)
                classes[struct_name].methods.extend(methods)
                if trait_name:
                    if trait_name not in classes[struct_name].base_classes:
                        classes[struct_name].base_classes.append(trait_name)

        return list(classes.values())

    def _parse_rust_fields(self, body: str) -> list[UmlAttribute]:
        attributes = []
        field_pattern = re.compile(
            r"^\s*(?:pub\s+)?(\w+)\s*:\s*([^,\n]+)",
            re.MULTILINE,
        )
        for match in field_pattern.finditer(body):
            name = match.group(1)
            type_str = match.group(2).strip()

            visibility = Visibility.PUBLIC
            if name.startswith("_"):
                visibility = Visibility.PRIVATE

            for mod in ["Option", "Box", "Vec", "Rc", "Arc"]:
                if mod in type_str:
                    type_str = f"{mod}<...>"

            attributes.append(UmlAttribute(name=name, type=type_str, visibility=visibility))
        return attributes

    def _parse_rust_methods(self, body: str) -> list[UmlMethod]:
        methods = []
        method_pattern = re.compile(
            r"^\s*(?:pub\s+)?fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^\s{]+))?",
            re.MULTILINE,
        )
        for match in method_pattern.finditer(body):
            name = match.group(1)
            params_str = match.group(2) or ""
            return_type = match.group(3) or ""

            parameters = []
            if params_str:
                param_pattern = re.compile(r"(?:self,?\s*)?(\w+)\s*:\s*([^,]+)")
                for param_match in param_pattern.finditer(params_str):
                    pname = param_match.group(1)
                    ptype = param_match.group(2).strip()
                    if pname != "self":
                        parameters.append((pname, ptype))

            visibility = Visibility.PUBLIC
            if name.startswith("_"):
                visibility = Visibility.PRIVATE

            methods.append(
                UmlMethod(
                    name=name,
                    parameters=parameters,
                    return_type=return_type,
                    visibility=visibility,
                )
            )
        return methods
