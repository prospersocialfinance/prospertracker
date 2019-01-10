from datetime import date

import config
import json
import requests

####################
# Define constants #
####################

API_KEY = config.API_KEY
CURRENCIES = config.CURRENCIES
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

    for key, val in stock_dict['history'].items():
        stock_dict['history'][key] = str(float(val) * float(forex_dict['history'][key]))
    
    return json.dumps(stock_dict)


with requests.Session() as s:
    for ticker in STOCKS:
        payload = {
            'symbol': ticker,
            'sort': 'oldest',
            'api_token': API_KEY,
            'date_from': '2018-01-01',
            'date_to': TODAY,
            }
        
        data = s.get(URL + 'history', params = payload)

        with open('json/stocks/' + ticker + '.json', 'w') as f:
            f.write(data.text)

for ticker in STOCKS:
    with open('json/stocks/' + ticker + '.json', 'r+') as f:
        parsed_json = json.loads(f.read())
        for key, val in parsed_json['history'].items():
            parsed_json['history'][key] = val['close']
        f.seek(0)
        f.write(json.dumps(parsed_json))
        f.truncate()

with requests.Session() as s:
    for currency in CURRENCIES:
        # Define a dictionary of parameters that we will pass to the API endpoint
        payload = {
            'base': currency,
            'convert_to': 'GBP',
            'api_token': API_KEY,
            'sort': 'oldest',
        }
        
        data = s.get(URL + 'forex_history', params = payload)

        with open('json/currencies/' + currency + 'GBP.json', 'w') as f:
            f.write(data.text)

for currency in CURRENCIES:
    with open('json/currencies/' + currency + 'GBP.json', 'r+') as f:
        parsed_json = json.loads(f.read())
        temp = {key: val for key, val in parsed_json['history'].items()}
        for key, val in parsed_json['history'].items():
            date_val = date.fromisoformat(key)
            if (date_val < date(2018, 1, 1)) or (5 <= date_val.weekday() <= 6):
                temp.pop(key)
        parsed_json['history'] = temp
        f.seek(0)
        f.write(json.dumps(parsed_json))
        f.truncate()

for ticker, info in STOCKS.items():
    if info['curr'] == 'GBP':
        continue
    with open ('json/stocks/' + ticker + '.json', 'r+') as stock, open ('json/currencies/' + info['curr'] + 'GBP.json', 'r') as forex:
        converted = converter(stock.read(), forex.read())
        stock.seek(0)
        stock.write(converted)
        stock.truncate()





    