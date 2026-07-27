from app.services.recognition_metrics import (
    RecognitionMetricsStore,
    summarize_observations,
)


def annotation(label, score, raw_label=None, raw_score=None, track_id=1):
    return {
        "track_id": track_id,
        "label": label,
        "score": score,
        "raw_label": raw_label or label,
        "raw_score": raw_score if raw_score is not None else score,
    }


def test_recognition_metrics_stores_observations():
    store = RecognitionMetricsStore(
        database_path=":memory:",
        sample_interval_seconds=0,
    )

    saved = store.add_observations(
        [annotation("Mohammad", 0.82)],
        now=100.0,
    )

    assert saved[0]["label"] == "Mohammad"
    assert saved[0]["created_at"] == 100.0
    assert store.latest()[0]["raw_score"] == 0.82


def test_recognition_metrics_respects_sample_interval():
    store = RecognitionMetricsStore(
        database_path=":memory:",
        sample_interval_seconds=1.0,
    )

    store.add_observations([annotation("Mohammad", 0.82)], now=100.0)
    skipped = store.add_observations([annotation("Mohammad", 0.83)], now=100.5)
    store.add_observations([annotation("Mohammad", 0.84)], now=101.0)

    assert skipped == []
    assert [item["raw_score"] for item in reversed(store.latest())] == [0.82, 0.84]


def test_recognition_metrics_prunes_old_observations():
    store = RecognitionMetricsStore(
        database_path=":memory:",
        max_observations=2,
        sample_interval_seconds=0,
    )

    store.add_observations([annotation("Mohammad", 0.80)], now=100.0)
    store.add_observations([annotation("Omar", 0.81)], now=101.0)
    store.add_observations([annotation("Anonymous", 0.30)], now=102.0)

    latest = store.latest(limit=10)

    assert len(latest) == 2
    assert [item["label"] for item in latest] == ["Anonymous", "Omar"]


def test_recognition_metrics_filters_by_label():
    store = RecognitionMetricsStore(
        database_path=":memory:",
        sample_interval_seconds=0,
    )

    store.add_observations([annotation("Mohammad", 0.82)], now=100.0)
    store.add_observations([annotation("Omar", 0.78)], now=101.0)

    results = store.latest(label="moh")

    assert len(results) == 1
    assert results[0]["label"] == "Mohammad"


def test_recognition_metrics_summary_counts_threshold_cases():
    summary = summarize_observations(
        [
            {
                "created_at": 100.0,
                "label": "Mohammad",
                "score": 0.51,
                "raw_label": "Mohammad",
                "raw_score": 0.51,
            },
            {
                "created_at": 101.0,
                "label": "Anonymous",
                "score": 0.43,
                "raw_label": "Anonymous",
                "raw_score": 0.43,
            },
        ],
        threshold=0.45,
    )

    assert summary["total_observations"] == 2
    assert summary["known_observations"] == 1
    assert summary["anonymous_observations"] == 1
    assert summary["near_threshold_observations"] == 1
    assert summary["per_label"][0]["label"] == "Anonymous"
