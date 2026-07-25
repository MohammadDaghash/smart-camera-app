from collections import Counter, deque


def box_iou(first_box, second_box):
    first_x1, first_y1, first_x2, first_y2 = first_box
    second_x1, second_y1, second_x2, second_y2 = second_box

    intersection_x1 = max(first_x1, second_x1)
    intersection_y1 = max(first_y1, second_y1)
    intersection_x2 = min(first_x2, second_x2)
    intersection_y2 = min(first_y2, second_y2)

    intersection_width = max(0, intersection_x2 - intersection_x1)
    intersection_height = max(0, intersection_y2 - intersection_y1)
    intersection_area = intersection_width * intersection_height

    first_area = max(0, first_x2 - first_x1) * max(0, first_y2 - first_y1)
    second_area = max(0, second_x2 - second_x1) * max(0, second_y2 - second_y1)
    union_area = first_area + second_area - intersection_area

    if union_area <= 0:
        return 0.0

    return intersection_area / union_area


class FaceLabelSmoother:
    def __init__(
        self,
        enabled=True,
        history_size=5,
        min_votes=2,
        iou_threshold=0.2,
        ttl_frames=5,
    ):
        self.enabled = enabled
        self.history_size = max(1, int(history_size))
        self.min_votes = max(1, min(int(min_votes), self.history_size))
        self.iou_threshold = max(0.0, float(iou_threshold))
        self.ttl_frames = max(1, int(ttl_frames))
        self._tracks = {}
        self._next_track_id = 1

    def smooth(self, annotations, frame_index):
        if not self.enabled:
            return list(annotations)

        self._prune_tracks(frame_index)

        smoothed_annotations = []
        used_track_ids = set()

        for annotation in annotations:
            track = self._match_track(annotation["box"], used_track_ids)

            if track is None:
                track = self._create_track()

            used_track_ids.add(track["id"])
            track["box"] = annotation["box"]
            track["last_seen_frame"] = frame_index
            raw_label = annotation["label"]
            raw_score = annotation["score"]
            track["observations"].append(
                {
                    "label": raw_label,
                    "score": raw_score,
                }
            )

            label, score = self._stable_label_and_score(track, raw_label, raw_score)

            smoothed_annotation = dict(annotation)
            smoothed_annotation["track_id"] = track["id"]
            smoothed_annotation["raw_label"] = raw_label
            smoothed_annotation["raw_score"] = raw_score
            smoothed_annotation["label"] = label
            smoothed_annotation["score"] = score
            smoothed_annotations.append(smoothed_annotation)

        return smoothed_annotations

    def reset(self):
        self._tracks.clear()
        self._next_track_id = 1

    def _create_track(self):
        track = {
            "id": self._next_track_id,
            "box": None,
            "last_seen_frame": 0,
            "observations": deque(maxlen=self.history_size),
            "smoothed_label": None,
            "smoothed_score": 0.0,
        }
        self._tracks[track["id"]] = track
        self._next_track_id += 1
        return track

    def _match_track(self, face_box, used_track_ids):
        best_track = None
        best_iou = 0.0

        for track in self._tracks.values():
            if track["id"] in used_track_ids or track["box"] is None:
                continue

            overlap = box_iou(face_box, track["box"])

            if overlap > best_iou:
                best_iou = overlap
                best_track = track

        if best_iou < self.iou_threshold:
            return None

        return best_track

    def _stable_label_and_score(self, track, raw_label, raw_score):
        labels = [observation["label"] for observation in track["observations"]]
        most_common_label, votes = Counter(labels).most_common(1)[0]

        if votes >= self.min_votes:
            label = most_common_label
        elif track["smoothed_label"]:
            label = track["smoothed_label"]
        else:
            label = raw_label

        score = raw_score

        for observation in reversed(track["observations"]):
            if observation["label"] == label:
                score = observation["score"]
                break

        track["smoothed_label"] = label
        track["smoothed_score"] = score
        return label, score

    def _prune_tracks(self, frame_index):
        expired_track_ids = [
            track_id
            for track_id, track in self._tracks.items()
            if frame_index - track["last_seen_frame"] > self.ttl_frames
        ]

        for track_id in expired_track_ids:
            del self._tracks[track_id]
