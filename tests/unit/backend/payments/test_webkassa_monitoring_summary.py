from pathlib import Path


def test_webkassa_monitoring_source_does_not_contain_final_evaluation_step():
    source = Path("tests/backend/payments/test_webkassa_monitoring.py").read_text(encoding="utf-8")

    assert 'with allure.step("Итоговая оценка")' not in source
    assert 'name="❌ Нарушения порогов"' not in source
    assert "❌ WebKassa monitoring FAILED" not in source
