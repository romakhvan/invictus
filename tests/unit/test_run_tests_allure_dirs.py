import shutil
import uuid
from pathlib import Path

import run_tests


def test_run_tests_from_file_stores_fallback_allure_results_under_tmp(monkeypatch):
    workspace = (Path("tests/.tmp") / f"run-tests-{uuid.uuid4().hex}").resolve()
    workspace.mkdir(parents=True)

    try:
        test_list = workspace / "tests.txt"
        test_list.write_text("tests/unit/test_dummy.py\n", encoding="utf-8")

        repo_allure_dir = workspace / "allure-results"
        repo_allure_dir.mkdir()

        monkeypatch.chdir(workspace)
        fake_datetime = type(
            "FakeDateTime",
            (),
            {"now": staticmethod(lambda: type("Now", (), {
                "strftime": staticmethod(lambda _fmt: "20260420_180000")
            })())},
        )
        monkeypatch.setattr(run_tests, "datetime", fake_datetime)

        original_rmtree = run_tests.shutil.rmtree

        def fake_rmtree(path, *args, **kwargs):
            if Path(path) == Path("allure-results"):
                raise PermissionError("busy")
            return original_rmtree(path, *args, **kwargs)

        monkeypatch.setattr(run_tests.shutil, "rmtree", fake_rmtree)
        monkeypatch.setattr(run_tests.subprocess, "run", lambda *args, **kwargs: type("Result", (), {"returncode": 0})())

        result = run_tests.run_tests_from_file(
            file_path=test_list.name,
            generate_allure=True,
            open_report=False,
            mode="backend",
        )

        assert result == 0
        assert (workspace / "tmp" / "allure-results_20260420_180000").is_dir()
        assert (workspace / "allure-results_20260420_180000").exists() is False
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
