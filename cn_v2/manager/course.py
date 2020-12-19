from cn_v2.exception import CRNNotFound
from cn_v2.manager.base import BaseManager
from cn_v2.parser.course import CourseParser


class CourseManager(BaseManager):

    def __init__(self, config_file, school, term_code=None, cursor=None):
        super(CourseManager, self).__init__(config_file, school, cursor=cursor)
        self.parser = CourseParser(config_file, school, term_code)
        self.logger.name = "CourseManager-%s" % school
        self.logger.debug("Finish initializing %s" % self.logger.name)

    def __update_course_collection(self, data):
        self.logger.info("Updating course data in %s course collection" % self.school)
        for obj in data:
            self.course_cc.update_many({"crn": obj.crn}, {"$set": obj.__dict__}, upsert=True)
        self.logger.info("Updated %s course in %s course collection" % (len(data), self.school))

    def update_course_collection(self):
        self.__update_course_collection(self.parser.parse())

    def is_crn_exists(self, crn):
        return self.course_cc.count_documents({"crn": crn}) != 0

    def find_course_by_crn(self, crn, projection=None):
        if self.is_crn_exists(crn):
            return self.course_cc.find_one({"crn": crn}, projection)
        else:
            self.logger.error("CRN %s not found" % crn)
            raise CRNNotFound(crn)

    def find_course_by_id(self, course_id):
        # not tested
        result = self.course_cc.find_one({"_id": course_id})
        # self.logger.debug(result)
        # if result is None:
        #     return None
        # else:
        #     return result
        return result or None

    def find_course_by_crn_prefix(self, crn, projection=None):
        projection = projection or {"_id": 0, "title": 1, "name": 1, "crn": 1, "status": 1, }
        courses = self.course_cc.find({"crn": {"$regex": "^" + str(crn)}}, projection)
        return courses
