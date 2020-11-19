import unittest

from cn_v2.manager.base import BaseManager

class TestBaseManger(unittest.TestCase):

    def test_run(self):
        m = BaseManager("../config/dev.yaml")
