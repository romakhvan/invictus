"""Home content for a user with available Rabbit Hole trainings."""

from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.home.content.home_new_user_content import HomeNewUserContent


class HomeRabbitHoleContent(HomeNewUserContent):
    """Home content for a user with a purchased Rabbit Hole offer."""

    page_title = "Home (Rabbit Hole)"

    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="3 КОМБО-ТРЕНИРОВКИ"]',
    )
    COMBO_TRAININGS_LABEL = DETECT_LOCATOR
    AVAILABLE_UNTIL_LABEL = (
        AppiumBy.XPATH,
        '//android.widget.TextView[starts-with(@text, "Доступны до ")]',
    )
    DETECT_LOCATORS = (DETECT_LOCATOR, AVAILABLE_UNTIL_LABEL)
