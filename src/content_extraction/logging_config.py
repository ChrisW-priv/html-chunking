import logging
import sys


def setup_logging(level=logging.INFO):
    """
    Set up basic logging for the application.
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout,  # Log to stdout
    )
