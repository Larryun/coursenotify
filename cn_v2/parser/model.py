from typing import Dict, List, Union
from datetime import datetime
import hashlib


class CourseDocument(object):
    """
        Class definition for Course
    """

    def __init__(self, name, crn, title, status, days, class_time, start_date, end_date, room, campus, unit, instructor,
                 seats_num, waitlist_num, waitlist_capacity):

        self.name = name
        self.crn = str(crn)
        self.title = title
        self.status = status
        self.days = days
        # type string
        self.class_time = class_time
        # type datetime.datetime
        self.start_time = None
        self.end_time = None
        self.start_date = start_date
        self.end_date = end_date
        self.room = room
        self.campus = campus
        self.unit = unit
        self.instructor = instructor
        self.seats_num = int(seats_num)
        self.waitlist_num = int(waitlist_num)
        self.waitlist_capacity = int(waitlist_capacity)

        self.parse_days()
        self.parse_time()

    def parse_days(self):
        self.days = [x for x in filter(lambda x: x != '·', self.days)]
        # print([x for x in self.days])

    def parse_time(self):
        # print(self.class_time)
        if self.class_time == "TBA-TBA" or self.class_time == "TBA":
            self.start_time = ""
            self.end_time = ""
        else:
            self.start_time = datetime.strptime(self.class_time.split('-')[0], "%I:%M %p")
            self.end_time = datetime.strptime(self.class_time.split('-')[1], "%I:%M %p")

    def print_data(self):
        print("%s - %s - %s - %s" % (self.crn, self.name, self.class_time, self.days))

    def __str__(self):
        if self.room == "ONLINE" or self.class_time == "TBA":
            return "%s - %s\n(%s)" % (self.crn, self.name, "ONLINE")
        else:
            return "%s - %s\n(%s)" % (self.crn, self.name, "%s - %s" % (self.start_time.strftime("%H:%M"), self.end_time.strftime("%H:%M")))

    def __repr__(self):
        return "%s - %s" % (self.crn, self.name)

    def __eq__(self, other):
        return other.crn == self.crn

    def __hash__(self):
        return hash(self.crn)


class WatcheeDocument(object):
    def __init__(self, course_obj_id: str, last_notify: datetime = None, last_notify_status: str = "", removed=False):
        self.last_notify = last_notify or datetime(1, 1, 1, 1, 1, 1, 1)
        self.course_obj_id = course_obj_id
        h = hashlib.md5((str(self.course_obj_id) + datetime.now().strftime("%m/%d/%Y %H:%M:%S")).encode())
        self.remove_key = h.hexdigest()
        self.last_notify_status = last_notify_status
        self.removed = removed


class WatcherDocument(object):
    def __init__(self, watchee: Union[Dict, List[Dict]], email_addr: str):
        if not isinstance(watchee, List):
            watchee = [watchee]

        self.courses = watchee
        self.email_addr = email_addr

