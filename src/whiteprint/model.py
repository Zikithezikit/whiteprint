"""UML data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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
class UmlClass:
    name: str
    attributes: list[UmlAttribute] = field(default_factory=list)
    methods: list[UmlMethod] = field(default_factory=list)
    module: str = ""
    file_path: str = ""
    is_interface: bool = False
    is_abstract: bool = False
    base_classes: list[str] = field(default_factory=list)

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

    OPTIONAL_TYPES = {
        "python": {"Optional", "None", "Any"},
        "rust": {"Option", "Box", "Vec", "Rc", "Arc"},
    }

    def __init__(self, language: str = "python"):
        self.language = language

    def detect(
        self, classes: list[UmlClass]
    ) -> list[UmlRelationship]:
        relationships = []
        class_names = {c.name for c in classes}

        for cls in classes:
            for base in cls.base_classes:
                if base in class_names:
                    rel_type = RelationshipType.INHERITANCE
                    if self._is_trait(base):
                        rel_type = RelationshipType.IMPLEMENTATION
                    relationships.append(
                        UmlRelationship(
                            source=cls.name,
                            target=base,
                            type=rel_type,
                        )
                    )

            for attr in cls.attributes:
                if attr.type in class_names:
                    rel_type = self._classify_attribute(attr.type, classes)
                    relationships.append(
                        UmlRelationship(
                            source=cls.name,
                            target=attr.type,
                            type=rel_type,
                        )
                    )

            for method in cls.methods:
                for param_type in method.parameters:
                    if param_type[1] in class_names:
                        relationships.append(
                            UmlRelationship(
                                source=cls.name,
                                target=param_type[1],
                                type=RelationshipType.ASSOCIATION,
                            )
                        )

        return relationships

    def _classify_attribute(self, attr_type: str, classes: list[UmlClass]) -> RelationshipType:
        attr_type_clean = attr_type.replace("?", "").replace("'", "").split("<")[0]

        if attr_type_clean in self.OPTIONAL_TYPES.get(self.language, set()):
            return RelationshipType.AGGREGATION

        return RelationshipType.COMPOSITION

    def _is_trait(self, name: str) -> bool:
        if not name:
            return False
        if self.language == "python":
            return name.startswith("I") or name.endswith("Protocol") or name.endswith("Interface")
        if self.language == "rust":
            return name[0].isupper() and not name.endswith("Error")
        return False
