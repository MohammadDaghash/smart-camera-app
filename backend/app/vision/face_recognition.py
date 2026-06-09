import cv2
import numpy as np
from insightface.app import FaceAnalysis
from PIL import Image, ImageOps

from app.config import (
    ANONYMOUS_MATCH_THRESHOLD,
    FACE_IDENTITIES_FILE,
    FACE_MATCH_THRESHOLD,
    INSIGHTFACE_DETECTION_SIZE,
    INSIGHTFACE_MODEL_NAME,
    KNOWN_FACE_EXTENSIONS,
    KNOWN_FACES_DIR,
)
from app.services.identity_store import FaceIdentityStore
from app.utils.logging import logger


def create_face_analyzer():
    logger.info("Loading InsightFace model: %s", INSIGHTFACE_MODEL_NAME)

    analyzer = FaceAnalysis(
        name=INSIGHTFACE_MODEL_NAME,
        providers=["CPUExecutionProvider"],
    )
    analyzer.prepare(ctx_id=-1, det_size=INSIGHTFACE_DETECTION_SIZE)

    logger.info("InsightFace model is ready")
    return analyzer


def detect_faces(frame):
    return face_analyzer.get(frame)


def read_known_face_image(image_path):
    try:
        image = Image.open(image_path)
        image = ImageOps.exif_transpose(image).convert("RGB")
    except Exception as error:
        logger.warning("Could not read known face image %s: %s", image_path, error)
        return None

    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def face_area(face):
    x1, y1, x2, y2 = face.bbox
    return max(0, x2 - x1) * max(0, y2 - y1)


def face_box_from_detection(face, frame_shape):
    frame_height, frame_width = frame_shape[:2]
    x1, y1, x2, y2 = face.bbox.astype(int)

    x1 = max(0, min(x1, frame_width - 1))
    y1 = max(0, min(y1, frame_height - 1))
    x2 = max(0, min(x2, frame_width - 1))
    y2 = max(0, min(y2, frame_height - 1))

    return x1, y1, x2, y2


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


def name_from_file_path(path):
    name_parts = path.stem.replace("-", "_").split("_")
    return " ".join(part.capitalize() for part in name_parts if part)


def load_known_faces():
    loaded_faces = []

    if not KNOWN_FACES_DIR.exists():
        logger.warning("Known faces folder does not exist: %s", KNOWN_FACES_DIR)
        logger.info("Loaded 0 known face(s). All detected faces will be Anonymous.")
        return loaded_faces

    image_paths = sorted(
        path
        for path in KNOWN_FACES_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in KNOWN_FACE_EXTENSIONS
    )

    if not image_paths:
        logger.warning(
            "No known face images found in %s. All detected faces will be Anonymous.",
            KNOWN_FACES_DIR,
        )
        logger.info("Loaded 0 known face(s).")
        return loaded_faces

    for image_path in image_paths:
        image = read_known_face_image(image_path)

        if image is None:
            continue

        faces = detect_faces(image)

        if len(faces) == 0:
            logger.warning("No face was detected in known face image: %s", image_path)
            continue

        largest_face = max(faces, key=face_area)
        embedding = get_face_embedding(largest_face)
        name = name_from_file_path(image_path)

        if embedding is None:
            logger.warning("No face embedding was created for known face image: %s", image_path)
            continue

        loaded_faces.append(
            {
                "name": name,
                "embedding": embedding,
            }
        )

        logger.info("Loaded known face image for %s: %s", name, image_path)

    logger.info("Loaded %s known face(s)", len(loaded_faces))

    if not loaded_faces:
        logger.warning("No usable known faces were loaded. All detected faces will be Anonymous.")

    return loaded_faces


def match_known_face(face_embedding):
    best_name = None
    best_score = 0.0

    for known_face in known_faces:
        score = float(np.dot(face_embedding, known_face["embedding"]))

        if score > best_score:
            best_score = score
            best_name = known_face["name"]

    if best_name is not None and best_score >= FACE_MATCH_THRESHOLD:
        return best_name, best_score

    return None, best_score


def recognize_face(face):
    face_embedding = get_face_embedding(face)

    if face_embedding is None:
        return "Anonymous", 0.0

    known_name, known_score = match_known_face(face_embedding)

    if known_name is not None:
        return known_name, known_score

    promoted_name, promoted_score = identity_store.match_promoted_identity(face_embedding)

    if promoted_name is not None:
        return promoted_name, promoted_score

    anonymous_label, anonymous_score = identity_store.match_or_create_anonymous_identity(
        face_embedding
    )

    return anonymous_label, anonymous_score


def draw_face_label(frame, face_box, label):
    x1, y1, x2, y2 = face_box
    color = (0, 165, 255) if label.startswith("Anonymous") else (34, 197, 94)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    text_size, baseline = cv2.getTextSize(label, font, font_scale, thickness)
    text_width, text_height = text_size
    label_y = max(y1 - 10, text_height + 10)

    cv2.rectangle(
        frame,
        (x1, label_y - text_height - baseline - 6),
        (x1 + text_width + 10, label_y + baseline),
        color,
        cv2.FILLED,
    )
    cv2.putText(
        frame,
        label,
        (x1 + 5, label_y - 5),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


def annotate_faces(frame):
    faces = detect_faces(frame)
    labels = []

    for face in faces:
        face_box = face_box_from_detection(face, frame.shape)
        label, score = recognize_face(face)
        labels.append(f"{label}:{score:.2f}")
        draw_face_label(frame, face_box, label)

    return frame, len(faces), labels


face_analyzer = create_face_analyzer()
known_faces = load_known_faces()
identity_store = FaceIdentityStore(
    path=FACE_IDENTITIES_FILE,
    known_threshold=FACE_MATCH_THRESHOLD,
    anonymous_threshold=ANONYMOUS_MATCH_THRESHOLD,
)
