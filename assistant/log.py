import logging


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    cyan = "\x1b[36;20m"
    blue = "\x1b[34;20m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(filename)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: blue + format + reset,
        logging.INFO: cyan + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%d-%b %I:%M:%S %p')
        return formatter.format(record)
