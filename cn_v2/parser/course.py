import requests
import os
from bs4 import BeautifulSoup

from cn_v2.parser.model import *
from cn_v2.util.config import read_config
from cn_v2.util.parser import *


class Parser(object):
    """
        Abstract class for Parser
    """

    def __init__(self, config_file):
        self.config = read_config(config_file)
        self.data_path = self.config["data-path"]

        self.s = requests.Session()
        self.s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                                             "Chrome/79.0.3945.130 Safari/537.36"})

        self.HTML_FILE = self.config["data-path"] + "course.html"
        if os.environ["env"] == "dev":
            self.DEBUG = True

    @staticmethod
    def debug_p(message):
        if os.environ["env"] == "dev":
            print("[DEBUG] " + message)

    def get_soup(self, url, data, **kwargs):
        if self.DEBUG and os.path.isfile(self.HTML_FILE):
            return self.read_html()
        self.debug_p("Retrieving html page")
        rep = self.s.post(url, data=data)
        soup = BeautifulSoup(rep.text, "html.parser")
        return soup

    def read_html(self):
        self.debug_p("Reading html page from %s" % self.HTML_FILE)
        # Read html from file
        with open(self.HTML_FILE, "r") as f:
            return BeautifulSoup(f.read(), features="html.parser")

    def save_soup(self, soup):
        self.debug_p("Saving html page")
        # Save html to file
        with open(self.HTML_FILE, "w") as f:
            f.write(str(soup.prettify()))


class CourseParser(Parser):
    DA = "DA"
    FH = "FH"
    COURSE_URL = "https://ssb-prod.ec.fhda.edu/PROD/fhda_opencourses.P_GetCourseList"

    def __init__(self, config_file, school, term_code=None):
        super(CourseParser, self).__init__(config_file)
        self.term_code = term_code or {self.DA: "202132", self.FH: "202131"}
        self.term = self.get_school_term_code(school)

    def get_school_term_code(self, school):
        if school in [self.DA, self.FH]:
            return self.term_code[school]
        else:
            raise RuntimeError("School invalid")

    def get_soup(self, **kwargs):
        return super().get_soup(self.COURSE_URL, {"termcode": self.term})

    def parse(self):
        soup = self.get_soup()
        self.debug_p("Parsing")
        tables = soup.find_all("table")
        courses = []

        for table in tables:
            courses.extend(self._parse_table(table))
        return list(set(courses))

    def _parse_table(self, table_soup):
        """
            Parse the whole table and yield each course data
        :param table_soup: BeautifulSoup object for table
        :param kwargs: Optional
        :return: Generator for CourseData object
        """
        results = []
        rows = table_soup.find_all("tr")
        # Ignore the first two row
        rows = rows[2:]
        for r in rows:
            cols = r.find_all("td")[1:]
            for i in range(len(cols)):
                cols[i] = normalize(cols[i].text.strip())
            results.append(CourseDocument(*cols))
        return results
