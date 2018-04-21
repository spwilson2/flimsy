
from .test import *
from .suite import *
from .runner import *
from .loader import *
from .fixture import *


def main():
    Loader().load_root('example')