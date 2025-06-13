import os
import logging
import colorama
from logging.handlers import RotatingFileHandler
from typing_extensions import Literal

# Inisialisasi colorama untuk support ANSI di Windows
colorama.init()

log_level = Literal[
    "CRITICAL",
    "ERROR",
    "WARNING",
    "INFO",
    "DEBUG",
]


def get_logging_level(level: str) -> int:
    levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }
    return levels.get(level.upper(), logging.INFO)


class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: colorama.Fore.BLUE,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED,
        logging.CRITICAL: colorama.Fore.LIGHTRED_EX,
    }
    RESET = colorama.Style.RESET_ALL

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(log_level: log_level = "INFO", save_logs: bool = False) -> logging.Logger:
    logger = logging.getLogger("qwen_api")
    logger.propagate = False

    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(get_logging_level(log_level))

    base_format = "[%(levelname)s] %(asctime)s - %(name)s -> %(message)s"

    # Handler untuk console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter(base_format))
    logger.addHandler(console_handler)

    # Handler untuk file
    if save_logs:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            f"{log_dir}/qwen.log",
            maxBytes=5*1024*1024,
            backupCount=3
        )
        file_handler.setFormatter(logging.Formatter(base_format))
        logger.addHandler(file_handler)

    return logger
