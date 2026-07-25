from collections import deque
import time
from threading import Lock

from app.config import FACE_ANALYSIS_INTERVAL_FRAMES, MOTION_DETECTION_ENABLED

FPS_WINDOW_SECONDS = 5.0


class PipelineStats:
    def __init__(
        self,
        face_analysis_interval_frames,
        motion_detection_enabled=True,
        fps_window_seconds=FPS_WINDOW_SECONDS,
    ):
        self.face_analysis_interval_frames = face_analysis_interval_frames
        self.motion_detection_enabled = motion_detection_enabled
        self.fps_window_seconds = fps_window_seconds
        self._lock = Lock()
        self.reset()

    def reset(self, now=None):
        reset_at = now if now is not None else time.time()

        with self._lock:
            self.started_at = reset_at
            self.active_streams = 0
            self.current_camera_index = None
            self.frames_read = 0
            self.frames_streamed = 0
            self.failed_reads = 0
            self.consecutive_failed_reads = 0
            self.reconnects = 0
            self.encoding_failures = 0
            self.analysis_frames = 0
            self.last_face_count = 0
            self.last_labels = []
            self.last_faces = []
            self.motion_frames = 0
            self.motion_events = 0
            self.motion_active = False
            self.last_motion_score = 0.0
            self.last_motion_area = 0
            self.last_frame_at = None
            self.last_analysis_at = None
            self.last_motion_at = None
            self.frame_read_times = deque()
            self.frame_streamed_times = deque()
            self.analysis_times = deque()
            self.motion_process_times = deque()

    def mark_stream_started(self, camera_index):
        with self._lock:
            self.active_streams += 1
            self.current_camera_index = camera_index

    def mark_stream_stopped(self):
        with self._lock:
            self.active_streams = max(0, self.active_streams - 1)

            if self.active_streams == 0:
                self.current_camera_index = None

    def record_frame_read(self, camera_index, now=None):
        recorded_at = now if now is not None else time.time()

        with self._lock:
            self.current_camera_index = camera_index
            self.frames_read += 1
            self.consecutive_failed_reads = 0
            self.last_frame_at = recorded_at
            self._record_timestamp(self.frame_read_times, recorded_at)

    def record_frame_streamed(self, now=None):
        recorded_at = now if now is not None else time.time()

        with self._lock:
            self.frames_streamed += 1
            self._record_timestamp(self.frame_streamed_times, recorded_at)

    def record_frame_read_failed(self, camera_index):
        with self._lock:
            self.current_camera_index = camera_index
            self.failed_reads += 1
            self.consecutive_failed_reads += 1

    def record_reconnect(self, camera_index):
        with self._lock:
            self.current_camera_index = camera_index
            self.reconnects += 1
            self.consecutive_failed_reads = 0

    def record_encoding_failure(self):
        with self._lock:
            self.encoding_failures += 1

    def record_analysis(self, face_count, labels, faces=None, now=None):
        recorded_at = now if now is not None else time.time()

        with self._lock:
            self.analysis_frames += 1
            self.last_face_count = face_count
            self.last_labels = list(labels)
            self.last_faces = [self._serialize_face(face) for face in faces or []]
            self.last_analysis_at = recorded_at
            self._record_timestamp(self.analysis_times, recorded_at)

    def record_motion(self, motion_detected, motion_score, motion_area, now=None):
        recorded_at = now if now is not None else time.time()

        with self._lock:
            was_motion_active = self.motion_active
            self.motion_frames += 1
            self.motion_active = motion_detected
            self.last_motion_score = motion_score
            self.last_motion_area = motion_area
            self._record_timestamp(self.motion_process_times, recorded_at)

            if motion_detected and not was_motion_active:
                self.motion_events += 1
                self.last_motion_at = recorded_at

    def snapshot(self, now=None):
        snapshot_at = now if now is not None else time.time()

        with self._lock:
            camera_fps = self._fps(self.frame_read_times, snapshot_at)
            stream_fps = self._fps(self.frame_streamed_times, snapshot_at)
            analysis_fps = self._fps(self.analysis_times, snapshot_at)
            motion_fps = self._fps(self.motion_process_times, snapshot_at)

            return {
                "camera": {
                    "active_streams": self.active_streams,
                    "current_camera_index": self.current_camera_index,
                    "frames_read": self.frames_read,
                    "frames_streamed": self.frames_streamed,
                    "failed_reads": self.failed_reads,
                    "consecutive_failed_reads": self.consecutive_failed_reads,
                    "reconnects": self.reconnects,
                    "encoding_failures": self.encoding_failures,
                },
                "analysis": {
                    "face_analysis_interval_frames": self.face_analysis_interval_frames,
                    "analysis_frames": self.analysis_frames,
                    "last_face_count": self.last_face_count,
                    "last_labels": list(self.last_labels),
                    "last_faces": [dict(face) for face in self.last_faces],
                },
                "motion": {
                    "enabled": self.motion_detection_enabled,
                    "motion_frames": self.motion_frames,
                    "motion_events": self.motion_events,
                    "motion_active": self.motion_active,
                    "last_motion_score": self.last_motion_score,
                    "last_motion_area": self.last_motion_area,
                },
                "performance": {
                    "fps_window_seconds": self.fps_window_seconds,
                    "camera_fps": camera_fps,
                    "stream_fps": stream_fps,
                    "analysis_fps": analysis_fps,
                    "motion_fps": motion_fps,
                    "skipped_analysis_fps": round(
                        max(0.0, camera_fps - analysis_fps),
                        2,
                    ),
                    "uptime_seconds": round(
                        max(0.0, snapshot_at - self.started_at),
                        2,
                    ),
                },
                "runtime": {
                    "last_frame_at": self.last_frame_at,
                    "last_analysis_at": self.last_analysis_at,
                    "last_motion_at": self.last_motion_at,
                },
            }

    def _record_timestamp(self, timestamps, recorded_at):
        timestamps.append(recorded_at)

        while (
            timestamps
            and recorded_at - timestamps[0] > self.fps_window_seconds
        ):
            timestamps.popleft()

    def _fps(self, timestamps, now):
        recent_count = sum(
            1
            for timestamp in timestamps
            if now - timestamp <= self.fps_window_seconds
        )

        return round(recent_count / self.fps_window_seconds, 2)

    def _serialize_face(self, face):
        box = face.get("box", ())

        return {
            "track_id": face.get("track_id"),
            "box": [int(value) for value in box],
            "label": str(face.get("label", "Anonymous")),
            "score": round(float(face.get("score", 0.0)), 4),
            "raw_label": str(face.get("raw_label", face.get("label", "Anonymous"))),
            "raw_score": round(
                float(face.get("raw_score", face.get("score", 0.0))),
                4,
            ),
        }


pipeline_stats = PipelineStats(
    face_analysis_interval_frames=FACE_ANALYSIS_INTERVAL_FRAMES,
    motion_detection_enabled=MOTION_DETECTION_ENABLED,
)
