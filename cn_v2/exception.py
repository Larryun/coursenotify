class CRNNotFound(Exception):

    def __init__(self, crn):
        self.crn = crn

    def __str__(self):
        return "CRN %s not found" % str(self.crn)


class RemoveKeyNotFound(Exception):
    def __init__(self, email, key):
        self.key = key
        self.email = email

    def __str__(self):
        return "Remove key %s not found in watcher %s" % (self.key, self.email)


class WatcheeNotFound(Exception):
    def __init__(self, email, crn):
        self.crn = crn
        self.email = email

    def __str__(self):
        return "Watchee %s not found in watcher %s" % (self.crn, self.email)
