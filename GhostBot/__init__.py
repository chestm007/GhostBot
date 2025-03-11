import logging

logger = logging.getLogger(__name__)

level = logging.DEBUG

logging.basicConfig(level=level, format='%(asctime)s: %(name)s: %(threadName)s: %(message)s')
logger.setLevel(level)
