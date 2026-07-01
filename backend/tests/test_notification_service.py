import unittest
from unittest import mock

from app.services import notification_service


class ShouldNotifyTests(unittest.TestCase):
    def setUp(self):
        notification_service._last_notified_at.clear()

    @mock.patch.object(notification_service, "NOTIFY_COOLDOWN_SECONDS", 300)
    def test_first_call_allowed_then_blocked_within_cooldown(self):
        self.assertTrue(notification_service._should_notify("Omar"))
        self.assertFalse(notification_service._should_notify("Omar"))

    @mock.patch.object(notification_service, "NOTIFY_COOLDOWN_SECONDS", 0)
    def test_zero_cooldown_always_allows(self):
        self.assertTrue(notification_service._should_notify("Omar"))
        self.assertTrue(notification_service._should_notify("Omar"))

    @mock.patch.object(notification_service, "NOTIFY_COOLDOWN_SECONDS", 300)
    def test_cooldown_is_per_person(self):
        self.assertTrue(notification_service._should_notify("Omar"))
        self.assertTrue(notification_service._should_notify("Mohammad"))


class EnabledAndRecipientsTests(unittest.TestCase):
    @mock.patch.object(notification_service, "SMTP_HOST", "smtp.example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_FROM", "cam@example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_TO", "alerts@example.com")
    def test_enabled_when_configured(self):
        self.assertTrue(notification_service.notifications_enabled())

    @mock.patch.object(notification_service, "SMTP_HOST", "")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_FROM", "cam@example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_TO", "alerts@example.com")
    def test_disabled_when_host_missing(self):
        self.assertFalse(notification_service.notifications_enabled())

    @mock.patch.object(notification_service, "NOTIFY_EMAIL_TO", "a@example.com, b@example.com ,c@example.com")
    def test_recipients_parses_comma_separated_list(self):
        self.assertEqual(
            notification_service._recipients(),
            ["a@example.com", "b@example.com", "c@example.com"],
        )


class SendEmailTests(unittest.TestCase):
    @mock.patch.object(notification_service, "SMTP_HOST", "smtp.example.com")
    @mock.patch.object(notification_service, "SMTP_PORT", 587)
    @mock.patch.object(notification_service, "SMTP_USERNAME", "user")
    @mock.patch.object(notification_service, "SMTP_PASSWORD", "secret")
    @mock.patch.object(notification_service, "SMTP_USE_TLS", True)
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_FROM", "cam@example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_TO", "alerts@example.com")
    @mock.patch.object(notification_service.smtplib, "SMTP")
    def test_send_email_logs_in_and_sends(self, mock_smtp_cls):
        server = mock_smtp_cls.return_value.__enter__.return_value

        notification_service._send_email("Omar", 0.73)

        mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=15)
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("user", "secret")
        server.send_message.assert_called_once()

        sent_message = server.send_message.call_args.args[0]
        self.assertEqual(sent_message["From"], "cam@example.com")
        self.assertEqual(sent_message["To"], "alerts@example.com")
        self.assertIn("Omar", sent_message["Subject"])

    @mock.patch.object(notification_service, "SMTP_USE_TLS", False)
    @mock.patch.object(notification_service, "SMTP_USERNAME", "")
    @mock.patch.object(notification_service, "SMTP_PASSWORD", "")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_FROM", "cam@example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_TO", "alerts@example.com")
    @mock.patch.object(notification_service.smtplib, "SMTP")
    def test_send_email_skips_tls_and_login_when_not_configured(self, mock_smtp_cls):
        server = mock_smtp_cls.return_value.__enter__.return_value

        notification_service._send_email("Omar", 0.51)

        server.starttls.assert_not_called()
        server.login.assert_not_called()
        server.send_message.assert_called_once()

    @mock.patch.object(notification_service, "NOTIFY_EMAIL_FROM", "cam@example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_TO", "alerts@example.com")
    @mock.patch.object(notification_service.smtplib, "SMTP", side_effect=OSError("boom"))
    def test_send_email_swallows_errors(self, _mock_smtp_cls):
        # Should not raise even if the SMTP server is unreachable.
        notification_service._send_email("Omar", 0.9)


class NotifyIfTargetSeenTests(unittest.TestCase):
    def setUp(self):
        notification_service._last_notified_at.clear()

    @mock.patch.object(notification_service, "NOTIFY_PERSON_NAME", "Omar")
    @mock.patch.object(notification_service, "SMTP_HOST", "smtp.example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_FROM", "cam@example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_TO", "alerts@example.com")
    @mock.patch.object(notification_service, "_send_in_background")
    def test_notifies_for_matching_target_case_insensitive(self, mock_send):
        notification_service.notify_if_target_seen([("omar", 0.8)])
        mock_send.assert_called_once_with("omar", 0.8)

    @mock.patch.object(notification_service, "NOTIFY_PERSON_NAME", "Omar")
    @mock.patch.object(notification_service, "SMTP_HOST", "smtp.example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_FROM", "cam@example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_TO", "alerts@example.com")
    @mock.patch.object(notification_service, "_send_in_background")
    def test_ignores_non_target_people(self, mock_send):
        notification_service.notify_if_target_seen([("Mohammad", 0.95), ("Anonymous", 0.1)])
        mock_send.assert_not_called()

    @mock.patch.object(notification_service, "NOTIFY_PERSON_NAME", "Omar")
    @mock.patch.object(notification_service, "NOTIFY_COOLDOWN_SECONDS", 300)
    @mock.patch.object(notification_service, "SMTP_HOST", "smtp.example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_FROM", "cam@example.com")
    @mock.patch.object(notification_service, "NOTIFY_EMAIL_TO", "alerts@example.com")
    @mock.patch.object(notification_service, "_send_in_background")
    def test_cooldown_limits_repeated_sightings(self, mock_send):
        notification_service.notify_if_target_seen([("Omar", 0.8)])
        notification_service.notify_if_target_seen([("Omar", 0.8)])
        self.assertEqual(mock_send.call_count, 1)

    @mock.patch.object(notification_service, "NOTIFY_PERSON_NAME", "Omar")
    @mock.patch.object(notification_service, "SMTP_HOST", "")
    @mock.patch.object(notification_service, "_send_in_background")
    def test_no_send_when_notifications_disabled(self, mock_send):
        notification_service.notify_if_target_seen([("Omar", 0.8)])
        mock_send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
