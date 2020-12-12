import pymongo
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure

from cn_v2.util.config import read_config
from cn_v2.util.logger import BasicLogger
from cn_v2.exception import SchoolInvalid

from logging import DEBUG, INFO


class BaseManager(object):
    FH = "FH"
    DA = "DA"

    def __init__(self, config_file, school, cursor=None):
        self.school = school
        if school != "FH" and school != "DA":
            raise SchoolInvalid(school)
        self.config = read_config(config_file)
        self.logger = BasicLogger("BaseManager")
        if not self.config["debug"]:
            self.logger = BasicLogger("BaseManager", level=INFO)

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
        timeout = self.config["manager"]["db"]["selectionTimeout"]
        self.cursor = self.__create_cursor(ip, port, username, password, timeout)

    def __setup_collection(self):
        self.course_cc = self.db[self.config["manager"]["collection"][self.school.lower()]["course"]]
        self.watcher_cc = self.db[self.config["manager"]["collection"][self.school.lower()]["watcher"]]

    def __create_cursor(self, ip, port, username, password, timeout=500):
        self.logger.debug("Connecting to DB")
        uri = "mongodb://%s:%s@%s:%s/?authSource=admin&authMechanism=SCRAM-SHA-1" % (username, password, ip, port)
        return pymongo.MongoClient(uri, serverSelectionTimeoutMS=timeout)

    def check_mongo_connection(self):
        self.logger.debug("Checking connection to DB")
        try:
            self.cursor.server_info()
            self.logger.debug("DB connected")
            return True
        except ServerSelectionTimeoutError as e:
            self.logger.error("Connection to MongoDB timeout")
            self.logger.warning("Quitting...")
            raise e
        except ConnectionFailure as e:
            self.logger.error("Fail to connect MongoDB")
            self.logger.warning("Quitting...")
            raise e

    def __del__(self):
        if "logger" in self.__dict__:
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)

        self.cursor.close()

