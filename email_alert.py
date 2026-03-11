import smtplib
from email.mime.text import MIMEText
from config import EMAIL_ALERT


def send_email(parent_email, student_name, attendance):

    if not EMAIL_ALERT:
        return

    sender = "charanichowdaryaetukuri@gmail.com"
    password = "ggrl mxic jzgs pnga"

    message = f"""
    Low Attendance Alert

    Student: {student_name}
    Attendance: {attendance}%

    Please ensure regular attendance.
    """

    msg = MIMEText(message)

    msg["Subject"] = "Student Attendance Alert"
    msg["From"] = sender
    msg["To"] = parent_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()

        print("Email sent")

    except Exception as e:
        print("Email error:", e)
