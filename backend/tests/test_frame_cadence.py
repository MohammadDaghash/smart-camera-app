from app.services.frame_cadence import normalized_frame_interval, should_process_frame


def test_normalized_frame_interval_never_goes_below_one():
    assert normalized_frame_interval(0) == 1
    assert normalized_frame_interval(-5) == 1
    assert normalized_frame_interval(3) == 3


def test_should_process_first_frame_and_interval_frames():
    assert should_process_frame(frame_count=1, interval=3) is True
    assert should_process_frame(frame_count=2, interval=3) is False
    assert should_process_frame(frame_count=3, interval=3) is True
    assert should_process_frame(frame_count=4, interval=3) is False
    assert should_process_frame(frame_count=6, interval=3) is True
