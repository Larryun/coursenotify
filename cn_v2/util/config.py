import yaml


def read_config(filename):
    with open(filename) as f:
        return yaml.load(f, yaml.Loader)
