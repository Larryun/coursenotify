import unittest
import string
import random

from cn_v2.manager.course import *
from cn_v2.manager.watcher import *
from cn_v2.exception import *

CONFIG_FILE = "../config/test.yaml"


class TestCourseManager(unittest.TestCase):

    def test_run(self):
        m = CourseManager(CONFIG_FILE, BaseManager.DA)

    def test_update_course_collection(self):
        m = CourseManager(CONFIG_FILE, BaseManager.DA)
        original_count = m.course_cc.count_documents({})
        original_id = m.course_cc.find_one({"crn": "37067"})["_id"]
        original = m.course_cc.find_one({"crn": "37067"})["class_time"]
        m.course_cc.update_one(
            {"crn": "37067"},
            {"$set": {"class_time": "IDFK"}}
        )

        self.assertEqual(m.course_cc.find_one({"crn": "37067"})["class_time"], "IDFK")
        m.update_course_collection()
        self.assertEqual(m.course_cc.find_one({"crn": "37067"})["_id"], original_id)
        self.assertEqual(m.course_cc.find_one({"crn": "37067"})["class_time"], original)
        self.assertEqual(m.course_cc.count_documents({}), original_count)


class TestWatcherManager(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestWatcherManager, self).__init__(*args, **kwargs)
        school = BaseManager.DA
        self.watcher_m = WatcherManager(CONFIG_FILE, school)
        self.course_m = CourseManager(CONFIG_FILE, school)
        # self.course_m.update_course_collection()

    def get_random_crn(self, size):
        return [x["crn"] for x in self.course_m.course_cc.aggregate([{"$sample": {"size": size}}])]

    @staticmethod
    def get_random_email(size):
        email_length = 10
        letters = string.ascii_lowercase
        results = []
        for i in range(size):
            results.append("".join(random.choice(letters) for j in range(email_length)) + "@gmail.com")
        return results

    def drop_watchers(self, emails):
        self.watcher_m.watcher_cc.delete_many({"email_addr": {"$in": emails}})

    def test_add_watchee(self):
        emails = self.get_random_email(1)
        crns = self.get_random_crn(20)
        add_operation = 100
        expected = {}
        count = 0
        while count < add_operation:
            r = random.choice(emails)
            c = random.choice(crns)
            if r not in expected:
                expected[r] = {c}
            else:
                expected[r].add(c)
            count += 1

        for k in expected.keys():
            self.watcher_m.add_all_watchee(k, expected[k])

        for email in emails:
            if email not in expected or len(expected[email]) == 0:
                continue
            result_crn = set(
                [x["course_obj_id"] for x in self.watcher_m.watcher_cc.find_one({"email_addr": email})["crn"]])
            expected_crn = set([self.watcher_m.find_course_by_crn(x)["_id"] for x in expected[email]])
            self.assertEqual(result_crn, expected_crn)

        self.drop_watchers(emails)



class TestWatchManager_(unittest.TestCase):

    def __init__(self, *argv, **kwargs):
        super(TestWatchManager_, self).__init__(*argv, **kwargs)
        school = BaseManager.DA
        self.watcher = WatcherManager(CONFIG_FILE, school)
        self.course_manager = CourseManager(CONFIG_FILE, school)
        self.email_list = ["test1@gmail.com", "test2@gmail.com"]
        self.crn_list_1 = self.get_random_crn(2)
        self.crn_list_2 = self.get_random_crn(2)
        self.crn_list_3 = self.get_random_crn(2)
        self.crn_list_4 = self.get_random_crn(2)

    def test(self):
        self.add_test_watch()

    def get_random_crn(self, size):
        return [x["crn"] for x in self.course_manager.course_cc.aggregate([{"$sample": {"size": size}}])]

    def print_test_message(self, msg):
        print("[TEST] %s", msg)

    def add_test_watch(self):
        self.watcher.add_watchee(self.crn_list_1, self.email_list[0])
        self.watcher.add_watchee(self.crn_list_2, self.email_list[0])
        self.watcher.add_watchee(self.crn_list_3, self.email_list[1])
        self.watcher.add_watchee(self.crn_list_4, self.email_list[1])
        res = list(self.watcher.watcher_cc.find({"$or":
                                                     [{"email_addr": x} for x in self.email_list]
                                                 }))
        return res

    def remove_test_watch(self):
        self.watcher.watcher_cc.delete_many({"email_addr": {"$in": self.email_list}})

    def test_add_watch(self):
        crn = ['40750', '40415', '40996', '41150']

        res = self.add_test_watch()
        self.assertEqual(len(res), 2)

        self.watcher.add_watchee(self.crn_list_4, self.email_list[1])
        self.assertEqual(len(res[0]['crn']), 4)
        self.assertEqual(len(res[1]['crn']), 4)
        self.remove_test_watch()

    def test_remove_watch(self):
        self.add_test_watch()

        first_watch_obj = list(self.watcher.get_watch(self.email_list[0]))[0]
        first_watchee = first_watch_obj["crn"][0]
        self.assertFalse(first_watchee["removed"])

        crn = self.watcher.course_c.find_one({"_id": first_watchee["course_obj_id"]})["crn"]
        self.watcher.remove_watch(crn, self.email_list[0])

        first_watch_obj = list(self.watcher.get_watch(self.email_list[0]))[0]
        first_watchee = first_watch_obj["crn"][0]
        self.assertTrue(first_watchee["removed"])

        self.watcher.remove_watch(crn, self.email_list[0])
        first_watch_obj = list(self.watcher.get_watch(self.email_list[0]))[0]
        first_watchee = first_watch_obj["crn"][0]
        self.assertTrue(first_watchee["removed"])

        crn = self.watcher.course_c.find_one({"_id": first_watchee["course_obj_id"]})

        self.remove_test_watch()

    def test_get_watch(self):
        self.add_test_watch()
        # Test regular get watch
        res = list(self.watcher.get_watch(self.email_list[0]))
        self.assertEqual(len(res[0]['crn']), 4)
        # remove all crn
        self.remove_test_watch()
        # Test get watch when watch_list is empty
        res = list(self.watcher.get_watch(self.email_list[0]))
        self.assertEqual(len(res), 0)
        self.remove_test_watch()

    def test_crn_not_found_exception(self):
        self.add_test_watch()
        # Test CrnNotFound exception
        self.assertRaises(CRNNotFound, self.watcher.remove_watch, ["00001", "00000"], self.email_list[0])
        self.remove_test_watch()

    def test_email_not_found_exception(self):
        self.add_test_watch()
        # Test EmailNotFound exception
        self.assertRaises(CRNNotFound, self.watcher.remove_watch, self.crn_list_1[0], "notandemail")
        self.remove_test_watch()

    def test_update_last_notify(self):
        self.add_test_watch()
        # Pick the first watch_obj from watch_list_collection
        watch_obj = self.watcher.watcher_c.find_one({"email_addr": self.email_list[0]})
        # Mark last_notify time before update
        datetime_1 = watch_obj["crn"][0]["last_notify"].replace(microsecond=0)
        crn_id = watch_obj["crn"][0]["course_obj_id"]

        # update now
        new_time = self.watcher.update_last_notify(watch_obj["_id"], crn_id, new_status="Full")

        # get current time
        datetime_2 = new_time.replace(microsecond=0)
        self.assertTrue(datetime_1 != datetime_2)

        watch_obj = self.watcher.watcher_c.find_one({"email_addr": self.email_list[0]})
        self.assertTrue(watch_obj["crn"][0]["last_notify_status"], "Full")

        self.watcher.update_last_notify(watch_obj["_id"], crn_id, new_status="Waitlist")
        watch_obj = self.watcher.watcher_c.find_one({"email_addr": self.email_list[0]})
        self.assertTrue(watch_obj["crn"][0]["last_notify_status"], "Waitlist")

        self.watcher.update_last_notify(watch_obj["_id"], crn_id, new_status="Open")
        watch_obj = self.watcher.watcher_c.find_one({"email_addr": self.email_list[0]})
        self.assertTrue(watch_obj["crn"][0]["last_notify_status"], "Open")

        self.remove_test_watch()

    def test_check(self):
        # self.add_test_watch()
        test_course = {"status": "Full",
                       "name": "TEST_COURSE"}
        test_watchee = {"course_obj_id": 123,
                        "removed": False,
                        "last_notify_status": ""}

        self.assertFalse(self.watcher.check(test_course, test_watchee))
        test_watchee["last_notify_status"] = "Full"

        test_course["status"] = "Waitlist"
        self.assertTrue(self.watcher.check(test_course, test_watchee))
        test_watchee["last_notify_status"] = "Waitlist"

        test_course["status"] = "Open"
        self.assertTrue(self.watcher.check(test_course, test_watchee))
        test_watchee["last_notify_status"] = "Open"

        test_course["status"] = "Full"
        self.assertFalse(self.watcher.check(test_course, test_watchee))
        test_watchee["last_notify_status"] = "Full"

        test_watchee["removed"] = True
        self.assertFalse(self.watcher.check(test_course, test_watchee))

        test_course["status"] = "Waitlist"
        test_watchee["removed"] = True
        self.assertFalse(self.watcher.check(test_course, test_watchee))

        test_watchee["removed"] = False
        test_course["status"] = "Waitlist"
        self.assertTrue(self.watcher.check(test_course, test_watchee))
        test_watchee["status"] = "Waitlist"

    def test_find_and_remove_by_remove_key(self):
        self.add_test_watch()
        first_watch_obj = list(self.watcher.get_watch(self.email_list[0]))[0]
        first_watchee = first_watch_obj["crn"][0]
        self.assertFalse(first_watchee["removed"])

        remove_key = first_watchee["remove_key"]
        self.watcher.remove_watch_by_remove_key(remove_key)

        first_watch_obj = list(self.watcher.get_watch(self.email_list[0]))[0]
        first_watchee = first_watch_obj["crn"][0]

        self.assertTrue(first_watchee["removed"])
        self.remove_test_watch()

    def test_is_crn_exists(self):
        self.add_test_watch()
        a_very_random_crn = "123"
        self.assertFalse(self.watcher.is_crn_exists(a_very_random_crn))
        a_crn_in_db = next(self.watcher.course_c.find({}))["crn"]
        self.assertTrue(self.watcher.is_crn_exists(a_crn_in_db))
        self.remove_test_watch()


if __name__ == "__main__":
    unittest.main()
