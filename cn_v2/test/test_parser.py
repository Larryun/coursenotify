import unittest
from cn_v2.parser.course import *


class TestParser(unittest.TestCase):

    def test_run(self):
        p = CourseParser("../config/dev.yaml", CourseParser.DA)
        # soup = p.get_soup()
        # p.save_soup(soup)
        result = list(set(p.parse()))
        print(len(result))


