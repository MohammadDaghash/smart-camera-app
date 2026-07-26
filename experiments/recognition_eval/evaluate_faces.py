from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import cv2
import matplotlib
import numpy as np
import pandas as pd
from PIL import Image, ImageOps
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)


matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


ANONYMOUS_LABEL = "Anonymous"
NO_FACE_LABEL = "No Face"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWN_DIR = PROJECT_ROOT / "backend" / "known_faces"
DEFAULT_TEST_DIR = PROJECT_ROOT / "experiments" / "recognition_eval" / "dataset" / "test"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "experiments" / "recognition_eval" / "results"


@dataclass(frozen=True)
class ImageSource:
    label: str
    path: Path


@dataclass(frozen=True)
class EmbeddingRecord:
    label: str
    path: Path
    embedding: np.ndarray


@dataclass(frozen=True)
class EvaluationSample:
    true_label: str
    path: Path
    best_label: str
    best_score: float
    status: str


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate Smart Camera face-recognition thresholds.",
    )
    parser.add_argument(
        "--known-dir",
        type=Path,
        default=DEFAULT_KNOWN_DIR,
        help="Known-face reference folder. Defaults to backend/known_faces.",
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=DEFAULT_TEST_DIR,
        help="Labeled test image folder. Defaults to experiments dataset/test.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Folder for CSV reports and plots.",
    )
    parser.add_argument(
        "--thresholds",
        default="0.30:0.80:0.01",
        help="Threshold sweep. Use start:stop:step or comma values.",
    )
    parser.add_argument(
        "--current-threshold",
        type=float,
        default=0.45,
        help="Threshold used for predictions.csv and confusion_matrix.png.",
    )
    return parser.parse_args()


def parse_thresholds(raw_thresholds):
    raw_thresholds = raw_thresholds.strip()

    if ":" in raw_thresholds:
        start, stop, step = [float(part) for part in raw_thresholds.split(":")]

        if step <= 0:
            raise ValueError("Threshold step must be positive.")

        thresholds = []
        value = start

        while value <= stop + step / 2:
            thresholds.append(round(value, 4))
            value += step

        return thresholds

    return sorted(
        {
            round(float(part.strip()), 4)
            for part in raw_thresholds.split(",")
            if part.strip()
        }
    )


def name_from_file_path(path):
    name_parts = path.stem.replace("-", "_").split("_")
    return " ".join(part.capitalize() for part in name_parts if part)


def discover_known_sources(known_dir):
    if not known_dir.exists():
        return []

    image_sources = []

    for path in sorted(known_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            image_sources.append(ImageSource(name_from_file_path(path), path))
            continue

        if not path.is_dir() or path.name.startswith("."):
            continue

        label = path.name.strip()

        if not label:
            continue

        for image_path in sorted(path.iterdir()):
            if image_path.is_file() and image_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                image_sources.append(ImageSource(label, image_path))

    return image_sources


def discover_test_sources(test_dir):
    if not test_dir.exists():
        return []

    image_sources = []

    for label_dir in sorted(test_dir.iterdir()):
        if not label_dir.is_dir() or label_dir.name.startswith("."):
            continue

        label = label_dir.name.strip()

        if not label:
            continue

        for image_path in sorted(label_dir.iterdir()):
            if image_path.is_file() and image_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                image_sources.append(ImageSource(label, image_path))

    return image_sources


def read_image(image_path):
    try:
        image = Image.open(image_path)
        image = ImageOps.exif_transpose(image).convert("RGB")
    except Exception:
        return None

    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def create_face_analyzer():
    from insightface.app import FaceAnalysis

    analyzer = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    analyzer.prepare(ctx_id=-1, det_size=(640, 640))
    return analyzer


def face_area(face):
    x1, y1, x2, y2 = face.bbox
    return max(0, x2 - x1) * max(0, y2 - y1)


def get_face_embedding(face):
    embedding = getattr(face, "normed_embedding", None)

    if embedding is None:
        embedding = getattr(face, "embedding", None)

        if embedding is None:
            return None

        norm = np.linalg.norm(embedding)

        if norm == 0:
            return None

        embedding = embedding / norm

    return np.asarray(embedding, dtype=np.float32)


def embedding_from_image(analyzer, image_path):
    image = read_image(image_path)

    if image is None:
        return None, "read_error"

    faces = analyzer.get(image)

    if not faces:
        return None, "no_face"

    largest_face = max(faces, key=face_area)
    embedding = get_face_embedding(largest_face)

    if embedding is None:
        return None, "no_embedding"

    return embedding, "ok"


def load_known_embeddings(analyzer, known_sources):
    known_embeddings = []

    for source in known_sources:
        embedding, status = embedding_from_image(analyzer, source.path)

        if status != "ok":
            print(f"Skipping known image ({status}): {source.path}")
            continue

        known_embeddings.append(
            EmbeddingRecord(
                label=source.label,
                path=source.path,
                embedding=embedding,
            )
        )

    return known_embeddings


def match_embedding(query_embedding, known_embeddings):
    best_label = ANONYMOUS_LABEL
    best_score = 0.0

    for known in known_embeddings:
        score = float(np.dot(query_embedding, known.embedding))

        if score > best_score:
            best_label = known.label
            best_score = score

    return best_label, best_score


def build_evaluation_samples(analyzer, test_sources, known_embeddings):
    samples = []

    for source in test_sources:
        embedding, status = embedding_from_image(analyzer, source.path)

        if status != "ok":
            samples.append(
                EvaluationSample(
                    true_label=source.label,
                    path=source.path,
                    best_label=NO_FACE_LABEL,
                    best_score=0.0,
                    status=status,
                )
            )
            continue

        best_label, best_score = match_embedding(embedding, known_embeddings)
        samples.append(
            EvaluationSample(
                true_label=source.label,
                path=source.path,
                best_label=best_label,
                best_score=best_score,
                status="ok",
            )
        )

    return samples


def predicted_label(sample, threshold):
    if sample.status != "ok":
        return NO_FACE_LABEL

    if sample.best_score >= threshold:
        return sample.best_label

    return ANONYMOUS_LABEL


def prediction_rows(samples, threshold):
    return [
        {
            "image_path": str(sample.path),
            "true_label": sample.true_label,
            "predicted_label": predicted_label(sample, threshold),
            "best_label": sample.best_label,
            "best_score": round(sample.best_score, 6),
            "threshold": threshold,
            "status": sample.status,
        }
        for sample in samples
    ]


def metric_summary(rows, threshold):
    y_true = [row["true_label"] for row in rows]
    y_pred = [row["predicted_label"] for row in rows]
    labels = sorted(set(y_true) | set(y_pred))

    precision, recall, f1, _support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    anonymous_rows = [
        row for row in rows if row["true_label"].lower() == ANONYMOUS_LABEL.lower()
    ]
    known_rows = [
        row for row in rows if row["true_label"].lower() != ANONYMOUS_LABEL.lower()
    ]
    no_face_rows = [row for row in rows if row["predicted_label"] == NO_FACE_LABEL]

    return {
        "threshold": threshold,
        "total_samples": len(rows),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6) if rows else 0.0,
        "macro_precision": round(float(precision), 6),
        "macro_recall": round(float(recall), 6),
        "macro_f1": round(float(f1), 6),
        "anonymous_false_positive_rate": round(
            rate(
                [
                    row["predicted_label"] not in {ANONYMOUS_LABEL, NO_FACE_LABEL}
                    for row in anonymous_rows
                ]
            ),
            6,
        ),
        "known_false_anonymous_rate": round(
            rate([row["predicted_label"] == ANONYMOUS_LABEL for row in known_rows]),
            6,
        ),
        "no_face_rate": round(rate([True for _row in no_face_rows], len(rows)), 6),
    }


def rate(values, denominator=None):
    if denominator is None:
        denominator = len(values)

    if denominator == 0:
        return 0.0

    return sum(1 for value in values if value) / denominator


def build_threshold_report(samples, thresholds):
    return pd.DataFrame(
        [
            metric_summary(prediction_rows(samples, threshold), threshold)
            for threshold in thresholds
        ]
    )


def choose_recommended_threshold(threshold_report):
    if threshold_report.empty:
        return None

    ranked = threshold_report.sort_values(
        by=[
            "macro_f1",
            "anonymous_false_positive_rate",
            "known_false_anonymous_rate",
            "threshold",
        ],
        ascending=[False, True, True, True],
    )
    return float(ranked.iloc[0]["threshold"])


def ordered_labels(rows):
    labels = sorted(
        label
        for label in {row["true_label"] for row in rows}
        | {row["predicted_label"] for row in rows}
        if label not in {ANONYMOUS_LABEL, NO_FACE_LABEL}
    )

    if ANONYMOUS_LABEL in {row["true_label"] for row in rows} | {
        row["predicted_label"] for row in rows
    }:
        labels.append(ANONYMOUS_LABEL)

    if NO_FACE_LABEL in {row["predicted_label"] for row in rows}:
        labels.append(NO_FACE_LABEL)

    return labels


def save_confusion_matrix(rows, output_path):
    labels = ordered_labels(rows)
    matrix = confusion_matrix(
        [row["true_label"] for row in rows],
        [row["predicted_label"] for row in rows],
        labels=labels,
    )

    fig, axis = plt.subplots(figsize=(max(6, len(labels)), max(5, len(labels))))
    axis.imshow(matrix, cmap="Blues")
    axis.set_title("Face Recognition Confusion Matrix")
    axis.set_xlabel("Predicted label")
    axis.set_ylabel("True label")
    axis.set_xticks(np.arange(len(labels)), labels=labels, rotation=35, ha="right")
    axis.set_yticks(np.arange(len(labels)), labels=labels)

    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            axis.text(
                col_index,
                row_index,
                str(matrix[row_index, col_index]),
                ha="center",
                va="center",
                color="#111827",
            )

    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_outputs(samples, thresholds, output_dir, current_threshold):
    output_dir.mkdir(parents=True, exist_ok=True)
    threshold_report = build_threshold_report(samples, thresholds)
    recommended_threshold = choose_recommended_threshold(threshold_report)
    predictions = prediction_rows(samples, current_threshold)

    pd.DataFrame(predictions).to_csv(output_dir / "predictions.csv", index=False)
    threshold_report.to_csv(output_dir / "threshold_report.csv", index=False)
    save_confusion_matrix(predictions, output_dir / "confusion_matrix.png")

    with open(output_dir / "recommended_threshold.txt", "w", encoding="utf-8") as file:
        file.write(f"recommended_threshold={recommended_threshold}\n")
        file.write(f"current_threshold={current_threshold}\n")
        file.write("\nSelection rule:\n")
        file.write("Maximize macro F1, then minimize anonymous false positives.\n")

    return recommended_threshold


def main():
    args = parse_args()
    thresholds = parse_thresholds(args.thresholds)
    known_sources = discover_known_sources(args.known_dir)
    test_sources = discover_test_sources(args.test_dir)

    if not known_sources:
        raise SystemExit(f"No known images found in {args.known_dir}")

    if not test_sources:
        raise SystemExit(
            "No test images found. Add images under "
            f"{args.test_dir}/<TrueLabel>/ before running evaluation."
        )

    print(f"Known image sources: {len(known_sources)}")
    print(f"Test image sources: {len(test_sources)}")
    print("Loading InsightFace model...")
    analyzer = create_face_analyzer()
    known_embeddings = load_known_embeddings(analyzer, known_sources)

    if not known_embeddings:
        raise SystemExit("No usable known-face embeddings were created.")

    print(f"Known embeddings: {len(known_embeddings)}")
    samples = build_evaluation_samples(analyzer, test_sources, known_embeddings)
    recommended_threshold = save_outputs(
        samples=samples,
        thresholds=thresholds,
        output_dir=args.output_dir,
        current_threshold=args.current_threshold,
    )

    print(f"Evaluated samples: {len(samples)}")
    print(f"Current threshold: {args.current_threshold}")
    print(f"Recommended threshold: {recommended_threshold}")
    print(f"Reports written to: {args.output_dir}")


if __name__ == "__main__":
    main()
