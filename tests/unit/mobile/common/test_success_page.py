from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.common.success_page import SuccessPage


def test_success_page_defines_common_success_locators():
    assert SuccessPage.TITLE == (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Ура!"]',
    )
    assert SuccessPage.SUBTITLE == (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Вы получили"]',
    )
    assert SuccessPage.GO_TO_MAIN_BUTTON == (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="На главную"]',
    )


def test_success_page_asserts_reward_text_visible(monkeypatch):
    page = object.__new__(SuccessPage)
    calls = []

    monkeypatch.setattr(
        SuccessPage,
        "wait_visible",
        lambda self, locator, message=None, timeout=None: calls.append(
            (locator, message, timeout)
        ),
    )

    page.assert_reward_text_visible("3 посещения в Invictus GO", timeout=7)

    assert calls == [
        (
            SuccessPage.reward_text_locator("3 посещения в Invictus GO"),
            "Текст результата '3 посещения в Invictus GO' не найден на success-экране",
            7,
        )
    ]


def test_success_page_click_go_to_main(monkeypatch):
    page = object.__new__(SuccessPage)
    calls = []

    monkeypatch.setattr(
        SuccessPage,
        "click",
        lambda self, locator: calls.append(locator),
    )

    page.click_go_to_main()

    assert calls == [SuccessPage.GO_TO_MAIN_BUTTON]
