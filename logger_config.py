import logging
from logging.handlers import RotatingFileHandler
import datetime

def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file_with_date = f"{log_file}_{today}.log"
    
    file_handler = RotatingFileHandler(log_file_with_date, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)

    return logger
