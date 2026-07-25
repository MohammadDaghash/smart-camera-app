import pytest

from app.vision.label_smoothing import FaceLabelSmoother, box_iou


def annotation(box, label, score=0.8):
    return {
        "box": box,
        "label": label,
        "score": score,
    }


def test_box_iou_returns_overlap_ratio():
    assert box_iou((0, 0, 10, 10), (5, 5, 15, 15)) == pytest.approx(25 / 175)
    assert box_iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0


def test_smoother_keeps_previous_label_through_one_frame_flicker():
    smoother = FaceLabelSmoother(history_size=3, min_votes=2, iou_threshold=0.2)

    first = smoother.smooth(
        [annotation((0, 0, 100, 100), "Mohammad", score=0.91)],
        frame_index=1,
    )
    second = smoother.smooth(
        [annotation((2, 2, 102, 102), "Anonymous", score=0.38)],
        frame_index=2,
    )

    assert first[0]["label"] == "Mohammad"
    assert second[0]["label"] == "Mohammad"
    assert second[0]["raw_label"] == "Anonymous"
    assert second[0]["score"] == 0.91


def test_smoother_switches_label_after_repeated_votes():
    smoother = FaceLabelSmoother(history_size=3, min_votes=2, iou_threshold=0.2)

    smoother.smooth(
        [annotation((0, 0, 100, 100), "Mohammad", score=0.91)],
        frame_index=1,
    )
    second = smoother.smooth(
        [annotation((2, 2, 102, 102), "Anonymous", score=0.38)],
        frame_index=2,
    )
    third = smoother.smooth(
        [annotation((3, 3, 103, 103), "Anonymous", score=0.36)],
        frame_index=3,
    )

    assert second[0]["label"] == "Mohammad"
    assert third[0]["label"] == "Anonymous"
    assert third[0]["score"] == 0.36


def test_smoother_creates_new_track_when_face_location_changes():
    smoother = FaceLabelSmoother(history_size=3, min_votes=2, iou_threshold=0.2)

    first = smoother.smooth(
        [annotation((0, 0, 100, 100), "Mohammad")],
        frame_index=1,
    )
    second = smoother.smooth(
        [annotation((200, 200, 300, 300), "Anonymous", score=0.3)],
        frame_index=2,
    )

    assert first[0]["track_id"] != second[0]["track_id"]
    assert second[0]["label"] == "Anonymous"


def test_smoother_drops_old_tracks_after_ttl():
    smoother = FaceLabelSmoother(history_size=3, min_votes=2, ttl_frames=2)

    first = smoother.smooth(
        [annotation((0, 0, 100, 100), "Mohammad")],
        frame_index=1,
    )
    smoother.smooth([], frame_index=2)
    smoother.smooth([], frame_index=3)
    second = smoother.smooth(
        [annotation((0, 0, 100, 100), "Anonymous", score=0.3)],
        frame_index=4,
    )

    assert first[0]["track_id"] != second[0]["track_id"]
    assert second[0]["label"] == "Anonymous"
