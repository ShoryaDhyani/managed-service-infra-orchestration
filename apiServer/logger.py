import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,filename=f'logs/log-{datetime.now().strftime("%Y-%m-%d")}.log',filemode='w',format='%(asctime)s |%(filename)s| - %(levelname)s - %(message)s'
)

def publish_log(message):
    logging.info(message)

def publish_error(message):
    logging.error(message)