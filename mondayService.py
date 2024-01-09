import os 
import requests
from monday import MondayClient
from monday.exceptions import MondayError
from coingeckoService import get_list_of_coins
from dotenv import load_dotenv
load_dotenv() 

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_API_KEY_PERSONAL = os.getenv("MONDAY_API_KEY_PERSONAL")
MONDAY_API_KEY_NOVATIDE = os.getenv("MONDAY_API_KEY_NOVATIDE")


monday = MondayClient(MONDAY_API_KEY_NOVATIDE)
mondayUrl = "https://api.monday.com/v2"

headers = {
    "Content-Type": "application/json",
    "Authorization": MONDAY_API_KEY_NOVATIDE
}

# Fetches the columns, groups... Helper function
def get_board_by_id():

    CEX_board_id = 1355564217
    DEX_board_id = 1355568860

    response = monday.boards.fetch_boards_by_id(board_ids=[1355568860, 1355564217])
    boards = response['data']['boards']
    return boards


# Fetches its main items from the MAIN COLUMN
def get_values_column():

    CEX_board_id = 1355564217
    DEX_board_id = 1355568860

    try:
        response = monday.boards.fetch_items_by_board_id(board_ids=[DEX_board_id])
        boards = response['data']['boards']

        if boards:
            coins = []
            list_of_coins, status = get_list_of_coins()

            if status == 200:
                print('Processing Monday values...')
                for board in boards:
                    items = board['items']
                    board_name = board['name']
                
                    if board_name == 'DEX Balance Sheet':
                        board_id = 1355568860
                        column_id = 'numbers7'
                    else:
                        board_id = 1355564217
                        column_id = 'numbers7'

                    for item in items:
                        item_value = item['name'].casefold().strip()
                        item_id = item['id']
                        column_values = item['column_values']

                        symbol = None
                        buy_price = None
                        for row in column_values:
                            if row['id'] == 'text':
                                symbol = row['text'].casefold()

                            if row['id'] == 'numbers6':
                                buy_price = row['text']

                        for coin in list_of_coins:
                            if item_value == coin['name'].casefold() and symbol == coin['symbol'].casefold():
                                item_name = coin['id']
                                coins.append({'coin': item_name, 'id': item_id, 'board_id': board_id, 'column_id': column_id, 'buy_price': buy_price})

                print('Len: ', len(coins))
                return {'coins': coins}
            
            print(list_of_coins)    
            return {'error': list_of_coins}

        print('No board was found')    
        return {'error': 'No board was found'}
    
    except MondayError as e:
        print(f'Monday error {str(e)}')
        return {'error': f'Monday error {str(e)}'}

    except Exception as e:
        print(f'Error getting values from Monday Column {str(e)}')
        return {'error': f'Error getting values from Monday column {str(e)}'}


# Updates an Item in Monday board
def update_value(board_id, item_id, column_id, value, item_name):

    try:            
        response = monday.items.change_item_value(board_id=board_id, item_id=item_id, column_id=column_id, value=value)
        if 'error_code' not in response:
            return True
        
        print(response['error_message'])
        return False

    except MondayError as e:
        print(f'Monday error {str(e)}')
        return False

    except Exception as e:
        print(f'Error updating {item_name} value {str(e)}')
        return False


def make_update_over_price(item_id, value):

    try:
        update = monday.updates.create_update(item_id=item_id, update_value=value)
        if 'data' in update:
            return True
        else:
            return False
    except Exception as e:
        print(str(e))
        return False


# Creates an update over a coin and notifies.
def make_update_notification(user_id, item_id, value):

    query = """
    mutation ($user_id: Int!, $item_id: Int!, $value: String!) {
        create_notification (
            user_id: $user_id,
            target_id: $item_id,
            text: $value,
            target_type: Project
        ) {
            text
        }
    }
    """

    variables = {
        "user_id": user_id,
        "item_id": int(item_id),
        "value": str(value),
    }

    data = {
        "query": query,
        "variables": variables
    }

    try:
        response = requests.post(mondayUrl, headers=headers, json=data)

        if response.status_code == 200:
            return True
        else:
            return False

    except Exception as e:
        print(f'Error found creating update {str(e)}')
        return False




# update_value(board_id=1355564217, item_id=1355566335, column_id='numbers7', value=0, item_name='polylastic')
# print(make_update_over_price(user_id=53919924, item_id=1355566335, value=f'polylastic has grown 10%', item_name='polylastic'))
# print(get_values_column())
