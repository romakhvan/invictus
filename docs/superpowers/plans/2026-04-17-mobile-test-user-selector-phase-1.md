# Mobile Test User Selector Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить единый модуль селектора тестовых mobile-пользователей и покрыть его unit-тестами, не переводя пока существующие flow и фикстуры на новый API.

**Architecture:** На первом этапе создаётся новый модуль `src/repositories/mobile_test_users_repository.py`, который инкапсулирует сценарии, контекст результата и минимальную стратегию выбора для ключевых сценариев. Существующие функции из `users_repository.py` остаются на месте и используются как низкоуровневые зависимости, поэтому интеграция в рабочие mobile-flow откладывается на следующий этап.

**Tech Stack:** Python, pytest, dataclasses, enum, существующие repository helpers, `HomeState`

---

### Task 1: Добавить unit-тесты для селектора

**Files:**
- Create: `tests/unit/repositories/test_mobile_test_users_repository.py`
- Test: `tests/unit/repositories/test_mobile_test_users_repository.py`

- [ ] **Step 1: Написать падающие тесты**

Покрыть минимальный набор поведения этапа 1:

- `ONBOARDING_NEW_USER` возвращает `override_phone`, если он передан
- `ONBOARDING_NEW_USER` подбирает свободный номер через низкоуровневый helper, если override не передан
- `POTENTIAL_USER` использует helper существующего potential-пользователя и заполняет `expected_home_state`
- `SUBSCRIBED_USER` и `MEMBER_USER` возвращают правильный `expected_home_state`
- если helper вернул `None`, селектор выбрасывает понятное исключение

- [ ] **Step 2: Запустить тесты и убедиться, что они падают**

Run:

```powershell
pytest tests/unit/repositories/test_mobile_test_users_repository.py -v
```

Expected:

- `FAIL` или `ERROR`, потому что модуля `mobile_test_users_repository.py` ещё нет

- [ ] **Step 3: Реализовать минимальный production-код**

Добавить:

- enum `MobileTestUserScenario`
- dataclass `TestUserContext`
- класс `MobileTestUserSelector`
- минимальную поддержку сценариев:
  - `ONBOARDING_NEW_USER`
  - `POTENTIAL_USER`
  - `SUBSCRIBED_USER`
  - `MEMBER_USER`
  - `COACH_USER`
  - `KYRGYZSTAN_ONBOARDING_NEW_USER`

На этом этапе селектор может опираться на существующие low-level helper-функции из `users_repository.py`.

- [ ] **Step 4: Запустить тесты и убедиться, что они проходят**

Run:

```powershell
pytest tests/unit/repositories/test_mobile_test_users_repository.py -v
```

Expected:

- все тесты `PASS`

- [ ] **Step 5: Проверить синтаксис изменённых Python-файлов**

Run:

```powershell
python -m py_compile src/repositories/mobile_test_users_repository.py tests/unit/repositories/test_mobile_test_users_repository.py
```

Expected:

- команда завершается без ошибок

### Task 2: Подготовить основу для следующего этапа без изменения flow

**Files:**
- Modify: `src/repositories/__init__.py` (только если в проекте принято экспортировать новые репозитории)

- [ ] **Step 1: Проверить, нужен ли re-export**

Если `src/repositories/__init__.py` не используется как публичная точка импорта для таких модулей, ничего не менять.

- [ ] **Step 2: Не переводить существующие mobile-flow на новый селектор**

Этап 1 считается завершённым без правок в:

- `tests/mobile/onboarding/test_client_onboarding.py`
- `tests/mobile/helpers/session_helpers.py`
- `tests/mobile/conftest.py`

Это сознательное ограничение области изменений.
