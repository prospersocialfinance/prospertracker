import config
import json

# Define constants
API_KEY = config.API_KEY
BASE_URL = 'https://www.worldtradingdata.com/api/v1/history'
STOCKS = config.STOCKS

with requests.Session() as s:
    for ticker in STOCKS:
        # Define a dictionary of parameters that we will pass to the API endpoint
        payload = {
            'symbol': ticker,
            'sort': 'oldest',
            'api_token': API_KEY,
            'date_from': '2017-12-31',
            'date_to': '2019-01-09',
            }
        
        data = s.get(BASE_URL, params = payload)

        with open(ticker + '.json', 'w') as f:
            writer = csv.writer(f)
            reader = csv.reader(data.text.splitlines())

            for row in reader:
                writer.writerow([row[0], row[2]])

    