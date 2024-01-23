import os
import requests
import re
import json
from dotenv import load_dotenv
from services.slack.actions import send_list_of_coins, send_INFO_message_to_slack_channel

load_dotenv() 

# CoinGecko API endpoint
coingecko_url = "https://pro-api.coingecko.com/api/v3"

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
david_channel = 'D05DLG37GSY'

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
        else:
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



def get_100_gainers_and_losers():

    try:
        response = requests.get(f'{coingecko_url}/coins/top_gainers_losers?vs_currency=usd&duration=24h&top_coins=300', headers=headers)
        if response.status_code == 200:
            coins = response.json()

            top_gainers = coins.get('top_gainers', [])
            top_losers = coins.get('top_losers', [])
            print('top_gainers:', len(top_gainers))
            print('top_losers:', len(top_losers))
          
            send_list_of_coins(top_gainers, title=f"Top {len(top_gainers)} Gainers")
            send_list_of_coins(top_losers, title=f"Top {len(top_losers)} Losers")
           
        else:
            print('response.content: ', response.content)
            return response.content, response.status_code

    except Exception as e:
        print(f'Error getting 100 gainers and losers, {str(e)}')
        return f'Error getting 100 gainers and losers, {str(e)}', 500


def get_200_gainers_and_losers():

    try:
        coins_response, status = get_list_of_coins()

        if status == 200:

            # write all available coins in Coingecko into a txt file
            with open("all_available_coins.txt", 'w') as file:
                json.dump(coins_response, file, indent=2)

            print('All available coins:', len(coins_response))
            
            batch_size = 100
            batches = [coins_response[i:i+batch_size] for i in range(0, len(coins_response), batch_size)]

            # Create list of strings with ids
            result_list = []
            separator = "%2C%20"
            for batch in batches:
                ids_string = separator.join(coin["id"] for coin in batch)
                result_list.append(ids_string)

            # Request data in batches
            coins_data = []
            for coins_string in result_list:
                URL = f"{coingecko_url}/coins/markets?vs_currency=usd&ids={coins_string}&order=market_cap_desc&sparkline=false&price_change_percentage=24h&locale=en"
                coins_value = requests.get(URL, headers=headers)
                if coins_value.status_code == 200:
                    coins_data.extend(coins_value.json())
                else:
                    print('coins_value:', coins_value.content)
                    continue

            # Write all the data of the available coins into a txt file            
            with open("all_available_coins_data.txt", 'w') as file:
                json.dump(coins_data, file, indent=2)

            # Filter the data
            filtered_crypto_list = [
                x for x in coins_data
                if x.get("market_cap") is not None
                and x.get("market_cap") > 0
                and x.get("price_change_percentage_24h") is not None
                and x.get("total_volume") is not None
                # and x.get("total_volume") >= 50000
            ]

            # Sort the data from Higest to lowest market cap
            sorted_data = sorted(filtered_crypto_list, key=lambda x: x['market_cap'], reverse=True)
            top_200_coins = sorted_data[:200]

            # Write the top 200 sorted coins data 
            with open('top_200_coins.txt', 'w') as file:
                json.dump(top_200_coins, file, indent=2)

            send_list_of_coins(coins=top_200_coins, title="Top 200 Coins Sorted by Market Cap")
            return 'Top 200 coins sent to Slack', 200

        else:
            return coins_response, status

    except Exception as e:
        print({str(e)})
        return f'Error getting the 200 coins from coingecko: {str(e)}', 200

get_200_gainers_and_losers()
# print(check_price('WagyuSwap'))
# print(calculate_percentage_change_over_buy_price('0.1116','0.129964', 'AIPad'))
# print(percentage_variation('AIPad', '-7.67517', 'weekly'))