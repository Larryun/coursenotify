from string import Template

from cn_v2.exception import *
from cn_v2.manager.base import BaseManager
from cn_v2.parser.model import *
from cn_v2.parser.model import gen_md5_key
from cn_v2.util.email import GmailAccount


class WatcherManager(BaseManager):
    FULLED = "Full"
    WAITLIST = "Waitlist"
    OPEN = "Open"

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
        # self.logger.debug(result)
        # if result is None:
        #     return None
        # else:
        #     return result
        return result or None

    def __update_watchee_status(self, email, course_id, new_status):
        set_query = {"crn.$[course]." + k: new_status[k] for k in new_status.keys()}
        # self.logger.debug(set_query)
        self.watcher_cc.update_one({"email_addr": email},
                                   {"$set": set_query},
                                   array_filters=[{"course.course_obj_id": course_id}])

    def update_watchee_notify_status(self, email, course_id, notify_status):
        new_time = datetime.now()
        self.__update_watchee_status(email, course_id, {
            "notify_status": notify_status,
            "notify_time": new_time
        })

    def reset_watchee_status(self, email, course_id):
        self.__update_watchee_status(email, course_id, {
            "notify_status": "",
            "removed": False,
            "remove_key": gen_md5_key(12345),
        })

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

    def find_not_removed_watchee(self, email):
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

    def __check_notify_status(self, watchee, current_status):
        if watchee["removed"] or current_status == self.FULLED or current_status == watchee["notify_status"]:
            return False
        elif current_status == self.OPEN or current_status == self.WAITLIST:
            return True
        else:
            return False

    def notify(self, email):
        notify_course = self.find_not_removed_watchee(email)
        notified_count = 0
        for i in notify_course:
            course = self.find_course_by_id(i["course_obj_id"])
            current_status = course["status"]
            if self.__check_notify_status(i, current_status):
                self.update_watchee_notify_status(email, i["course_obj_id"], current_status)
                self.logger.info("Notify %s for course %s" % (email, i["course_obj_id"]))
                notified_count += 1
        return notified_count
