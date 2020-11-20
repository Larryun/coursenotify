import unittest

# from cn_v2.manager.base import BaseManager
from cn_v2.manager.course import *


class TestBaseManger(unittest.TestCase):

    def test_run(self):
        m = CourseManager("../config/dev.yaml", BaseManager.DA)

    def test_update_course_collection(self):
        m = CourseManager("../config/dev.yaml", BaseManager.DA)
        original_count = m.course_cc.count_documents({})
        original_id = m.course_cc.find_one({"crn": "37067"})["_id"]
        original = m.course_cc.find_one({"crn": "37067"})["class_time"]
        m.course_cc.update_one(
            {"crn": "37067"},
            {"$set": {"class_time": "IDFK"}}
        )
        assert m.course_cc.find_one({"crn": "37067"})["class_time"] == "IDFK"

        m.update_course_collection()
        assert m.course_cc.find_one({"crn": "37067"})["_id"] == original_id
        assert m.course_cc.find_one({"crn": "37067"})["class_time"] == original
        assert m.course_cc.count_documents({}) == original_count
