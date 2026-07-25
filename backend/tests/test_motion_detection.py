import numpy as np

from app.vision.motion_detection import MotionDetector


def test_motion_detector_needs_a_previous_frame():
    detector = MotionDetector(min_area=50, score_threshold=0.01)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    result = detector.detect(frame)

    assert result["motion_detected"] is False
    assert result["motion_score"] == 0.0
    assert result["motion_area"] == 0


def test_motion_detector_ignores_unchanged_frames():
    detector = MotionDetector(min_area=50, score_threshold=0.01)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    detector.detect(frame)
    result = detector.detect(frame.copy())

    assert result["motion_detected"] is False
    assert result["motion_area"] == 0


def test_motion_detector_detects_large_frame_changes():
    detector = MotionDetector(min_area=50, score_threshold=0.01)
    first_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    second_frame = first_frame.copy()
    second_frame[30:70, 30:70] = 255

    detector.detect(first_frame)
    result = detector.detect(second_frame)

    assert result["motion_detected"] is True
    assert result["motion_score"] > 0
    assert result["motion_area"] > 0
    assert result["motion_boxes"]


def test_motion_detector_can_be_disabled():
    detector = MotionDetector(enabled=False)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    result = detector.detect(frame)

    assert result["motion_detected"] is False
    assert result["motion_score"] == 0.0
    assert result["motion_area"] == 0
