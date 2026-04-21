from __future__ import annotations

from typing import Iterable

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_content_block import BaseContentBlock
from src.utils.club_card_data import ClubCardData, normalize_club_text


class ClubFilterComponent(BaseContentBlock):
    """
    Reusable component for club/city filters and club cards list.

    Supports screens where the same UI pattern is used:
    - clubs list with "Все города"
    - cities selector opened from that filter
    - club cards that expose name/city/address
    """

    content_title = "Club Filter"
    DEFAULT_CITY_NAME = "Алматы"

    ALL_CITIES_FILTER = (AppiumBy.XPATH, '//android.widget.TextView[@text="Все города"]')
    APPLY_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Применить")
    CLUBS_LIST_MARKER = (
        AppiumBy.XPATH,
        '//android.widget.TextView[contains(@text, "Invictus")]',
    )
    CITIES_LIST_MARKER = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Астана"]',
    )
    CLUB_TITLE_ELEMENTS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[starts-with(@text, "Invictus")]',
    )
    TEXT_VIEW_ELEMENTS = (AppiumBy.CLASS_NAME, "android.widget.TextView")

    def __init__(self, driver: Remote):
        super().__init__(driver)

    @staticmethod
    def _city_option(city_name: str):
        return (AppiumBy.XPATH, f'//android.widget.TextView[@text="{city_name}"]')

    @staticmethod
    def _club_option(club_name: str):
        return (AppiumBy.XPATH, f'//android.widget.TextView[@text="{club_name}"]')

    def assert_ui(self) -> None:
        self.wait_visible(
            self.ALL_CITIES_FILTER,
            'Экран выбора клуба/города не найден (ожидался фильтр "Все города")',
        )

    def is_clubs_list_open(self, timeout: float = 1) -> bool:
        return self.is_visible(self.CLUBS_LIST_MARKER, timeout=timeout)

    def is_cities_list_open(self, timeout: float = 1) -> bool:
        return self.is_visible(self.CITIES_LIST_MARKER, timeout=timeout)

    def get_state(self, timeout: float = 1) -> str:
        if self.is_clubs_list_open(timeout=timeout):
            return "clubs_list"
        if self.is_cities_list_open(timeout=timeout):
            return "cities_list"
        return "unknown"

    def is_any_selector_state_open(self, timeout: float = 1) -> bool:
        return self.get_state(timeout=timeout) != "unknown"

    def open_city_filter(self) -> "ClubFilterComponent":
        self.click(self.ALL_CITIES_FILTER)
        self.wait_visible(
            self.CITIES_LIST_MARKER,
            'Список городов не открылся (не найден маркер "Астана")',
        )
        return self

    def select_city(self, city_name: str) -> "ClubFilterComponent":
        if self.get_state(timeout=1) == "clubs_list":
            self.open_city_filter()
        self.wait_visible(
            self.CITIES_LIST_MARKER,
            "Нельзя выбрать город: список городов не открыт",
        )
        self.click(self._city_option(city_name))
        self.wait_visible(
            self.CLUBS_LIST_MARKER,
            'После выбора города не отображается список клубов (не найден маркер "Invictus")',
        )
        return self

    def select_default_city(self, city_name: str = DEFAULT_CITY_NAME) -> "ClubFilterComponent":
        self.wait_visible(
            self.CITIES_LIST_MARKER,
            "Нельзя выбрать город по умолчанию: список городов не открыт",
        )
        self.click(self._city_option(city_name))
        return self

    def select_all_cities(self) -> "ClubFilterComponent":
        state = self.get_state()
        if state == "clubs_list":
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

    def select_club(self, club_name: str) -> "ClubFilterComponent":
        self.click(self._club_option(club_name))
        return self

    def apply_selection(self) -> "ClubFilterComponent":
        self.wait_visible(
            self.APPLY_BUTTON,
            'Кнопка "Применить" не найдена на экране выбора клуба/города',
        )
        self.click(self.APPLY_BUTTON)
        return self

    def select_club_and_apply(self, club_name: str) -> "ClubFilterComponent":
        self.assert_ui()
        self.select_club(club_name)
        self.apply_selection()
        return self

    def get_visible_club_cards(self) -> list[ClubCardData]:
        cards = self._parse_cards_from_visible_texts()
        if not cards:
            raise AssertionError("На экране не найдено видимых карточек клубов Invictus")
        return cards

    def get_all_club_cards(self, max_swipes: int = 12) -> list[ClubCardData]:
        collected: dict[tuple[str, str, str], ClubCardData] = {}
        stable_iterations = 0

        for _ in range(max_swipes):
            before_count = len(collected)
            for card in self.get_visible_club_cards():
                collected[card.key] = card

            if len(collected) == before_count:
                stable_iterations += 1
            else:
                stable_iterations = 0

            if stable_iterations >= 2:
                break

            self._swipe_list_up()

        return list(collected.values())

    def _swipe_list_up(self) -> None:
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = int(size["height"] * 0.78)
        end_y = int(size["height"] * 0.34)
        self.swipe(start_x, start_y, start_x, end_y, 600)

    def _parse_cards_from_visible_texts(self) -> list[ClubCardData]:
        text_nodes = self._collect_visible_text_nodes()
        title_nodes = [node for node in text_nodes if node["text"].startswith("Invictus")]
        cards: list[ClubCardData] = []
        seen_keys: set[tuple[str, str, str]] = set()

        for title_node in title_nodes:
            below_lines = self._texts_below_title(title_node, text_nodes)
            card = ClubCardData(
                name=title_node["text"],
                city=below_lines[0] if len(below_lines) >= 1 else "",
                address=below_lines[1] if len(below_lines) >= 2 else "",
            )
            if card.key not in seen_keys:
                seen_keys.add(card.key)
                cards.append(card)

        return cards

    def _collect_visible_text_nodes(self) -> list[dict]:
        nodes: list[dict] = []
        for element in self.find_elements(self.TEXT_VIEW_ELEMENTS):
            try:
                if not element.is_displayed():
                    continue
                text = normalize_club_text(element.text)
                if not text:
                    continue
                location = element.location
                size = element.size
                nodes.append(
                    {
                        "text": text,
                        "x": int(location.get("x", 0)),
                        "y": int(location.get("y", 0)),
                        "width": int(size.get("width", 0)),
                        "height": int(size.get("height", 0)),
                    }
                )
            except Exception:
                continue
        nodes.sort(key=lambda item: (item["y"], item["x"], item["text"]))
        return nodes

    def _texts_below_title(self, title_node: dict, all_nodes: Iterable[dict]) -> list[str]:
        title_x = title_node["x"]
        title_y = title_node["y"]
        collected: list[str] = []

        for node in all_nodes:
            if node is title_node:
                continue
            if node["y"] <= title_y:
                continue
            if node["y"] - title_y > 220:
                break
            if abs(node["x"] - title_x) > 90:
                continue
            if node["text"].startswith("Invictus"):
                break
            if node["text"] == "Все города":
                continue
            if node["text"] not in collected:
                collected.append(node["text"])
            if len(collected) == 2:
                break

        return collected
