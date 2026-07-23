import cv2


MJPEG_MEDIA_TYPE = "multipart/x-mixed-replace; boundary=frame"


def encode_jpeg_frame(frame):
    success, encoded_frame = cv2.imencode(".jpg", frame)

    if not success:
        return None

    return encoded_frame.tobytes()


def build_mjpeg_frame(frame_bytes):
    return (
        b"--frame\r\n"
        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
    )


def encode_mjpeg_frame(frame):
    frame_bytes = encode_jpeg_frame(frame)

    if frame_bytes is None:
        return None

    return build_mjpeg_frame(frame_bytes)
