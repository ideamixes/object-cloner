# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
"""Operator's entrypoint. Sets logging configuration."""
import logging
from os import getenv

from .operator import *

logging.basicConfig(
    level=getenv("OBJECT_CLONER_LOG_LEVEL", str(logging.INFO)),
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
