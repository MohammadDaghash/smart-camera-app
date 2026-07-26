from app.services.settings_summary import build_settings_summary


def all_settings(summary):
    for group in summary["groups"]:
        yield from group["settings"]


def test_settings_summary_groups_tuning_values():
    summary = build_settings_summary()

    group_ids = [group["id"] for group in summary["groups"]]

    assert summary["mode"] == "read_only"
    assert summary["restart_required"] is True
    assert group_ids == ["face_recognition", "motion", "events_alerts"]


def test_settings_summary_includes_expected_tuning_keys():
    summary = build_settings_summary()
    env_vars = {setting["env_var"] for setting in all_settings(summary)}

    assert "FACE_MATCH_THRESHOLD" in env_vars
    assert "FACE_ANALYSIS_INTERVAL_FRAMES" in env_vars
    assert "MOTION_SCORE_THRESHOLD" in env_vars
    assert "ALERT_COOLDOWN_SECONDS" in env_vars
    assert "REVIEW_EVENT_GAP_SECONDS" in env_vars


def test_settings_summary_does_not_expose_secrets():
    summary = build_settings_summary()
    env_vars = {setting["env_var"] for setting in all_settings(summary)}

    assert "AUTH_PASSWORD" not in env_vars
    assert "SESSION_SECRET" not in env_vars
