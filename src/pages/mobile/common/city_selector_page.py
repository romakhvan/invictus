"""
Page Object: универсальный экран выбора клуба с фильтром по городу.

Экран может появляться в разных модулях приложения перед открытием целевой страницы.

Фактический UX:
- по умолчанию отображается список клубов
- сверху есть фильтр «Все города»
- по нажатию на фильтр открывается список городов
- выбор города фильтрует список клубов
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class CitySelectorPage(BaseMobilePage):
    """Экран выбора клуба с фильтром по городу."""

    page_title = "Выбор клуба/города"

    # Маркеры экрана: фильтр по городу присутствует на экране со списком клубов
    ALL_CITIES_FILTER = (AppiumBy.XPATH, '//android.widget.TextView[@text="Все города"]')
    APPLY_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Применить")

    # Маркеры состояний:
    # - список клубов: в списке есть клубы с текстом, содержащим "Invictus"
    # - список городов: в списке городов есть элемент с текстом "Астана"
    CLUBS_LIST_MARKER = (
        AppiumBy.XPATH,
        '//android.widget.TextView[contains(@text, "Invictus")]',
    )
    CITIES_LIST_MARKER = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Астана"]',
    )

    # Элементы списка городов (открывается после нажатия на фильтр)
    TITLE_SELECT_CITY = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Выберите город"]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран выбора клуба с фильтром по городу."""
        self.wait_visible(
            self.ALL_CITIES_FILTER,
            'Экран выбора клуба/города не найден (ожидался фильтр "Все города")',
        )
        print('✅ Открыт экран выбора клуба/города')

    def is_clubs_list_open(self, timeout: float = 1) -> bool:
        """True, если сейчас отображается список клубов (по маркеру текста 'Invictus')."""
        return self.is_visible(self.CLUBS_LIST_MARKER, timeout=timeout)

    def is_cities_list_open(self, timeout: float = 1) -> bool:
        """True, если сейчас отображается список городов (по маркеру текста 'Астана')."""
        return self.is_visible(self.CITIES_LIST_MARKER, timeout=timeout)

    def get_state(self, timeout: float = 1) -> str:
        """
        Определяет текущее состояние экрана.

        Возвращает:
        - "clubs_list" если отображается список клубов
        - "cities_list" если отображается список городов
        - "unknown" если по маркерам определить не удалось
        """
        if self.is_clubs_list_open(timeout=timeout):
            return "clubs_list"
        if self.is_cities_list_open(timeout=timeout):
            return "cities_list"
        return "unknown"

    @staticmethod
    def _city_option(city_name: str):
        return (AppiumBy.XPATH, f'//android.widget.TextView[@text="{city_name}"]')

    @staticmethod
    def _club_option(club_name: str):
        return (AppiumBy.XPATH, f'//android.widget.TextView[@text="{club_name}"]')

    def open_city_filter(self) -> "CitySelectorPage":
        """Открывает список городов через фильтр «Все города». Возвращает self."""
        self.click(self.ALL_CITIES_FILTER)
        self.wait_visible(
            self.CITIES_LIST_MARKER,
            'Список городов не открылся (не найден маркер "Астана")',
        )
        return self

    def select_city(self, city_name: str) -> "CitySelectorPage":
        """
        Выбрать город в списке городов.

        После выбора ожидается возврат к списку клубов (заголовок выбора города исчезает).
        """
        self.wait_visible(
            self.CITIES_LIST_MARKER,
            'Нельзя выбрать город: не открыт список городов (не найден маркер "Астана")',
        )
        self.click(self._city_option(city_name))
        # Возврат к экрану со списком клубов
        self.wait_visible(
            self.CLUBS_LIST_MARKER,
            'После выбора города не отображается список клубов (не найден маркер "Invictus")',
        )
        return self

    def select_all_cities(self) -> "CitySelectorPage":
        """
        Сбросить фильтр по городу на «Все города».

        Совместимо с текущими тестами: метод сам открывает список городов (если нужно),
        нажимает «Все города» и возвращает на список клубов.
        """
        state = self.get_state()
        if state == "clubs_list":
            # На экране клубов открываем список городов, чтобы выбрать "Все города".
            self.open_city_filter()
        elif state != "cities_list":
            raise AssertionError(
                f"Нельзя выполнить select_all_cities: неизвестное состояние экрана ({state})"
            )
        self.click(self.ALL_CITIES_FILTER)
        self.wait_visible(
            self.CLUBS_LIST_MARKER,
            'После выбора "Все города" не отображается список клубов (не найден маркер "Invictus")',
        )
        return self

    def select_club(self, club_name: str) -> "CitySelectorPage":
        """Выбрать клуб из списка клубов. Возвращает self (следующую страницу определяет вызывающий код)."""
        self.click(self._club_option(club_name))
        return self

    def apply_selection(self) -> "CitySelectorPage":
        """Нажать кнопку «Применить» на экране выбора клуба."""
        self.wait_visible(
            self.APPLY_BUTTON,
            'Кнопка "Применить" не найдена на экране выбора клуба/города',
        )
        self.click(self.APPLY_BUTTON)
        return self

    def select_club_and_apply(self, club_name: str) -> "CitySelectorPage":
        """
        Полный флоу выбора клуба: валидация → выбор клуба → «Применить».

        Возвращает self, т.к. целевая страница зависит от сценария вызывающего кода.
        """
        self.assert_ui()
        self.select_club(club_name)
        self.apply_selection()
        return self

