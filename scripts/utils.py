import os
import yaml
import time
import datetime
import pandas as pd
from scripts.constants import Constants
from typing import Literal



def get_timestamp(precision: Literal["year", "month", "day", "hours", "minutes", "seconds"]="seconds",
                  separator="") -> str:
    """ Input: Optional precision and/or optional separator
        Returns: Timestamp in format "2023{}05{}20_13{}37{}00". 
                 Examples: "20230520_133700"
                           "2023-05-20_13-37-00"
                           "2023/05/20"
    """
    timestamp_precision_types = {
        "year": "%Y",
        "month": "{seperator}%m",
        "day": "{seperator}%d",
        "hours": "_%H",
        "minutes": "{seperator}%M",
        "seconds": "{seperator}%S"
    }

    if precision not in timestamp_precision_types.keys():
        raise ValueError(f"Invalid precision value: {precision}. Options: {', '.join(list(timestamp_precision_types.keys()))}")
    if separator == "%":
        raise ValueError("separator cannot be '%'")
    
    epoch_time = time.time()
    date_time = datetime.datetime.fromtimestamp(epoch_time)
    time_format = ""
    for key, value in timestamp_precision_types.items():
        time_format += value.format(seperator=separator)
        if key == precision:
            break
    timestamp: str = date_time.strftime(time_format)

    return timestamp


def load_config(path):
  with open(path, 'r') as cf:
      return yaml.safe_load(cf)


def save_data_to_csv(data):
    timestamp = time.time()
    date_time = datetime.datetime.fromtimestamp(timestamp)
    date_str = date_time.strftime('%Y%m%d')
    time_str = date_time.strftime('%H%M%S')
    output_folder = os.path.join(Constants.PROJECT_ROOT, "trades", date_str)
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, time_str+".csv")
    df = pd.DataFrame.from_dict(data)
    df.to_csv(output_path)
   
