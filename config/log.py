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


logger = logging.getLogger("Assistant")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(CustomLogsFormatter())
logger.addHandler(handler)
