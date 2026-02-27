"""Sample module for testing whiteprint."""

from dataclasses import dataclass

from __future__ import annotations
from typing import Optional


class Animal:
    """Base animal class."""

    name: str
    age: int

    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        """Make a sound."""
        return "..."


class Dog(Animal):
    """Dog class."""

    breed: str

    def __init__(self, name: str, breed: str) -> None:
        super().__init__(name)
        self.breed = breed

    def speak(self) -> str:
        return "Woof!"


class Cat(Animal):
    """Cat class."""

    indoor: bool

    def __init__(self, name: str, indoor: bool = True) -> None:
        super().__init__(name)
        self.indoor = indoor

    def speak(self) -> str:
        return "Meow!"


class Owner:
    """Owner of pets."""

    name: str
    pet: Optional[Animal]

    def __init__(self, name: str) -> None:
        self.name = name
        self.pet = None

    def adopt(self, animal: Animal) -> None:
        """Adopt a pet."""
        self.pet = animal

@dataclass
class Zoo:
    "the zoo class"

    pet: Animal