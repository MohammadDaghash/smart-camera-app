def normalized_frame_interval(interval):
    return max(1, int(interval))


def should_process_frame(frame_count, interval):
    return frame_count == 1 or frame_count % normalized_frame_interval(interval) == 0
