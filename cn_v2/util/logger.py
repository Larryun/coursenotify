import logging


class BasicLogger(logging.Logger):

    def __init__(self, name, formatting=None, level=logging.DEBUG):
        super(BasicLogger, self).__init__(name, level)
        self.formatter = logging.Formatter(
            formatting or "[%(levelname)s][%(asctime)s][%(name)s] - %(message)s"
        )
        ch = logging.StreamHandler()
        ch.setFormatter(self.formatter)
        ch.setLevel(logging.DEBUG)

        self.addHandler(ch)
        self.setLevel(level)
        # logger.setLevel(logging.DEBUG)

    def add_file_handler(self, log_path="../data/output.log"):
        ch = logging.FileHandler(log_path)
        ch.setFormatter(self.formatter)
        ch.setLevel(self.level)
        self.addHandler(ch)
