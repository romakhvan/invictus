def test_mobile_locator_debug_opens_interactive_menu(monkeypatch):
    from tests.mobile.infra import test_mobile_locator_debug

    calls = []
    driver = object()

    monkeypatch.setattr(
        test_mobile_locator_debug,
        "interactive_debug_menu",
        lambda received_driver: calls.append(received_driver),
    )

    test_mobile_locator_debug.test_mobile_locator_debug(driver)

    assert calls == [driver]


def test_mobile_locator_debug_does_not_request_teardown_menu():
    from tests.mobile.infra import test_mobile_locator_debug

    marker_names = {
        marker.name
        for marker in getattr(test_mobile_locator_debug.test_mobile_locator_debug, "pytestmark", [])
    }

    assert "mobile" in marker_names
    assert "interactive_mobile" not in marker_names
