import json
from datetime import date, datetime
from sqlalchemy import func
from typing import List, Dict, Any
from sqlalchemy import Date, cast
from collections import defaultdict
from config import session, Coin, Alert, Board
from services.slack.actions import send_INFO_message_to_slack_channel
from services.monday.actions import (get_board_items, get_board_item_general,
                           change_column_value, get_all_boards,
                           create_notification, calculate_profit,
                           write_new_update)

from services.coingecko.coingecko import (check_price, get_list_of_coins,
                              calculate_percentage_change_over_buy_price, 
                              percentage_variation_daily, 
                              percentage_variation_week)

david_user_id = 53919924
catalina_user_id = 61348775
aman_user_id = 53919777
rajan_user_id = 53845740
kontopyrgou_user_id = 53889497
DEX_board_id = 1355568860
LOGS_SLACK_CHANNEL='C06FTS38JRX'
MONDAY_TP_ALERTS='C0753RC839P'
MONDAY_PRICE_VOLATILITY_SLACK_CHANNEL="C078K2GKG20"
MONDAY_AUTOMATIONS_SLACK_CHANNEL="C0785HRL8G3"

users_ids = [david_user_id]

# Notifies to #monday-tp-alerts an Error or TP is hit
def log_and_notify(error_message,
                         title_message="NV Invest Bot has an error", 
                         sub_title="Error", 
                         SLACK_CHANNEL_ID=MONDAY_TP_ALERTS):
    print('--- Error message to send: ', error_message)
    # send_INFO_message_to_slack_channel(channel_id=SLACK_CHANNEL_ID, 
    #                                    title_message=title_message, 
    #                                    sub_title=sub_title,
    #                                    message=error_message)


# Process each token
# Define the cache globally
available_tokens_dict = None


# Helper to save a list of Dicts to JSON
def save_to_json(obj_list, filename):
    """
    Saves a list of objects to a JSON file.
    
    Parameters:
    obj_list (list): List of objects to save.
    filename (str): The name of the JSON file to save to.
    """
    try:
        with open(filename, 'w') as json_file:
            json.dump(obj_list, json_file, indent=4)
        print(f"----Successfully saved to {filename}----")
    except Exception as e:
        print(f"Error saving to {filename}: {e}")


# Batch request of tokens
def batch_list(input_list, batch_size):
    """Yield successive n-sized chunks from the input_list."""
    for i in range(0, len(input_list), batch_size):
        yield input_list[i:i + batch_size]


def initialize_available_tokens_dict(available_tokens):
    global available_tokens_dict
    available_tokens_dict = {(t['name'].casefold(), t['symbol'].casefold()): t for t in available_tokens}


# Validates each coin against CoinGecko list of coins, if coin is valid, then it's added to the DB
def process_coins(coin, available_tokens, board_name, board_id):
    from collections import defaultdict
    from datetime import datetime

    response = {'error': None, 'data': None, 'message': None, 'success': False, 'item_id': None}

    global available_tokens_dict
    if available_tokens_dict is None:
        initialize_available_tokens_dict(available_tokens)

    token_name = coin.get('column_name')
    monday_token_id = coin.get('column_id')
    monday_token_values = coin.get('column_values')

    response['item_id'] = monday_token_id

    print(f"\n--- Processing {token_name} ----")

    if not monday_token_values:
        print(f"No values for {board_name}")
        response['error'] = f"No values found in {token_name}"
        return response

    # Create a defaultdict
    token_data = defaultdict(lambda: None)

    for value in monday_token_values:
        column_name = str(value['column_name']).lower().strip()
        column_value = value['column_value']
        column_id = value['column_id']

        if column_name == "code":
            token_data['symbol'] = column_value
        if column_name == "valuation price":
            token_data['valuation_price_id'] = column_id

    if not token_data['symbol'] or not token_data['valuation_price_id']:
        print(f'{str(token_name).capitalize()} does not have all required parameters')
        response['error'] = f'{str(token_name).capitalize()} does not have all required parameters'
        return response

    symbol = token_data['symbol']
    valuation_price_id = token_data['valuation_price_id']

    # Check if the coin is already in the database
    existing_coin = session.query(Coin).filter_by(coin_id=monday_token_id).first()

    if not existing_coin:
        # Create a new coin
        new_coin = Coin(
            coin_id=monday_token_id,
            coin_name=token_name,
            coin_symbol=symbol,
            buy_price='',
            total_quantity_value='0',
            board_id=board_id,
            board_name=board_name,
            valuation_price_column_id=valuation_price_id,
            percentage_change_column_id='',
            projected_value_column_id='',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(new_coin)
        session.commit()
        print(f'Added new coin: {token_name}')
        for user_id in users_ids:
            create_notification(user_id=user_id,
                                item_id=monday_token_id,
                                value=f"{token_name} was added to the Monday Bot"
                                )
    else:
        # Update existing coin if name or symbol has changed
        if existing_coin.coin_name != token_name or existing_coin.coin_symbol != symbol:
            existing_coin.coin_name = token_name
            existing_coin.coin_symbol = symbol
            existing_coin.updated_at = datetime.now()
            session.commit()
            print(f'Updated coin: {token_name} with new name or symbol')

    key = (token_name.casefold(), token_data['symbol'].casefold())
    available_token = available_tokens_dict.get(key)

    if not available_token:
        print(f'{str(token_name)} was not found on Coingecko, please check availability on the website.')
        response['error'] = f'{str(token_name)} was not found on Coingecko, please check availability on the website.'
        return response

    price_change_daily = None
    token_data['gecko_id'] = available_token['id']
    price_data = check_price(coin=available_token['id'])

    if price_data and price_data.get('current_price'):
        token_price = price_data.get('current_price')
        price_change_daily = price_data.get('price_change_daily')
        token_data['token_price'] = token_price
        print(f"price for {token_name} is ${token_price}")

        # update price on Monday.com
        if token_price:
            change_column_value(board_id=board_id,
                                item_id=monday_token_id,
                                column_id=valuation_price_id,
                                value=token_price)
            print("--- Price update on Monday ----")

        if price_change_daily:
            if float(price_change_daily) >= 20 or float(price_change_daily) <= -20:
                direction_daily = "increased" if float(price_change_daily) >= 20 else "decreased"
                message_daily = f"The price of {token_name.capitalize()} has {direction_daily.upper()} by {price_change_daily}% today."
                print("message_daily: ", message_daily)
                log_and_notify(error_message=message_daily,
                               title_message="NV Invest Bot",
                               sub_title="Alert",
                               SLACK_CHANNEL_ID=MONDAY_PRICE_VOLATILITY_SLACK_CHANNEL
                               )
            else:
                print("price_change_daily: ", price_change_daily)

    response['success'] = True
    return response

    


# Saves the board in the DB
def process_boards(boards):
    response = {'error': None, 'data': None, 'message': None, 'success': False}

    if not boards:
        response['error'] = "Boards data is required"
        return response

    try:
        for board in boards:
            id = board.get('id')
            name = board.get('name')
            if id and name:
                existing_board = session.query(Board).filter(func.lower(Board.board_name) == name.lower()).first()
                if not existing_board:
                    new_board = Board(
                        monday_board_id=id,
                        board_name=name.lower()
                    )
                    session.add(new_board)
                    print(f"---Saved to DB: {name}---")
                    for user_id in users_ids:
                        create_notification(user_id=user_id,
                                            item_id=id,
                                            value=f"{name} board was added to the Monday Bot"
                                            )
        
        print("--- All Monday Boards are saved to the DB ---")
        session.commit()
        response['success'] = True
        response['message'] = "Boards processed successfully"
        response['data'] = boards
        return response
    
    except Exception as e:
        response['error'] = f"Main error processing  boards: {str(e)}"
        return response


# Main
def activate_nv_invest_bot():

    response = {'error': None, 'data': None, 'message': None, 'success': False}
    start = datetime.now()
    print("start: ", start)

    # Fetch available tokens
    available_tokens, status = get_list_of_coins()
    if status != 200:
        response['error'] = 'Error asking for available tokens on CoinGecko'
        log_and_notify(error_message='Error getting available tokens on CoinGecko',
                       SLACK_CHANNEL_ID=MONDAY_AUTOMATIONS_SLACK_CHANNEL
                       )
        return response

    print('Available tokens on Coingecko', len(available_tokens))

    # Get all boards
    boards_data = get_all_boards(search_param='master')
    if not boards_data['success']:
        response['error'] = boards_data['error']
        log_and_notify(error_message=f"Failure getting Monday boards: {boards_data['error']}",
                       SLACK_CHANNEL_ID=MONDAY_AUTOMATIONS_SLACK_CHANNEL
                       )
        return response

    boards = boards_data['data']
    print("boards", boards)
    # Saves to DB
    boards_result = process_boards(boards=boards)
    if not boards_data['success']:
        response['error'] = boards_result['error']
        log_and_notify(error_message=boards_result['error'],
                       SLACK_CHANNEL_ID=MONDAY_AUTOMATIONS_SLACK_CHANNEL
                       )
        return response

    board_ids = [board['id'] for board in boards]
    print('All found boards', len(board_ids))

    # Get board items
    all_items = []

    # Process board_ids in batches of 20
    for batch in batch_list(board_ids, 20):
        board_items_data = get_board_item_general(board_ids=batch)
        if not board_items_data['success']:
            response['error'] = board_items_data['error']
            log_and_notify(error_message=board_items_data['error'],
                           SLACK_CHANNEL_ID=MONDAY_AUTOMATIONS_SLACK_CHANNEL
                           )
        all_items.extend(board_items_data['data'])
   
    print('All found tokens', len(all_items))

    # Process each item in the board
    for item in all_items:
        board_name = item.get('board_name')
        board_id = item.get('board_id')
        data = item.get('data')

        print('\nProcessing board:', f"{board_name} ({len(data)})")

        if data:
            for token in data:
                process_coins(token, available_tokens, board_name, board_id)   

    end = datetime.now()
    print('Time spent:', end - start)   
             
    response['data'] = all_items
    response['success'] = True
    return response


