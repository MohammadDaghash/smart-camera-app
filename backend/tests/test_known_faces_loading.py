import importlib
import sys
import types
from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture()
def face_recognition_module(monkeypatch):
    fake_app_module = types.ModuleType("insightface.app")

    class FakeFaceAnalysis:
        def __init__(self, *args, **kwargs):
            pass

        def prepare(self, *args, **kwargs):
            pass

        def get(self, frame):
            return []

    fake_app_module.FaceAnalysis = FakeFaceAnalysis
    monkeypatch.setitem(sys.modules, "insightface.app", fake_app_module)
    sys.modules.pop("app.vision.face_recognition", None)

    module = importlib.import_module("app.vision.face_recognition")

    yield module

    sys.modules.pop("app.vision.face_recognition", None)


def _create_image_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"test-image")


def _fake_face_for_path(path):
    seed = sum(ord(char) for char in str(path))
    embedding = np.array([seed % 5 + 1, seed % 7 + 1], dtype=np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    return SimpleNamespace(
        bbox=np.array([0, 0, 10, 10], dtype=np.float32),
        normed_embedding=embedding,
    )


def test_load_known_faces_supports_person_folders_and_flat_files(
    face_recognition_module,
    monkeypatch,
    tmp_path,
):
    _create_image_file(tmp_path / "mohammad.jpg")
    _create_image_file(tmp_path / "Mohammad" / "1.jpg")
    _create_image_file(tmp_path / "Mohammad" / "2.png")
    _create_image_file(tmp_path / "Omar" / "1.jpeg")
    _create_image_file(tmp_path / "Omar" / "notes.txt")

    monkeypatch.setattr(face_recognition_module, "KNOWN_FACES_DIR", tmp_path)
    monkeypatch.setattr(
        face_recognition_module,
        "read_known_face_image",
        lambda image_path: image_path,
    )
    monkeypatch.setattr(
        face_recognition_module,
        "detect_faces",
        lambda image_path: [_fake_face_for_path(image_path)],
    )

    loaded_faces = face_recognition_module.load_known_faces()
    counts = Counter(face["name"] for face in loaded_faces)

    assert counts == {
        "Mohammad": 3,
        "Omar": 1,
    }
    assert len(loaded_faces) == 4


def test_recognize_face_uses_best_embedding_match(face_recognition_module, monkeypatch):
    monkeypatch.setattr(
        face_recognition_module,
        "known_faces",
        [
            {"name": "Mohammad", "embedding": np.array([1.0, 0.0], dtype=np.float32)},
            {"name": "Mohammad", "embedding": np.array([0.0, 1.0], dtype=np.float32)},
            {"name": "Omar", "embedding": np.array([-1.0, 0.0], dtype=np.float32)},
        ],
    )
    query_face = SimpleNamespace(normed_embedding=np.array([0.0, 1.0], dtype=np.float32))

    label, score = face_recognition_module.recognize_face(query_face)

    assert label == "Mohammad"
    assert score == pytest.approx(1.0)


def test_build_face_annotations_returns_boxes_labels_and_scores(
    face_recognition_module,
    monkeypatch,
):
    face = SimpleNamespace(
        bbox=np.array([2, 3, 12, 13], dtype=np.float32),
        normed_embedding=np.array([1.0, 0.0], dtype=np.float32),
    )
    frame = np.zeros((20, 20, 3), dtype=np.uint8)

    monkeypatch.setattr(face_recognition_module, "detect_faces", lambda image: [face])
    monkeypatch.setattr(
        face_recognition_module,
        "recognize_face",
        lambda detected_face: ("Mohammad", 0.87),
    )

    annotations = face_recognition_module.build_face_annotations(frame)

    assert annotations == [
        {
            "box": (2, 3, 12, 13),
            "label": "Mohammad",
            "score": 0.87,
        }
    ]
    assert face_recognition_module.labels_from_annotations(annotations) == [
        "Mohammad:0.87"
    ]
