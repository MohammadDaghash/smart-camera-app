from app.services import mjpeg_streamer


class FakeEncodedFrame:
    def tobytes(self):
        return b"jpeg-bytes"


def test_encode_mjpeg_frame_returns_valid_multipart_chunk(monkeypatch):
    monkeypatch.setattr(
        mjpeg_streamer.cv2,
        "imencode",
        lambda extension, frame: (True, FakeEncodedFrame()),
    )

    chunk = mjpeg_streamer.encode_mjpeg_frame(frame=object())

    assert chunk == (
        b"--frame\r\n"
        b"Content-Type: image/jpeg\r\n\r\n"
        b"jpeg-bytes"
        b"\r\n"
    )


def test_encode_mjpeg_frame_returns_none_when_encoding_fails(monkeypatch):
    monkeypatch.setattr(
        mjpeg_streamer.cv2,
        "imencode",
        lambda extension, frame: (False, None),
    )

    assert mjpeg_streamer.encode_mjpeg_frame(frame=object()) is None
