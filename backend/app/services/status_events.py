from threading import Lock

from app.services.event_log import event_log


class StatusEventRecorder:
    def __init__(self, event_log):
        self.event_log = event_log
        self._lock = Lock()
        self._last_status = None

    def reset(self):
        with self._lock:
            self._last_status = None

    def record_if_changed(self, system_status):
        new_status = system_status.get("status")

        if not new_status:
            return None

        with self._lock:
            previous_status = self._last_status
            self._last_status = new_status

        if previous_status is None or previous_status == new_status:
            return None

        return self.event_log.add_event(
            event_type="system",
            message=(
                f"System status changed from {previous_status} "
                f"to {new_status}"
            ),
            metadata={
                "previous_status": previous_status,
                "new_status": new_status,
                "attention_checks": attention_checks(system_status),
            },
        )


def attention_checks(system_status):
    checks = system_status.get("checks", [])

    return [
        {
            "name": check.get("name"),
            "status": check.get("status"),
            "message": check.get("message"),
        }
        for check in checks
        if check.get("status") in {"degraded", "error"}
    ]


status_event_recorder = StatusEventRecorder(event_log)
