import logging
from define import *

# create file handler 
fh = logging.FileHandler(FILEPATH_LOG)
fh.setLevel(LOG_LEVEL_FILE)
# create formatter
formatter_f = logging.Formatter(FORMAT_LOG_FILE)
# add formatter to the handlers
fh.setFormatter(formatter_f)

# create console handler 
ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL_STREAM)
# create formatter
formatter_s = logging.Formatter(FORMAT_LOG_STREAM)
# add formatter to the handlers
ch.setFormatter(formatter_s)

# ルートロガーにハンドラーsを紐付けておく
rootlogger = logging.getLogger("WEAK3")
rootlogger.setLevel(logging.DEBUG)

"""
# remove pre-existing handlers (同じメッセージの重複を防ぐ)
for hdr in rootlogger.handlers:
    if isinstance(hdr, logging.StreamHandler):
        rootlogger.removeHandler(hdr)

# remove pre-existing handlers
for hdr in rootlogger.handlers:
    if isinstance(hdr, logging.FileHandler):
        rootlogger.removeHandler(hdr)
"""
# add the handlers to the logger
rootlogger.addHandler(fh)
rootlogger.addHandler(ch)

def getLogger(logger_name):
    return logging.getLogger(f"WEAK3.{logger_name}")
