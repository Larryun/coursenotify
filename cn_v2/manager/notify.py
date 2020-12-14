from string import Template

from cn_v2.manager.base import BaseManager
from cn_v2.util.email import *


class NotifyManger(BaseManager):

    def __init__(self, config_file, school, log_path="../data/notify.log", cursor=None):
        super(NotifyManger, self).__init__(config_file, school, cursor=cursor)
        self.logger.name = "NotifyManager-%s" % school
        self.logger.add_file_handler(log_path)
        self.email_client = None
        self.logger.debug("Finish initializing %s" % self.logger.name)

    def send_email(self, email):
        self.__get_email_client().send_email(email)
        self.logger.info("Sent email from %s to %s" % (email.sent_from, email.to))

    def send_notification_email(self, remove_key, course, recipient_email):
        """
        Send email
        :param remove_key: remove key
        :param course: course dict
        :param recipient_email:
        :return:
        """
        email = self.compose_notify_email(remove_key, course, recipient_email)
        self.send_email(email)

    def send_confirmation_email(self, remove_key, course, recipient_email):
        email = self.compose_conformation_email(remove_key, course, recipient_email)
        self.send_email(email)

    def compose_email(self, subject, content, template, recipient_email):
        self.logger.debug("Rendering email template %s" % template)
        # render email template
        body = self.__render_email_template(template, content)
        return Email(self.config["email"]["username"], recipient_email, subject, body)

    def compose_notify_email(self, remove_key, course, recipient_email, template="", subject=""):
        """
        Composes notification email that render template with some specific content
        :param remove_key: remove key
        :param course: course dict
        :param recipient_email:
        :param template: email template to render, default is notify_email
        :param subject: subject of the email
        :return: composed Email object
        """
        template = self.config["email"]["template"][template or "notify"]
        subject = subject or "%s Class Notification" % self.school

        remove_url = self.config["host-url"] + ("/%s/remove/%s" % (self.school.lower(), remove_key))
        content = {"status": course["status"],
                   "classname": course["name"],
                   "remove_url": remove_url,
                   "crn": course["crn"], }
        return self.compose_email(subject, content, template, recipient_email)

    def compose_conformation_email(self, remove_key, course, recipient_email):
        subject = "%s CourseNotify Confirmation" % self.school
        return self.compose_notify_email(remove_key, course, recipient_email, "confirm", subject)

    @staticmethod
    def __render_email_template(email_template, content):
        """
        Render a email template with the given content
        :param email_template: path to email template
        :param content: a dict, content to be substituted
        :return: rendered email in str
        """
        with open(email_template) as f:
            return Template(f.read()).substitute(content)

    def __get_email_client(self):
        if self.email_client is None:
            self.email_client = GmailAccount(self.config["email"]["username"], self.config["email"]["pass"])
        return self.email_client