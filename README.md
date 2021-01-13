# Coursenotify
CourseNotify is a package built for parsing course database for De Anza and Foothill College.  
It handles retriving and parsing course data, and sending out course availbility notifications via email.

# Installation
Since the course data is parsed and stored in  ```MongoDB``` so you will need to have ```MongoDB``` setup first.  
```
git clone https://github.com/Larryun/coursenotify_v2.git
pip3 install coursenotify_v2/cn_v2
```

# Configuration
See ```config/base.yaml``` and fill in the required configurations

# Usage
### Parser
```python3
from cn_v2.parser.course import *
parser = CourseParser("path/to/config.yaml", CourseParser.DA)
# soup = p.get_soup()     # returns a BeautifulSoup4 object
result = p.parse()        # returns a list of course objects
print(len(result))
```

### Managers
```python3
from cn_v2.manager.watcher import *

CONFIG_FILE = "path/to/config.yaml"
course_m = CourseManager(CONFIG_FILE, BaseManager.DA)
course_m.update_course_collection()                          # update courses data
print(course_m.find_course_by_crn("34065"))                  # returns a course object

watcher_m = WatcherManager(CONFIG_FILE, BaseManager.DA)
watcher_m.find_watcher_by_email("test@email.com", limit=1)   # returns a watcher objects
```
