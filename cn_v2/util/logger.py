import logging


def creat_stream_logger(logger_name, formatting=None):
    formatter = logging.Formatter(
        formatting or "[%(levelname)s][%(asctime)s][%(name)s] - %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.DEBUG)

    logger = logging.getLogger(logger_name)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)
    return logger
