import logging

logger = logging.getLogger(__name__)

level = logging.INFO

logging.basicConfig(level=level, format='%(asctime)s: %(name)s: %(threadName)s: %(message)s')
logger.setLevel(level)
