import logging
import sys
import os

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str


def get_settings() -> Settings:
    return Settings(
        database_url=os.environ["DATABASE_URL"]
    )


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("output")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s >>> %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


setup_logger()
