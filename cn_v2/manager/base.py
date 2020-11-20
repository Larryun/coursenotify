import yaml
import pymongo
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure

from cn_v2.util.config import read_config
from cn_v2.util.logger import creat_stream_logger


class BaseManager(object):

    def __init__(self, config_file):
        self.config = read_config(config_file)
        self.logger = creat_stream_logger("BaseManager")

        # setting up mongodb cursor
        ip = self.config["manager"]["db"]["ip"]
        port = self.config["manager"]["db"]["port"]
        username = self.config["manager"]["db"]["username"]
        password = self.config["manager"]["db"]["pass"]
        self.cursor = self.__create_cursor(ip, port, username, password)
        self.check_mongo_connection()

    @staticmethod
    def __create_cursor(ip, port, username, password):
        uri = "mongodb://%s:%s@%s:%s/?authSource=admin&authMechanism=SCRAM-SHA-1" % (username, password, ip, port)
        return pymongo.MongoClient(uri, severSelectionTimeoutMS=50)

    def check_mongo_connection(self):
        try:
            self.cursor.server_info()
            return 1
        except ServerSelectionTimeoutError:
            self.logger.error("Connection to MongoDB timeout")
            self.logger.warning("Quitting...")
            raise ServerSelectionTimeoutError
        except ConnectionFailure:
            self.logger.error("Fail to connect MongoDB")
            self.logger.warning("Quitting...")
            raise ConnectionFailure

