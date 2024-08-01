import logging


class CustomLogsFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    cyan = "\x1b[36;20m"
    blue = "\x1b[34;20m"
    reset = "\x1b[0m"
    _format = "%(asctime)s - %(filename)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: blue + _format + reset,
        logging.INFO: cyan + _format + reset,
        logging.WARNING: yellow + _format + reset,
        logging.ERROR: red + _format + reset,
        logging.CRITICAL: bold_red + _format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%d-%b %I:%M:%S %p')
        return formatter.format(record)


def get_logger(name: str, level: str = "DEBUG") -> logging.Logger:
    """
    Returns a logger object
    :param name: Name of the logger
    :param level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :return: Logger object
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(CustomLogsFormatter())
    logger.addHandler(handler)
    return logger
