# Legacy Docs Index

## Назначение

Карта существующих документов в `docs/`, чтобы новая Obsidian-структура не потеряла полезные материалы.

## Статусы

- `keep` - оставить как deep-dive источник
- `migrate` - постепенно перенести ключевое содержимое в новую структуру
- `merge` - объединить с другим документом
- `outdated` - содержит устаревшие команды или требует сверки

## QA automation docs

| Текущий файл | Новый entrypoint | Статус | Назначение / действие |
|---|---|---:|---|
| `docs/backend_testing_strategy.md` | [[backend]] | keep | Источник правды по backend checks, профилям `backend_check`/`backend_monitoring`/`backend_research`, repositories и правилам запуска. |
| `docs/qa/domain/webkassa.md` | [[webkassa]] | keep | Deep-dive по Web-Kassa monitoring/checks, тестам, данным и известным проблемам. |
| `docs/web_testing_strategy.md` | [[web]] | keep | Источник правды по Playwright web-тестам, Page Objects, фикстурам и особенностям сайта. |
| `docs/mobile_testing_strategy.md` | [[mobile]] | keep | Актуальный deep-dive по mobile-архитектуре, Appium, Page Objects и запуску через `run_tests.py`. |
| `docs/ui_testing_setup.md` | [[getting-started]], [[web]], [[mobile]] | merge | Общий setup UI-тестов; ключевые команды вынести в entrypoints. |
| `docs/testing_roadmap.md` | [[test-strategy]] | keep | Roadmap и исторический контекст покрытия. |
| `docs/mobile_testing_audit.md` | [[mobile]], [[best-practices]] | keep | Аудит mobile-подходов и технического долга. |
| `docs/coach_wallet_testing_guide.md` | [[backend]] | keep | Доменно-специфичный deep-dive для coach wallet. |

## Allure docs

| Текущий файл | Новый entrypoint | Статус | Назначение / действие |
|---|---|---:|---|
| `docs/allure/README.md` | [[reporting-allure]] | keep | Главная точка входа по Allure. |
| `docs/allure/backend_reporting_rules.md` | [[reporting-allure]], [[backend]] | keep | Канонический стандарт backend Allure-отчетов. |
| `docs/allure/report_generation.md` | [[reporting-allure]], [[run-tests]] | keep | Как `run_tests.py` собирает `allure-results` и `allure-report`. |
| `docs/allure/report_ui_patch.md` | [[reporting-allure]] | keep | Описание `src/utils/allure_report_patcher.py`. |

## Android / Appium docs

| Текущий файл | Новый entrypoint | Статус | Назначение / действие |
|---|---|---:|---|
| `docs/android_setup.md` | [[getting-started]], [[mobile]] | keep | Подробная настройка Android окружения. |
| `docs/ANDROID_QUICK_START.md` | [[getting-started]], [[mobile]] | keep | Быстрый старт Android/mobile. |
| `docs/appium_troubleshooting.md` | [[debugging]], [[mobile]] | keep | Диагностика Appium и устройств. |
| `docs/appium_inspector_guide.md` | [[mobile]], [[debugging]] | keep | Работа с Appium Inspector. |
| `docs/APP_MINIMIZE_PREVENTION.md` | [[debugging]], [[mobile]] | keep | Диагностика сворачивания приложения и keepalive-сценариев. |

## Notifications / Telegram docs

| Текущий файл | Новый entrypoint | Статус | Назначение / действие |
|---|---|---:|---|
| `docs/telegram_notifications_setup.md` | [[ci-cd]], [[reporting-allure]] | keep | Настройка Telegram-уведомлений и ссылок на Allure. |
| `docs/TELEGRAM_SETUP_QUICK.md` | [[ci-cd]] | merge | Быстрая версия Telegram setup; можно слить с основным гайдом. |

## Refactoring / planning docs

| Текущий файл | Новый entrypoint | Статус | Назначение / действие |
|---|---|---:|---|
| `docs/backend_refactoring_roadmap.md` | [[backend]], [[best-practices]] | keep | План рефакторинга backend-тестов и отчетности. |
| `docs/refactoring_comparison.md` | [[best-practices]] | keep | Сравнение подходов к рефакторингу. |
| `docs/superpowers/specs/2026-04-17-mobile-test-user-selector-design.md` | [[mobile]], [[test-data]] | keep | Спецификация выбора mobile test user. |
| `docs/superpowers/plans/2026-04-17-mobile-test-user-selector-phase-1.md` | [[mobile]], [[test-data]] | keep | План реализации выбора mobile test user. |

## Quick start docs

| Текущий файл | Новый entrypoint | Статус | Назначение / действие |
|---|---|---:|---|
| `docs/QUICK_START.md` | [[getting-started]], [[run-tests]] | keep | Короткий актуальный старт с ссылками на новую QA Automation документацию. |
| `README.md` | [[README]] | keep | Корневой README с краткой структурой проекта и ссылкой на `docs/qa/README.md`. |

## Известные расхождения

- `run_tests_mobile.py` отсутствует в репозитории; вместо него используется `run_tests.py` или прямой `pytest -m mobile`.
- В старых документах встречаются historical/roadmap sections; новые entrypoints должны ссылаться на них, а не копировать полностью.
- CI/CD-конфигов в репозитории нет; [[ci-cd]] описывает универсальный pytest + Allure pipeline.

## Следующий этап миграции

1. Проверить `docs/android_setup.md` и `docs/ANDROID_QUICK_START.md`: заменить устаревшие mobile test paths, если они не существуют.
2. Проверить `docs/ui_testing_setup.md`: убрать ссылки на несуществующие example files или пометить их как исторические.
3. Постепенно переносить короткие актуальные summaries в entrypoints, deep-dive оставлять в legacy docs.
