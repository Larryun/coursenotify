from string import Template

from cn_v2.exception import *
from cn_v2.manager.base import BaseManager
from cn_v2.parser.model import *
from cn_v2.parser.model import gen_md5_key
from cn_v2.util.email import GmailAccount


class WatcherManager(BaseManager):

    def __init__(self, config_file, school, log_path="../data/watcher.log"):
        super(WatcherManager, self).__init__(config_file, school)
        self.logger.name = "WatcherManager-%s" % school
        self.logger.add_file_handler(log_path)

    def send_email(self, email):
        gmail_account = GmailAccount(
            self.config["manager"]["email"]["username"],
            self.config["manager"]["email"]["pass"]
        )
        gmail_account.send_email(email)

    @staticmethod
    def render_email(template, content):
        with open(template) as f:
            body = Template(f.read()).substitute()
            return body

    def get_watcher(self, email):
        self.logger.debug("Querying all watchee of %s" % email)
        return list(self.watcher_cc.find({"email_addr": email}))

    def is_crn_exists(self, crn):
        return self.course_cc.count_documents({"crn": crn}) != 0

    def find_course_by_crn(self, crn):
        if self.is_crn_exists(crn):
            return self.course_cc.find_one({"crn": crn})
        else:
            self.logger.error("CRN %s not found" % crn)
            raise CRNNotFound(crn)

    def find_course_by_id(self, course_id):
        # not tested
        result = self.course_cc.find_one({"_id": course_id})
        self.logger.debug(result)
        if len(result) == 0:
            return None
        else:
            return result

    def reset_watchee_status(self, email, course_id):
        self.watcher_cc.update_one({"email_addr": email},
                                   {"$set":
                                       {
                                           "crn.$[course].last_notify_status": "",
                                           "crn.$[course].removed": False,
                                           "crn.$[course].remove_key": gen_md5_key(12345)
                                       }},
                                   array_filters=[{"course.course_obj_id": course_id}])

    def add_all_watchee(self, email, crn_list):
        for crn in crn_list:
            self.add_watchee(email, crn)

    def add_watchee(self, email, crn):
        course_id = self.find_course_by_crn(crn)["_id"]
        watchee = WatcheeDocument(course_id)
        if self.watcher_cc.count_documents({"email_addr": email, "crn.course_obj_id": course_id}) == 0:
            self.logger.info("Add watchee %s to watcher %s" % (course_id, email))
            self.watcher_cc.update_one({"email_addr": email},
                                       {"$push": {"crn": watchee.__dict__}},
                                       upsert=True)
        else:
            self.logger.info("Watchee %s already exists in watcher %s" % (course_id, email))
            self.reset_watchee_status(email, course_id)

    def remove_watchee_by_remove_key(self, email, remove_key):
        res = self.watcher_cc.update_one({"email_addr": email},
                                         {"$set": {
                                             "crn.$[course].removed": True
                                         }},
                                         array_filters=[{"course.remove_key": remove_key}])

        if res.matched_count == 0:
            raise RemoveKeyNotFound(email, remove_key)
        self.logger.info("Remove watchee with remove_key %s from watcher %s" % (remove_key, email))

    def remove_watchee_by_crn(self, email, crn):
        course_id = self.find_course_by_crn(crn)["_id"]
        res = self.watcher_cc.update_one({"email_addr": email},
                                         {"$set": {
                                             "crn.$[course].removed": True
                                         }},
                                         array_filters=[{"course.course_obj_id": course_id}])

        if res.matched_count == 0:
            raise WatcheeNotFound(email, crn)
        self.logger.info("Remove watchee %s from watcher %s" % (crn, email))

    def is_watchee_removed(self, email, crn):
        course_id = self.find_course_by_crn(crn)["_id"]
        res = self.watcher_cc.count_documents(
            {"email_addr": email, "crn.course_obj_id": course_id, "crn.removed": True})
        return res == 1
