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

# Calculate the profit of a coin compared to the Buy Price
def calculate_profit(current_price, buy_price, total_quantity):
    try:
        if not current_price or not buy_price or not total_quantity:
            print("Can't calculate profit, not all required values are present")
            return False

        # Ensure input values are numeric
        current_price = float(current_price)
        buy_price = float(buy_price)
        total_quantity = float(total_quantity)

        # Ensure non-negative values for prices and number of coins
        if current_price < 0 or buy_price < 0 or total_quantity < 0:
            raise ValueError("Prices and number of coins must be non-negative.")

        # Calculate profit using the provided formula
        profit = (current_price - buy_price) * total_quantity

        return profit

    except ValueError as ve:
        print(f"Error: {ve}")
        return False

    except Exception as e:
        print(f"An unexpected error occurred: {e}" )
        return False

# Gets the items of the boards along with its, ID, name, column values, buy price of the coin and board details - MONDAY NATIVE API
def get_board_items(board_ids, limit=500):

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
                
                column_ids = {}

                # Finds the column ID of the Code column
                code_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Code".casefold().strip():
                        code_column_id = item["id"]
                        column_ids['code_column_id'] = item["id"]
                
                # Finds the column ID of the Quantities column
                quantity_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Quantity".casefold().strip():
                        quantity_column_id = item["id"]
                
                second_quantity = None
                for item in columns:
                    if item["title"].casefold().strip() == "2nd Quantity".casefold().strip():
                        second_quantity = item["id"]
                
                third_quantity = None
                for item in columns:
                    if item["title"].casefold().strip() == "3rd Quantity".casefold().strip():
                        third_quantity = item["id"]
                
                fouth_quantity = None
                for item in columns:
                    if item["title"].casefold().strip() == "4th Quantity".casefold().strip():
                        fouth_quantity = item["id"]
                
                fifth_quantity = None
                for item in columns:
                    if item["title"].casefold().strip() == "5th Quantity".casefold().strip():
                        fifth_quantity = item["id"]

                # Finds the column ID of the Buy Price column
                buy_price_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Buy Price".casefold().strip():
                        buy_price_column_id = item["id"]
                        column_ids['buy_price_column_id'] = item["id"]

                # Finds the column ID of the Valuation Price column
                valuation_price_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Valuation Price".casefold().strip():
                        valuation_price_column_id = item["id"]
                        column_ids['valuation_price_column_id'] = item["id"]

                # Finds the column ID of the % Change column
                percentage_change_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "% Change".casefold().strip():
                        percentage_change_column_id = item["id"]
                        column_ids['percentage_change_column_id'] = item["id"]

                # Finds the column ID of the PProjected Value column
                projected_value_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Projected Value".casefold().strip():
                        projected_value_column_id = item["id"]
                        column_ids['projected_value_column_id'] = item["id"]

                for item in items:
                    item_name = item['name'].casefold().strip()
                    item_id = item['id']
                    column_values = item['column_values']

                    symbol = None
                    buy_price = None
                    total_quantity_value = None
                    for row in column_values:
                        if row['id'] == code_column_id:
                            symbol = row['text'].casefold().strip()

                        if row['id'] == buy_price_column_id:
                            buy_price = row['text']
                        
                        if quantity_column_id and row['id'] == quantity_column_id:
                            if row['text']:
                                total_quantity_value = float(row['text'])
                        if second_quantity and row['id'] == second_quantity:
                            if row['text']:
                                total_quantity_value = total_quantity_value + float(row['text'])
                        if third_quantity and row['id'] == third_quantity:
                            if row['text']:
                                total_quantity_value = total_quantity_value + float(row['text'])
                        if fouth_quantity and row['id'] == fouth_quantity:
                            if row['text']:
                                total_quantity_value = total_quantity_value + float(row['text'])
                        if fifth_quantity and row['id'] == fifth_quantity:
                            if row['text']:
                                total_quantity_value = total_quantity_value + float(row['text'])

                    coins_data.append({'coin_name': item_name, 'coin_id': item_id, 'board_id': board_id, 
                                      'total_quantity_value': total_quantity_value, 'column_ids': column_ids,
                                    'board_name': board_name, 'coin_symbol': symbol, 'buy_price': buy_price,
                                    })

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
        response_data = response.json()
        
        if 'error_code' in response_data:
            error_message = response_data['error_message']
            print(f'--- Error changing column value: {error_message}---')
            return False
        elif 'data' in response_data and 'change_column_value' in response_data['data']:
            return True
        else:
            print('--- Unexpected response format ---')
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


# print(get_board_items(board_ids=[1366238676]))
