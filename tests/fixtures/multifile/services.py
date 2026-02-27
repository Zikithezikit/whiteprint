"""Services module."""

from typing import Optional


from models import Animal


class Owner:
    """Owner of pets."""

    _name: str
    _pet: Optional[Animal]

    def adopt(self, animal: Animal) -> None:
        """Adopt a pet."""
        self.pet = animal
