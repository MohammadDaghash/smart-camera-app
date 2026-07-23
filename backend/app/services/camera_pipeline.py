import time

from app.config import RECONNECT_AFTER_FAILURES
from app.services.camera_source import open_working_camera, release_camera
from app.services.mjpeg_streamer import encode_mjpeg_frame
from app.utils.logging import logger
from app.vision.face_recognition import annotate_faces


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

            frame, face_count, face_labels = annotate_faces(frame)

            if face_count != last_face_count or (face_count > 0 and frame_count % 60 == 0):
                logger.info(
                    "Detected %s face(s) on frame %s: %s",
                    face_count,
                    frame_count,
                    ", ".join(face_labels) if face_labels else "none",
                )
                last_face_count = face_count

            mjpeg_frame = encode_mjpeg_frame(frame)

            if mjpeg_frame is None:
                logger.warning("Frame encoding failed for camera index %s", index)
                continue

            yield mjpeg_frame
    finally:
        release_camera(camera, index)
