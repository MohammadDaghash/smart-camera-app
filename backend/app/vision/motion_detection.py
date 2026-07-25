import cv2

from app.config import (
    MOTION_DETECTION_ENABLED,
    MOTION_MIN_AREA,
    MOTION_SCORE_THRESHOLD,
)


class MotionDetector:
    def __init__(
        self,
        enabled=MOTION_DETECTION_ENABLED,
        min_area=MOTION_MIN_AREA,
        score_threshold=MOTION_SCORE_THRESHOLD,
    ):
        self.enabled = enabled
        self.min_area = min_area
        self.score_threshold = score_threshold
        self.previous_gray = None

    def detect(self, frame):
        if not self.enabled:
            return self._result(False, 0.0, 0, [])

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.previous_gray is None:
            self.previous_gray = gray
            return self._result(False, 0.0, 0, [])

        frame_delta = cv2.absdiff(self.previous_gray, gray)
        _, threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)
        threshold = cv2.dilate(threshold, None, iterations=2)

        contours, _ = cv2.findContours(
            threshold,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        boxes = []
        motion_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < self.min_area:
                continue

            x, y, width, height = cv2.boundingRect(contour)
            boxes.append((x, y, width, height))
            motion_area += int(area)

        frame_area = frame.shape[0] * frame.shape[1]
        motion_score = motion_area / frame_area if frame_area else 0.0
        motion_detected = (
            motion_area >= self.min_area
            and motion_score >= self.score_threshold
        )

        self.previous_gray = gray

        return self._result(motion_detected, motion_score, motion_area, boxes)

    def _result(self, motion_detected, motion_score, motion_area, boxes):
        return {
            "motion_detected": motion_detected,
            "motion_score": motion_score,
            "motion_area": motion_area,
            "motion_boxes": boxes,
        }
