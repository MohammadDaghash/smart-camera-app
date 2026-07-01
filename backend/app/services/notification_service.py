import smtplib
import threading
import time
from email.message import EmailMessage

from app.config import (
    NOTIFY_COOLDOWN_SECONDS,
    NOTIFY_EMAIL_FROM,
    NOTIFY_EMAIL_TO,
    NOTIFY_PERSON_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_USE_TLS,
)
from app.utils.logging import logger


_last_notified_at = {}
_cooldown_lock = threading.Lock()


def notifications_enabled():
    return bool(SMTP_HOST and NOTIFY_EMAIL_FROM and NOTIFY_EMAIL_TO)


def _recipients():
    return [address.strip() for address in NOTIFY_EMAIL_TO.split(",") if address.strip()]


def _should_notify(name):
    now = time.monotonic()

    with _cooldown_lock:
        last_sent = _last_notified_at.get(name)

        if last_sent is not None and (now - last_sent) < NOTIFY_COOLDOWN_SECONDS:
            return False

        _last_notified_at[name] = now
        return True


def _build_message(name, score):
    seen_at = time.strftime("%Y-%m-%d %H:%M:%S")

    message = EmailMessage()
    message["Subject"] = f"Smart Camera: {name} was seen on the live feed"
    message["From"] = NOTIFY_EMAIL_FROM
    message["To"] = ", ".join(_recipients())
    message.set_content(
        f"{name} was detected in the camera live feed at {seen_at} "
        f"(match score {score:.2f})."
    )

    return message


def _send_email(name, score):
    message = _build_message(name, score)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if SMTP_USE_TLS:
                server.starttls()

            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)

            server.send_message(message)

        logger.info("Sent %s notification email to %s", name, message["To"])
    except Exception as error:
        logger.error("Failed to send %s notification email: %s", name, error)


def _send_in_background(name, score):
    thread = threading.Thread(
        target=_send_email,
        args=(name, score),
        name=f"notify-{name}",
        daemon=True,
    )
    thread.start()


def notify_person_seen(name, score):
    if not notifications_enabled():
        return

    if not _should_notify(name):
        return

    logger.info("%s seen on live feed (score %.2f); sending email notification", name, score)
    _send_in_background(name, score)


def notify_if_target_seen(recognized):
    if not recognized:
        return

    target = NOTIFY_PERSON_NAME.strip().lower()

    if not target:
        return

    for name, score in recognized:
        if name.strip().lower() == target:
            notify_person_seen(name, score)


if notifications_enabled():
    logger.info(
        "Email notifications enabled for '%s' (cooldown %ss)",
        NOTIFY_PERSON_NAME,
        NOTIFY_COOLDOWN_SECONDS,
    )
else:
    logger.info("Email notifications disabled (set SMTP_HOST, NOTIFY_EMAIL_FROM, NOTIFY_EMAIL_TO to enable)")
