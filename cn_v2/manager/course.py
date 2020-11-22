from cn_v2.manager.base import BaseManager
from cn_v2.parser.course import CourseParser


class CourseManager(BaseManager):

    def __init__(self, config_file, school, term_code=None):
        super(CourseManager, self).__init__(config_file, school)
        self.parser = CourseParser(config_file, school, term_code)
        self.logger.name = "CourseManager-%s" % school
        self.logger.debug("Finish initializing manager")

    def __update_course_collection(self, data):
        self.logger.info("Updating course data in %s course collection" % self.school)
        for obj in data:
            self.course_cc.update_many({"crn": obj.crn}, {"$set": obj.__dict__}, upsert=True)

    def update_course_collection(self):
        self.__update_course_collection(self.parser.parse())
