import smtplib
import sys
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _require_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

# Get the receiver email and the code from command line arguments
receiver_email = sys.argv[1]
code = sys.argv[2]

# Define the email subject and the body of the email
subject = "Reset password link from DofE Journey Tracker"
message = f"""\
Click the button below to reset your password:<br><br>
<a href='http://127.0.0.1:5000/email-confirm/{code}' style='
background-color: #4CAF50;
border: none;
color: white;
padding: 15px 32px;
text-align: center;
text-decoration: none;
display: inline-block;
font-size: 16px;
margin: 4px 2px;
cursor: pointer;'>Reset Password</a><br><br>
Please do not share this link with anybody. This link will expire in 15 minutes.
This action cannot be reversed.
"""

# Create the MIMEMultipart message container
msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = _require_env("SMTP_USERNAME")
msg['To'] = receiver_email

# Create the plain text version of the email body
plain_text_message = f"""\
Click the link below to reset your password:

http://127.0.0.1:5000/email-confirm/{code}

Please do not share this link with anybody. This link will expire in 15 minutes.
This action cannot be reversed.
"""

# Attach both plain text and HTML parts to the message
msg.attach(MIMEText(plain_text_message, 'plain'))
msg.attach(MIMEText(message, 'html'))

# Establish connection with the SMTP server
server = smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587")))
server.starttls()
server.login(_require_env("SMTP_USERNAME"), _require_env("SMTP_PASSWORD"))

# Send the email
server.sendmail(_require_env("SMTP_USERNAME"), receiver_email, msg.as_string())

# Quit the server
server.quit()
