import yaml
import pymongo
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure

from cn_v2.util.config import read_config
from cn_v2.util.logger import BasicLogger


class BaseManager(object):
    FH = "FH"
    DA = "DA"

    def __init__(self, config_file, school, cursor=None):
        self.school = school
        self.config = read_config(config_file)
        self.logger = BasicLogger("BaseManager")

        # setting up mongodb cursor
        if not cursor:
            self.__setup_cursor()
        else:
            self.cursor = cursor

        self.check_mongo_connection()
        self.db = self.cursor[self.config["manager"]["db"]["db_name"]]
        self.__setup_collection()

    def __setup_cursor(self):
        ip = self.config["manager"]["db"]["ip"]
        port = self.config["manager"]["db"]["port"]
        username = self.config["manager"]["db"]["username"]
        password = self.config["manager"]["db"]["pass"]
        self.cursor = self.__create_cursor(ip, port, username, password)

    def __setup_collection(self):
        self.course_cc = self.db[self.config["manager"]["collection"][self.school.lower()]["course"]]
        self.watcher_cc = self.db[self.config["manager"]["collection"][self.school.lower()]["watcher"]]

    def __create_cursor(self, ip, port, username, password):
        self.logger.debug("Connecting to DB")
        uri = "mongodb://%s:%s@%s:%s/?authSource=admin&authMechanism=SCRAM-SHA-1" % (username, password, ip, port)
        return pymongo.MongoClient(uri)

    def check_mongo_connection(self):
        self.logger.debug("Checking connection to DB")
        try:
            self.cursor.server_info()
            self.logger.debug("DB connected")
            return True
        except ServerSelectionTimeoutError:
            self.logger.error("Connection to MongoDB timeout")
            self.logger.warning("Quitting...")
            raise ServerSelectionTimeoutError
        except ConnectionFailure:
            self.logger.error("Fail to connect MongoDB")
            self.logger.warning("Quitting...")
            raise ConnectionFailure

    def __del__(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
