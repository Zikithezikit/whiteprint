"""Models module."""


class Animal:
    """Base animal class."""

    name: str
    age: int

    def speak(self) -> str:
        return "..."


class Dog(Animal):
    """Dog class."""

    breed: str

    def speak(self) -> str:
        return "Woof!"
