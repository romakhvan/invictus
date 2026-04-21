from __future__ import annotations

from dataclasses import dataclass
import re


_MULTISPACE_RE = re.compile(r"\s+")


def normalize_club_text(value: object) -> str:
    """Normalize club UI/Mongo text before comparisons."""
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    return _MULTISPACE_RE.sub(" ", text)


@dataclass(frozen=True, slots=True)
class ClubCardData:
    name: str
    city: str
    address: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_club_text(self.name))
        object.__setattr__(self, "city", normalize_club_text(self.city))
        object.__setattr__(self, "address", normalize_club_text(self.address))

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.name, self.city, self.address)
