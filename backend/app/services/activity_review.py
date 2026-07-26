from app.config import REVIEW_EVENT_GAP_SECONDS, REVIEW_SOURCE_EVENT_LIMIT


TYPE_ORDER = {
    "alert": 0,
    "face": 1,
    "motion": 2,
    "system": 3,
}


def build_activity_review(
    events,
    event_gap_seconds=REVIEW_EVENT_GAP_SECONDS,
    source_event_limit=REVIEW_SOURCE_EVENT_LIMIT,
):
    ordered_events = sorted(
        events,
        key=lambda event: (event.get("created_at", 0), event.get("id", 0)),
    )
    grouped_events = group_events_by_time(ordered_events, event_gap_seconds)

    return {
        "items": [
            build_review_item(group)
            for group in reversed(grouped_events)
        ],
        "settings": {
            "event_gap_seconds": event_gap_seconds,
            "source_event_limit": source_event_limit,
        },
    }


def group_events_by_time(events, event_gap_seconds):
    groups = []
    current_group = []

    for event in events:
        if (
            current_group
            and event["created_at"] - current_group[-1]["created_at"]
            > event_gap_seconds
        ):
            groups.append(current_group)
            current_group = []

        current_group.append(event)

    if current_group:
        groups.append(current_group)

    return groups


def build_review_item(events):
    start_at = events[0]["created_at"]
    end_at = events[-1]["created_at"]
    event_types = sorted(
        {event["type"] for event in events},
        key=lambda event_type: TYPE_ORDER.get(event_type, 99),
    )
    labels = sorted(extract_labels(events))
    severity = choose_severity(event_types)

    return {
        "id": f"review-{events[0]['id']}-{events[-1]['id']}",
        "start_at": start_at,
        "end_at": end_at,
        "duration_seconds": round(max(0, end_at - start_at), 2),
        "event_count": len(events),
        "severity": severity,
        "types": event_types,
        "labels": labels,
        "summary": summarize_review(severity, event_types, labels),
        "events": events,
    }


def extract_labels(events):
    labels = set()

    for event in events:
        metadata = event.get("metadata") or {}
        label = metadata.get("label")

        if isinstance(label, str) and label.strip():
            labels.add(label.strip())

    return labels


def choose_severity(event_types):
    if "alert" in event_types:
        return "alert"

    if "face" in event_types or "motion" in event_types:
        return "detection"

    return "info"


def summarize_review(severity, event_types, labels):
    readable_labels = ", ".join(labels)

    if severity == "alert":
        if readable_labels:
            return f"Alert review: {readable_labels} near activity"

        return "Alert review: suspicious activity"

    if severity == "detection":
        if readable_labels and "motion" in event_types:
            return f"Detection review: {readable_labels} with motion"

        if readable_labels:
            return f"Detection review: {readable_labels}"

        return "Detection review: motion activity"

    return "System review: status changed"
