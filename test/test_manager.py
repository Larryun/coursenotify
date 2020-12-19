import random
import string
import unittest

from cn_v2.manager.watcher import *

CONFIG_FILE = "../config/test.yaml"


class TestCourseManager(unittest.TestCase):

    def test_run(self):
        m = CourseManager(CONFIG_FILE, BaseManager.DA)
        m.update_course_collection()

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
        self.watcher_m.watcher_cc.delete_many({})
        # self.course_m.update_course_collection()

    def get_random_crn(self, size):
        """
        Generate random crn by sampling from the current crn db
        :param size: number of crns
        :return: array of random crn
        """
        return [x["crn"] for x in self.course_m.course_cc.aggregate([{"$sample": {"size": size}}])]

    @staticmethod
    def get_random_email(size):
        """
        Generate random emails with random letters + @gmail.com
        :param size: number of random emails
        :return: array of random emails
        """
        email_length = 10
        letters = string.ascii_lowercase
        results = []
        for i in range(size):
            results.append("".join(random.choice(letters) for j in range(email_length)) + "@gmail.com")
        return results

    def remove_random_watchee(self, data, count):
        """
        Remove random watchee in the set of given data
        :param data: the set of watcher data to be remove randomly
        :param count: the number of watchee to remove
        :return: a dict of removed watcher_email -> array of crns
        """
        removed = {}
        for i in range(count):
            email = random.choice(list(data.keys()))
            crn = random.choice(list(data[email]))
            if email not in removed:
                removed[email] = [crn]
            else:
                removed[email].append(crn)

        # remove
        for watcher_email in removed:
            for crn in removed[watcher_email]:
                self.watcher_m.remove_watchee_by_crn(watcher_email, crn)
        return removed

    def create_watcher_data(self, num_emails, num_crns):
        """
        Generate random emails and crn
        :param num_emails:
        :param num_crns:
        :return: array of random emails, array of random crns
        """
        return self.get_random_email(num_emails), self.get_random_crn(num_crns)

    def add_test_watcher(self, num_watchers):
        """
        Add the random watchers from the sets of emails and crn with the random emails and crns to the db
        :param num_watchers:
        :return: array of dict of added watchers
        """
        num_emails = num_watchers * 2
        num_crns = num_watchers * 3
        emails, crns = self.create_watcher_data(num_emails, num_crns)
        expected = {}
        count = 0
        # building expected data
        while count < num_watchers:
            r = random.choice(emails)
            c = random.choice(crns)
            if r not in expected:
                expected[r] = [c]
            else:
                expected[r].append(c)
            count += 1

        # add expected data to db
        for k in expected.keys():
            self.watcher_m.add_all_watchee(k, expected[k])
        return expected

    def drop_watchers(self, emails):
        """
        Drop all watchers within the array of emails
        :param emails: email of the watchers to drop
        :return:
        """
        self.watcher_m.watcher_cc.delete_many({"email_addr": {"$in": emails}})

    def test_add_watchee(self):
        """
        Add random watchers to db then check if the added courses are same as expected
        :return:
        """
        expected = self.add_test_watcher(100)

        for email in expected:
            result_crn = set(
                [x["course_obj_id"] for x in self.watcher_m.watcher_cc.find_one({"email_addr": email})["crn"]]
            )
            expected_crn = set([self.course_m.find_course_by_crn(x)["_id"] for x in expected[email]])
            self.assertEqual(result_crn, expected_crn)

        self.drop_watchers(list(expected.keys()))

    def test_remove_watchee(self):
        """
        Add random watchers then check if the removed is actually removed
        :return:
        """
        added = self.add_test_watcher(200)
        remove_count = 400
        removed = self.remove_random_watchee(added, remove_count)
        # assert True is watchee in expected_removed
        # assert False is not in expected_removed
        for watcher_email in removed:
            watchee = self.watcher_m.find_watcher_by_email(watcher_email, limit=1)[0]["crn"]
            for w in watchee:
                crn = self.course_m.find_course_by_id(w["course_obj_id"])["crn"]
                if w in removed[watcher_email]:
                    self.assertTrue(self.watcher_m.is_watchee_removed(watcher_email, crn))
                else:
                    self.assertFalse(not self.watcher_m.is_watchee_removed(watcher_email, crn))

        self.drop_watchers(list(added.keys()))

    def test_find_not_removed_watchee(self):
        """
        Add random watchers then remove randomly and test find_not_removed_watchee is return correclty
        """
        added = self.add_test_watcher(100)
        removed = self.remove_random_watchee(added, 50)
        for email in added:
            for crn in added[email]:
                if email not in removed:
                    self.assertFalse(self.watcher_m.is_watchee_removed(email, crn))
                else:
                    self.assertTrue(self.watcher_m.is_watchee_removed(email, crn))
        self.drop_watchers(list(added.keys()))

    def test_get_emails(self):
        added = self.add_test_watcher(100)

        self.assertEqual(len(added.keys()), len(self.watcher_m.get_emails()))
        self.drop_watchers(list(added.keys()))


def test_notify(self):
    # expected = self.add_test_watcher(200)
    # random_emails = {random.choice(list(expected.keys())) for _ in range(20)}
    # for email in random_emails:
    self.watcher_m.add_all_watchee("lerryun@gmail.com", ["00714", "34065", "31752", "32473"], True)
    # self.watcher_m.notify("lerryun@gmail.com")


if __name__ == "__main__":
    unittest.main()
