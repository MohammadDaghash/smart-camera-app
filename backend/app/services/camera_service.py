import platform
import time

import cv2

from app.config import CAMERA_INDEXES, READ_ATTEMPTS, RECONNECT_AFTER_FAILURES
from app.services.notification_service import notify_if_target_seen
from app.utils.logging import logger
from app.vision.face_recognition import annotate_faces


def create_camera(index):
    if platform.system() == "Darwin":
        return cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)

    return cv2.VideoCapture(index)


def release_camera(camera, index):
    if camera is not None:
        camera.release()
        logger.info("Released camera index %s", index)


def read_first_frame(camera, index):
    for attempt in range(1, READ_ATTEMPTS + 1):
        success, frame = camera.read()

        if success and frame is not None:
            logger.info("Read frame from camera index %s", index)
            return True

        logger.warning(
            "Camera index %s did not return a frame (attempt %s/%s)",
            index,
            attempt,
            READ_ATTEMPTS,
        )
        time.sleep(0.1)

    return False


def open_working_camera():
    for index in CAMERA_INDEXES:
        logger.info("Trying camera index %s", index)
        camera = create_camera(index)

        if not camera.isOpened():
            logger.warning("Camera index %s did not open", index)
            release_camera(camera, index)
            continue

        logger.info("Camera index %s opened", index)

        if read_first_frame(camera, index):
            logger.info("Using camera index %s", index)
            return camera, index, None

        logger.warning("Camera index %s opened but frames could not be read", index)
        release_camera(camera, index)

    error = "Could not open and read from camera indexes 0, 1, or 2"
    logger.error(error)
    return None, None, error


def generate_frames(camera, index):
    frame_count = 0
    failed_reads = 0
    last_face_count = None

    try:
        while True:
            success, frame = camera.read()

            if not success or frame is None:
                failed_reads += 1
                logger.warning(
                    "Frame read failed from camera index %s (%s/%s)",
                    index,
                    failed_reads,
                    RECONNECT_AFTER_FAILURES,
                )

                if failed_reads >= RECONNECT_AFTER_FAILURES:
                    release_camera(camera, index)
                    camera, index, error = open_working_camera()
                    failed_reads = 0

                    if camera is None:
                        logger.error("Could not reopen camera stream: %s", error)
                        break

                time.sleep(0.1)
                continue

            failed_reads = 0
            frame_count += 1

            if frame_count == 1 or frame_count % 120 == 0:
                logger.info("Streaming frame %s from camera index %s", frame_count, index)

            frame, face_count, face_labels, recognized = annotate_faces(frame)

            notify_if_target_seen(recognized)

            if face_count != last_face_count or (face_count > 0 and frame_count % 60 == 0):
                logger.info(
                    "Detected %s face(s) on frame %s: %s",
                    face_count,
                    frame_count,
                    ", ".join(face_labels) if face_labels else "none",
                )
                last_face_count = face_count

            success, encoded_frame = cv2.imencode(".jpg", frame)

            if not success:
                logger.warning("Frame encoding failed for camera index %s", index)
                continue

            frame_bytes = encoded_frame.tobytes()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
    finally:
        release_camera(camera, index)
