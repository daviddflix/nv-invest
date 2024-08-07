import requests
import json
from ast import literal_eval
from monday.exceptions import MondayError
# from services.monday.monday_client import monday_client, monday_url, MONDAY_API_KEY_NOVATIDE

import os 
from monday import MondayClient
from dotenv import load_dotenv
load_dotenv() 

MONDAY_API_KEY_NOVATIDE = os.getenv("MONDAY_API_KEY_NOVATIDE")

monday_client = MondayClient(MONDAY_API_KEY_NOVATIDE)
monday_url = "https://api.monday.com/v2"

headers = {
    "Content-Type": "application/json",
    "Authorization": MONDAY_API_KEY_NOVATIDE
}

# Define a SUM function to handle the SUM in the formula
def SUM(*args):
    return sum(args)

# ---------------------------- NV BOT S&R ----------------------

# Get all private board, if search param is passed, the board that match the param will be return
def get_all_boards(search_param=None, board_kind='private'):
    """
    Retrieve all private boards, with optional filtering by a search parameter.

    This function queries a Monday.com API to get all boards of a specified kind 
    (default is 'private'). If a search parameter is provided, only the boards 
    whose names contain the search parameter (case-insensitive) will be returned.

    Parameters:
    search_param (str, optional): The term to filter board names by. Defaults to None.
    board_kind (str, optional): The kind of boards to retrieve (e.g., 'private', 'public'). 
                                Defaults to 'private'.

    Returns:
    dict: A dictionary containing the result of the operation:
          - 'error' (str or None): Error message if an error occurred, else None.
          - 'success' (bool): True if the operation was successful, False otherwise.
          - 'data' (list or None): A list of boards if successful, else None.
    """
    
    query = f"""
    query {{
      boards(board_kind: {board_kind}, limit: 200) {{
        id 
        name
        board_kind
      }}
    }}
    """
    
    result = {
        'error': None,
        'success': False,
        'data': None
    }

    try:
        response = requests.post(monday_url, headers=headers, json={'query': query})
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()

        # Check for errors in the response
        if 'errors' in data:
            result['error'] = data['errors']
        else:
            boards = data['data']['boards']
            if search_param:
                # Filter boards based on the search parameter
                boards = [board for board in boards if search_param.lower() in board['name'].lower()]
            
            result['success'] = True
            result['data'] = boards
    
    except requests.exceptions.RequestException as e:
        result['error'] = str(e)
    
    except Exception as e:
        result['error'] = str(e)
    
    return result


# Get column id, name and value of each column and row in the boards
def get_board_item_general(board_ids, limit=500):
    result = {'error': None, 'data': [], 'success': False}
    
    if not board_ids or not isinstance(board_ids, list):
        result['error'] = 'Invalid board_ids parameter. It should be a non-empty list.'
        return result
    
    if not isinstance(limit, int) or limit <= 0:
        result['error'] = 'Invalid limit parameter. It should be a positive integer.'
        return result

    board_ids_str = ', '.join(map(str, board_ids))
    
    query = f'''
    query {{
        boards(ids: [{board_ids_str}]) {{
            id
            name
            columns {{
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
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()
        
        if 'errors' in data:
            result['error'] = data['errors']
        else:
            boards = data['data']['boards']
            transformed_data = []
            
            for board in boards:
                board_data = {
                    'board_name': board['name'],
                    'board_id': board['id'],
                    'data': []
                }
                
                columns_dict = {col['id']: col['title'] for col in board['columns']}
                
                for item in board['items_page']['items']:
                    item_data = {
                        'column_id': item['id'],
                        'column_name': item['name'],
                        'column_values': [
                            {
                                'column_id': col_val['id'],
                                'column_name': columns_dict[col_val['id']],
                                'column_value': col_val['text']
                            } for col_val in item['column_values'] if col_val['text'] is not None
                        ]
                    }
                    board_data['data'].append(item_data)
                
                transformed_data.append(board_data)
            
            result['data'] = transformed_data
            result['success'] = True

    except requests.exceptions.RequestException as e:
        result['error'] = str(e)
    
    except Exception as e:
        result['error'] = str(e)
    
    return result

# Get column id, name and value of each column and row in the boards
def get_board_item_general_test(board_ids, limit=500):
    result = {'error': None, 'data': [], 'success': False}
    
    if not board_ids or not isinstance(board_ids, list):
        result['error'] = 'Invalid board_ids parameter. It should be a non-empty list.'
        return result
    
    if not isinstance(limit, int) or limit <= 0:
        result['error'] = 'Invalid limit parameter. It should be a positive integer.'
        return result

    board_ids_str = ', '.join(map(str, board_ids))
    
    query = f'''
    query {{
        boards(ids: [{board_ids_str}]) {{
            id
            name
            columns {{
                title
                id
                settings_str
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
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()
        
        if 'errors' in data:
            result['error'] = data['errors']
        else:
            boards = data['data']['boards']
            transformed_data = []
            
            for board in boards:
                board_data = {
                    'board_name': board['name'],
                    'board_id': board['id'],
                    'data': []
                }
                
                columns_dict = {col['id']: col['title'] for col in board['columns']}
                columns_formulas = {col['id']: col['settings_str'] for col in board['columns']}
                
                for item in board['items_page']['items'][:1]:
                    item_data = {
                        'item_id': item['id'],
                        'item_name': item['name'],
                        'column_values': []
                    }

                    column_values_dict = {col_val['id']: col_val['text'] for col_val in item['column_values']}
                   
                    for col_val in item['column_values']:
                        column_formula = json.loads(columns_formulas[col_val['id']])
                        is_formula = column_formula.get('formula', None)

                        # Replace column IDs with actual values
                        formula = is_formula
                        if is_formula:
                            for column_id, column_value in column_values_dict.items():
                                column_value = column_value if column_value else 0
                                formula = str(formula).replace("\n", "")
                                formula = formula.replace(f"{{{column_id}}}", str(column_value))

                        column_value_final = col_val['text']
                        # Evaluate the formula
                        if is_formula:
                            
                            try:
                                column_value_final = eval(formula, {"SUM": SUM, "__builtins__": {}})
                            except Exception as e:
                                column_value_final = f'Error in formula: {str(e)}'
                       
                        
                        item_data['column_values'].append({
                            'type': 'formula' if is_formula else 'string',
                            'column_id': col_val['id'],
                            'column_name': columns_dict[col_val['id']],
                            'column_value': column_value_final,
                            'formula': formula if is_formula else None,
                            'raw_formula': is_formula if is_formula else None
                        })

                    board_data['data'].append(item_data)
                
                transformed_data.append(board_data)
            
            result['data'] = transformed_data
            result['success'] = True

    except requests.exceptions.RequestException as e:
        result['error'] = str(e)
    
    except Exception as e:
        result['error'] = str(e)
    
    return result


# ----------------------- NV BOT -------------------------

# Creates a new notification in the Monday Notification center - MONDAY NATIVE API
def create_notification(user_id, item_id, value):
    """
    Creates a new notification in the Monday.com Notification center using the MONDAY NATIVE API.

    This function sends a GraphQL mutation to create a notification for a specified user and item.

    Parameters:
    user_id (int): The ID of the user to notify.
    item_id (int): The ID of the item to associate with the notification.
    value (str): The text content of the notification.

    Returns:
    bool: True if the notification was created successfully, False otherwise.
    """

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
        print('\n--- create_notification_response ---', response.content)
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
            return {'message': "Can't calculate profit, not all required values are present", 'status': False}

        # Ensure input values are numeric
        current_price = float(current_price)
        buy_price = float(buy_price)
        total_quantity = float(total_quantity)

        # Ensure non-negative values for prices and number of coins
        if current_price < 0 or buy_price < 0 or total_quantity < 0:
            raise ValueError("Prices and number of coins must be non-negative.")

        # Calculate profit using the provided formula
        profit = (current_price - buy_price) * total_quantity

        return {'message': profit, 'status': True}

    except ValueError as ve:
        print(f"Error: {ve}")
        return {'message': f"Error: {ve}", 'status': False}

    except Exception as e:
        print(f"An unexpected error occurred: {e}" )
        return {'message': f"An unexpected error occurred: {e}", 'status': False}


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
                    total_quantity_value = 0
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

            # Save coins_data to a text file
            # with open('coins_data.txt', 'w') as file:
            #     for coin in coins_data:
            #         file.write(str(coin) + '\n')
            # print('Len coins:', len(coins_data))
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



def write_new_update(item_id, value):
    """
    Updates the item with a new message using the MONDAY LIBRARY.

    This function attempts to create a new update for a given item ID with the provided value.
    It uses the `monday_client` to interact with the Monday.com API.

    Args:
        item_id (int): The ID of the item to be updated.
        value (str): The value of the update to be written.

    Returns:
        bool: True if the update was successfully created, False otherwise.
    """
    try:
        # Create a new update for the specified item
        update = monday_client.updates.create_update(item_id=item_id, update_value=value)
        print('\nUpdate Monday Item:', update)
        # Check if the update was successfully created
        if 'data' in update and update['data']['create_update']['id']:
            return True
        else:
            return False
    except Exception as e:
        # Handle any exceptions that occur during the update process
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



def get_user_id(email=None):
    """
    Get the user ID of a user in Monday.com based on their email address.
    
    Args:
        api_key (str): Your Monday.com API key.
        email (str): The email address of the user whose ID you want to retrieve.
        
    Returns:
        str: The user ID of the user with the given email address, or None if not found.
    """

    # Query parameters
    query = """
            query {
            users(kind: all) {
                id
                name
                email
            }
            }
        """

    response = requests.get(monday_url, headers=headers, json={"query": query})
    
    if response.status_code == 200:
        users = response.json()["data"]["users"]
        
        if email:
            # Search for the user with the given email address
            for user in users:
                if user["email"] == email:
                    return user
        
        return users
    else:
        # Handle error
        print(f"Error: {response.status_code} - {response.text}")
        return None



# Example usage
# user_email = "s.tamulyte@novatidelabs.com"
# print(get_user_id(user_email))


# --------- TESTS ------------------------------

# print(get_column_ids(board_id=1366947918))
# print(write_new_update(item_id=1355566235, value=f'new test'))
# create_notification(user_id=53919924, item_id=1355566235, value="test")
# print(change_column_value(board_id=1355564217, item_id=1355566235, column_id="numbers7", value="0.0002"))


# get_board_items(board_ids=[1364995332])
# print(get_all_boards(search_param="Master Sheet"))
# print(get_board_item_general_test(board_ids=[1397034863]))