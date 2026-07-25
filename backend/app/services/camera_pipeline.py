import time

from app.config import FACE_ANALYSIS_INTERVAL_FRAMES, RECONNECT_AFTER_FAILURES
from app.services.camera_source import open_working_camera, release_camera
from app.services.event_log import event_log
from app.services.frame_cadence import should_process_frame
from app.services.mjpeg_streamer import encode_mjpeg_frame
from app.services.pipeline_stats import pipeline_stats
from app.utils.logging import logger
from app.vision.face_recognition import (
    build_face_annotations,
    draw_face_annotations,
    labels_from_annotations,
)
from app.vision.motion_detection import MotionDetector


def generate_frames(camera, index):
    frame_count = 0
    failed_reads = 0
    last_face_count = None
    last_motion_detected = False
    last_face_labels = set()
    latest_face_annotations = []
    motion_detector = MotionDetector()
    pipeline_stats.mark_stream_started(index)

    try:
        while True:
            success, frame = camera.read()

            if not success or frame is None:
                failed_reads += 1
                pipeline_stats.record_frame_read_failed(index)
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

                    pipeline_stats.record_reconnect(index)

                time.sleep(0.1)
                continue

            failed_reads = 0
            frame_count += 1
            pipeline_stats.record_frame_read(index)

            if frame_count == 1 or frame_count % 120 == 0:
                logger.info("Streaming frame %s from camera index %s", frame_count, index)

            motion = motion_detector.detect(frame)
            pipeline_stats.record_motion(
                motion_detected=motion["motion_detected"],
                motion_score=motion["motion_score"],
                motion_area=motion["motion_area"],
            )

            if motion["motion_detected"] and (
                not last_motion_detected or frame_count % 120 == 0
            ):
                logger.info(
                    "Motion detected on frame %s: score %.4f, area %s",
                    frame_count,
                    motion["motion_score"],
                    motion["motion_area"],
                )

            if motion["motion_detected"] and not last_motion_detected:
                event_log.add_event(
                    event_type="motion",
                    message="Motion detected",
                    metadata={
                        "score": round(motion["motion_score"], 4),
                        "area": motion["motion_area"],
                    },
                )

            last_motion_detected = motion["motion_detected"]

            if should_process_frame(frame_count, FACE_ANALYSIS_INTERVAL_FRAMES):
                latest_face_annotations = build_face_annotations(frame)
                face_count = len(latest_face_annotations)
                face_labels = labels_from_annotations(latest_face_annotations)
                current_face_labels = {
                    annotation["label"]
                    for annotation in latest_face_annotations
                }
                pipeline_stats.record_analysis(face_count, face_labels)

                for label in sorted(current_face_labels - last_face_labels):
                    event_log.add_event(
                        event_type="face",
                        message=f"{label} detected",
                        metadata={"label": label},
                    )

                last_face_labels = current_face_labels

                if face_count != last_face_count or (face_count > 0 and frame_count % 60 == 0):
                    logger.info(
                        "Detected %s face(s) on frame %s: %s",
                        face_count,
                        frame_count,
                        ", ".join(face_labels) if face_labels else "none",
                    )
                    last_face_count = face_count

            frame = draw_face_annotations(frame, latest_face_annotations)

            mjpeg_frame = encode_mjpeg_frame(frame)

            if mjpeg_frame is None:
                pipeline_stats.record_encoding_failure()
                logger.warning("Frame encoding failed for camera index %s", index)
                continue

            pipeline_stats.record_frame_streamed()
            yield mjpeg_frame
    finally:
        pipeline_stats.mark_stream_stopped()
        release_camera(camera, index)
