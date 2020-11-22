class CRNNotFound(Exception):

    def __init__(self, crn):
        self.crn = crn

    def __str__(self):
        return "CRN %s not found" % str(self.crn)
