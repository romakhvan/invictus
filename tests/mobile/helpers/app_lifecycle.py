import time
from typing import Any

from src.config.app_config import MOBILE_APP_ACTIVITY, MOBILE_APP_PACKAGE


def _wait_for_package(
    driver: Any,
    package_name: str,
    *,
    timeout: float,
    poll_interval: float,
) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        if driver.current_package == package_name:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(poll_interval)


def ensure_mobile_app_in_foreground(
    driver: Any,
    *,
    package_name: str = MOBILE_APP_PACKAGE,
    activity_name: str = MOBILE_APP_ACTIVITY,
    timeout: float = 5.0,
    poll_interval: float = 0.5,
) -> None:
    """Bring the tested mobile app to foreground before a test starts."""
    current_package = driver.current_package
    if current_package == package_name:
        return

    print(
        f"⚠️ Приложение не в фокусе: текущий package={current_package}, "
        f"активируем {package_name}..."
    )
    driver.activate_app(package_name)
    if _wait_for_package(
        driver,
        package_name,
        timeout=timeout,
        poll_interval=poll_interval,
    ):
        return

    if hasattr(driver, "start_activity"):
        print(f"⚠️ activate_app не вывел приложение в foreground, пробуем start_activity {activity_name}...")
        driver.start_activity(package_name, activity_name)
        if _wait_for_package(
            driver,
            package_name,
            timeout=timeout,
            poll_interval=poll_interval,
        ):
            return

    raise AssertionError(
        f"Не удалось открыть приложение {package_name}; текущий package={driver.current_package}"
    )
