import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import os
from dotenv import load_dotenv

load_dotenv()  # loads .env file into environment


def send_mail(text, to, cc):
    # send the email
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.ehlo()
        server.login(
            os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_PASSWORD")
        )
        # sending the mail
        server.sendmail(
            os.environ.get("GMAIL_USER"),
            to.split(";") + cc.split(";"),
            text,
        )

        # terminating the session
        server.quit()
        print("  Success!")
        return True
    except Exception as e:
        print("  Something went wrong: %s" % e)
        return False


class Email:
    def __init__(
        self, to, subject, cc="", body="", actually_send=True, attach=[]
    ):
        self.ACTUALLY_SEND = actually_send
        self.RECP_LIST = to
        self.CC_LIST = cc
        self.subject = subject
        self.body = body
        self.attach = attach

    def set_body(self, body):
        self.body = body

    def send_email(self):
        # instance of MIMEMultipart
        msg = MIMEMultipart()

        msg["From"] = "robot@intwineconnect.com"
        msg["To"] = self.RECP_LIST
        msg["Cc"] = self.CC_LIST
        msg["Subject"] = self.subject

        print("Generating email to: %s" % self.RECP_LIST)

        # attach the body with the msg instance
        msg.attach(MIMEText(self.body, "plain"))

        filename = self.attach
        f, clean = (filename, filename)
        attachment = open(f, "rb")

        # instance of MIMEBase and named as p
        p = MIMEBase("application", "octet-stream")

        # To change the payload into encoded form
        p.set_payload(attachment.read())

        # encode into base64
        encoders.encode_base64(p)

        p.add_header("Content-Disposition", "attachment; filename= %s" % clean)
        # attach the instance 'p' to instance 'msg'
        msg.attach(p)

        # Converts the Multipart msg into a string
        text = msg.as_string()

        if self.ACTUALLY_SEND:
            print("  Sending...")
            return send_mail(text, self.RECP_LIST, self.CC_LIST)
        else:
            print("Intentionally not sent!")
            return False
