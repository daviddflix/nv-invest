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

    try:
        coingecko_response = requests.get(f'{coingecko_url}/coins/list', headers=headers)

        if coingecko_response.status_code == 200:
            return coingecko_response.json(), coingecko_response.status_code
        
        return coingecko_response.content, coingecko_response.status_code
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None


# Calculate the closest multiple of 5 less than or equal to the number
def closest_multiples_of_5(number):
    lower_multiple = (number // 5) * 5
    if lower_multiple == 0:
        return False
    return lower_multiple

# Calculate the closest multiple of 10 less than or equal to the number
def closest_multiples_of_10(number):
    lower_multiple = (number // 10) * 10
    if lower_multiple == 0:
        return False
    return lower_multiple


# calculate percentage variation - price has increased/decreased by 5% or 10%
def calculate_percentage_change_over_buy_price(buy_price, current_price, coin):
    try:
        percentage_change = ((float(current_price) - float(buy_price)) / float(buy_price)) * 100
        direction = "increased" if percentage_change >= 0 else "decreased"
        absolute_percentage_change = abs(percentage_change)

        closest_percentage = closest_multiples_of_5(absolute_percentage_change)

        if closest_percentage:
            if absolute_percentage_change >= closest_percentage:
                return {'alert_message': f'The price of {coin.capitalize()} has {direction} in {closest_percentage}% from your original buy price.',
                        'alert_type': f'{closest_percentage}'}
            else:
                return None
        else:
            return None

    except ZeroDivisionError:
        print(f"Error calculating buy price change for {coin}: Buy price cannot be zero.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# Checks the percentage change of a coin in a day
def percentage_variation_by_day(coin, percentage_change):
    
    direction = "increased" if float(percentage_change) >= 0 else "decreased"
    absolute_percentage_change = abs(float(percentage_change))

    closest_percentage = closest_multiples_of_5(absolute_percentage_change)

    try:
        if closest_percentage:
            if absolute_percentage_change >= closest_percentage:
                return {'alert_message': f'The price of {coin.capitalize()} has {direction} in {closest_percentage}% today.',
                        'alert_type': f'{closest_percentage}'}
            else:
                return None
        else:
            return None

    except ZeroDivisionError:
        print(f"Error in percentage_variation_by_day for {coin}: number cannot be zero.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    

# Calculates the percentage change of a coin in a week
def percentage_variation_week(coin, percentage_change):
    
    direction = "increased" if float(percentage_change) >= 0 else "decreased"
    absolute_percentage_change = abs(float(percentage_change))

    closest_percentage = closest_multiples_of_10(absolute_percentage_change)


    try:
        if closest_percentage:
            if absolute_percentage_change >= closest_percentage:
                return {'alert_message': f'The price of {coin.capitalize()} has {direction} in {closest_percentage}% since the start of the week.',
                        'alert_type': f'{closest_percentage}'}
            else:
                return None
        else:
            return None

    except ZeroDivisionError:
        print(f"Error in percentage_variation_week for {coin}: number cannot be zero.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# Checks the price of a coin - it uses all functions from above and returns their values.
def check_price(coin):

    try: 
        formatted_coin = coin.casefold().strip()

        coingecko_response = requests.get(f'{coingecko_url}/coins/{formatted_coin}', headers=headers) 

        if coingecko_response.status_code == 200:
            data = coingecko_response.json()
            market_data = data.get('market_data')

            current_price = market_data['current_price']['usd']
            price_change_daily = market_data['price_change_percentage_24h']
            price_change_weekly = market_data['price_change_percentage_7d']

            return {'current_price': current_price, 'price_change_daily': price_change_daily, 'price_change_weekly': price_change_weekly}
        
        return False
    except Exception as e:
        print(f'Error getting data for {coin}, {str(e)}')
        return False





# print(check_price('WagyuSwap'))
# print(calculate_percentage_change_over_buy_price('0.1116','0.129964', 'AIPad'))
# print(percentage_variation('AIPad', '-7.67517', 'weekly'))