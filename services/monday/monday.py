import os 
import requests
from monday import MondayClient
from monday.exceptions import MondayError
from services.coingecko.coingecko import get_list_of_coins
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

    # CEX_board_id = 1355564217
    # DEX_board_id = 1355568860
    # KU_COIN_board_id = 1362987416
    # NV_OKX_board_id = 1364995332
    # BYBIT_SEPIA_board_id = 1365577256
    # OKX_SEPIA_INTERNATIONAL_board_id = 1365552286
    # OKX_SEPIA_board_id = 1365759185
    # rabby_wallet_master_sheet=1368448935
    # rajan_metamask_wallet_master_sheet=1367129332
    # metamask_avalanche_wallet_master_sheet=1366240359
    # metamask_bnb_wallet_master_sheet=1366234172
    # metamask_polygon_wallet_master_sheet=1366238676
    # metamask_Optimism_wallet_master_sheet=1366282633
    # keplr_wallet_master_sheet=1366947918
    # hashpack_wallet_master_sheet=1368425094

    board_ids_mapping = {
    'CEX Balance Sheet': {'board_id': 1355564217, 'column_id': 'numbers7'},
    'DEX Balance Sheet': {'board_id': 1355568860, 'column_id': 'numbers7'},
    'KuCoin Master Sheet': {'board_id': 1362987416, 'column_id': 'numbers92'},
    'NV OKX Master Sheet': {'board_id': 1364995332, 'column_id': 'numbers92'},
    'Bybit Sepia Wallet Master Sheet': {'board_id': 1365577256, 'column_id': 'numbers92'},
    'OKX Sepia International Wallet Master Sheet': {'board_id': 1365552286, 'column_id': 'numbers92'},
    'OKX Sepia Wallet Master Sheet': {'board_id': 1365759185, 'column_id': 'numbers92'},
    'Rabby Wallet Master Sheet': {'board_id': 1368448935, 'column_id': 'numbers92'},
    'Rajan Metamask Wallet Master Sheet': {'board_id': 1367129332, 'column_id': 'numbers92'},
    'Metamask Avalanche Wallet Master Sheet': {'board_id': 1366240359, 'column_id': 'numbers92'},
    'Metamask BNB Wallet Master Sheet': {'board_id': 1366234172, 'column_id': 'numbers92'},
    'Metamask Polygon Wallet Master Sheet': {'board_id': 1366238676, 'column_id': 'numbers92'},
    'Metamask Optimism Wallet Master Sheet': {'board_id': 1366282633, 'column_id': 'numbers92'},
    'Keplr Wallet Master Sheet': {'board_id': 1366947918, 'column_id': 'numbers92'},
    'HashPack Wallet Master Sheet': {'board_id': 1368425094, 'column_id': 'numbers92'},
    }

    # Extract the list of board_ids
    board_ids = [mapping['board_id'] for mapping in board_ids_mapping.values()]

    try:
        # response = monday.boards.fetch_items_by_board_id(board_ids=[KU_COIN_board_id, NV_OKX_board_id, BYBIT_SEPIA_board_id,
        #                                                             OKX_SEPIA_board_id, rabby_wallet_master_sheet, rajan_metamask_wallet_master_sheet,
        #                                                             metamask_avalanche_wallet_master_sheet, metamask_bnb_wallet_master_sheet,
        #                                                             metamask_polygon_wallet_master_sheet, metamask_Optimism_wallet_master_sheet,
        #                                                             keplr_wallet_master_sheet, hashpack_wallet_master_sheet
        #                                                             ])
        response = monday.boards.fetch_items_by_board_id(board_ids=board_ids)
        boards = response['data']['boards']
        
        if boards:
            coins = []
            list_of_coins, status = get_list_of_coins()

            if status == 200:
                print('Processing Monday values...')
                for board in boards:
                    items = board['items']
                    board_name = board['name']
                    

                    if board_name in board_ids_mapping:
                        print('board_name: ', board_name)
                        board_id = board_ids_mapping[board_name]['board_id']
                        column_id = board_ids_mapping[board_name]['column_id']
                    else:
                        print('jumped')
                        continue
                
                    # if board_name == 'DEX Balance Sheet':
                    #     board_id = DEX_board_id
                    #     column_id = 'numbers7'
                    # elif board_name == 'KuCoin Master Sheet':
                    #     board_id = KU_COIN_board_id
                    #     column_id = 'numbers92'
                    # elif board_name == 'NV OKX Master Sheet':
                    #     board_id = NV_OKX_board_id
                    #     column_id = 'numbers92'
                    # elif board_name == 'Bybit Sepia Wallet Master Sheet':
                    #     board_id = BYBIT_SEPIA_board_id
                    #     column_id = 'numbers92'
                    # elif board_name == 'OKX Sepia International Wallet Master Sheet':
                    #     board_id = OKX_SEPIA_INTERNATIONAL_board_id
                    #     column_id = 'numbers92'
                    # elif board_name == 'OKX Sepia Wallet Master Sheet':
                    #     board_id = OKX_SEPIA_board_id
                    #     column_id = 'numbers92'
                    # else:
                    #     board_id = CEX_board_id
                    #     column_id = 'numbers7'

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
                                coins.append({'coin': item_name, 'id': item_id, 'board_id': board_id, 'column_id': column_id, 'buy_price': buy_price, 'board_name': board_name})

                print('Total coins: ', len(coins))
                return {'coins': coins}
            else:
                print('list_of_coins response: ', list_of_coins)    
                return {'error': list_of_coins}

        print('No board was found')    
        return {'error': 'No board was found'}
    
    except MondayError as e:
        print(f'Monday error {str(e)}')
        return {'error': f'Monday error: {str(e)}'}

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


# Updates the price of a coin on Monday
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


# Creates an update over a coin when this one is click on Monday.com and notifies.
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
