from src.pages.mobile.common.payment_confirmation_page import PaymentConfirmationPage


def test_select_payment_method_opens_current_method_and_selects_requested_method(monkeypatch):
    page = object.__new__(PaymentConfirmationPage)
    calls = []

    monkeypatch.setattr(
        PaymentConfirmationPage,
        "assert_any_payment_method_visible",
        lambda self: calls.append(("assert_any", None)) or "Текущая карта",
    )
    monkeypatch.setattr(
        PaymentConfirmationPage,
        "click",
        lambda self, locator: calls.append(("click", locator)),
    )
    monkeypatch.setattr(
        PaymentConfirmationPage,
        "assert_payment_method_visible",
        lambda self, method_name: calls.append(("assert_selected", method_name)),
    )

    page.select_payment_method("Kaspi Pay")

    assert calls == [
        ("assert_any", None),
        ("click", PaymentConfirmationPage.payment_method_locator("Текущая карта")),
        ("click", PaymentConfirmationPage.payment_method_locator("Kaspi Pay")),
        ("assert_selected", "Kaspi Pay"),
    ]
