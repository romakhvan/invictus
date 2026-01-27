"""
Тест: Новый клиент покупает Rabbit Hole.

Сценарий:
1. Запуск приложения
2. Регистрация/Вход нового пользователя
3. Навигация к Rabbit Hole
4. Выбор продукта Rabbit Hole
5. Оформление покупки
6. Проверка в БД (rabbitholev2)
"""

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from appium.webdriver import Remote

# ============================================================================
# ШАГ 1: Импорты и подготовка
# ============================================================================
# Подсказка: Добавьте необходимые импорты:
# - pytest (уже есть)
# - mobile_driver фикстура из conftest (используется через параметр)
# - Page Objects для экранов (если они есть)
# - Репозитории для проверки БД (rabbitholev2_repository)
# - Утилиты для работы с тестовыми данными (если нужны)

# Пример импортов (раскомментируйте и дополните по необходимости):
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy
from src.config.app_config import MOBILE_APP_PACKAGE, MOBILE_APP_ACTIVITY
from src.repositories.rabbitholev2_repository import get_rabbitholev2_subscriptions_by_user
from src.utils.test_data import TestDataGenerator
from src.utils.ui_helpers import take_screenshot, click_element_with_fallback, verify_text_on_screen
from datetime import datetime, timedelta
import time


def enter_phone_number(driver, wait, phone_number: str, phone_input_xpath: str):
    """
    Ввод номера телефона в поле.
    
    Args:
        driver: Appium WebDriver объект
        wait: WebDriverWait объект
        phone_number: Номер телефона для ввода
        phone_input_xpath: XPath селектор поля ввода
    
    Returns:
        Элемент поля ввода
    """
    phone_input = wait.until(
        EC.presence_of_element_located((AppiumBy.XPATH, phone_input_xpath))
    )
    print("✅ Поле ввода номера телефона найдено")
    
    phone_input.click()
    time.sleep(1.5)
    
    print(f"Ввод номера через send_keys: {phone_number}")
    phone_input.send_keys(phone_number)
    phone_input.send_keys(phone_number)
    time.sleep(1.5)
    print(f"✅ Номер телефона введен: {phone_number}")
    
    return phone_input


# ============================================================================
# ШАГ 2: Запуск приложения
# ============================================================================
# Подсказка: Используйте фикстуру mobile_driver из conftest.py
# Приложение запускается автоматически при использовании фикстуры
# 
# Базовая структура теста (начните отсюда):
@pytest.mark.mobile
def test_new_client_buys_rabbit_hole(mobile_driver: "Remote", db):
    """
    Тест: Новый клиент покупает Rabbit Hole.
    
    Шаги:
    1. Запуск приложения (автоматически через фикстуру)
    2. Проверка запуска
    3. Ожидание загрузки главного экрана
    4. Создание/Вход нового пользователя
    5. Навигация к Rabbit Hole
    6. Выбор продукта
    7. Оформление покупки
    8. Проверка в БД
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("ТЕСТ: Новый клиент покупает Rabbit Hole")
    print("=" * 80)
    
    wait = WebDriverWait(driver, 20)
    
    try:
        # ШАГ 3: Проверка запуска приложения
        assert driver.current_package == MOBILE_APP_PACKAGE, \
            f"Неверный package: ожидался {MOBILE_APP_PACKAGE}, получен {driver.current_package}"
        print(f"✅ Приложение запущено: {driver.current_package}")
        
        # ШАГ 4: Ожидание и клик по кнопке "Начать" на превью
        print("\n--- ШАГ 1: Обработка превью с кнопкой 'Начать' ---")
        
        # Ищем кнопку "Начать" на превью
        start_button_xpath = '//android.widget.TextView[@text="Начать"]'
        
        # Используем утилиту для клика с fallback методами
        click_element_with_fallback(driver, wait, start_button_xpath, element_name="кнопка 'Начать'")
        
        # Небольшая задержка для перехода на следующий экран
        time.sleep(1)
        print("✅ Переход с превью выполнен")
        
        # ШАГ 2: Проверка экрана ввода номера телефона
        print("\n--- ШАГ 2: Проверка экрана ввода номера телефона ---")
        
        # Проверяем наличие текстовых элементов на экране
        verify_text_on_screen(wait, '//android.widget.TextView[@text="Введите ваш номер телефона"]', 
                             "Введите ваш номер телефона")
        verify_text_on_screen(wait, '//android.widget.TextView[@text="Отправим проверочный код"]', 
                             "Отправим проверочный код")
        verify_text_on_screen(wait, 
                             '//android.widget.TextView[contains(@text, "Нажимая «Продолжить», вы соглашаетесь c Условиями использования") and contains(@text, "Политикой конфиденциальности")]',
                             "Условия использования и Политика конфиденциальности")
        # verify_text_on_screen(wait, '//android.widget.TextView[starts-with(@text, "v")]', 
        #                      "Версия приложения")
        
        # ШАГ 3: Ввод номера телефона
        print("\n--- ШАГ 3: Ввод номера телефона ---")
        
        phone_input_xpath = '//android.widget.EditText[@text="(000) 000 00 00"]'
        test_phone = "7001234567"  # 10 цифр для заполнения маски
        
        enter_phone_number(driver, wait, test_phone, phone_input_xpath)
        
        # ШАГ 4: Переход к следующему шагу
        print("\n--- ШАГ 4: Переход к следующему шагу ---")
        
        next_button_xpath = '//android.widget.Button[@text="Продолжить"] | //android.widget.TextView[@text="Продолжить"]'
        click_element_with_fallback(driver, wait, next_button_xpath, element_name="кнопка 'Продолжить'")
        time.sleep(1)
        click_element_with_fallback(driver, wait, next_button_xpath, element_name="кнопка 'Продолжить'")
        time.sleep(1)
        
        # TODO: Добавить остальные шаги теста (навигация к Rabbit Hole, покупка, проверка в БД)
        
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
        
        # Пробрасываем оригинальную ошибку
        raise
  
# ============================================================================
# ШАГ 3: Проверка запуска приложения
# ============================================================================
# Подсказка: Убедитесь, что приложение запустилось корректно
# 
# Что проверить:
# - driver.current_package должен соответствовать MOBILE_APP_PACKAGE
# - driver.current_activity должна содержать ожидаемую activity
# - Можно сделать скриншот для отладки: driver.save_screenshot("step_1_app_launched.png")
# 
# Пример (раскомментируйте и используйте внутри функции теста):
# assert driver.current_package == MOBILE_APP_PACKAGE
# print(f"✅ Приложение запущено: {driver.current_package}")


# ============================================================================
# ШАГ 4: Ожидание загрузки главного экрана
# ============================================================================
# Подсказка: Дождитесь загрузки главного экрана приложения
# 
# Что сделать:
# - Используйте WebDriverWait для ожидания характерных элементов
# - Или используйте Page Object, если он есть (например, MainPage)
# - Проверьте видимость ключевых элементов (кнопки, текст)
# 
# Пример:
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from appium.webdriver.common.appiumby import AppiumBy
# 
# wait = WebDriverWait(driver, 20)
# # Замените селектор на реальный
# main_element = wait.until(EC.presence_of_element_located(
#     (AppiumBy.XPATH, '//android.widget.TextView[@text="Главная"]')
# ))
# print("✅ Главный экран загружен")


# ============================================================================
# ШАГ 5: Создание/Вход нового пользователя
# ============================================================================
# Подсказка: Создайте нового пользователя или войдите как новый пользователь
# 
# Варианты:
# A) Если есть тестовый пользователь - войдите под ним
# B) Если нужно создать нового - пройдите регистрацию
# 
# Что сделать:
# - Найдите кнопку "Войти" или "Регистрация"
# - Заполните форму (email, пароль, и т.д.)
# - Сохраните user_id для последующей проверки в БД
# 
# Пример структуры:
# # Найти кнопку входа
# login_button = driver.find_element(...)
# login_button.click()
# 
# # Заполнить форму
# email_input = driver.find_element(...)
# email_input.send_keys("test@example.com")
# 
# # Войти
# submit_button = driver.find_element(...)
# submit_button.click()
# 
# # Сохранить user_id (если можно получить из UI или создать через API)
# user_id = "..."  # Получить из UI или создать через API


# ============================================================================
# ШАГ 6: Навигация к разделу Rabbit Hole
# ============================================================================
# Подсказка: Перейдите к экрану/разделу Rabbit Hole
# 
# Что сделать:
# - Найдите элемент навигации (таб, кнопка, меню)
# - Кликните по нему
# - Дождитесь загрузки экрана Rabbit Hole
# 
# Пример:
# # Найти элемент навигации (замените на реальный селектор)
# rabbit_hole_tab = wait.until(EC.element_to_be_clickable(
#     (AppiumBy.XPATH, '//android.widget.TextView[@text="Rabbit Hole"]')
# ))
# rabbit_hole_tab.click()
# 
# # Дождаться загрузки экрана Rabbit Hole
# rabbit_hole_screen = wait.until(EC.presence_of_element_located(
#     (AppiumBy.ID, "rabbit_hole_container")  # Замените на реальный ID
# ))
# print("✅ Экран Rabbit Hole загружен")


# ============================================================================
# ШАГ 7: Выбор продукта Rabbit Hole
# ============================================================================
# Подсказка: Выберите конкретный продукт Rabbit Hole для покупки
# 
# Что сделать:
# - Найдите список продуктов Rabbit Hole
# - Выберите нужный продукт (клик по карточке/кнопке)
# - Дождитесь открытия экрана продукта
# 
# Пример:
# # Найти продукт (замените селектор)
# product_card = wait.until(EC.element_to_be_clickable(
#     (AppiumBy.XPATH, '//android.widget.TextView[@text="Rabbit Hole Premium"]')
# ))
# product_card.click()
# 
# # Дождаться экрана продукта
# product_screen = wait.until(EC.presence_of_element_located(
#     (AppiumBy.ID, "product_details")  # Замените на реальный ID
# ))
# print("✅ Экран продукта открыт")


# ============================================================================
# ШАГ 8: Оформление покупки
# ============================================================================
# Подсказка: Нажмите кнопку покупки и пройдите процесс оплаты
# 
# Что сделать:
# - Найдите кнопку "Купить" / "Оформить"
# - Кликните по ней
# - Если есть форма оплаты - заполните её (или используйте тестовый способ оплаты)
# - Подтвердите покупку
# - Дождитесь подтверждения успешной покупки
# 
# Пример:
# # Найти кнопку покупки
# buy_button = wait.until(EC.element_to_be_clickable(
#     (AppiumBy.ID, "buy_button")  # Замените на реальный ID
# ))
# buy_button.click()
# 
# # Если есть форма оплаты
# # payment_method = wait.until(...)
# # payment_method.click()
# 
# # Подтвердить покупку
# # confirm_button = wait.until(...)
# # confirm_button.click()
# 
# # Дождаться подтверждения
# success_message = wait.until(EC.presence_of_element_located(
#     (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "успешно")]')
# ))
# print("✅ Покупка оформлена")


# ============================================================================
# ШАГ 9: Проверка в базе данных
# ============================================================================
# Подсказка: Проверьте, что запись появилась в коллекции rabbitholev2
# 
# Что проверить:
# - Запись в rabbitholev2 для этого user_id существует
# - Поля записи корректны (status, created_at, и т.д.)
# - Запись создана недавно (в пределах последних минут)
# 
# Пример:
# from src.repositories.rabbitholev2_repository import get_rabbitholev2_subscriptions_by_user
# from datetime import datetime, timedelta
# 
# # Получить записи для пользователя за последний час
# results = get_rabbitholev2_subscriptions_by_user(db, user_id=user_id, days=1)
# 
# # Проверить, что есть хотя бы одна запись
# assert len(results) > 0, "Запись в rabbitholev2 не найдена"
# 
# # Проверить последнюю запись
# latest_record = results[0]  # Сортировка по created_at DESC
# 
# # Проверить, что запись создана недавно (в последние 5 минут)
# created_at = latest_record.get("rabbithole_created_at")
# time_diff = datetime.now() - created_at
# assert time_diff < timedelta(minutes=5), "Запись слишком старая"
# 
# print(f"✅ Запись в БД найдена: {latest_record.get('rabbithole_id')}")


# ============================================================================
# ШАГ 10: Дополнительные проверки (опционально)
# ============================================================================
# Подсказка: Добавьте дополнительные проверки, если нужно
# 
# Что можно проверить:
# - Статус подписки в UI соответствует статусу в БД
# - Сумма покупки корректна
# - Дата окончания подписки правильная
# - Скриншот финального состояния
# 
# Пример:
# # Сделать скриншот успешной покупки
# driver.save_screenshot("rabbit_hole_purchase_success.png")
# 
# # Проверить статус в UI
# # status_text = driver.find_element(...).text
# # assert "активна" in status_text.lower()


# ============================================================================
# ШАГ 11: Очистка (если нужна)
# ============================================================================
# Подсказка: Если нужно очистить тестовые данные после теста
# 
# Что сделать:
# - Удалить тестового пользователя (если создавали)
# - Откатить транзакцию (если возможно)
# - Или просто закомментировать этот шаг, если очистка не нужна
# 
# Пример:
# # Очистка выполняется автоматически через фикстуры
# # mobile_driver автоматически закрывается после теста
# # Если нужно удалить тестовые данные из БД:
# # db.rabbitholev2.delete_one({"_id": ObjectId(latest_record.get("rabbithole_id"))})


# ============================================================================
# ПРИМЕЧАНИЯ:
# ============================================================================
# 1. Замените все селекторы (XPath, ID) на реальные из вашего приложения
# 2. Используйте Page Objects для переиспользования кода
# 3. Добавьте обработку ошибок (try/except) где необходимо
# 4. Используйте явные ожидания (WebDriverWait) вместо time.sleep()
# 5. Делайте скриншоты на ключевых этапах для отладки
# 6. Проверяйте результаты каждого шага перед переходом к следующему
# 7. Сохраняйте user_id и другие важные данные для проверок в БД

