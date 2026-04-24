import logging
import os

logger = logging.getLogger(__name__)


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(name)s: %(threadName)s: %(message)s')
level = getattr(logging, os.environ.get('GHOSTBOT_LOGLEVEL', 'INFO'))
logger.setLevel(level)

def enable_thread_name_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(name)s: %(threadName)s: %(message)s')
