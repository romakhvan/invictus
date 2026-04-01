"""
Тесты страницы клубов invictus.kz/clubs
"""

import pytest
from playwright.sync_api import Page
from src.pages.web.clubs_page import ClubsPage


@pytest.mark.web
@pytest.mark.smoke
def test_clubs_page_loads(web_page: Page):
    """Страница клубов загружается с корректным заголовком."""
    page = ClubsPage(web_page)
    page.open()
    assert page.is_loaded(), "Страница клубов не загрузилась"


@pytest.mark.web
@pytest.mark.smoke
def test_clubs_list_not_empty(web_page: Page):
    """На странице клубов отображается хотя бы один клуб."""
    page = ClubsPage(web_page)
    page.open()
    count = page.get_clubs_count()
    assert count > 0, "Список клубов пуст"


@pytest.mark.web
def test_type_filter_buttons_visible(web_page: Page):
    """Кнопки фильтрации Fitness, GO, Girls отображаются."""
    page = ClubsPage(web_page)
    page.open()

    assert page.is_visible(page.FILTER_FITNESS), "Фильтр 'Fitness' не найден"
    assert page.is_visible(page.FILTER_GO), "Фильтр 'GO' не найден"
    assert page.is_visible(page.FILTER_GIRLS), "Фильтр 'Girls' не найден"


@pytest.mark.web
def test_city_filter_visible(web_page: Page):
    """Фильтр городов отображается."""
    page = ClubsPage(web_page)
    page.open()
    assert page.is_visible(page.CITY_FILTER), "Фильтр городов не найден"


@pytest.mark.web
def test_filter_fitness_updates_url(web_page: Page):
    """Клик по фильтру 'Fitness' добавляет параметр type=Fitness в URL."""
    page = ClubsPage(web_page)
    page.open()
    page.filter_by_fitness()
    page.page.wait_for_url("**/clubs?type=Fitness**")
    assert "type=Fitness" in page.get_current_url(), "URL не содержит type=Fitness после фильтрации"


@pytest.mark.web
def test_filter_go_updates_url(web_page: Page):
    """Клик по фильтру 'GO' добавляет параметр type=GO в URL."""
    page = ClubsPage(web_page)
    page.open()
    page.filter_by_go()
    page.page.wait_for_url("**/clubs?type=GO**")
    assert "type=GO" in page.get_current_url(), "URL не содержит type=GO после фильтрации"


@pytest.mark.web
def test_filter_girls_updates_url(web_page: Page):
    """Клик по фильтру 'Girls' добавляет параметр type=Girls в URL."""
    page = ClubsPage(web_page)
    page.open()
    page.filter_by_girls()
    page.page.wait_for_url("**/clubs?type=Girls**")
    assert "type=Girls" in page.get_current_url(), "URL не содержит type=Girls после фильтрации"


@pytest.mark.web
def test_pagination_next_button_enabled(web_page: Page):
    """Кнопка 'следующая страница' активна (клубов больше одной страницы)."""
    page = ClubsPage(web_page)
    page.open()
    assert page.is_next_page_enabled(), "Кнопка следующей страницы недоступна"


@pytest.mark.web
def test_pagination_goes_to_page_two(web_page: Page):
    """Нажатие кнопки 'следующая страница' загружает вторую страницу клубов."""
    page = ClubsPage(web_page)
    page.open()
    first_club_before = page.get_first_club_name()
    page.go_to_next_page()
    page.page.wait_for_load_state("networkidle")
    first_club_after = page.get_first_club_name()
    assert first_club_before != first_club_after, "Список клубов не изменился после перехода на стр. 2"


@pytest.mark.web
def test_club_card_opens_detail_page(web_page: Page):
    """Клик на карточку клуба открывает страницу деталей клуба."""
    page = ClubsPage(web_page)
    page.open()
    page.click_first_club()
    page.page.wait_for_load_state("networkidle")
    current_url = page.get_current_url()
    assert "/clubs/" in current_url, f"Не открылась страница клуба, URL: {current_url}"


@pytest.mark.web
def test_show_on_map_button_visible(web_page: Page):
    """Кнопка 'Картадан көрсету' отображается."""
    page = ClubsPage(web_page)
    page.open()
    assert page.is_visible(page.SHOW_ON_MAP), "Кнопка показа на карте не найдена"
