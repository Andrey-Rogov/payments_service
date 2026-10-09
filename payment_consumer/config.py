from dataclasses import dataclass
import os
import logging
import sys


@dataclass(frozen=True)
class Settings:
    database_url: str
    rabbitmq_url: str
    api_key: str


def get_settings() -> Settings:
    return Settings(
        database_url=os.environ["DATABASE_URL"],
        rabbitmq_url=os.environ["RABBITMQ_URL"],
        api_key=os.environ["API_KEY"]
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
