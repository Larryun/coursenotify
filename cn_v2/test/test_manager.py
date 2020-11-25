import random
import string
import unittest

from cn_v2.manager.course import *
from cn_v2.manager.watcher import *

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

    def create_watcher_data(self, num_emails, num_crns):
        return self.get_random_email(num_emails), self.get_random_crn(num_crns)

    def add_test_watcher(self, num_emails, num_crns):
        emails, crns = self.create_watcher_data(num_emails, num_crns)
        expected = {}
        trial_count = int((num_emails + num_crns) / 2)
        count = 0
        while count < trial_count:
            r = random.choice(emails)
            c = random.choice(crns)
            if r not in expected:
                expected[r] = [c]
            else:
                expected[r].append(c)
            count += 1

        for k in expected.keys():
            self.watcher_m.add_all_watchee(k, expected[k])
        return emails, crns, expected

    def drop_watchers(self, emails):
        self.watcher_m.watcher_cc.delete_many({"email_addr": {"$in": emails}})

    def test_add_watchee(self):
        emails, crns, expected = self.add_test_watcher(100, 200)

        for email in expected:
            result_crn = set(
                [x["course_obj_id"] for x in self.watcher_m.watcher_cc.find_one({"email_addr": email})["crn"]]
            )
            expected_crn = set([self.watcher_m.find_course_by_crn(x)["_id"] for x in expected[email]])
            self.assertEqual(result_crn, expected_crn)

        self.drop_watchers(emails)

    def test_remove_watchee(self):
        emails, crns, expected = self.add_test_watcher(100, 200)
        remove_count = 400
        expected_removed = {}
        for i in range(remove_count):
            email = random.choice(list(expected.keys()))
            crn = random.choice(list(expected[email]))
            if email not in expected_removed:
                expected_removed[email] = [crn]
            else:
                expected_removed[email].append(crn)

        for k in expected_removed:
            for c in expected_removed[k]:
                self.watcher_m.remove_watchee_by_crn(k, c)
                self.assertTrue(self.watcher_m.is_watchee_removed(k, c))

        self.drop_watchers(emails)

    def test_notify(self):
        emails, crns, expected = self.add_test_watcher(200, 600)
        random_emails = {random.choice(emails) for _ in range(20)}
        for email in random_emails:
            self.watcher_m.notify(email)


if __name__ == "__main__":
    unittest.main()
