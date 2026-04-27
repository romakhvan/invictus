# План: тест entrypoints страницы «Профиль»

Файл отслеживает прогресс добавления каждого entrypoint.
После каждого шага запускать:

```bash
pytest tests/mobile/profile/test_profile_entrypoints.py -v --mobile-no-reset
```

---

## Целевой тест

**Файл:** `tests/mobile/profile/test_profile_entrypoints.py`  
**Сценарий:** `new_user` (POTENTIAL_USER)  
**Паттерн:** `@pytest.mark.parametrize("entrypoint_method, ExpectedPage", [...])`

---

## Entrypoints

| # | Кнопка на экране | Метод в ProfilePage | Целевой page object | Статус |
|---|---|---|---|---|
| 1 | Купить абонемент | `open_buy_subscription()` | `ClubsPage` | ✅ метод добавлен |
| 2 | Смотреть (Скидки от партнёров) | `open_partner_discounts()` | `PartnerDiscountsPage` | ✅ метод добавлен |
| 3 | Добавить услугу | `open_add_service()` | `TrainingsPromoPage` | ✅ метод добавлен |
| 4 | Использовать промокод | `open_promo_code()` | `PromoCodePage` | ✅ метод добавлен |
| 5 | Гостевые посещения | `open_guest_visits()` | `GuestVisitsPage` | ✅ метод добавлен |
| 6 | Уведомления | `open_notifications()` | `NotificationsPage` | ✅ метод добавлен |
| 7 | Личная информация | `open_personal_info()` | ? | ⏳ ждём локатор |
| 8 | Мои карты | `open_my_cards()` | ? | ⏳ ждём локатор |
| 9 | История платежей | `open_payment_history()` | ? | ⏳ ждём локатор |
| 10 | Помощь | `open_help()` | ? | ⏳ ждём локатор |
| 11 | Документы | `open_documents()` | ? | ⏳ ждём локатор |
| 12 | Язык | `open_language()` | ? | ⏳ ждём локатор |

---

## Шаги реализации

### Шаг 1 — `open_buy_subscription()` → `ClubsPage` ✅

- Кнопка: `CTA_BUY_SUBSCRIPTION` (`@text="Купить абонемент"`)
- Метод добавлен в `ProfilePage`
- `ClubsPage` уже существует, `assert_ui` покрывает вариант покупки
- Написать тест с первым parametrize-кейсом и запустить

### Шаг 2 — `open_partner_discounts()` → `PartnerDiscountsPage` ✅

- Кнопка: `LINK_WATCH` (`@text="Смотреть"`)
- Маркеры: `DETECT_LOCATORS` = `"Развлечение"` + `"Рестораны"` (таб-фильтры категорий)
- Файл: `src/pages/mobile/profile/partner_discounts_page.py`

### Шаг 3 — `open_add_service()` → ? ⏳

- Кнопка: `CTA_ADD_SERVICE` (`@text="Добавить услугу"`)
- Целевой экран и маркер: **нужно уточнить**

### Шаг 4 — `open_promo_code()` → ? ⏳

- Кнопка: `CTA_USE_PROMO` (`@text="Использовать промокод"`)
- Целевой экран и маркер: **нужно уточнить**

---

## Файлы затронутые в рамках задачи

- `src/pages/mobile/profile/profile_page.py` — добавляются `open_*` методы
- `tests/mobile/profile/test_profile_entrypoints.py` — создаётся
- `tests_to_run_mobile.txt` — добавить строку после финального шага
- Новые page objects (по мере выяснения целевых экранов)
