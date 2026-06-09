import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from services.email.config import Config


class SmtpSendError(Exception):
    pass


def send_email(
    *,
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> None:
    message = MIMEMultipart("alternative")
    message["From"] = Config.GMAIL_FROM
    message["To"] = to
    message["Subject"] = subject

    plain = text_body or _html_to_plain(html_body)
    message.attach(MIMEText(plain, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(Config.GMAIL_USER, Config.GMAIL_APP_PASSWORD)
            smtp.sendmail(Config.GMAIL_FROM, [to], message.as_string())
    except smtplib.SMTPException as exc:
        raise SmtpSendError("Failed to send email.") from exc


def _html_to_plain(html: str) -> str:
    return html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
