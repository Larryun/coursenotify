import yaml
from cn_v2.util.config import read_config
import pymongo

class BaseManager(object):

    def __init__(self, config_file):
        self.config = read_config(config_file)
        print(self.config)
