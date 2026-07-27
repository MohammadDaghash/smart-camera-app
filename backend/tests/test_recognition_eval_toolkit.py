import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLKIT_PATH = PROJECT_ROOT / "experiments" / "recognition_eval" / "evaluate_faces.py"

spec = importlib.util.spec_from_file_location("recognition_eval_toolkit", TOOLKIT_PATH)
recognition_eval = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = recognition_eval
spec.loader.exec_module(recognition_eval)


def test_parse_threshold_range():
    thresholds = recognition_eval.parse_thresholds("0.40:0.60:0.10")

    assert thresholds == [0.4, 0.5, 0.6]


def test_discover_known_sources_supports_flat_and_person_folders(tmp_path):
    known_dir = tmp_path / "known"
    (known_dir / "mohammad.jpg").parent.mkdir(parents=True)
    (known_dir / "mohammad.jpg").write_bytes(b"image")
    (known_dir / "Omar").mkdir()
    (known_dir / "Omar" / "1.png").write_bytes(b"image")
    (known_dir / "Omar" / "notes.txt").write_text("skip")

    sources = recognition_eval.discover_known_sources(known_dir)

    assert sorted((source.label, source.path.name) for source in sources) == [
        ("Mohammad", "mohammad.jpg"),
        ("Omar", "1.png"),
    ]


def test_discover_test_sources_uses_folder_as_true_label(tmp_path):
    test_dir = tmp_path / "test"
    (test_dir / "Anonymous").mkdir(parents=True)
    (test_dir / "Anonymous" / "unknown.jpeg").write_bytes(b"image")

    sources = recognition_eval.discover_test_sources(test_dir)

    assert len(sources) == 1
    assert sources[0].label == "Anonymous"
    assert sources[0].path.name == "unknown.jpeg"


def test_match_embedding_uses_best_similarity():
    known_embeddings = [
        recognition_eval.EmbeddingRecord(
            label="Mohammad",
            path=Path("mohammad.jpg"),
            embedding=np.array([1.0, 0.0], dtype=np.float32),
        ),
        recognition_eval.EmbeddingRecord(
            label="Omar",
            path=Path("omar.jpg"),
            embedding=np.array([0.0, 1.0], dtype=np.float32),
        ),
    ]

    label, score = recognition_eval.match_embedding(
        np.array([0.0, 1.0], dtype=np.float32),
        known_embeddings,
    )

    assert label == "Omar"
    assert score == 1.0


def test_threshold_report_and_recommendation_penalize_anonymous_false_positives():
    samples = [
        recognition_eval.EvaluationSample(
            true_label="Mohammad",
            path=Path("mohammad-test.jpg"),
            best_label="Mohammad",
            best_score=0.8,
            status="ok",
        ),
        recognition_eval.EvaluationSample(
            true_label="Anonymous",
            path=Path("anonymous-test.jpg"),
            best_label="Mohammad",
            best_score=0.6,
            status="ok",
        ),
    ]

    report = recognition_eval.build_threshold_report(samples, [0.5, 0.7])
    recommendation = recognition_eval.choose_recommended_threshold(report)

    assert recommendation == 0.7
    assert report.loc[report["threshold"] == 0.5, "anonymous_false_positive_rate"].iloc[0] == 1.0
    assert report.loc[report["threshold"] == 0.7, "accuracy"].iloc[0] == 1.0


def test_prediction_rows_marks_no_face_samples():
    sample = recognition_eval.EvaluationSample(
        true_label="Mohammad",
        path=Path("blurred.jpg"),
        best_label=recognition_eval.NO_FACE_LABEL,
        best_score=0.0,
        status="no_face",
    )

    rows = recognition_eval.prediction_rows([sample], threshold=0.45)

    assert rows[0]["predicted_label"] == recognition_eval.NO_FACE_LABEL
    assert rows[0]["status"] == "no_face"


def test_dataset_summary_reports_counts_and_warnings():
    known_sources = [
        recognition_eval.ImageSource(label="Mohammad", path=Path("mohammad.jpg")),
        recognition_eval.ImageSource(label="Omar", path=Path("omar.jpg")),
    ]
    known_embeddings = [
        recognition_eval.EmbeddingRecord(
            label="Mohammad",
            path=Path("mohammad.jpg"),
            embedding=np.array([1.0, 0.0], dtype=np.float32),
        ),
        recognition_eval.EmbeddingRecord(
            label="Omar",
            path=Path("omar.jpg"),
            embedding=np.array([0.0, 1.0], dtype=np.float32),
        ),
    ]
    test_sources = [
        recognition_eval.ImageSource(label="Mohammad", path=Path("test.jpg")),
    ]
    samples = [
        recognition_eval.EvaluationSample(
            true_label="Mohammad",
            path=Path("test.jpg"),
            best_label="Mohammad",
            best_score=0.8,
            status="ok",
        ),
    ]

    summary = recognition_eval.build_dataset_summary(
        known_sources,
        known_embeddings,
        test_sources,
        samples,
    )
    warnings = recognition_eval.dataset_warnings(summary)

    assert summary["known_usable_embeddings"] == 2
    assert summary["test_images_by_label"] == {"Mohammad": 1}
    assert any("No Anonymous test images" in warning for warning in warnings)
    assert any("Omar" in warning for warning in warnings)


def test_save_outputs_writes_complete_report(tmp_path):
    samples = [
        recognition_eval.EvaluationSample(
            true_label="Mohammad",
            path=Path("mohammad-test.jpg"),
            best_label="Mohammad",
            best_score=0.8,
            status="ok",
        ),
        recognition_eval.EvaluationSample(
            true_label="Anonymous",
            path=Path("anonymous-test.jpg"),
            best_label="Mohammad",
            best_score=0.6,
            status="ok",
        ),
    ]
    known_sources = [
        recognition_eval.ImageSource(label="Mohammad", path=Path("mohammad.jpg")),
    ]
    test_sources = [
        recognition_eval.ImageSource(label="Mohammad", path=Path("mohammad-test.jpg")),
        recognition_eval.ImageSource(label="Anonymous", path=Path("anonymous-test.jpg")),
    ]
    known_embeddings = [
        recognition_eval.EmbeddingRecord(
            label="Mohammad",
            path=Path("mohammad.jpg"),
            embedding=np.array([1.0, 0.0], dtype=np.float32),
        ),
    ]

    recommendation = recognition_eval.save_outputs(
        samples=samples,
        thresholds=[0.5, 0.7],
        output_dir=tmp_path,
        current_threshold=0.5,
        known_sources=known_sources,
        test_sources=test_sources,
        known_embeddings=known_embeddings,
    )

    assert recommendation == 0.7
    assert (tmp_path / "predictions.csv").exists()
    assert (tmp_path / "score_distribution.csv").exists()
    assert (tmp_path / "per_label_metrics.csv").exists()
    assert (tmp_path / "threshold_report.csv").exists()
    assert (tmp_path / "confusion_matrix.png").exists()
    assert (tmp_path / "threshold_plot.png").exists()

    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["recommended_threshold"] == 0.7
    assert summary["dataset"]["test_images_by_label"] == {
        "Anonymous": 1,
        "Mohammad": 1,
    }
