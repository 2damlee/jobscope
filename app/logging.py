import logging
from app.config import LOG_LEVEL


def setup_logger():
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("jobscope")