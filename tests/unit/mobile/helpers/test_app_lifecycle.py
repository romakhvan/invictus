import pytest

from tests.mobile.helpers.app_lifecycle import ensure_mobile_app_in_foreground


class _FakeDriver:
    def __init__(self, packages):
        self._packages = list(packages)
        self.activate_calls = []
        self.start_activity_calls = []

    @property
    def current_package(self):
        if len(self._packages) > 1:
            return self._packages.pop(0)
        return self._packages[0]

    def activate_app(self, package_name):
        self.activate_calls.append(package_name)

    def start_activity(self, package_name, activity_name):
        self.start_activity_calls.append((package_name, activity_name))


def test_ensure_mobile_app_in_foreground_does_nothing_when_app_is_active():
    driver = _FakeDriver(["kz.fitnesslabs.invictus.staging"])

    ensure_mobile_app_in_foreground(
        driver,
        package_name="kz.fitnesslabs.invictus.staging",
        activity_name=".MainActivity",
        timeout=0,
    )

    assert driver.activate_calls == []
    assert driver.start_activity_calls == []


def test_ensure_mobile_app_in_foreground_activates_app_from_launcher():
    driver = _FakeDriver(
        [
            "com.sec.android.app.launcher",
            "kz.fitnesslabs.invictus.staging",
        ]
    )

    ensure_mobile_app_in_foreground(
        driver,
        package_name="kz.fitnesslabs.invictus.staging",
        activity_name=".MainActivity",
        timeout=0,
    )

    assert driver.activate_calls == ["kz.fitnesslabs.invictus.staging"]
    assert driver.start_activity_calls == []


def test_ensure_mobile_app_in_foreground_falls_back_to_start_activity():
    driver = _FakeDriver(
        [
            "com.sec.android.app.launcher",
            "com.sec.android.app.launcher",
            "kz.fitnesslabs.invictus.staging",
        ]
    )

    ensure_mobile_app_in_foreground(
        driver,
        package_name="kz.fitnesslabs.invictus.staging",
        activity_name=".MainActivity",
        timeout=0,
    )

    assert driver.activate_calls == ["kz.fitnesslabs.invictus.staging"]
    assert driver.start_activity_calls == [
        ("kz.fitnesslabs.invictus.staging", ".MainActivity")
    ]


def test_ensure_mobile_app_in_foreground_raises_when_app_stays_backgrounded():
    driver = _FakeDriver(
        [
            "com.sec.android.app.launcher",
            "com.sec.android.app.launcher",
            "com.sec.android.app.launcher",
        ]
    )

    with pytest.raises(AssertionError, match="com.sec.android.app.launcher"):
        ensure_mobile_app_in_foreground(
            driver,
            package_name="kz.fitnesslabs.invictus.staging",
            activity_name=".MainActivity",
            timeout=0,
        )
