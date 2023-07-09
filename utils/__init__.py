from .checks import *
from .presence import *
from .tracks import *


def remove_brackets(string: str) -> str:
    """Removes brackets from a string"""
    return re.sub("[\(\[].*?[\)\]]", "", string).strip()
