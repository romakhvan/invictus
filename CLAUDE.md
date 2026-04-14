# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
pip install -r requirements.txt
playwright install chromium

# Run all tests by type
pytest -m web -v           # Web (Playwright)
pytest -m mobile -v        # Mobile (Appium)
pytest -m backend -v       # Backend (MongoDB)
pytest -m smoke -v         # Smoke only

# Backend-specific flags
pytest -m backend --backend-env prod   # MongoDB PROD (default)
pytest -m backend --backend-env stage  # MongoDB STAGE
pytest -m backend --period-days 14     # Analysis period in days (default: 7)

# Run a single test file
pytest tests/web/test_clubs_page.py -v

# Run a single test by name
pytest tests/web/test_clubs_page.py::test_clubs_list_not_empty -v

# Mobile-specific flags
pytest -m mobile --keepalive          # Keep app open after test for debugging
pytest -m mobile --mobile-no-reset    # Skip app data reset between tests
pytest -m mobile --mobile-ui-logs     # Verbose UI interaction logs (WAIT/CLICK/etc.)
```

**Preferred way to run mobile tests** — via `run_tests_mobile.py` and `tests_to_run_mobile.txt`:

```bash
python run_tests_mobile.py                  # Run tests listed in tests_to_run_mobile.txt
python run_tests_mobile.py -f other.txt     # Use a different list file
python run_tests_mobile.py --no-allure      # Skip Allure report generation
```

`tests_to_run_mobile.txt` format: each line is a relative pytest path (can include `|` followed by per-line pytest args, e.g. `-v -m mobile --mobile-no-reset`). Special directives: `ALLURE`, `OPEN_REPORT`, `INTERACTIVE`, `PYTEST_ARGS`. Do **not** run this file directly with Python — it is not a script.

```bash
# Examples from the file directly with pytest
pytest tests/mobile/bookings/test_bookings_entrypoints.py -v -m mobile --mobile-no-reset
pytest tests/mobile/bookings/test_bookings_entrypoints.py -v -m mobile --mobile-no-reset -k personal --keepalive
```

Allure results are written to `allure-results/` on every run (`--clean-alluredir` wipes them first).

**Rule: every new test file must be added to the corresponding run list:**
- Mobile tests → `tests_to_run_mobile.txt`
- Backend tests → `tests_to_run_backend.txt`

**Rule: backend tests must NOT define a local `db` fixture or hardcode `ENVIRONMENT`/`ANALYSIS_DAYS` constants.** Use the centralized `db` fixture from `tests/backend/conftest.py` (controlled by `--backend-env`). Tests that analyze a time window must accept the `period_days` fixture and use it instead of any hardcoded day count. The analysis period is automatically reported in Allure for every test via the `attach_test_period` autouse fixture.
- Web tests → `tests_to_run_web.txt`

## Configuration

All runtime config comes from `.env` (see `.env.example` for all keys). Key variables:

| Variable | Purpose |
|---|---|
| `WEB_BASE_URL` | Base URL for web tests (currently `https://invictus.kz`) |
| `ENVIRONMENT` | `prod` / `staging` / `development` — selects mobile app package/activity |
| `APPIUM_SERVER_URL` | Appium server (default `http://localhost:4723`) |
| `MOBILE_DEVICE_NAME` | Android device or emulator name |

`src/config/app_config.py` reads `.env` and exposes typed constants. `src/config/db_config.py` builds MongoDB URIs from individual env parts.

## Architecture

### Test layers

- **`tests/web/`** — Playwright tests. Each test receives a `web_page: Page` fixture (defined in `tests/conftest.py`). The browser starts non-headless (`headless=False`) — change in `tests/conftest.py` for CI.
- **`tests/mobile/`** — Appium tests. The `mobile_driver` fixture is defined in `tests/conftest.py`. Mobile tests use the STAGE MongoDB (overridden in `tests/mobile/conftest.py`).
- **`tests/backend/`** — Direct MongoDB validation tests. Environment is controlled by `--backend-env` (default: `prod`). Analysis period is controlled by `--period-days` (default: `7`). Both parameters are automatically added to every Allure report via the `attach_test_period` autouse fixture in `tests/backend/conftest.py`.
- **`tests/integration/`** — Combined UI + backend tests.

### Page Object hierarchy

```
BasePage (src/pages/base_page.py)
├── BaseWebPage (src/pages/web/base_web_page.py)       ← wraps playwright Page
│   └── HomePage / ClubsPage / AuthPage / ...
└── BaseMobilePage (src/pages/mobile/base_mobile_page.py) ← wraps Appium Remote
    ├── BaseShellPage (src/pages/mobile/shell/base_shell_page.py)
    │   └── Pages WITH tabbar: HomePage, BookingsPage, StatsPage, ProfilePage
    └── Pages WITHOUT tabbar: auth, onboarding, bonuses, notifications, fullscreen flows
```

`BaseWebPage` exposes `click(selector)`, `fill(selector, value)`, `get_text(selector)`, `is_visible(selector)`, `navigate_to(url)`, `get_current_url()`. Use `self.page` for raw Playwright access.

`BaseMobilePage` mixes in `MobileInteractionMixin` (from `src/pages/mobile/base_content_block.py`) for tap, swipe, and element-wait helpers. Use `self.driver` for raw Appium access.

### Mobile shell + tabbar architecture

`BaseShellPage` exposes `.nav → BottomNav`. Each `BottomNav` method clicks a tab, waits for load, and returns the target Page Object. Navigation in tests:

```python
home = HomePage(driver).wait_loaded()
bookings = home.nav.open_bookings()
stats = bookings.nav.open_stats()
profile = stats.nav.open_profile()
home = profile.nav.open_main()
```

Every page validates key elements (`DETECT_LOCATOR` / `assert_ui`) on open — actions are only allowed after successful validation.

### Mobile home page: state-based content

`HomePage` is a shell that detects which content to show via `HomeState` enum (`NEW_USER`, `SUBSCRIBED`, `MEMBER`, `UNKNOWN`). Content classes (`HomeNewUserContent`, `HomeSubscribedContent`, `HomeMemberContent`) inherit from `BaseContentBlock` (not a page — a section inside a page). Each has a `DETECT_LOCATOR` used for state detection.

```python
home = HomePage(driver).wait_loaded()
state = home.get_current_home_state()   # → HomeState.NEW_USER / SUBSCRIBED / MEMBER
content = home.get_content()            # → HomeNewUserContent / ...
```

### Mobile app modes: Client / Coach

The app has two modes based on user role:
- **Client app** — default for all users, all current tests target this mode.
- **Coach app** — only for users with coach role; at launch shows a **mode-selection screen** before entering the app.

Current test users (`role: potential`) have no coach access, so the mode-selection screen is never shown and the flow is: launch → Preview → auth → main (Client). When Coach app tests are needed: add `AppModeSelectionPage` (in `auth/` or `shell/`), add a mode-selection step to Client fixtures, and create Coach-specific fixtures and pages under `pages/mobile/coach/` + tests under `tests/mobile/coach/`.

### Mobile test state management

The `potential_user_on_main_screen` fixture (defined in `tests/mobile/conftest.py`) ensures a clean authenticated state before each test:
1. Restarts the app.
2. Checks the currently logged-in user's role via profile screen → MongoDB lookup.
3. If wrong user or not logged in, calls `run_auth_to_main()` (OTP auth helper) using a `role=potential` user from MongoDB STAGE.

`tests/mobile/helpers/` contains reusable flows: `auth_helpers.py`, `onboarding_helpers.py`, `session_helpers.py`, `profile_helpers.py`.

**Boundary rules for `helpers/` vs Page Objects:**
- **Page Objects** — all locators, waits, UI actions, page validation (`wait_loaded`). Single source of truth for every UI step.
- **Helpers** — orchestration only: chain Page Object methods into end-to-end flows. No locators, no `driver.find_element`, no `time.sleep`.
- **Fixtures** — environment/state setup (driver, db, user preconditions).

Forbidden in helpers: duplicating page methods, storing XPath/CSS/Appium locators, implementing waits that belong in the page layer, using `time.sleep` instead of page-level waits.

### Repositories (`src/repositories/`)

MongoDB access objects, one per collection: `users_repository.py`, `subscriptions_repository.py`, `notifications_repository.py`, etc. Used directly in backend tests and in mobile fixture setup (e.g. `get_phone_for_potential_user(db)`).

### Mobile environments

`ENVIRONMENT` in `.env` controls the app package used in Appium capabilities:
- `prod` → `kz.fitnesslabs.invictus`
- `staging` → `kz.fitnesslabs.invictus.staging`
- `development` → `kz.fitnesslabs.invictus.development`

### Web site under test

`https://invictus.kz` — Next.js site in Kazakh language. Page Objects in `src/pages/web/` use Playwright's extended CSS selectors (`:has-text()`, `[href*=]`). Cookie consent dialog appears on first load — tests must account for it or dismiss it if it blocks interaction.

## Test Design Guidelines

### ✅ Required

**Allure reporting must be meaningful and consistent**
- Each test must have a clear and descriptive title
- Steps should reflect business logic, not just technical actions
- Backend tests must automatically include: environment (`--backend-env`) and analysis period (`period_days`)
- On failure, attach key debugging data: identifiers (e.g. `user_id`, `transaction_id`), expected vs actual values, query results or snapshots where applicable

**Run-list consistency across test types**
- Every test file must be added to its corresponding run-list
- Run-list format must be consistent across: mobile (`tests_to_run_mobile.txt`), backend (`tests_to_run_backend.txt`), web (`tests_to_run_web.txt`)
- Each line must follow the same structure: `path/to/test.py | optional pytest args`

**Clear separation of responsibilities**
- Page Objects → UI logic, locators, waits, validations
- Helpers → orchestration only (no locators, no raw driver/page usage)
- Fixtures → environment and state setup

**Helper usage rule**
- Create a helper only if: logic is reused in 2+ tests, or it combines multiple Page Object actions into a flow
- Do NOT create helpers for single-step or page-specific actions

### ❌ Forbidden

**Poor or missing Allure structure**
- No vague or generic test titles
- No "technical-only" steps without business meaning
- No silent failures without attached context

**Inconsistent or manual test execution**
- Do not run tests outside of run-list when they are meant to be part of a suite
- Do not create custom run formats per test type

**Violating architecture boundaries**
- No locators inside helpers
- No `driver.find_element` / `page.locator` in helpers or tests (if it belongs in Page Object)
- No duplication of Page Object methods inside helpers

**Misuse of helpers**
- Do not create helpers for: single actions, one-time logic, logic tightly coupled to a single test

### 💡 Recommended

**Allure best practices**
- Group steps logically (e.g. "Open bookings screen", "Validate subscription state")
- Keep reports readable for non-developers (QA, product, analysts)
- Attach only meaningful data (avoid noise)
- Prefer compact output format in both Allure attachments and console `print()`: one line per entity with `|`-separated fields (e.g. `- 2025-01-01 12:00:00 | trans_id | 5 000 тг | ошибка`), grouped by entity header (`Club X (N)`). Avoid verbose multi-line blocks per record — they hurt readability when there are many items.

**Run-list scalability**
- Keep run-lists clean and structured (group by feature/domain)
- Use per-line pytest flags when needed instead of duplicating files

**Helper design clarity**
- Think of helpers as user flows, not technical shortcuts
- Name helpers by intent: `run_auth_to_main()`, `complete_onboarding_flow()`
- Keep helpers thin — orchestration only

**Consistency over flexibility**
- Prefer predictable structure over "smart" or complex abstractions
- If unsure — keep logic in Page Object instead of helper
