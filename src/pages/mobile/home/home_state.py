"""Home screen states by user/content type."""

from enum import Enum


class HomeState(Enum):
    """Type of content shown on the home screen after sign-in."""

    RABBIT_HOLE = "rabbit_hole"
    NEW_USER = "new_user"
    SUBSCRIBED = "subscribed"
    MEMBER = "member"
    UNKNOWN = "unknown"
