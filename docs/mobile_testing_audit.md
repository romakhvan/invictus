# Аудит мобильного тестового проекта

> Дата: 2026-03-30

---

## Что сделано хорошо (не менять)

- Паттерн `assert_ui()` / `wait_loaded()` с цепочками — правильный подход
- Паттерн `open_*()` методов, возвращающих загруженный Page Object
- Определение состояния главной через `HomeState` enum + `DETECT_LOCATOR` — элегантно
- Параметризация тестов в `test_bookings_entrypoints.py` и `test_home_entrypoints_new_user.py`
- Проверка роли пользователя через БД в `session_helpers.py`
- Структура `MobileInteractionMixin` — хорошая базовая абстракция

---

## 🔴 Критические проблемы

### 1. Локаторы и WebDriverWait в хелперах (нарушение CLAUDE.md)

**Файл:** `tests/mobile/helpers/auth_helpers.py` строки 31–50

```python
# ❌ Локаторы в хелпере — нарушение архитектурных правил
phone_input_xpaths = [
    '//android.widget.EditText[contains(@text, "000")]',
    ...
]
wait.until(EC.presence_of_element_located((AppiumBy.XPATH, xpath)))
```

Эти XPath'ы дублируют `PhoneAuthPage.PHONE_INPUT_XPATHS`.
**Исправление:** хелпер должен просто вызывать `PhoneAuthPage.enter_phone(phone)` — без своих локаторов и WebDriverWait.

---

### 2. `time.sleep()` вместо явных ожиданий

Главная причина нестабильных (flaky) тестов. Вхождения:

| Файл | Строки | Контекст |
|---|---|---|
| `tests/mobile/helpers/auth_helpers.py` | 60, 68 | После клика на поле ввода |
| `tests/mobile/helpers/onboarding_helpers.py` | 106–111 | После свайпа datepicker |
| `src/pages/mobile/onboarding/birth_date_page.py` | 42 | В методе `assert_ui()` |
| `src/pages/mobile/onboarding/sms_code_page.py` | 94 | В цикле ввода цифр keycode |
| `tests/conftest.py` | 715, 719, 726 | После `activate_app()` |

**Исправление:** заменить на `wait_visible()` / `wait_present()` из `MobileInteractionMixin` с конкретным элементом-маркером готовности.

---

### 3. Хрупкие селекторы

**`src/pages/mobile/shell/bottom_nav.py` строки 26–36:**
```python
# XPath с 27+ уровнями вложенности — поломается при любом изменении layout
QR_SCAN_XPATH = '//android.widget.FrameLayout[@resource-id="android:id/content"]/...'
```

**`src/pages/mobile/home/content/home_new_user_content.py` строки 127–135:**
```python
# Жёстко закодированные пиксельные координаты вместо локатора
center_x = (924 + 1032) // 2
center_y = (93 + 201) // 2
```

**Исправление:** найти `content-desc`, `resource-id` или `accessibility-id` через Appium Inspector.

---

### 4. Устаревшие методы не удалены

**Файлы:** `PhoneAuthPage`, `PreviewPage`, `SmsCodePage`

```python
def is_loaded(self) -> bool:
    """Устаревший метод. Используйте wait_loaded()."""
    ...

def verify_all_elements(self) -> bool:
    """Устаревший метод. Используйте assert_ui()."""
    ...
```

**Исправление:** удалить эти методы — они создают путаницу и могут случайно использоваться.

---

## 🟠 Важные проблемы

### 5. ~70% Page Objects без тестов

| Page Object | Файл | Статус |
|---|---|---|
| `StatsPage` | `src/pages/mobile/stats/stats_page.py` | ❌ нет тестов |
| `HomeSubscribedContent` | `src/pages/mobile/home/content/home_subscribed_content.py` | ❌ нет тестов |
| `HomeMemberContent` | `src/pages/mobile/home/content/home_member_content.py` | ❌ нет тестов |
| `CitySelectorPage` | `src/pages/mobile/common/city_selector_page.py` | ❌ нет тестов |
| `ProfilePage` | `src/pages/mobile/profile/profile_page.py` | ⚠️ только в e2e flow |
| `PersonalBookingsPage` | `src/pages/mobile/bookings/personal_bookings_page.py` | ⚠️ только `isinstance()` |
| `GroupBookingsPage` | `src/pages/mobile/bookings/group_bookings_page.py` | ⚠️ только `isinstance()` |
| `DoctorsBookingsPage` | `src/pages/mobile/bookings/doctors_bookings_page.py` | ⚠️ только `isinstance()` |
| `EventsBookingsPage` | `src/pages/mobile/bookings/events_bookings_page.py` | ⚠️ только `isinstance()` |

---

### 6. `test_bottom_navigation.py` — прямой Appium API вместо Page Objects

**Файл:** `tests/mobile/navigation/test_bottom_navigation.py` строки 29–52

```python
# ❌ Обходит Page Object слой
nav_elements = driver.find_elements(AppiumBy.XPATH, "//androidx.compose.material3.NavigationBarItem")
tab = driver.find_element(AppiumBy.XPATH, f"//*[@text='{tab_name}']")
```

**Исправление:** переписать через `HomePage.nav.open_*()` методы — как это делается в `test_navigation_new_user.py`.

---

### 7. Дублирование `hide_keyboard()`

**Файлы:**
- `src/pages/mobile/onboarding/name_page.py` строки 92–96
- `src/pages/mobile/auth/sms_code_page.py` строка 107

**Исправление:** добавить метод `hide_keyboard()` в `MobileInteractionMixin` (`src/pages/mobile/base_content_block.py`).

---

### 8. Нет teardown в фикстурах

**Файл:** `tests/mobile/conftest.py` строки 58–62

```python
@pytest.fixture
def potential_user_on_main_screen(mobile_driver, db):
    ensure_potential_user_on_main_screen(mobile_driver, db)
    yield mobile_driver
    # ❌ После теста приложение остаётся в произвольном состоянии
```

**Исправление:** добавить навигацию на главный экран после `yield` там, где важна изоляция.

---

## 🟡 Улучшения

### 9. `ActionChains` вместо встроенного `swipe()`

**Файл:** `src/pages/mobile/onboarding/birth_date_page.py` строки 57–78

Используются сложные W3C ActionChains для свайпа, хотя `self.swipe()` из `MobileInteractionMixin` уже есть.

---

### 10. Нет negative тестов

Ни один тест не проверяет, что элемент **не виден** или **недоступен** в определённых состояниях. Например: что кнопка "Купить" скрыта для уже подписанного пользователя.

---

### 11. Нет тестов для состояний SUBSCRIBED и MEMBER

`HomeSubscribedContent` и `HomeMemberContent` созданы, но нет фикстур с нужными пользователями и нет тестов. Нужно: добавить пользователей в STAGE БД и создать соответствующие фикстуры.

---

### 12. Огромный диагностический метод

**Файл:** `src/pages/mobile/base_mobile_page.py` строки 238–458

Метод `diagnose_current_screen()` — 220 строк. Делает три вещи: собирает данные, сохраняет файл, открывает редактор. Нарушает принцип единственной ответственности.

**Исправление:** разбить на `_collect_screen_data()` и отдельный шаг сохранения.

---

## Приоритизация

### Sprint 1 — архитектурные нарушения
- [ ] Убрать локаторы и WebDriverWait из `auth_helpers.py`
- [ ] Заменить все `time.sleep()` в helpers и Page Objects на explicit waits
- [ ] Удалить устаревшие методы `is_loaded()` / `verify_all_elements()`

### Sprint 2 — покрытие и стабильность
- [ ] Добавить `hide_keyboard()` в `MobileInteractionMixin`
- [ ] Создать тесты для `StatsPage` и `ProfilePage`
- [ ] Переписать `test_bottom_navigation.py` через `BottomNav` Page Object
- [ ] Заменить хрупкие XPath и координаты на нормальные локаторы

### Sprint 3 — расширение
- [ ] Создать фикстуры для SUBSCRIBED/MEMBER пользователей и их тесты
- [ ] Добавить negative тесты
- [ ] Рефакторинг `diagnose_current_screen()`
