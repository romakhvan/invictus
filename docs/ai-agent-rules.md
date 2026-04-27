# AI Agent Rules

This file is the shared source of truth for AI agents working in this repository.
Claude, Codex, Cursor, and other agents should read this file before making code
changes.

## Project Overview

This repository is an automated testing system for Invictus web, mobile, and
backend checks.

Main goals:

- Stable, repeatable, maintainable automation.
- Clear separation between tests, page objects, helpers, fixtures, repositories,
  and validators.
- Meaningful Allure reports that are useful for QA, product, and developers.
- Minimal duplication and predictable structure for long-term maintenance.

Main areas:

- `tests/web/` - Playwright tests.
- `tests/mobile/` - Appium tests.
- `tests/backend/` - direct backend and database validation tests.
- `src/pages/` - page objects and UI interaction layers.
- `src/repositories/` - database access objects.
- `src/validators/` - validation logic.
- `docs/qa/` - main QA documentation.

## Agent Operating Rules

- Prefer the smallest safe change that satisfies the request.
- Read the relevant code and documentation before editing.
- Do not introduce new dependencies without calling them out.
- Do not perform large unrelated refactors unless explicitly requested.
- Preserve existing project patterns and naming conventions.
- When unsure, propose one or two options with trade-offs and default to the
  safest minimal change.
- Do not replace intentional emojis in `print()` or log messages with ASCII
  alternatives unless the user explicitly asks.

## Setup And Test Commands

```bash
pip install -r requirements.txt
playwright install chromium
```

Run tests by type:

```bash
pytest -m web -v
pytest -m mobile -v
pytest -m backend -v
pytest -m smoke -v
```

Backend-specific options:

```bash
pytest -m backend --backend-env prod
pytest -m backend --backend-env stage
pytest -m backend --period-days 14
```

Run a single test file or test:

```bash
pytest tests/web/test_clubs_page.py -v
pytest tests/web/test_clubs_page.py::test_clubs_list_not_empty -v
```

Mobile-specific options:

```bash
pytest -m mobile --keepalive
pytest -m mobile --mobile-no-reset
pytest -m mobile --mobile-ui-logs
```

Preferred suite entrypoint:

```bash
python run_tests.py
```

Allure results are written to `allure-results/`. See `docs/allure/README.md`.

## Run-List Rules

Every new test file must be added to the corresponding run list:

- Mobile tests -> `tests_to_run_mobile.txt`
- Backend gate checks -> `tests_to_run_backend.txt`
- Backend monitoring checks -> `tests_to_run_backend_monitoring.txt`
- Web tests -> `tests_to_run_web.txt`

Run-list lines should use this structure:

```text
path/to/test.py | optional pytest args
```

Keep run lists clean, grouped by feature/domain where practical, and avoid
inventing custom formats for one test type.

## Configuration

Runtime configuration comes from `.env`; `.env.example` documents available
keys.

Important variables:

| Variable | Purpose |
|---|---|
| `WEB_BASE_URL` | Base URL for web tests, currently `https://invictus.kz` |
| `ENVIRONMENT` | `prod`, `staging`, or `development`; selects mobile app package/activity |
| `APPIUM_SERVER_URL` | Appium server URL, default `http://localhost:4723` |
| `MOBILE_DEVICE_NAME` | Android device or emulator name |

`src/config/app_config.py` reads `.env` and exposes typed constants.
`src/config/db_config.py` builds MongoDB URIs from individual env parts.

## Architecture

Use strict responsibility boundaries:

- Tests describe business scenarios and expected outcomes.
- Page objects contain locators, waits, UI actions, and screen validation.
- Helpers orchestrate reusable flows through page object methods.
- Fixtures manage environment, driver lifecycle, database access, and state setup.
- Repositories encapsulate database queries.
- Validators encapsulate reusable assertions and business checks.

Forbidden in helpers:

- Locators.
- Raw `driver.find_element`.
- Raw `page.locator`.
- `time.sleep`.
- Duplicated page object methods.

Create helpers only when logic is reused in two or more tests, or when it
combines multiple page object actions into an end-to-end flow.

## Page Object Rules

Page objects must validate that the page or screen is open before allowing
actions.

Validation should confirm required key elements and screen identity. Actions are
allowed only after successful validation.

Recommended navigation pattern:

```python
home = HomePage(driver).wait_loaded()
bookings = home.nav.open_bookings()
stats = bookings.nav.open_stats()
profile = stats.nav.open_profile()
home = profile.nav.open_main()
```

Page methods should perform one logical action and return the next page object
when navigation occurs.

## Mobile Architecture

`BaseMobilePage` mixes in `MobileInteractionMixin` from
`src/pages/mobile/base_content_block.py` for tap, swipe, and element-wait
helpers.

`BaseShellPage` exposes `.nav -> BottomNav`. Pages with a tab bar use shell page
navigation; full-screen flows such as auth, onboarding, bonuses, and
notifications do not.

`HomePage` detects state through `HomeState`:

- `NEW_USER`
- `SUBSCRIBED`
- `MEMBER`
- `UNKNOWN`

Content classes inherit from `BaseContentBlock`; they are sections inside a page,
not standalone pages.

Current mobile tests target the Client app mode. Coach mode shows a mode
selection screen and should get dedicated page objects and fixtures when needed.

## Mobile Page Recognition Rules

When adding or changing mobile page or screen recognition markers
(`DETECT_LOCATOR` / `DETECT_LOCATORS`), agents must not silently choose the first
visible text as the primary marker.

The agent must:

1. Inspect the current screen source, screenshot, or visible element list.
2. Offer two to four candidate recognition markers for review when practical.
3. Prefer stable markers in this order:
   accessibility id / `content-desc`, resource id / test id, exact visible text,
   then combined XPath/text conditions.
4. Explain which candidate is recommended and why.
5. Verify that the chosen marker is unique enough for screen detection:
   it is visible on the target screen or state and is not shared by competing
   screens, home states, bottom navigation, generic controls, or reusable cards.
6. Avoid using generic labels such as `Назад`, `Продолжить`, `Клубы`, prices,
   dates, user-specific values, or shared bottom-navigation text as the primary
   detection marker.
7. If no single marker is unique, use a small `DETECT_LOCATORS` combination and
   document why multiple markers are needed.

## Mobile State Management

The `potential_user_on_main_screen` fixture should ensure a clean authenticated
state before each test:

1. Restart the app.
2. Check the currently logged-in user role through profile and MongoDB.
3. If the wrong user is logged in or no user is logged in, run OTP auth through
   the shared auth helper using a `POTENTIAL_USER` candidate from MongoDB STAGE.

Onboarding depends on the `usermetadatas` collection:

- Users with a `usermetadatas` record skip onboarding after auth.
- Tests that must land on the main screen after OTP should use a `role=potential`
  user with a `usermetadatas` record and no records in `rabbitholev2`,
  `visits`, `usersubscriptions`, or `accesscontrols`. This is the mobile
  `new_user` data state; `users.role="potential"` alone is not enough.
- Tests that verify full onboarding should use a fresh phone/user without a
  `usermetadatas` record.

## Backend Test Rules

Backend tests must not define local `db` fixtures or hardcode `ENVIRONMENT` /
`ANALYSIS_DAYS` constants.

Use the centralized `db` fixture from `tests/backend/conftest.py`, controlled by
`--backend-env`.

Tests that analyze a time window must accept the `period_days` fixture and use it
instead of a hardcoded day count. The analysis period is automatically reported
in Allure via the `attach_test_period` autouse fixture.

Backend profiles:

- `backend_check` - gate checks that may fail the main run.
- `backend_monitoring` - operational monitoring and reports.
- `backend_research` - one-off analytical scenarios.

## Database Rules

When showing example database records in explanations or docs, use the freshest
relevant documents:

- Sort by a reliable timestamp field such as `createdAt`, `updatedAt`,
  `purchaseDate`, or `startDate`, descending.
- If no timestamp is available, sort by `_id` descending.
- Show the latest one to three documents and state the sort key used.

Database assertions should validate:

- Required fields.
- Types and formats.
- UI/backend consistency.
- Relationship integrity for ids and references.

Database helper and repository methods should encapsulate queries, return clear
typed structures where practical, and provide helpful errors.

## SQL Rules

For SQL work, follow the Cursor rule in `.cursor/rules/sqlmcppostgree.mdc`:

1. Inspect database schema before generating queries.
2. Never assume column names or foreign keys.
3. Validate joins and filters against the real schema.
4. Generate final SQL only after schema is known.

## Appium And Wait Strategy

- Avoid `time.sleep()` in tests and pages except as a last resort with a clear
  justification.
- Use centralized wait utilities for visibility, clickable state, presence, and
  stable screen state.
- Prefer accessibility ids and test ids.
- Avoid brittle XPath unless there is no better locator.

## Allure Reporting Rules

Allure reporting must be meaningful and consistent:

- Each test needs a clear descriptive title.
- Steps should reflect business logic, not only technical actions.
- Backend reports must include environment and analysis period.
- Reports must show how many records were processed, even when all passed.
- On failure, attach useful context: identifiers, expected vs actual values,
  query results, snapshots, and relevant records.
- When failures include historical records, highlight the latest erroneous record
  so it is clear whether the problem is still happening now.

Prefer compact output in Allure attachments and console logs:

- One line per entity with `|`-separated fields.
- Group by entity header when there are many records.
- Avoid verbose multi-line blocks per record.

For backend Allure details, see `docs/allure/backend_reporting_rules.md`.

## Test Execution Time

Test execution time must be logged automatically and consistently.

Duration should include setup, test steps, and teardown, and should be visible in
console output and CI logs.

Prefer framework-level solutions such as pytest hooks or fixtures instead of
manual timing inside test bodies.

## Web Tests

The site under test is `https://invictus.kz`, a Next.js site in Kazakh.

Page objects in `src/pages/web/` may use Playwright extended CSS selectors such
as `:has-text()` and `[href*=]`.

Cookie consent may appear on first load. Tests must handle it if it blocks
interaction.

## Documentation Rules

Main documentation lives under `docs/`.

Important entrypoints:

- `docs/qa/README.md`
- `docs/qa/platforms/backend.md`
- `docs/qa/platforms/backend-tests.md`
- `docs/qa/platforms/mobile.md`
- `docs/qa/platforms/web.md`
- `docs/qa/domain/webkassa.md`
- `docs/qa/legacy/legacy-docs-index.md`

Do not put mandatory agent rules only in ordinary docs unless they are linked
from this file or from an agent entrypoint.

## Definition Of Done

A change is done when:

- It is minimal and readable.
- It follows project boundaries.
- Tests or verification appropriate to the change have been run.
- New test files are added to run lists.
- Reports and docs are updated when behavior changes.
- Any inability to run verification is clearly stated.
