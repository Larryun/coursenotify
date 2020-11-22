import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from cn_v2.util.logger import BasicLogger


class GmailAccount:

    def __init__(self, gmail, password):
        self.gmail = gmail
        self.password = password
        self.logger = BasicLogger("Gmail Account")
        self.server = None
        self.connect_server()
        self.login()

    def connect_server(self):
        try:
            self.server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            self.server.ehlo()
            self.logger.info("SMTP server connected")
        except Exception as e:
            self.logger.error("SMTP server connection failed")

    def login(self):
        self.logger.debug("Logging to email server")
        self.server.login(self.gmail, self.password)
        self.logger.info("Login succeed")

    def send_email(self, email):
        # TODO: Add threading
        sent_from, to, content = email.sent_from, email.to, email.content()
        self.server.sendmail(sent_from, to, content)
        self.logger.info("Email sent to %s" % to)

    def close(self):
        self.server.close()
        self.logger.debug("Connection closed")

    def __del__(self):
        self.close()


class Email:
    def __init__(self, sent_from, to, subject="", body=""):
        self.body = body
        self.subject = subject
        self.to = to
        self.sent_from = sent_from
        self.msg = ""

    def content(self):
        self.msg = MIMEMultipart("alternative")
        self.msg["Subject"] = self.subject
        self.msg["From"] = self.sent_from
        self.msg["To"] = self.to
        self.body = MIMEText(self.body, 'html')
        self.msg.attach(self.body)
        return self.msg.as_string()


# Test
if __name__ == "__main__":
    gmail_user = ""
    gmail_password = ""

    subject = "<Test> Class Notification"
    body = "<Test>Class Current Status: --"

    gmail_account = GmailAccount(gmail_user, gmail_password)
    email1 = Email(gmail_user, gmail_user, subject, body)
    # gmail_account.send_email(email1)
