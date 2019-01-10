import config
import json
import requests

# Define constants
API_KEY = config.API_KEY
BASE_URL = 'https://www.worldtradingdata.com/api/v1/history'
STOCKS = config.STOCKS

# with requests.Session() as s:
#     for ticker in STOCKS:
#         # Define a dictionary of parameters that we will pass to the API endpoint
#         payload = {
#             'symbol': ticker,
#             'sort': 'oldest',
#             'api_token': API_KEY,
#             'date_from': '2018-01-01',
#             'date_to': '2019-01-09',
#             }
        
#         data = s.get(BASE_URL, params = payload)

#         with open('json/' + ticker + '.json', 'w') as f:
#             f.write(data.text)

for ticker in STOCKS:
    with open('json/' + ticker + '.json', 'r+') as f:
        parsed_json = json.loads(f.read())
        for key, val in parsed_json['history'].items():
            val.pop('open')
            val.pop('high')
            val.pop('low')
            val.pop('volume')
        f.seek(0)
        f.write(json.dumps(parsed_json))
        f.truncate()




    