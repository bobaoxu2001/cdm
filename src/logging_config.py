import logging

from src.utils import runtime_config


def configure_logging(name: str = "biomed_harmonization") -> logging.Logger:
    config = runtime_config()
    level = getattr(logging, str(config.get("log_level", "INFO")).upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    return logging.getLogger(name)
