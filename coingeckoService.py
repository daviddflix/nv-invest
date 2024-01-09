import os
import requests
from dotenv import load_dotenv

load_dotenv() 

# CoinGecko API endpoint
coingecko_url = "https://pro-api.coingecko.com/api/v3"

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

headers = {
            "Content-Type": "application/json",
            "x-cg-pro-api-key": COINGECKO_API_KEY,
        }


# Returns a list of Dicts with all the available coins in Coingecko
def get_list_of_coins():

    coingecko_response = requests.get(f'{coingecko_url}/coins/list', headers=headers)

    if coingecko_response.status_code == 200:
        return coingecko_response.json(), coingecko_response.status_code
    
    return coingecko_response.content, coingecko_response.status_code



def check_price(coin):

    try: 
        formatted_coin = coin.casefold().strip()

        coingecko_response = requests.get(f'{coingecko_url}/coins/{formatted_coin}', headers=headers) 

        if coingecko_response.status_code == 200:
            data = coingecko_response.json()
            market_data = data.get('market_data')
            current_price = market_data['current_price']['usd']

            price_change_percentage = None
            price_change = market_data['price_change_percentage_24h']
            if price_change and price_change > float(10):
                price_change_percentage = f'{coin} has increaced {price_change}%'
            elif price_change and price_change < float(-10):
                price_change_percentage = f'{coin} has decreaced {price_change}%'
            else:
                price_change_percentage = None

            return current_price, price_change_percentage
        
        return False, False
    except Exception as e:
        print(f'Error getting data for {coin}, {str(e)}')
        return False, False

# print(check_price('sats-ordinals'))
