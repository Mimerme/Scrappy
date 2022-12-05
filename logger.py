import logging

def setup_log():
	logging.basicConfig(filename="log.txt", level=logging.DEBUG, datefmt = '%I:%M:%S %p', format = '%(asctime)s - %(levelname)s: {%(pathname)s:%(lineno)d} %(message)s',filemode = 'a')