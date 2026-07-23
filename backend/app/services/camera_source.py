import platform
import time

import cv2

from app.config import CAMERA_INDEXES, READ_ATTEMPTS
from app.utils.logging import logger


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

    tested_indexes = ", ".join(str(index) for index in CAMERA_INDEXES)
    error = f"Could not open and read from camera indexes {tested_indexes}"
    logger.error(error)
    return None, None, error
