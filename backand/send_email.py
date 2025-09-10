import smtplib
from email.message import EmailMessage
import os





USERNAME = os.getenv("USERNAME", "fallback_secret_key")
PASSWORD = os.getenv("PASSWORD", "HS256")


def send_email(user_name: str, user_email: str, link: str):

    smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp_server.login(USERNAME, PASSWORD)

    msg = EmailMessage()
    msg['Subject'] = 'Test Email from Python'
    msg['From'] = USERNAME
    msg['To'] = user_email
    msg.set_content(f"Hello {user_name}, your verify link is:\n{link}")

    smtp_server.send_message(msg)
    smtp_server.quit()

    print(f"✅Verification email sent to {user_email}")



