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

# calculate percentage variation - price has increased/decreased by 5% or 10%
def calculate_percentage_change_over_buy_price(buy_price, current_price, coin):
    try:
        percentage_change = ((float(current_price) - float(buy_price)) / float(buy_price)) * 100
        direction = "increased" if percentage_change >= 0 else "decreased"
        absolute_percentage_change = abs(percentage_change)

        if absolute_percentage_change >= 20:
            return f'The price of {coin.capitalize()} has {direction} by 20% from your original buy price.'
        elif absolute_percentage_change >= 15:
            return f'The price of {coin.capitalize()} has {direction} by 15% from your original buy price.'
        elif absolute_percentage_change >= 10:
            return f'The price of {coin.capitalize()} has {direction} by 10% from your original buy price.'
        elif absolute_percentage_change >= 5:
            return f'The price of {coin.capitalize()} has {direction} by 5% from your original buy price.'
        else:
            return None

    except ZeroDivisionError:
        print("Error: Buy price cannot be zero.")
        return None

def percentage_variation(coin, percentage_change, timeframe):
    
    direction = "increased" if float(percentage_change) >= 0 else "decreased"
    absolute_percentage_change = abs(float(percentage_change))
    end = ''
    if timeframe == 'weekly':
        end = 'since the start of the week'
    else:
        end = 'today'

    try:
        if absolute_percentage_change >= 30:
            return f'The price of {coin.capitalize()} has {direction} by 30% {end}.'
        if absolute_percentage_change >= 25:
            return f'The price of {coin.capitalize()} has {direction} by 25% {end}.'
        if absolute_percentage_change >= 20:
            return f'The price of {coin.capitalize()} has {direction} by 20% {end}.'
        elif absolute_percentage_change >= 15:
            return f'The price of {coin.capitalize()} has {direction} by 15% {end}.'
        elif absolute_percentage_change >= 10:
            return f'The price of {coin.capitalize()} has {direction} by 10% {end}.'
        elif absolute_percentage_change >= 5:
            return f'The price of {coin.capitalize()} has {direction} by 5% {end}.'
        else:
            return None

    except ZeroDivisionError:
        print("Error: Buy price cannot be zero.")
        return None

    
# The price of (Arbitrum) has increased/decreased by 10% from your original buy price.
def check_price(coin, buy_price):

    try: 
        formatted_coin = coin.casefold().strip()

        coingecko_response = requests.get(f'{coingecko_url}/coins/{formatted_coin}', headers=headers) 

        if coingecko_response.status_code == 200:
            data = coingecko_response.json()
            market_data = data.get('market_data')
            current_price = market_data['current_price']['usd']

            percentage_variation_over_buy_price = calculate_percentage_change_over_buy_price(buy_price=buy_price, 
                                                                                             current_price=current_price, 
                                                                                             coin=formatted_coin)
            price_change_daily = market_data['price_change_percentage_24h']
            price_change_weekly = market_data['price_change_percentage_7d']
            percentage_variation_daily = percentage_variation(coin=formatted_coin, percentage_change=price_change_daily, timeframe='daily')
            percentage_variation_weekly= percentage_variation(coin=formatted_coin, percentage_change=price_change_weekly, timeframe='weekly')


            return current_price, percentage_variation_daily, percentage_variation_weekly, percentage_variation_over_buy_price
        
        return False, False, False, False
    except Exception as e:
        print(f'Error getting data for {coin}, {str(e)}')
        return False, False, False, False

# print(check_price('sats-ordinals'))
# print(calculate_percentage_change_over_buy_price('0.1116','0.129964', 'AIPad'))
# print(percentage_variation('AIPad', '-7.67517', 'weekly'))