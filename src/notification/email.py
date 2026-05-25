import datetime as dt
import smtplib
from email.message import EmailMessage
import mimetypes
from pathlib import Path


def is_workday(date: dt.date | None = None) -> bool:
    """Return True if it's a workday (Tue–Sat in your logic)."""
    if date is None:
        date = dt.date.today()
    return date.weekday() not in [6, 0]  # Sunday=6, Monday=0


def _send_email_with_attachment(
    file_path: str,
    subject: str,
    body: str,
    sender_email: str,
    receiver_email: str,
    password: str,
) -> None:
    """Handle only email sending logic."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content(body)

    file_path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)

    if mime_type is None:
        mime_type = "application/octet-stream"

    maintype, subtype = mime_type.split("/")

    with open(file_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype=maintype,
            subtype=subtype,
            filename=file_path.name,
        )

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(sender_email, password)
        smtp.send_message(msg)


def email_notify(file_path: str) -> None:
    """Orchestrator function."""
    today = dt.date.today()
    if not is_workday(today):
        return

    print(f"Sending email because today ({today}) is a workday")
    _send_email_with_attachment(
        file_path=file_path,
        subject=f"Daily Report - {today}",
        body="Hi Boss,\n\nPlease find the attached report.\n",
        sender_email="lilmissmj.0606@gmail.com",
        receiver_email="stan.mng@gmail.com",
        password="fwkm pglp ggjv olcn",
    )
