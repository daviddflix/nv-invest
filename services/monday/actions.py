import requests
from monday.exceptions import MondayError
from services.monday.monday_client import monday_client, monday_url, MONDAY_API_KEY_NOVATIDE

headers = {
    "Content-Type": "application/json",
    "Authorization": MONDAY_API_KEY_NOVATIDE
}

# Creates a new notification in the Monday Notification center - MONDAY NATIVE API
def create_notification(user_id, item_id, value):

    new_query = f'''
            mutation {{
                create_notification(
                    text: "{value}",
                    user_id: {user_id},
                    target_id: {item_id},
                    target_type: Project
                ) {{
                    id
                }}
            }}
        '''

    try:
        response = requests.post(monday_url, headers=headers, json={'query': new_query})

        if response.status_code == 200:
            return True
        else:
            print(f'Error creating new notififcation: {response.content}')
            return False

    except Exception as e:
        print(f'Error found creating update {str(e)}')
        return False
    

# Gets the items of the boards along with its, ID, name, column values, buy price of the coin and board details - MONDAY NATIVE API
def get_board_items(board_ids, limit=500):

    board_ids = [mapping['board_id'] for mapping in board_ids.values()]

    query = f'''
        query {{
            boards(ids: {board_ids}) {{
                id
                name
                columns{{
                    title
                    id
                }}
                items_page(limit: {limit}) {{
                    items {{
                        id
                        name
                        column_values {{
                            id
                            text
                        }}
                    }}
                }}
            }}
        }}
    '''

    try:
        response = requests.post(monday_url, headers=headers, json={'query': query})
        if response.status_code == 200:
            response_data = response.json()

            coins_data = []
            boards = response_data['data']['boards']
            for board in boards:
                board_id = board['id']
                board_name = board['name']
                columns = board['columns']
                items = board['items_page']['items']
                
                # Finds the ID of the names of the columns in "column_names" param
                column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Valuation Price".casefold().strip():
                        column_id = item["id"]


                for item in items:
                    item_name = item['name'].casefold().strip()
                    item_id = item['id']
                    column_values = item['column_values']

                    symbol = None
                    buy_price = None
                    for row in column_values:
                        if row['id'] == 'text':
                            symbol = row['text'].casefold().strip()

                        if row['id'] == 'numbers6':
                            buy_price = row['text']

                    coins_data.append({'coin_name': item_name, 'coin_id': item_id, 'board_id': board_id, 'valuation_price_column_id': column_id,
                                    'board_name': board_name, 'coin_symbol': symbol, 'buy_price': buy_price})

            # # Save coins_data to a text file
            # with open('coins_data.txt', 'w') as file:
            #     for coin in coins_data:
            #         file.write(str(coin) + '\n')

            return coins_data
        else:
            print(f'Error getting board items: {response.content}')
            return None

    except Exception as e:
        print(f'Error found getting board items: {str(e)}')
        return None


# Changes the value of a column item - MONDAY NATIVE API
def change_column_value(item_id, board_id, column_id, value):
    mutation_query = f'''
        mutation {{
            change_column_value(
                item_id: {item_id},
                board_id: {board_id},
                column_id: "{column_id}",
                value: "{value}"
            ) {{
                id
            }}
        }}
    '''

    try:
        response = requests.post(monday_url, headers=headers, json={'query': mutation_query})

        if response.status_code == 200:
            return True
        else:
            print(f'Error changing column value: {response.content}')
            return False

    except Exception as e:
        print(f'Error found changing column value: {str(e)}')
        return False


# Updates the item with a new message - MONDAY LIBRARY
def write_new_update(item_id, value):
    try:
        update = monday_client.updates.create_update(item_id=item_id, update_value=value)
        if 'data' in update and update['data']['create_update']['id']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error writing new update: {str(e)}")
        return False
    

# Get column IDs for one board - MONDAY LIBRARY
def get_column_ids(board_id):
    try:
        board_info = monday_client.boards.fetch_columns_by_board_id(board_ids=[board_id])
        columns = board_info['data']['boards'][0]['columns']
        
        columns_data = []
        for column in columns:
            title = column['title']
            column_id = column['id']
            columns_data.append({'column_title': title, 'column_id': column_id})
        return columns_data

    except MondayError as e:
        print(f'Error getting column IDs, Monday error: {str(e)}')
        return None

    except Exception as e:
        print(f'Error getting column IDs, error: {str(e)}')
        return None



# --------- TESTS ------------------------------

# print(get_column_ids(board_id=1366947918))
# print(write_new_update(item_id=1355566235, value=f'new test'))
# create_notification(user_id=53919924, item_id=1355566235, value="test")
# print(change_column_value(board_id=1355564217, item_id=1355566235, column_id="numbers7", value="0.0002"))

# board_ids = {
#     'CEX Balance Sheet': {'board_id': 1355564217},
#     'DEX Balance Sheet': {'board_id': 1355568860},
#     'KuCoin Master Sheet': {'board_id': 1362987416},
#     'NV OKX Master Sheet': {'board_id': 1364995332},
#     'Bybit Sepia Wallet Master Sheet': {'board_id': 1365577256},
#     'OKX Sepia International Wallet Master Sheet': {'board_id': 1365552286},
#     'OKX Sepia Wallet Master Sheet': {'board_id': 1365759185},
#     'Rabby Wallet Master Sheet': {'board_id': 1368448935},
#     'Rajan Metamask Wallet Master Sheet': {'board_id': 1367129332},
#     'Metamask Avalanche Wallet Master Sheet': {'board_id': 1366240359},
#     'Metamask BNB Wallet Master Sheet': {'board_id': 1366234172},
#     'Metamask Polygon Wallet Master Sheet': {'board_id': 1366238676},
#     'Metamask Optimism Wallet Master Sheet': {'board_id': 1366282633},
#     'Keplr Wallet Master Sheet': {'board_id': 1366947918},
#     'HashPack Wallet Master Sheet': {'board_id': 1368425094},
#     'Doge Labs Wallet Master Sheet': {'board_id': 1411047183},
#     'Solflare Wallet Master Sheet': {'board_id': 1411045630},
#     'NinjaVault Wallet Master Sheet': {'board_id': 1411045311},
#     }


# get_board_items(board_ids=board_ids)
