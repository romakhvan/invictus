"""Контент главного экрана в зависимости от типа пользователя."""

from src.pages.mobile.home.content.home_new_user_content import HomeNewUserContent
from src.pages.mobile.home.content.home_rabbit_hole_content import HomeRabbitHoleContent
from src.pages.mobile.home.content.home_subscribed_content import HomeSubscribedContent
from src.pages.mobile.home.content.home_member_content import HomeMemberContent

__all__ = [
    "HomeNewUserContent",
    "HomeRabbitHoleContent",
    "HomeSubscribedContent",
    "HomeMemberContent",
]
