"""
Page Object для главной страницы invictus.kz
"""

from playwright.sync_api import Page
from src.pages.web.base_web_page import BaseWebPage
from src.config.app_config import WEB_BASE_URL


class HomePage(BaseWebPage):
    """Главная страница invictus.kz"""

    URL = WEB_BASE_URL

    # Навигация
    NAV = "nav[aria-label='Main navigation']"
    NAV_CLUBS = f"{NAV} a[href*='/clubs']"
    NAV_TRAININGS = f"{NAV} a[href*='/group-trainings']"
    NAV_COACHES = f"{NAV} a[href*='/personal-trainings']"
    NAV_STORE = f"{NAV} a[href*='/shop']"
    NAV_FRANCHISE = f"{NAV} a[href*='/franchise']"
    NAV_ABOUT = f"{NAV} a[href*='/about-us']"

    # Хедер — кнопки действий
    LOGIN_LINK = "a[href*='/auth']"
    LEAVE_REQUEST_LINK = "a[href='/feedback/form']"
    DOWNLOAD_APP_BUTTON = "button:has-text('Қолданбаны жүктеу')"
    LANGUAGE_BUTTON = "button:has-text('Қазақша')"

    # Hero-секция
    HERO_HEADING = "h1"
    HERO_BUY_SUBSCRIPTION = "a[href='/clubs']:has-text('Абонемент')"
    HERO_LEAVE_REQUEST = "a[href='/feedback/form']:has-text('Өтінім')"

    # Секции типов клубов
    FITNESS_SECTION_HEADING = "h2:has-text('Invictus Fitness')"
    GO_SECTION_HEADING = "h2:has-text('Invictus GO')"
    GIRLS_SECTION_HEADING = "h2:has-text('Invictus Girls')"
    KIDS_SECTION_HEADING = "h2:has-text('Invictus Kids')"

    CHOOSE_CLUB_FITNESS = "a[href='/clubs?type=Fitness']:has-text('Клубты')"
    CHOOSE_CLUB_GO = "a[href='/clubs?type=GO']:has-text('Клубты')"
    CHOOSE_CLUB_GIRLS = "a[href='/clubs?type=Girls']:has-text('Клубты')"

    # Футер
    FOOTER = "footer, [role='contentinfo']"
    FOOTER_INSTAGRAM = "a[href*='instagram.com']"
    FOOTER_COPYRIGHT = "p:has-text('Invictus Fitness')"

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self):
        """Перейти на главную страницу."""
        self.navigate_to(self.URL)

    def is_loaded(self) -> bool:
        """Проверка загрузки главной страницы."""
        return self.is_visible(self.HERO_HEADING)

    def get_hero_heading_text(self) -> str:
        return self.get_text(self.HERO_HEADING)

    def get_nav_links(self) -> list[str]:
        """Вернуть список href всех навигационных ссылок."""
        links = self.page.locator(f"{self.NAV} a").all()
        return [link.get_attribute("href") or "" for link in links]

    def click_login(self):
        self.click(self.LOGIN_LINK)

    def click_clubs_nav(self):
        self.click(self.NAV_CLUBS)

    def click_trainings_nav(self):
        self.click(self.NAV_TRAININGS)

    def click_buy_subscription(self):
        self.click(self.HERO_BUY_SUBSCRIPTION)

    def is_footer_visible(self) -> bool:
        return self.is_visible(self.FOOTER_COPYRIGHT)
