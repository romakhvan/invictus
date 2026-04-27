from datetime import datetime

from src.repositories.trainings import checks_repository


class _FakeCollection:
    def __init__(self, aggregate_docs):
        self.aggregate_docs = aggregate_docs
        self.aggregate_calls = []

    def aggregate(self, pipeline):
        self.aggregate_calls.append(pipeline)
        return self.aggregate_docs


def test_get_manual_count_update_infos_uses_update_count_changes_filter():
    changed_at = datetime(2026, 4, 13, 13, 18, 44)
    histories_col = _FakeCollection(
        [
            {
                "_id": "usp-1",
                "lastRecord": {
                    "_id": "history-1",
                    "created_at": changed_at,
                    "changes": [{"field": "count", "from": 10, "to": 9}],
                },
            }
        ]
    )
    db = {"userserviceproductshistories": histories_col}

    result = checks_repository.get_manual_count_update_infos(db, usp_ids=["usp-1"])

    assert result == {
        "usp-1": {
            "history_id": "history-1",
            "changed_at": changed_at,
            "change": "10 -> 9",
        }
    }
    assert histories_col.aggregate_calls[0][0] == {
        "$match": {
            "userServiceProduct": {"$in": ["usp-1"]},
            "type": "UPDATE",
            "changes.field": "count",
        }
    }
    assert histories_col.aggregate_calls[0][1:] == [
        {"$sort": {"created_at": -1}},
        {
            "$group": {
                "_id": "$userServiceProduct",
                "lastRecord": {"$first": "$$ROOT"},
            }
        },
    ]


def test_get_service_product_infos_projects_report_fields():
    serviceproducts_col = _FakeCollection(
        [
            {
                "_id": "service-product-1",
                "title": "Fitness Start",
                "type": "SPECIALIST",
                "trainingType": "trial",
            }
        ]
    )
    db = {"serviceproducts": serviceproducts_col}

    result = checks_repository.get_service_product_infos(db, service_product_ids=["service-product-1"])

    assert result == {
        "service-product-1": {
            "title": "Fitness Start",
            "type": "SPECIALIST",
            "trainingType": "trial",
        }
    }
    assert serviceproducts_col.aggregate_calls[0] == [
        {"$match": {"_id": {"$in": ["service-product-1"]}}},
        {"$project": {"_id": 1, "title": 1, "type": 1, "trainingType": 1}},
    ]
