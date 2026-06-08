from pathlib import Path
import logging
import platform
import time

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from insightface.app import FaceAnalysis
from PIL import Image, ImageOps


app = FastAPI(title="Smart Camera App")

FRONTEND_FILE = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
KNOWN_FACES_DIR = Path(__file__).resolve().parent / "known_faces"
CAMERA_INDEXES = [0, 1, 2]
READ_ATTEMPTS = 10
RECONNECT_AFTER_FAILURES = 10
INSIGHTFACE_MODEL_NAME = "buffalo_l"
INSIGHTFACE_DETECTION_SIZE = (640, 640)
FACE_MATCH_THRESHOLD = 0.45
KNOWN_FACE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("smart-camera")
face_analyzer = None
known_faces = []


@app.get("/")
def home():
    """Serve the simple camera page."""
    return FileResponse(FRONTEND_FILE)


@app.get("/health")
def health():
    return {"status": "ok"}


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


def recognize_face(face):
    if not known_faces:
        return "Anonymous", 0.0

    face_embedding = get_face_embedding(face)

    if face_embedding is None:
        return "Anonymous", 0.0

    best_name = "Anonymous"
    best_score = 0.0

    for known_face in known_faces:
        score = float(np.dot(face_embedding, known_face["embedding"]))

        if score > best_score:
            best_score = score
            best_name = known_face["name"]

    if best_score >= FACE_MATCH_THRESHOLD:
        return best_name, best_score

    return "Anonymous", best_score


def draw_face_label(frame, face_box, label):
    x1, y1, x2, y2 = face_box
    color = (34, 197, 94) if label != "Anonymous" else (0, 165, 255)

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


def create_camera(index):
    if platform.system() == "Darwin":
        return cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)

    return cv2.VideoCapture(index)


def release_camera(camera, index):
    if camera is not None:
        camera.release()
        logger.info("Released camera index %s", index)


def read_first_frame(camera, index):
    for attempt in range(1, READ_ATTEMPTS + 1):
        success, frame = camera.read()

        if success and frame is not None:
            logger.info("Read frame from camera index %s", index)
            return True

        logger.warning(
            "Camera index %s did not return a frame (attempt %s/%s)",
            index,
            attempt,
            READ_ATTEMPTS,
        )
        time.sleep(0.1)

    return False


def open_working_camera():
    for index in CAMERA_INDEXES:
        logger.info("Trying camera index %s", index)
        camera = create_camera(index)

        if not camera.isOpened():
            logger.warning("Camera index %s did not open", index)
            release_camera(camera, index)
            continue

        logger.info("Camera index %s opened", index)

        if read_first_frame(camera, index):
            logger.info("Using camera index %s", index)
            return camera, index, None

        logger.warning("Camera index %s opened but frames could not be read", index)
        release_camera(camera, index)

    error = "Could not open and read from camera indexes 0, 1, or 2"
    logger.error(error)
    return None, None, error


@app.get("/camera-test")
async def camera_test():
    camera, index, error = open_working_camera()

    if camera is None:
        return {
            "camera_available": False,
            "working_index": None,
            "tested_indexes": CAMERA_INDEXES,
            "message": error,
        }

    release_camera(camera, index)

    return {
        "camera_available": True,
        "working_index": index,
        "tested_indexes": CAMERA_INDEXES,
        "message": f"Camera is available on index {index}",
    }


def generate_frames(camera, index):
    frame_count = 0
    failed_reads = 0
    last_face_count = None

    try:
        while True:
            success, frame = camera.read()

            if not success or frame is None:
                failed_reads += 1
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

                time.sleep(0.1)
                continue

            failed_reads = 0
            frame_count += 1

            if frame_count == 1 or frame_count % 120 == 0:
                logger.info("Streaming frame %s from camera index %s", frame_count, index)

            frame, face_count, face_labels = annotate_faces(frame)

            if face_count != last_face_count or (face_count > 0 and frame_count % 60 == 0):
                logger.info(
                    "Detected %s face(s) on frame %s: %s",
                    face_count,
                    frame_count,
                    ", ".join(face_labels) if face_labels else "none",
                )
                last_face_count = face_count

            success, encoded_frame = cv2.imencode(".jpg", frame)

            if not success:
                logger.warning("Frame encoding failed for camera index %s", index)
                continue

            frame_bytes = encoded_frame.tobytes()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
    finally:
        release_camera(camera, index)


@app.get("/video")
async def video():
    camera, index, error = open_working_camera()

    if camera is None:
        raise HTTPException(status_code=503, detail=error)

    return StreamingResponse(
        generate_frames(camera, index),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


face_analyzer = create_face_analyzer()
known_faces = load_known_faces()
