import logging

logging.basicConfig(
    level=logging.INFO,filename='backend.log',filemode='w',format='%(asctime)s - %(levelname)s - %(message)s'
)

def publish_log(message):
    logging.info(message)

def publish_error(message):
    logging.error(message)