"""
Page Object для страницы клубов invictus.kz/clubs
"""

from playwright.sync_api import Page, Locator
from src.pages.web.base_web_page import BaseWebPage
from src.config.app_config import WEB_BASE_URL


class ClubsPage(BaseWebPage):
    """Страница со списком клубов /clubs"""

    URL = f"{WEB_BASE_URL}/clubs"

    # Заголовок
    PAGE_HEADING = "h1:has-text('Клубтар')"

    # Фильтры по типу
    FILTER_FITNESS = "button:has-text('Fitness')"
    FILTER_GO = "button:has-text('GO')"
    FILTER_GIRLS = "button:has-text('Girls')"

    # Фильтр по городу
    CITY_FILTER = "button:has-text('Барлық қалалар')"

    # Карточки клубов
    CLUB_CARDS = "a[href*='/clubs/']"

    # Пагинация
    PAGINATION_NEXT = "button:has-text('Next page')"
    PAGINATION_PREV = "button:has-text('Previous page')"

    # Кнопка "Показать на карте"
    SHOW_ON_MAP = "button:has-text('Картадан көрсету')"

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self):
        """Перейти на страницу клубов."""
        self.navigate_to(self.URL)

    def is_loaded(self) -> bool:
        """Проверка загрузки страницы клубов."""
        return self.is_visible(self.PAGE_HEADING)

    def get_club_cards(self) -> list[Locator]:
        """Вернуть все карточки клубов на текущей странице."""
        return self.page.locator(self.CLUB_CARDS).all()

    def get_clubs_count(self) -> int:
        return len(self.get_club_cards())

    def filter_by_fitness(self):
        self.click(self.FILTER_FITNESS)

    def filter_by_go(self):
        self.click(self.FILTER_GO)

    def filter_by_girls(self):
        self.click(self.FILTER_GIRLS)

    def is_next_page_enabled(self) -> bool:
        btn = self.page.locator(self.PAGINATION_NEXT)
        return btn.is_visible() and btn.is_enabled()

    def go_to_next_page(self):
        self.click(self.PAGINATION_NEXT)

    def get_first_club_name(self) -> str:
        cards = self.get_club_cards()
        if not cards:
            return ""
        return cards[0].inner_text().strip().split("\n")[0]

    def click_first_club(self):
        """Перейти на страницу первого клуба."""
        cards = self.get_club_cards()
        if cards:
            cards[0].click()
