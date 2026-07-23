from app.services import camera_source


class FakeCamera:
    def __init__(self, opened, reads):
        self.opened = opened
        self.reads = list(reads)
        self.released = False

    def isOpened(self):
        return self.opened

    def read(self):
        if self.reads:
            return self.reads.pop(0)

        return False, None

    def release(self):
        self.released = True


def test_open_working_camera_skips_unusable_indexes(monkeypatch):
    cameras = {
        0: FakeCamera(opened=False, reads=[]),
        1: FakeCamera(opened=True, reads=[(False, None)]),
        2: FakeCamera(opened=True, reads=[(True, object())]),
    }

    monkeypatch.setattr(camera_source, "CAMERA_INDEXES", [0, 1, 2])
    monkeypatch.setattr(camera_source, "READ_ATTEMPTS", 1)
    monkeypatch.setattr(camera_source, "create_camera", lambda index: cameras[index])
    monkeypatch.setattr(camera_source.time, "sleep", lambda seconds: None)

    camera, index, error = camera_source.open_working_camera()

    assert camera is cameras[2]
    assert index == 2
    assert error is None
    assert cameras[0].released is True
    assert cameras[1].released is True
    assert cameras[2].released is False


def test_open_working_camera_returns_error_when_no_camera_works(monkeypatch):
    cameras = {
        0: FakeCamera(opened=False, reads=[]),
        1: FakeCamera(opened=False, reads=[]),
    }

    monkeypatch.setattr(camera_source, "CAMERA_INDEXES", [0, 1])
    monkeypatch.setattr(camera_source, "create_camera", lambda index: cameras[index])

    camera, index, error = camera_source.open_working_camera()

    assert camera is None
    assert index is None
    assert "Could not open and read" in error
    assert cameras[0].released is True
    assert cameras[1].released is True
