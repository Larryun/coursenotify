import yaml


class BaseManager(object):

    def __init__(self, config_file):
        with open(config_file) as f:
            self.config = yaml.load(f, yaml.Loader)
        print(self.config)
