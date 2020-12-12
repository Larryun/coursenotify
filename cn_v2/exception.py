class CRNNotFound(Exception):

    def __init__(self, crn):
        self.crn = crn

    def __str__(self):
        return "CRN %s not found" % str(self.crn)

class SchoolInvalid(Exception):

    def __init__(self, school):
        self.school = school

    def __str__(self):
        return "School %s is invalid" % str(self.school)

class RemoveKeyNotFound(Exception):
    def __init__(self, key):
        self.key = key

    def __str__(self):
        return "Remove key %s not found" % self.key


class RemoveKeyUsed(Exception):
    def __init__(self, key):
        self.key = key

    def __str__(self):
        return "Remove key %s is used" % self.key


class WatcheeNotFound(Exception):
    def __init__(self, email, crn):
        self.crn = crn
        self.email = email

    def __str__(self):
        return "Watchee %s not found in watcher %s" % (self.crn, self.email)
