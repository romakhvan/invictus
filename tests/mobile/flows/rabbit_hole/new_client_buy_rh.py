"""
Тест: Новый клиент покупает Rabbit Hole.

Сценарий:
1. Запуск приложения
2. Регистрация/Вход нового пользователя (через хелпер)
3. Навигация к Rabbit Hole
4. Выбор продукта Rabbit Hole
5. Оформление покупки
6. Проверка в БД (rabbitholev2)
"""

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from appium.webdriver import Remote

from selenium.webdriver.support.ui import WebDriverWait
from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.clubs.clubs_page import ClubsPage
from src.pages.mobile.common import PaymentConfirmationPage, SuccessPage
from src.pages.mobile.home import HomePage, HomeState
from src.pages.mobile.home.content import HomeNewUserContent
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
)
from src.repositories.cards_repository import attach_latest_saved_card_to_user
from src.repositories.rabbitholev2_repository import get_rabbitholev2_subscriptions_by_user
from src.repositories.transactions_repository import get_recent_transaction_by_user
from src.repositories.visits_repository import get_recent_rabbit_visits_by_user
from src.utils.ui_helpers import take_screenshot
from tests.mobile.helpers.auth_helpers import authorize_user
from datetime import datetime, timedelta
import time


def _resolve_user_id(context, db):
    """Берёт user_id из контекста выбранного тестового пользователя."""
    if context.user_id:
        return context.user_id
    raise ValueError("Rabbit Hole flow требует context с заполненным user_id.")


def _payment_transaction_since(now_utc: datetime | None = None) -> datetime:
    """Возвращает UTC-границу поиска transaction.created_at в Mongo."""
    current_utc = now_utc or datetime.utcnow()
    return current_utc - timedelta(seconds=5)


def _wait_recent_transaction_by_user(
    db,
    *,
    user_id,
    since: datetime,
    expected_amount,
    timeout_seconds: int = 30,
    poll_interval_seconds: int = 2,
) -> list[dict]:
    """Ожидает появления свежей transaction после клика оплаты."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        transactions = get_recent_transaction_by_user(
            db,
            user_id=user_id,
            since=since,
            expected_amount=expected_amount,
            limit=1,
        )
        if transactions:
            return transactions
        if time.monotonic() >= deadline:
            return []
        time.sleep(poll_interval_seconds)


def _assert_rabbit_visits_created(
    db,
    *,
    user_id,
    since: datetime,
    timeout_seconds: int = 30,
    poll_interval_seconds: int = 2,
) -> list[dict]:
    """Проверяет, что после покупки Rabbit Hole пользователю выданы 3 visit."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        visits = get_recent_rabbit_visits_by_user(
            db,
            user_id=user_id,
            since=since,
            limit=3,
        )
        if len(visits) == 3:
            return visits
        if time.monotonic() >= deadline:
            break
        time.sleep(poll_interval_seconds)

    assert len(visits) == 3, (
        "Ожидалось 3 купленных visit после покупки Rabbit Hole, "
        f"найдено {len(visits)} для user_id={user_id}."
    )


# Точный текст из списка выбора оплаты: "Kaspi.kz" для Kaspi,
# "•• 6267" для сохранённой карты, 
# "Добавить банковскую карту" для добавления карты.
PAYMENT_METHOD_NAME = "•• 6267"
RABBIT_HOLE_SUCCESS_REWARD_TEXT = "3 посещения в Invictus GO"


def _assert_rabbitholev2_subscription_created(
    db,
    *,
    user_id,
    days: int = 1,
) -> list[dict]:
    """Check that Rabbit Hole purchase record exists."""
    records = get_rabbitholev2_subscriptions_by_user(db, user_id=user_id, days=days)
    assert records, (
        "Rabbit Hole purchase record was not found in rabbitholev2 "
        f"for user_id={user_id} during the last {days} day(s)."
    )
    return records


def _assert_rabbit_hole_success_page(driver) -> SuccessPage:
    """Проверяет success-экран после покупки Rabbit Hole."""
    success_page = SuccessPage(driver).wait_loaded()
    success_page.assert_reward_text_visible(RABBIT_HOLE_SUCCESS_REWARD_TEXT)
    success_page.click_go_to_main()
    home = HomePage(driver).wait_loaded()
    current_state = home.get_current_home_state()
    assert current_state == HomeState.RABBIT_HOLE, (
        "После нажатия 'На главную' ожидалась главная в состоянии "
        f"RABBIT_HOLE, получено {current_state.value}."
    )
    return success_page


@pytest.mark.mobile
@pytest.mark.flow
def test_new_client_buys_rabbit_hole(mobile_driver: "Remote", db):
    """
    Flow-тест: Новый клиент покупает Rabbit Hole.
    
    Шаги:
    1. Запуск приложения (автоматически через фикстуру)
    2. Авторизация пользователя (через хелпер)
    3. Навигация к Rabbit Hole
    4. Выбор продукта
    5. Оформление покупки
    6. Проверка в БД
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("FLOW-ТЕСТ: Новый клиент покупает Rabbit Hole")
    print("=" * 80)
    
    wait = WebDriverWait(driver, 10)
    
    try:
        # Проверка запуска приложения
        assert driver.current_package == MOBILE_APP_PACKAGE, \
            f"Неверный package: ожидался {MOBILE_APP_PACKAGE}, получен {driver.current_package}"
        print(f"✅ Приложение запущено: {driver.current_package}")
        
        # ШАГ 1: Авторизация пользователя (используем хелпер)
        print("\n--- ШАГ 1: Авторизация пользователя ---")
        selector = MobileTestUserSelector(db)
        user_context = selector.select_or_skip(MobileTestUserScenario.POTENTIAL_USER)
        test_phone = user_context.phone
        if not test_phone:
            pytest.skip(
                "В БД не найден пользователь с role='potential' и записью в usermetadatas "
                "для авторизации в Rabbit Hole flow."
            )
        authorize_user(driver, wait, test_phone, expected_state=HomeState.NEW_USER)
        user_id = _resolve_user_id(user_context, db)
        attach_latest_saved_card_to_user(db, user_id=user_id)

        # ШАГ 2: Нажатие на «Расскажите подробнее!» на главной
        print("\n--- ШАГ 2: Открытие оффера Rabbit Hole с главной ---")
        home = HomePage(driver).wait_loaded()
        assert home.get_current_home_state() == HomeState.NEW_USER, (
            "После авторизации ожидалось состояние NEW_USER на главной."
        )

        content = home.get_content()
        assert isinstance(content, HomeNewUserContent), (
            "Ожидался контент главной для нового пользователя."
        )

        content.click_tell_more()
        assert content.is_visible(
            content.OFFER_TITLE
        ), "После клика по «Расскажите подробнее!» не открылся оффер Rabbit Hole."
        assert content.is_visible(
            content.RABBIT_HOLE_BUY_BTN, timeout=10
        ), "В оверлее Rabbit Hole не появилась кнопка «Купить»."
        expected_amount = content.assert_rabbit_hole_price_consistency()
        print("✅ Оффер Rabbit Hole открыт по кнопке «Расскажите подробнее!»")

        # ШАГ 3: Нажатие на кнопку «Купить за 2 990»
        print("\n--- ШАГ 3: Нажатие на кнопку «Купить за 2 990» ---")
        content.click(content.RABBIT_HOLE_BUY_BTN, timeout=10)
        print("✅ Нажата кнопка «Купить за 2 990»")

        # ШАГ 4: Открытие экрана выбора города/клуба для покупки тренировок
        print("\n--- ШАГ 4: Проверка открытия экрана выбора города/клуба ---")
        clubs_page = ClubsPage(driver).wait_loaded()
        clubs_page.assert_purchase_trainings_variant_open()
        print("✅ Открылся экран «Покупка тренировок» с выбором города и списком клубов")

        # ШАГ 5: Выбор первой верхней карточки клуба Invictus GO
        print("\n--- ШАГ 5: Выбор первой верхней карточки Invictus GO ---")
        selected_club_name = clubs_page.click_first_invictus_go_card()

        # ШАГ 6: Открытие универсальной страницы подтверждения оплаты
        print("\n--- ШАГ 6: Проверка открытия страницы подтверждения оплаты ---")
        payment_page = PaymentConfirmationPage(driver).wait_loaded()
        payment_page.assert_payment_summary_visible()
        payment_page.assert_product_title_visible("3 тренировки")
        payment_page.assert_selected_club_visible(selected_club_name)
        payment_page.select_payment_method(PAYMENT_METHOD_NAME)
        payment_page.assert_total_amount_visible(expected_amount)
        print("✅ Открыта страница подтверждения оплаты с продуктом, клубом и кнопкой оплаты")

        # ШАГ 7: Принятие оферты и переход к оплате
        print("\n--- ШАГ 7: Принятие оферты и нажатие на «Оплатить» ---")
        pay_clicked_at = _payment_transaction_since()
        payment_page.accept_terms()
        payment_page.click_pay()
        _assert_rabbit_hole_success_page(driver)

        # ШАГ 8: Проверка success-экрана и записи в transactions
        print("\n--- ШАГ 8: Проверка записи в transactions ---")
        assert user_id is not None, (
            f"Не удалось определить user_id по телефону {test_phone} для проверки transactions."
        )
        transactions = _wait_recent_transaction_by_user(
            db,
            user_id=user_id,
            since=pay_clicked_at,
            expected_amount=expected_amount,
        )
        assert transactions, (
            "После нажатия на «Оплатить» не найдена новая запись в transactions "
            f"для user_id={user_id} и суммы {expected_amount}."
        )
        print(f"✅ Найдена запись в transactions: {transactions[0]['_id']}")

        # ШАГ 9: Проверка выдачи 3 купленных visit
        print("\n--- ШАГ 9: Проверка записей в visits ---")
        visits = _assert_rabbit_visits_created(
            db,
            user_id=user_id,
            since=pay_clicked_at,
        )
        rabbithole_records = _assert_rabbitholev2_subscription_created(
            db,
            user_id=user_id,
        )
        print(
            "Найдены записи Rabbit Hole: "
            f"{[record['rabbithole_id'] for record in rabbithole_records]}"
        )
        print(f"✅ Найдены купленные visits: {[visit['_id'] for visit in visits]}")
        
    except Exception as e:
        # Автоматический скриншот при ошибке
        try:
            screenshot_path = take_screenshot(
                driver, 
                f"error_new_client_buy_rh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            print(f"📸 Скриншот ошибки сохранен: {screenshot_path}")
        except Exception as screenshot_error:
            print(f"⚠️ Не удалось сделать скриншот при ошибке: {screenshot_error}")
        
        raise
