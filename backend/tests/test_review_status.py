import pytest

from app.services.review_status import ReviewStatusStore


def test_review_status_defaults_to_new():
    store = ReviewStatusStore(database_path=":memory:")

    items = store.apply_statuses([{"id": "review-1-2", "summary": "Test"}])

    assert items[0]["review_status"] == "new"
    assert items[0]["review_status_updated_at"] is None


def test_review_status_can_be_saved_and_reloaded(tmp_path):
    database_path = tmp_path / "review_status.db"
    store = ReviewStatusStore(database_path=database_path)

    saved = store.set_status("review-1-2", "reviewed", now=100.0)

    assert saved == {
        "review_id": "review-1-2",
        "status": "reviewed",
        "updated_at": 100.0,
    }

    reloaded_store = ReviewStatusStore(database_path=database_path)
    statuses = reloaded_store.get_statuses(["review-1-2"])

    assert statuses["review-1-2"] == {
        "status": "reviewed",
        "updated_at": 100.0,
    }


def test_review_status_rejects_unknown_status():
    store = ReviewStatusStore(database_path=":memory:")

    with pytest.raises(ValueError):
        store.set_status("review-1-2", "ignored")


def test_review_status_normalizes_common_status_format():
    store = ReviewStatusStore(database_path=":memory:")

    saved = store.set_status("review-1-2", "False Positive", now=100.0)

    assert saved["status"] == "false_positive"


def test_review_status_applies_saved_status_to_matching_items():
    store = ReviewStatusStore(database_path=":memory:")
    store.set_status("review-1-2", "false_positive", now=123.0)

    items = store.apply_statuses(
        [
            {"id": "review-1-2", "summary": "Known item"},
            {"id": "review-3-4", "summary": "New item"},
        ]
    )

    assert items[0]["review_status"] == "false_positive"
    assert items[0]["review_status_updated_at"] == 123.0
    assert items[1]["review_status"] == "new"
    assert items[1]["review_status_updated_at"] is None
