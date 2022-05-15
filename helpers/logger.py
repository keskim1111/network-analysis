import sys

from loguru import logger


def define_the_logger(file_path):
    logger.add(file_path)
    logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")
