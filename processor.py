from datetime import date
import config
import requests

# Define constants
API_KEY = config.API_KEY
BASE_URL = 'https://www.worldtradingdata.com/api/v1/forex_history'
CURRENCIES = config.CURRENCIES

with requests.Session() as s:
    for currency in CURRENCIES:
        # Define a dictionary of parameters that we will pass to the API endpoint
        payload = {
            'base': currency,
            'convert_to': 'GBP',
            'api_token': API_KEY,
            'sort': 'oldest',
            'output': 'csv'
        }
        
        data = s.get(BASE_URL, params = payload)

        with open(''.join((currency, 'GBP', '.csv')), 'w') as f:
            writer = csv.writer(f)
            reader = csv.reader(data.text.splitlines())

            first_line = True

            for row in reader:
                # Handling the headers
                if first_line:
                    writer.writerow(row)
                    first_line = False
                    continue
                date_val = date.fromisoformat(row[0])
                if (date_val >= date(2018, 1, 2)) and (0 <= date_val.weekday() <= 4):
                    writer.writerow(row)




