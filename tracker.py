from datetime import datetime, date, timedelta
from pathlib import Path

import config
import csv
import json
import os
import requests
import shutil

####################
# Define constants #
####################

API_KEY = config.API_KEY
BENCHMARKS = config.BENCHMARKS
CURRENCIES = config.CURRENCIES
INVESTMENT_DATES = config.DATES
MSCI_FORMAT = config.MSCI["format"]
MSCI_URL = config.MSCI["url"]
URL = config.BASE_URL
STOCKS = config.STOCKS
TODAY = date.isoformat(date.today())

##################################################################################
# Converts a non-GBP stock's price to its GBP equivalent. Accepts the stock JSON #
# and relevant currency JSON as arguments, and outputs the converted stock JSON. #
##################################################################################


def converter(stock, forex):
    stock_dict = json.loads(stock)
    forex_dict = json.loads(forex)

    for key, val in stock_dict.items():
        stock_dict[key] = str(float(val) * float(forex_dict[key]))

    return json.dumps(stock_dict)


#######################################################################
# Converts JSON string to CSV. Accepts the JSON string, filename, and #
# a list of headers as arguments, and creates the CSV file in 'csv/'. #
#######################################################################


def json_to_csv(json_str, filename, headers):
    parsed_json = json.loads(json_str)

    Path("csv/").mkdir(parents=True, exist_ok=True)
    with open("csv/" + filename + ".csv", "w+") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)

        for key, val in parsed_json.items():
            writer.writerow([key, val])

    return None

#######################################################################
# Calculate the percentage growth of a value relative to a specified  #
# baseline. Returns the percentage growth with 2 d.p. accuracy.       #
#######################################################################


def pct_growth(val, base):
    return round(100 * val / base - 100, 2)


def get_json_names():
    return sorted(
        os.listdir("json/stocks"),
        key=lambda x: (datetime.strptime(x.split("_")[1], "%Y-%m-%d"), x.split("_")[0]),
    )


###############################
# Retrieve and clean datasets #
###############################

with requests.Session() as s:
    # Retrieve and clean benchmark datasets
    for benchmark in BENCHMARKS:
        payload = {
            "symbols": benchmark,
            "sort": "oldest",
            "access_key": API_KEY,
            "date_from": "2018-06-29",
            "date_to": TODAY,
        }

        data = s.get(URL + "eod", params=payload)
        print(data.text)
        Path("json/benchmarks/").mkdir(parents=True, exist_ok=True)
        with open("json/benchmarks/" + benchmark + ".json", "w+") as f:
            parsed_json = json.loads(data.text)
            for key, val in parsed_json["history"].items():
                parsed_json["history"][key] = val["close"]
            f.write(json.dumps(parsed_json["history"]))

    # Retrieve and clean MSCI dataset
    payload = {
        "indices": "96434,B,36",
        "startDate": date(2018, 6, 29).strftime(MSCI_FORMAT),
        "endDate": date.today().strftime(MSCI_FORMAT),
        "priceLevel": "0",
        "currency": "18",
        "frequency": "D",
        "scope": "R",
        "format": "CSV",
        "baseValue": "false",
        "site": "gimi",
    }
    data = s.get(MSCI_URL, params=payload)
    with open("csv/temp.csv", "w+") as f:
        f.write(data.text)

    # Retrieve and clean stock datasets
    for execution_date, stocks in STOCKS.items():
        for ticker in stocks:
            payload = {
                "symbol": ticker,
                "sort": "oldest",
                "api_token": API_KEY,
                "date_from": execution_date,
                "date_to": TODAY,
            }

            data = s.get(URL + "history", params=payload)
            Path("json/stocks/").mkdir(parents=True, exist_ok=True)
            with open(
                "json/stocks/{}_{}_.json".format(ticker, execution_date), "w+"
            ) as f:
                parsed_json = json.loads(data.text)
                for key, val in parsed_json["history"].items():
                    parsed_json["history"][key] = val["close"]
                f.write(json.dumps(parsed_json["history"]))

    # Retrieve and clean currency datasets
    for currency in CURRENCIES:
        payload = {
            "base": currency,
            "convert_to": "GBP",
            "api_token": API_KEY,
            "sort": "oldest",
        }

        data = s.get(URL + "forex_history", params=payload)

        Path("json/currencies/").mkdir(parents=True, exist_ok=True)
        with open("json/currencies/" + currency + "GBP.json", "w+") as f:
            parsed_json = json.loads(data.text)
            temp = {key: val for key, val in parsed_json["history"].items()}
            for key, val in parsed_json["history"].items():
                date_val = datetime.strptime(key, "%Y-%m-%d").date()
            if (date_val < date(2018, 1, 1)) or (5 <= date_val.weekday() <= 6):
                temp.pop(key)
            parsed_json["history"] = temp
            f.write(json.dumps(parsed_json["history"]))

#################################################
# Convert non-GBP items into its GBP equivalent #
#################################################

for benchmark, info in BENCHMARKS.items():
    if info["curr"] == "GBP":
        continue
    with open("json/benchmarks/" + benchmark + ".json", "r+") as index, open(
        "json/currencies/" + info["curr"] + "GBP.json", "r"
    ) as forex:
        converted = converter(index.read(), forex.read())
        index.seek(0)
        index.write(converted)
        index.truncate()


for execution_date, stocks in STOCKS.items():
    for ticker, info in stocks.items():
        if info["curr"] == "GBP":
            continue
        with open(
            "json/stocks/{}_{}_.json".format(ticker, execution_date), "r+"
        ) as stock, open("json/currencies/" + info["curr"] + "GBP.json", "r") as forex:
            converted = converter(stock.read(), forex.read())
            stock.seek(0)
            stock.write(converted)
            stock.truncate()

#####################################################
# Get the value of our portfolio per stock (in GBP) #
#####################################################

for execution_date, stocks in STOCKS.items():
    for ticker, info in stocks.items():
        with open(
            "json/stocks/{}_{}_.json".format(ticker, execution_date), "r+"
        ) as stock:
            stock_dict = json.loads(stock.read())

            for key, val in stock_dict.items():
                if info["curr"] == "GBP":
                    val = str(float(val) / 100)
                stock_dict[key] = str(float(val) * info["amount"])

            stock.seek(0)
            stock.write(json.dumps(stock_dict))
            stock.truncate()

###########################################
# Get the value of our portfolio (in GBP) #
###########################################

for index, json_file in enumerate(get_json_names()):
    if index == 0:
        with open("json/processed.json", "w") as processed:
            for line in open("json/stocks/" + json_file):
                processed.write(line)
        continue

    with open("json/processed.json", "r+") as processed, open(
        "json/stocks/" + json_file, "r"
    ) as stock:
        processed_dict = json.loads(processed.read())
        stock_dict = json.loads(stock.read())

        for key in processed_dict:
            try:
                processed_dict[key] = str(
                    float(processed_dict[key]) + float(stock_dict[key])
                )
            except KeyError:
                # Check if this is a case of missing data, or just adding data from newer stocks
                curr_date = datetime.strptime(key, "%Y-%m-%d").date()
                purchased_date = datetime.strptime(
                    json_file.split("_")[1], "%Y-%m-%d"
                ).date()

                # There is missing data
                if curr_date >= purchased_date:
                    stock_price = None
                    while stock_price is None:
                        # Interpolate based on yesterday's values
                        curr_date -= timedelta(days=1)
                        try:
                            yesterday = curr_date.strftime("%Y-%m-%d")
                            stock_price = float(stock_dict[yesterday])
                            processed_dict[key] = str(
                                float(processed_dict[key]) + stock_price
                            )
                        except KeyError:
                            # Missing data in yesterday's values. Go back one extra day.
                            pass

        processed.seek(0)
        processed.write(json.dumps(processed_dict))
        processed.truncate()

########################################################
# Get the growth of benchmarks since 29/06/2018 (in %) #
########################################################

for benchmark in BENCHMARKS:
    with open("json/benchmarks/" + benchmark + ".json", "r+") as f:
        benchmark_dict = json.loads(f.read())
        baseline = float(benchmark_dict["2018-06-29"])
        for key in benchmark_dict:
            benchmark_dict[key] = pct_growth(float(benchmark_dict[key]), baseline)
        f.seek(0)
        f.write(json.dumps(benchmark_dict))
        f.truncate()

with open("csv/temp.csv", "r+") as temp, open("csv/msci.csv", "w+") as msci:
    parsed_data = next(csv.reader(temp))
    parsed_data.pop(0)
    count = len(parsed_data) // 2
    writer = csv.writer(msci)
    writer.writerow(["date", "value"])
    baseline = float(parsed_data[1])
    for i in range(count):
        idx = 2 * i
        key = date.isoformat(datetime.strptime(parsed_data[idx], "%m/%d/%Y").date())
        val = pct_growth(float(parsed_data[idx + 1]), baseline)
        writer.writerow([key, val])

###########################################################
# Get the growth of our portfolio since 29/06/2018 (in %) #
###########################################################

with open("json/processed.json", "r+") as processed:
    processed_dict = json.loads(processed.read())
    baseline = 0
    for key in processed_dict:
        if key in INVESTMENT_DATES:
            for execution_date, stocks in STOCKS.items():
                if execution_date == key:
                    for ticker in stocks:
                        with open(
                            "json/stocks/{}_{}_.json".format(ticker, execution_date),
                            "r",
                        ) as stock:
                            stock_dict = json.loads(stock.read())
                            baseline += float(stock_dict[key])
        processed_dict[key] = pct_growth(float(processed_dict[key]), baseline)
    processed.seek(0)
    processed.write(json.dumps(processed_dict))
    processed.truncate()

#######################################################
# Convert data from JSON to CSV for use with amCharts #
#######################################################

with open("json/processed.json", "r") as f:
    json_to_csv(f.read(), "processed", ["date", "value"])

for benchmark in BENCHMARKS:
    with open("json/benchmarks/" + benchmark + ".json", "r") as f:
        json_to_csv(f.read(), benchmark, ["date", "value"])

#######################
# Delete unused files #
#######################

# os.remove("csv/temp.csv")
# shutil.rmtree("json/")

