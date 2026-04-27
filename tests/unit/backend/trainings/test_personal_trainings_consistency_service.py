from datetime import datetime

from bson import ObjectId

import src.services.backend_checks.trainings_checks_service as service


def test_manual_count_update_failures_are_split_from_regular_failures(monkeypatch):
    manual_usp_id = ObjectId("69dcec8b65abe3bb5e274267")
    regular_usp_id = ObjectId("69a51aa0245025ac661ad3b8")

    monkeypatch.setattr(
        service,
        "get_personal_training_usps",
        lambda *args, **kwargs: [
            {
                "_id": manual_usp_id,
                "user": ObjectId("661940bf07d20702e26509d7"),
                "serviceProduct": "service-product-1",
                "initialCount": 10,
                "count": 9,
                "created_at": datetime(2026, 4, 1, 10, 0, 0),
                "updated_at": datetime(2026, 4, 13, 13, 18, 44),
            },
            {
                "_id": regular_usp_id,
                "user": ObjectId("661940bf07d20702e26509d8"),
                "serviceProduct": "service-product-1",
                "initialCount": 12,
                "count": -1,
                "created_at": datetime(2026, 3, 2, 5, 5, 39),
                "updated_at": datetime(2026, 4, 23, 16, 45, 44),
            },
        ],
    )
    monkeypatch.setattr(service, "get_training_tickets_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(service, "get_latest_history_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(service, "get_training_sessions_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(service, "get_cancel_not_restored_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        service,
        "get_service_product_infos",
        lambda *args, **kwargs: {
            "service-product-1": {
                "title": "Fitness Start",
                "type": "SPECIALIST",
                "trainingType": "trial",
            }
        },
    )
    monkeypatch.setattr(
        service,
        "get_manual_count_update_infos",
        lambda *args, **kwargs: {
            manual_usp_id: {
                "history_id": ObjectId("69dced34747b785a86b1b0a2"),
                "changed_at": datetime(2026, 4, 13, 13, 18, 44),
                "change": "10 -> 9",
            }
        },
    )

    result = service.run_personal_trainings_consistency_check(db=object())

    assert result.failed_count == 2
    assert [record.usp_id for record in result.regular_failed_records] == [str(regular_usp_id)]
    assert [record.usp_id for record in result.manual_update_failed_records] == [str(manual_usp_id)]
    assert result.manual_update_failed_records[0].manual_count_update_id == "69dced34747b785a86b1b0a2"
    assert result.manual_update_failed_records[0].manual_count_change == "10 -> 9"


def test_service_product_fields_are_added_to_records(monkeypatch):
    usp_id = ObjectId("69dcec8b65abe3bb5e274267")
    service_product_id = ObjectId("68e5e92e3ea673017e768c4b")

    monkeypatch.setattr(
        service,
        "get_personal_training_usps",
        lambda *args, **kwargs: [
            {
                "_id": usp_id,
                "user": ObjectId("661940bf07d20702e26509d7"),
                "serviceProduct": service_product_id,
                "initialCount": 10,
                "count": 10,
            }
        ],
    )
    monkeypatch.setattr(service, "get_training_tickets_counts", lambda *args, **kwargs: {usp_id: 10})
    monkeypatch.setattr(service, "get_latest_history_counts", lambda *args, **kwargs: {usp_id: 10})
    monkeypatch.setattr(service, "get_training_sessions_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(service, "get_cancel_not_restored_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(service, "get_manual_count_update_infos", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        service,
        "get_service_product_infos",
        lambda *args, **kwargs: {
            service_product_id: {
                "title": "Fitness Start",
                "type": "SPECIALIST",
                "trainingType": "trial",
            }
        },
    )

    result = service.run_personal_trainings_consistency_check(db=object())

    assert result.records[0].service_product_title == "Fitness Start"
    assert result.records[0].service_product_type == "SPECIALIST"
    assert result.records[0].service_product_training_type == "trial"


def test_inbody_service_products_are_excluded_from_records(monkeypatch):
    inbody_usp_id = ObjectId("69dcec8b65abe3bb5e274267")
    regular_usp_id = ObjectId("69a51aa0245025ac661ad3b8")
    inbody_service_product_id = ObjectId("68e5e92e3ea673017e768c4b")
    regular_service_product_id = ObjectId("68e5e92e3ea673017e768c4c")
    ticket_queries = []

    monkeypatch.setattr(
        service,
        "get_personal_training_usps",
        lambda *args, **kwargs: [
            {
                "_id": inbody_usp_id,
                "user": ObjectId("661940bf07d20702e26509d7"),
                "serviceProduct": inbody_service_product_id,
                "initialCount": 1,
                "count": 1,
            },
            {
                "_id": regular_usp_id,
                "user": ObjectId("661940bf07d20702e26509d8"),
                "serviceProduct": regular_service_product_id,
                "initialCount": 1,
                "count": 1,
            },
        ],
    )
    monkeypatch.setattr(
        service,
        "get_service_product_infos",
        lambda *args, **kwargs: {
            inbody_service_product_id: {
                "title": "InBody диагностика",
                "type": "SPECIALIST",
                "trainingType": "pt",
            },
            regular_service_product_id: {
                "title": "Personal training",
                "type": "SPECIALIST",
                "trainingType": "pt",
            },
        },
    )

    def fake_tickets_counts(_db, usp_ids):
        ticket_queries.append(usp_ids)
        return {regular_usp_id: 1}

    monkeypatch.setattr(service, "get_training_tickets_counts", fake_tickets_counts)
    monkeypatch.setattr(service, "get_latest_history_counts", lambda *args, **kwargs: {regular_usp_id: 1})
    monkeypatch.setattr(service, "get_training_sessions_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(service, "get_cancel_not_restored_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(service, "get_manual_count_update_infos", lambda *args, **kwargs: {})

    result = service.run_personal_trainings_consistency_check(db=object())

    assert [record.usp_id for record in result.records] == [str(regular_usp_id)]
    assert ticket_queries == [[regular_usp_id]]


def test_only_tickets_mismatch_is_recorded_when_active_tickets_differ_from_count(monkeypatch):
    usp_id = ObjectId("6998819c73725cfb87abf3ff")
    service_product_id = ObjectId("67b5a25daa763400ffff9e4c")

    monkeypatch.setattr(
        service,
        "get_personal_training_usps",
        lambda *args, **kwargs: [
            {
                "_id": usp_id,
                "user": ObjectId("69494f41228a4a39efe73774"),
                "serviceProduct": service_product_id,
                "initialCount": 10,
                "count": 3,
            }
        ],
    )
    monkeypatch.setattr(service, "get_service_product_infos", lambda *args, **kwargs: {
        service_product_id: {"title": "TRIO product", "type": "SPECIALIST", "trainingType": "trio"}
    })
    monkeypatch.setattr(service, "get_training_tickets_counts", lambda *args, **kwargs: {usp_id: 4})
    monkeypatch.setattr(service, "get_latest_history_counts", lambda *args, **kwargs: {usp_id: 3})
    monkeypatch.setattr(service, "get_training_sessions_counts", lambda *args, **kwargs: {usp_id: 7})
    monkeypatch.setattr(service, "get_cancel_not_restored_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(service, "get_manual_count_update_infos", lambda *args, **kwargs: {})

    result = service.run_personal_trainings_consistency_check(db=object())
    record = result.records[0]

    assert record.status == "FAIL"
    assert record.tickets_mismatch is True
    assert record.tickets_mismatch_expected == "count=3"
    assert record.tickets_mismatch_actual == "activeTickets=4"
    assert record.history_count_mismatch is False
    assert record.tickets_history_mismatch is False
    assert record.sessions_usage_mismatch is False
    assert [violation.rule_id for violation in record.rule_violations] == ["tickets_mismatch"]


def test_multiple_rule_violations_are_recorded_for_one_usp(monkeypatch):
    usp_id = ObjectId("6998819c73725cfb87abf3ff")
    service_product_id = ObjectId("67b5a25daa763400ffff9e4c")

    monkeypatch.setattr(
        service,
        "get_personal_training_usps",
        lambda *args, **kwargs: [
            {
                "_id": usp_id,
                "user": ObjectId("69494f41228a4a39efe73774"),
                "serviceProduct": service_product_id,
                "initialCount": 10,
                "count": 3,
            }
        ],
    )
    monkeypatch.setattr(service, "get_service_product_infos", lambda *args, **kwargs: {
        service_product_id: {"title": "TRIO product", "type": "SPECIALIST", "trainingType": "trio"}
    })
    monkeypatch.setattr(service, "get_training_tickets_counts", lambda *args, **kwargs: {usp_id: 4})
    monkeypatch.setattr(service, "get_latest_history_counts", lambda *args, **kwargs: {usp_id: 2})
    monkeypatch.setattr(service, "get_training_sessions_counts", lambda *args, **kwargs: {usp_id: 6})
    monkeypatch.setattr(service, "get_cancel_not_restored_counts", lambda *args, **kwargs: {})
    monkeypatch.setattr(service, "get_manual_count_update_infos", lambda *args, **kwargs: {})

    result = service.run_personal_trainings_consistency_check(db=object())
    record = result.records[0]

    assert [violation.rule_id for violation in record.rule_violations] == [
        "tickets_mismatch",
        "history_count_mismatch",
        "tickets_history_mismatch",
        "sessions_usage_mismatch",
    ]
    assert record.history_count_mismatch_expected == "count=3"
    assert record.history_count_mismatch_actual == "hist=2"
    assert record.tickets_history_mismatch_expected == "tickets=4"
    assert record.tickets_history_mismatch_actual == "hist=2"
    assert record.sessions_usage_mismatch_expected == "initial-count=10-3"
    assert record.sessions_usage_mismatch_actual == "sessions+cancel=6+0"
