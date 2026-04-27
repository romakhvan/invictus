import pytest

from src.utils.mobile_debug_menu import interactive_debug_menu


@pytest.mark.mobile
def test_mobile_locator_debug(mobile_driver):
    """Открывает интерактивное меню локаторов без прохождения пользовательского flow."""
    interactive_debug_menu(mobile_driver)
