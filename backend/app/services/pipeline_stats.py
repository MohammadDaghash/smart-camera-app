import time
from threading import Lock

from app.config import FACE_ANALYSIS_INTERVAL_FRAMES, MOTION_DETECTION_ENABLED


class PipelineStats:
    def __init__(self, face_analysis_interval_frames, motion_detection_enabled=True):
        self.face_analysis_interval_frames = face_analysis_interval_frames
        self.motion_detection_enabled = motion_detection_enabled
        self._lock = Lock()
        self.reset()

    def reset(self):
        with self._lock:
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
        with self._lock:
            self.current_camera_index = camera_index
            self.frames_read += 1
            self.consecutive_failed_reads = 0
            self.last_frame_at = now if now is not None else time.time()

    def record_frame_streamed(self):
        with self._lock:
            self.frames_streamed += 1

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
        with self._lock:
            self.analysis_frames += 1
            self.last_face_count = face_count
            self.last_labels = list(labels)
            self.last_faces = [self._serialize_face(face) for face in faces or []]
            self.last_analysis_at = now if now is not None else time.time()

    def record_motion(self, motion_detected, motion_score, motion_area, now=None):
        with self._lock:
            was_motion_active = self.motion_active
            self.motion_frames += 1
            self.motion_active = motion_detected
            self.last_motion_score = motion_score
            self.last_motion_area = motion_area

            if motion_detected and not was_motion_active:
                self.motion_events += 1
                self.last_motion_at = now if now is not None else time.time()

    def snapshot(self):
        with self._lock:
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
                "runtime": {
                    "last_frame_at": self.last_frame_at,
                    "last_analysis_at": self.last_analysis_at,
                    "last_motion_at": self.last_motion_at,
                },
            }

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
