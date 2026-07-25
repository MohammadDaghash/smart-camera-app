from app.services import recognition_debug


def test_recognition_reason_explains_known_match():
    reason = recognition_debug.recognition_reason(
        {
            "label": "Mohammad",
            "raw_label": "Mohammad",
            "raw_score": 0.72,
        }
    )

    assert "reached threshold" in reason
    assert "0.72" in reason


def test_recognition_reason_explains_anonymous_match():
    reason = recognition_debug.recognition_reason(
        {
            "label": "Anonymous",
            "raw_label": "Anonymous",
            "raw_score": 0.32,
        }
    )

    assert "No known-face match reached threshold" in reason
    assert "0.32" in reason


def test_recognition_reason_explains_smoothed_label():
    reason = recognition_debug.recognition_reason(
        {
            "label": "Mohammad",
            "raw_label": "Anonymous",
            "raw_score": 0.36,
        }
    )

    assert "held by smoothing" in reason
    assert "Raw frame label was Anonymous" in reason
