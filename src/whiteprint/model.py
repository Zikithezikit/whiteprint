"""UML data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar


class Visibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"


class RelationshipType(Enum):
    INHERITANCE = "inheritance"
    IMPLEMENTATION = "implementation"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    ASSOCIATION = "association"


@dataclass
class UmlAttribute:
    name: str
    type: str
    visibility: Visibility = Visibility.PUBLIC

    def __str__(self) -> str:
        vis_prefix = {
            Visibility.PUBLIC: "+",
            Visibility.PROTECTED: "#",
            Visibility.PRIVATE: "-",
        }
        return f"{vis_prefix[self.visibility]} {self.name}: {self.type}"


@dataclass
class UmlMethod:
    name: str
    parameters: list[tuple[str, str]] = field(default_factory=list)
    return_type: str = ""
    visibility: Visibility = Visibility.PUBLIC
    is_abstract: bool = False

    def __str__(self) -> str:
        vis_prefix = {
            Visibility.PUBLIC: "+",
            Visibility.PROTECTED: "#",
            Visibility.PRIVATE: "-",
        }
        params = ", ".join(f"{n}: {t}" for n, t in self.parameters)
        return_type = f": {self.return_type}" if self.return_type else ""
        return f"{vis_prefix[self.visibility]} {self.name}({params}){return_type}"


@dataclass
class Import:
    """Represents an import statement."""

    module: str
    names: list[str]
    alias: str | None = None

    def __repr__(self) -> str:
        if self.alias:
            return f"from {self.module} import {', '.join(self.names)} as {self.alias}"
        return f"from {self.module} import {', '.join(self.names)}"


@dataclass
class UmlClass:
    name: str
    attributes: list[UmlAttribute] = field(default_factory=list)
    methods: list[UmlMethod] = field(default_factory=list)
    module: str = ""
    file_path: str = ""
    is_interface: bool = False
    is_abstract: bool = False
    base_classes: list[str] = field(default_factory=list)
    full_module_path: str = ""
    imports: list[Import] = field(default_factory=list)

    def get_qualified_name(self) -> str:
        """Return fully qualified name (module.ClassName)."""
        if self.module:
            return f"{self.module}.{self.name}"
        return self.name

    def __post_init__(self) -> None:
        if self.is_abstract:
            self.name = f"<<abstract>> {self.name}"

    def __str__(self) -> str:
        lines = [f"Class: {self.name}"]
        if self.base_classes:
            lines.append(f"Extends: {', '.join(self.base_classes)}")
        lines.append("Attributes:")
        for attr in self.attributes:
            lines.append(f"  {attr}")
        lines.append("Methods:")
        for method in self.methods:
            lines.append(f"  {method}")
        return "\n".join(lines)


@dataclass
class UmlRelationship:
    source: str
    target: str
    type: RelationshipType
    label: str = ""

    def __str__(self) -> str:
        return f"{self.source} --[{self.type.value}]--> {self.target}"


class RelationshipDetector:
    """Detects relationships between UML classes based on type annotations."""

    OPTIONAL_TYPES: ClassVar[dict[str, set[str]]] = {
        "python": {"Optional", "None", "Any"},
        "rust": {"Option", "Box", "Vec", "Rc", "Arc"},
    }

    GENERIC_CONTAINERS: ClassVar[dict[str, set[str]]] = {
        "python": {
            "Optional",
            "List",
            "Dict",
            "Set",
            "FrozenSet",
            "Tuple",
            "Sequence",
            "Mapping",
            "Iterable",
        },
        "rust": {"Option", "Box", "Vec", "Rc", "Arc", "HashMap", "HashSet"},
    }

    def __init__(self, language: str = "python"):
        self.language = language

    def _extract_inner_type(self, type_str: str) -> str:
        """Extract the inner type from generic types like Optional[T], List[T], Dict[K,V]."""
        if "[" not in type_str:
            return type_str

        containers = self.GENERIC_CONTAINERS.get(self.language, set())

        for container in containers:
            if type_str.startswith(f"{container}["):
                inner = type_str[len(container) + 1 : -1]
                if "," in inner:
                    parts = inner.split(",")
                    inner = parts[-1].strip() if container == "Dict" else parts[0].strip()
                return inner.strip()

        return type_str

    def _build_class_lookup(
        self, classes: list[UmlClass]
    ) -> tuple[dict[str, list[UmlClass]], dict[str, UmlClass]]:
        """Build lookup tables for class resolution across files."""
        by_name: dict[str, list[UmlClass]] = {}
        by_qualified: dict[str, UmlClass] = {}

        for cls in classes:
            if cls.name not in by_name:
                by_name[cls.name] = []
            by_name[cls.name].append(cls)

            if cls.full_module_path:
                by_qualified[cls.full_module_path] = cls

        return by_name, by_qualified

    def _build_import_lookup(self, classes: list[UmlClass]) -> dict[str, tuple[str, str]]:
        """Build lookup table from imports: alias -> (module, name)."""
        import_lookup: dict[str, tuple[str, str]] = {}

        for cls in classes:
            for imp in cls.imports:
                for name in imp.names:
                    if imp.alias:
                        import_lookup[imp.alias] = (imp.module, name)
                    else:
                        import_lookup[name] = (imp.module, name)

        return import_lookup

    def _resolve_class(
        self,
        name: str,
        by_name: dict[str, list[UmlClass]],
        by_qualified: dict[str, UmlClass],
        import_lookup: dict[str, tuple[str, str]],
        source_module: str = "",
    ) -> UmlClass | None:
        """Resolve a class name to a UmlClass, checking cross-file references."""
        if name in by_name:
            candidates = by_name[name]
            if len(candidates) == 1:
                return candidates[0]
            for c in candidates:
                if c.module == source_module:
                    return c
            return candidates[0]

        if source_module and f"{source_module}.{name}" in by_qualified:
            return by_qualified[f"{source_module}.{name}"]

        if name in import_lookup:
            module, orig_name = import_lookup[name]
            if module in by_qualified:
                cls = by_qualified[module]
                if cls.name == orig_name:
                    return cls
            for qualified_name, cls in by_qualified.items():
                if qualified_name == module and cls.name == orig_name:
                    return cls

        for qualified_name, cls in by_qualified.items():
            if qualified_name.endswith(f".{name}"):
                return cls

        return None

    def detect(self, classes: list[UmlClass]) -> list[UmlRelationship]:
        relationships = []
        by_name, by_qualified = self._build_class_lookup(classes)
        import_lookup = self._build_import_lookup(classes)

        for cls in classes:
            source_module = cls.module

            for base in cls.base_classes:
                resolved = self._resolve_class(
                    base, by_name, by_qualified, import_lookup, source_module
                )
                if resolved and resolved.name != cls.name:
                    rel_type = RelationshipType.INHERITANCE
                    if resolved.is_interface or self._is_trait(resolved.name):
                        rel_type = RelationshipType.IMPLEMENTATION
                    relationships.append(
                        UmlRelationship(
                            source=cls.name,
                            target=resolved.name,
                            type=rel_type,
                        )
                    )

            for attr in cls.attributes:
                inner_type = self._extract_inner_type(attr.type)
                if inner_type in by_name or inner_type in import_lookup:
                    resolved = self._resolve_class(
                        inner_type, by_name, by_qualified, import_lookup, source_module
                    )
                    if resolved and resolved.name != cls.name:
                        rel_type = self._classify_attribute(attr.type, classes)
                        relationships.append(
                            UmlRelationship(
                                source=cls.name,
                                target=resolved.name,
                                type=rel_type,
                            )
                        )

            for method in cls.methods:
                for _param_name, param_type in method.parameters:
                    inner_type = self._extract_inner_type(param_type)
                    if inner_type in by_name or inner_type in import_lookup:
                        resolved = self._resolve_class(
                            inner_type, by_name, by_qualified, import_lookup, source_module
                        )
                        if resolved and resolved.name != cls.name:
                            relationships.append(
                                UmlRelationship(
                                    source=cls.name,
                                    target=resolved.name,
                                    type=RelationshipType.ASSOCIATION,
                                )
                            )

        return relationships

    def _classify_attribute(self, attr_type: str, _classes: list[UmlClass]) -> RelationshipType:
        attr_type_clean = attr_type.replace("?", "").replace("'", "").split("[")[0]

        if attr_type_clean in self.OPTIONAL_TYPES.get(self.language, set()):
            return RelationshipType.AGGREGATION

        return RelationshipType.COMPOSITION

    def _is_trait(self, name: str) -> bool:
        if not name:
            return False
        if self.language == "python":
            return name.startswith("I") or name.endswith(("Protocol", "Interface"))
        if self.language == "rust":
            return name[0].isupper() and not name.endswith("Error")
        return False
