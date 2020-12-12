from string import Template

from cn_v2.exception import *
from cn_v2.manager.base import BaseManager
from cn_v2.manager.course import CourseManager
from cn_v2.parser.model import *
from cn_v2.parser.model import gen_md5_key
from cn_v2.util.email import GmailAccount, Email


class WatcherManager(BaseManager):
    FULLED = "Full"
    WAITLIST = "Waitlist"
    OPEN = "Open"

    def __init__(self, config_file, school, log_path="../data/watcher.log", cursor=None):
        super(WatcherManager, self).__init__(config_file, school)
        self.logger.name = "WatcherManager-%s" % school
        self.logger.add_file_handler(log_path)
        self.course_manger = CourseManager(config_file, school, cursor=self.cursor)

        self.email_client = None

    def get_watcher(self, email):
        """
        Retrieve watchers by email
        :param email: email address
        :return: list of watchers
        """
        self.logger.debug("Querying all watchee of %s" % email)
        return list(self.watcher_cc.find({"email_addr": email}))

    def __update_watchee_status(self, email, course_id, new_status):
        """
        Update a watchee's  status (Ex. notify_status/notify_time... etc)
        :param email: watcher's email
        :param course_id: course id
        :param new_status: a dict of new status
        :return:
        """
        set_query = {"crn.$[course]." + k: new_status[k] for k in new_status.keys()}
        # self.logger.debug(set_query)
        self.watcher_cc.update_one({"email_addr": email},
                                   {"$set": set_query},
                                   array_filters=[{"course.course_obj_id": course_id}])

    def update_watchee_notify_status(self, email, course_id, notify_status):
        """
        Update watchee notify_status and notify_time to current time
        :param email: watcher's email
        :param course_id: course id
        :param notify_status: status of the last notification(Open/Waitlist/Closed)
        :return:
        """
        new_time = datetime.now()
        self.__update_watchee_status(email, course_id, {
            "notify_status": notify_status,
            "notify_time": new_time
        })

    def reset_watchee_status(self, email, course_id):
        """
        Reset watchee notify_status, notify_time to current time and assign a new remove key
        :param email: watcher's email
        :param course_id: course id
        :return:
        """
        self.__update_watchee_status(email, course_id, {
            "notify_status": "",
            "removed": False,
            "remove_key": gen_md5_key(course_id),
        })

    def add_all_watchee(self, email, crn_list):
        """
        add watchees by list of crns to a watcher with given email
        :param email: watcher email
        :param crn_list: array of crns to be added
        :return:
        """
        for crn in crn_list:
            self.add_watchee(email, crn)

    def add_watchee(self, email, crn):
        """
        add a watchee with given crn to a watcher
        :param email: watcher email
        :param crn: crn (Ex. 31234)
        :return:
        """
        course_id = self.course_manger.find_course_by_crn(crn)["_id"]
        watchee = WatcheeDocument(course_id)
        if self.watcher_cc.count_documents({"email_addr": email, "crn.course_obj_id": course_id}) == 0:
            self.logger.info("Add watchee %s to watcher %s" % (course_id, email))
            self.watcher_cc.update_one({"email_addr": email},
                                       {"$push": {"crn": watchee.__dict__}},
                                       upsert=True)
        else:
            self.logger.info("Watchee %s already exists in watcher %s" % (course_id, email))
            self.reset_watchee_status(email, course_id)

    # TODO: add test
    def remove_watchee_by_remove_key(self, remove_key):
        """
        Remove a watchee by a remove_key, raise RemoveKeyNotFound when the remove cannot
        be found in any watchee
        :param remove_key: remove_key
        :return:
        """
        res = self.watcher_cc.update_one({"crn.remove_key": remove_key},
                                         {"$set": {
                                             "crn.$[course].removed": True
                                         }},
                                         array_filters=[{"course.remove_key": remove_key}])

        if res.matched_count == 0:
            raise RemoveKeyNotFound(remove_key)
        if res.modified_count == 0:
            raise RemoveKeyUsed(remove_key)
        self.logger.info("Remove watchee with remove_key %s" % (remove_key))

    def remove_watchee_by_crn(self, email, crn):
        """
        Remove a watchee of a watcher by a crn, raise WatcheeNotFound is the watchee is not found
        :param email: watcher's email
        :param crn: crn to be removed
        :return:
        """
        course_id = self.course_manger.find_course_by_crn(crn)["_id"]
        res = self.watcher_cc.update_one({"email_addr": email},
                                         {"$set": {
                                             "crn.$[course].removed": True
                                         }},
                                         array_filters=[{"course.course_obj_id": course_id}])

        if res.matched_count == 0:
            raise WatcheeNotFound(email, crn)
        self.logger.info("Remove watchee %s from watcher %s" % (crn, email))

    def is_watchee_removed(self, email, crn):
        """
        Check if a watchee is removed
        :param email: watcher's email
        :param crn: watchee's crn
        :return: boolean
        """
        course_id = self.course_manger.find_course_by_crn(crn)["_id"]
        res = self.watcher_cc.count_documents(
            {"email_addr": email, "crn.course_obj_id": course_id, "crn.removed": True})
        return res == 1

    def find_watcher_by_email(self, email, limit=0):
        """
        Find all watchers with the given email
        :param email: watcher's email
        :param limit: the number of watchers (default is 0/no limit)
        :return: list of watchers in dict
        """
        return list(self.watcher_cc.find({"email_addr": email}).limit(limit))

    def find_not_removed_watchee(self, email):
        """
        Find all watchee that is not removed in a watcher
        :param email: watcher's email
        :return: a array of not removed watchee of the watcher
        """
        res = self.watcher_cc.aggregate([
            {"$match": {"email_addr": email}},
            {"$project": {
                "not_removed": {"$filter": {
                    "input": "$crn",
                    "as": "courses",
                    "cond": {"$eq": ["$$courses.removed", False]}
                }}
            }}
        ])
        not_removed = []
        for i in res:
            not_removed.extend(i["not_removed"])
        return not_removed

    def find_watcher_by_remove_key(self, remove_key):
        """
        Find watcher that contains the watchee with the remove_key
        :param remove_key: watchee's remove key
        :return: watcher
        """
        return self.watcher_cc.find_one({"crn.remove_key": remove_key})

    def notify(self, email):
        """
        Notify a watcher of all of the not removed watchee
        :param email: watcher's email
        :return: the count of notified watchee
        """
        notify_course = self.find_not_removed_watchee(email)
        notified_count = 0
        for i in notify_course:
            course = self.course_manger.find_course_by_id(i["course_obj_id"])
            current_status = course["status"]
            if self.__check_notify_status(i, current_status):
                self.logger.info("Notify %s for course %s" % (email, i["course_obj_id"]))
                # TODO add worker for send email
                self.send_notification_email(self.compose_notify_email(i, course, email))
                self.update_watchee_notify_status(email, i["course_obj_id"], current_status)
                notified_count += 1
        return notified_count

    def send_notification_email(self, email):
        """
        Send email
        :param email: Email object to be sent
        :return:
        """
        self.__get_email_client().send_email(email)
        self.logger.info("Sent email from %s to %s" % (email.sent_from, email.to))

    @staticmethod
    def __render_email_template(email_template, content):
        """
        Render a email template with the given content
        :param email_template: path to email template
        :param content: a dict, content to be substituted
        :return: rendered email in str
        """
        with open(email_template) as f:
            body = Template(f.read()).substitute(content)
            return body

    def __get_email_client(self):
        if self.email_client is None:
            self.email_client = GmailAccount(self.config["email"]["username"], self.config["email"]["pass"])
        return self.email_client

    def compose_notify_email(self, watchee, course, recipient_email):
        """
        Composes notification email
        :param watchee: watchee dict for remove_url
        :param course: course dict
        :param recipient_email:
        :return: composed Email object
        """
        subject = "%s Class Notification" % self.school
        remove_url = self.config["host-url"] + ("/remove/%s/%s" % (self.school.lower(), watchee["remove_key"]))

        # render email template
        content = {"status": course["status"], "classname": course["name"],
                   "remove_url": remove_url, "crn": course["crn"], }
        self.logger.debug("Rendering email template")
        body = self.__render_email_template(self.config["email"]["template"], content)
        return Email(self.config["email"]["username"], recipient_email, subject, body)

    def __check_notify_status(self, watchee, current_status):
        """
        Check whether a watchee is ready to be notified
        :param watchee: watchee dict
        :param current_status: current status of the course
        :return: boolean
        """
        # TODO: add notify time difference check
        if watchee["removed"] or current_status == self.FULLED or current_status == watchee["notify_status"]:
            return False
        elif current_status == self.OPEN or current_status == self.WAITLIST:
            return True
        else:
            return False
