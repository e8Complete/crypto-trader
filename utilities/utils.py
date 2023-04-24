import time
import datetime


def get_timestamp():
  timestamp = time.time()
  date_time = datetime.datetime.fromtimestamp(timestamp)
  str_date_time = date_time.strftime('%Y%m%d_%H%M%S')
  return str_date_time