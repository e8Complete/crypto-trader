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


def save_data_to_csv(data, config): # Added config to know which indicators/sentiments are active
    run_epoch_time = time.time()
    run_date_time = datetime.datetime.fromtimestamp(run_epoch_time)
    
    # More readable timestamp for the CSV file and 'run_datetime' column
    date_str_folder = run_date_time.strftime('%Y%m%d') # For folder name
    time_str_file = run_date_time.strftime('%H%M%S') # For file name
    run_datetime_col_str = run_date_time.strftime('%Y-%m-%d %H:%M:%S') # For the column in CSV

    output_folder = os.path.join(Constants.PROJECT_ROOT, "trades", date_str_folder)
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, f"{time_str_file}_summary.csv") # Added _summary to filename

    processed_data_for_csv = []

    # Determine active indicators and sentiment analyzers from config to create dynamic columns
    active_indicator_names = [ind['name'] for ind in config.get('indicators', []) if ind.get('enable')]
    active_sentiment_names = [sa['name'] for sa in config.get('sentiment_analyzers', []) if sa.get('enable')]

    for symbol, symbol_data in data.items():
        if not symbol_data: # Skip if symbol_data is empty (e.g., fetch failed)
            continue

        row = {
            "run_datetime": run_datetime_col_str,
            "symbol": symbol,
            "current_price": symbol_data.get("current_price"),
            "opening_price_period": symbol_data.get("opening_price"), # This was the first opening price in klines
            "highest_price_period": symbol_data.get("highest_price"), # Max high from klines
            "lowest_price_period": symbol_data.get("lowest_price"),   # Min low from klines
            "closing_price_latest_interval": symbol_data.get("closing_price"), # Last closing price from klines
            "decision": symbol_data.get("decision", {}).get("decision", "N/A"),
            "decision_quantity": symbol_data.get("decision", {}).get("quantity"),
            "market_news_status": "Fetched" if "market_news" in symbol_data and symbol_data["market_news"] != "Error fetching news" else symbol_data.get("market_news", "N/A"),
        }

        # Add indicator signals
        for indicator_name in active_indicator_names:
            indicator_data = symbol_data.get("indicators", {}).get(indicator_name, {})
            row[f"{indicator_name}_signal"] = indicator_data.get("signal", "N/A")

        # Add sentiment scores
        for sentiment_name in active_sentiment_names:
            sentiment_data = symbol_data.get("sentiment", {}).get(sentiment_name, {})
            row[f"{sentiment_name}_sentiment_score"] = sentiment_data.get("sentiment_score", "N/A")
            
        processed_data_for_csv.append(row)

    if processed_data_for_csv:
        df = pd.DataFrame(processed_data_for_csv)
        # Reorder columns to have a more logical flow, run_datetime and symbol first
        cols = ["run_datetime", "symbol", "current_price", "opening_price_period", 
                "highest_price_period", "lowest_price_period", "closing_price_latest_interval",
                "decision", "decision_quantity", "market_news_status"]
        
        indicator_cols = [f"{name}_signal" for name in active_indicator_names]
        sentiment_cols = [f"{name}_sentiment_score" for name in active_sentiment_names]
        
        # Ensure all expected columns exist in the DataFrame before trying to reorder
        # This handles cases where some indicators/sentiments might not have produced data for any symbol
        final_cols = []
        for col_name in cols + indicator_cols + sentiment_cols:
            if col_name in df.columns:
                final_cols.append(col_name)
            else: # If a configured indicator/sentiment column is missing entirely, add it with N/A
                  # This might happen if it never ran or always errored out before adding to a row.
                  # Usually, the .get("N/A") in row creation handles this per row.
                  # This is more for ensuring column presence if NO row got data for it.
                  # However, if processed_data_for_csv is not empty, all keys added to `row` will be columns.
                  # This step is more of a safeguard or for explicit ordering if some dynamic columns were entirely absent.
                  pass # df.columns will already reflect all keys from processed_data_for_csv

        df = df.reindex(columns=final_cols if final_cols else df.columns) # Use existing columns if final_cols is empty (no data)

        df.to_csv(output_path, index=False)
        print(f"Saved trade summary to {output_path}") # Added a print statement for user feedback
    else:
        # Save an empty file with headers if no data was processed, or just log
        # For now, let's just print a message if no data.
        print(f"No data processed to save for this run. CSV not created at {output_path}")
