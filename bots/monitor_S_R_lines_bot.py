from services.coingecko.coingecko import check_price, get_list_of_coins
from services.slack.actions import send_INFO_message_to_slack_channel
from services.monday.actions import get_all_boards, get_board_item_general, create_notification, write_new_update
from config import Session, Board, Token, TokenAlert
from datetime import datetime, date, date
from collections import defaultdict
from typing import Optional, List, Dict, Any
import json

david_user_id = 5391992
MONDAY_TP_ALERTS='C0753RC839P'

# Define the local cache globally
available_tokens_dict = None

def create_slack_notification(message: str,
                              is_error: bool = False,
                              title_message: Optional[str] = None,
                              sub_title: Optional[str] = None,
                              SLACK_CHANNEL_ID: str = MONDAY_TP_ALERTS) -> None:
    """
    Log and notify a message to a specified Slack channel.
    
    Parameters:
    - message: str - The message to log and notify.
    - is_error: bool - Indicates if the message is an error message.
    - title_message: Optional[str] - The title of the message.
    - sub_title: Optional[str] - The subtitle of the message.
    - SLACK_CHANNEL_ID: str - The Slack channel ID to send the message to.
    
    Returns:
    - None
    """
    title_message = title_message or ("NV Invest Monitor Bot has an error" if is_error else "NV Invest Monitor Bot")
    sub_title = sub_title or ("Response" if is_error else "Notification")
    print(f'--- {"Error" if is_error else "Message"} to send: {message}')
    
    send_INFO_message_to_slack_channel(
        channel_id=SLACK_CHANNEL_ID, 
        title_message=title_message, 
        sub_title=sub_title,
        message=message
    )

def check_target_price(current_price, tp_name, tp_price, token_name: str):
    """
    Check if a target price has been hit for a given token.

    Parameters:
    - current_price - The current price of the token.
    - tp_name - The name of the target price (e.g., 'TP1', 'TP2').
    - tp_price - The value of the target price.
    - token_name - The name of the token.

    Returns:
    - dict: A dictionary containing the result of the check.
        - 'message' (str): Information about the target price status.
        - 'type' (str): The type of price movement.
        - 'success' (bool): Whether the check was successful.
        - 'error' (str, optional): Error message if the check was not successful.
    """
    missing_params = [param for param, name in zip([current_price, tp_name, tp_price], ["current_price", "tp_name", "tp_price"]) if not param]
    
    if missing_params:
        return {
            'error': f"One or more required parameters are missing: {', '.join(missing_params)}",
            'success': False
        }

    try:
        current_price = float(current_price)
        tp_price = float(tp_price)
    except ValueError as e:
        return {
            'error': f"An error occurred while converting prices to float: {str(e)}",
            'success': False
        }

    if current_price > tp_price:
        message = f"{token_name.upper()} price has crossed over {tp_name.upper()}: {tp_price}\nCurrent Price: {current_price}"
        movement_type = f'price has crossed over {tp_name}'
        success = True
    elif current_price == tp_price:
        message = f"{token_name.upper()} price has touched {tp_name.upper()}: {tp_price}\nCurrent Price: {current_price}"
        movement_type = f'price has touched {tp_name}'
        success = True
    else:
        return {
            'error': f"The token price hasn't hit any Take Profit yet.\nCurrent Price: {current_price}",
            'success': False
        }

    return {
        'message': message,
        'type': movement_type,
        'success': success
    }

def monday_monitor_prices():
    """
    Main function to monitor token prices.

    This function performs the following tasks:
    1. Fetches the list of available tokens from CoinGecko.
    2. Retrieves all boards from a specified source.
    3. Inserts new boards into the database if they are not already present.
    4. Retrieves items from the boards and processes each token.
    5. Saves processed data to the database.

    Returns:
        dict: A response dictionary containing 'error', 'data', 'message', and 'success' keys.
    """
    response = {'error': None, 'data': None, 'message': None, 'success': False}

    try:
        # Fetch available tokens
        available_tokens, status = get_list_of_coins()
        if status != 200:
            response['error'] = 'Error asking for available tokens on CoinGecko'
            create_slack_notification(message='Error asking for available tokens on CoinGecko', is_error=True)
            return response

        print(f'Available tokens: {len(available_tokens)}')

        # Initialize the global available_tokens_dict
        initialize_available_tokens_dict(available_tokens)

        # Get all boards
        boards_data = get_all_boards(search_param='take')
        if not boards_data['success']:
            response['error'] = boards_data['error']
            create_slack_notification(message=boards_data['error'], is_error=True)
            return response

        boards = boards_data['data']

        # Save new boards to database
        save_new_boards(boards)

        board_ids = [board['id'] for board in boards]
        print(f'All found boards: {len(board_ids)}')

        # Get boards with its tokens data
        board_items_data = get_board_item_general(board_ids=board_ids)
       
        if not board_items_data['success']:
            response['error'] = board_items_data['error']
            create_slack_notification(message=board_items_data['error'], is_error=True)
            return response

        items = board_items_data['data']
        print(f'All found tokens: {len(items)}')

        # Process each item in the board
        for item in items:
            board_name: str = item.get('board_name')
            data = item.get('data')

            print(f'\nProcessing board: {board_name}')

            if data:
                for token in data:
                    process_token(token, available_tokens, board_name)    

        response['data'] = items
        response['success'] = True
        return response

    except Exception as e:
        error_message = f'Error monitoring tokens: {str(e)}'
        response['error'] = error_message
        create_slack_notification(message=error_message, is_error=True)
        return response

def initialize_available_tokens_dict(available_tokens: List[Dict[str, Any]]) -> None:
    """
    Initialize the global `available_tokens_dict` dictionary with available tokens.

    This function processes a list of token dictionaries and constructs a global dictionary where each key
    is a tuple consisting of the token's name and symbol (both case-insensitive), and the value is the token's
    dictionary. This allows for efficient lookups of token information based on name and symbol.

    Args:
        available_tokens (List[Dict[str, Any]]): A list of dictionaries, where each dictionary contains details
            about a token. Each token dictionary should include at least 'name' and 'symbol' keys.

    Returns:
        None
    """
    global available_tokens_dict
    available_tokens_dict = {(t['name'].casefold(), t['symbol'].casefold()): t for t in available_tokens}

def save_new_boards(boards: List[Dict[str, Any]]) -> None:
    """
    Save new boards to the database.

    This function takes a list of board dictionaries and inserts those that are not already present in the
    database into the `Board` table. It uses SQLAlchemy's `bulk_insert_mappings` to efficiently insert
    multiple records and commits the transaction.

    Args:
        boards (List[Dict[str, Any]]): A list of dictionaries where each dictionary represents a board. Each
            dictionary should include the following keys:
            - 'name': The name of the board.
            - 'id': The unique identifier of the board.
            - 'board_kind': The type or category of the board.

    Returns:
        None

    Raises:
        Exception: If an error occurs while saving boards to the database, an exception is raised, and a notification
            is sent via Slack.
    """
    try:
        with Session() as session:
            existing_boards = session.query(Board.monday_board_id).all()
            existing_board_ids = {board_id for (board_id,) in existing_boards}

            boards_to_insert = [
                {
                    'board_name': board['name'],
                    'monday_board_id': int(board['id']),
                    'board_kind': board['board_kind']
                } for board in boards if int(board['id']) not in existing_board_ids
            ]

            if boards_to_insert:
                session.bulk_insert_mappings(Board, boards_to_insert)
                session.commit()
                print(f'Inserted {len(boards_to_insert)} new boards into the database.')
            else:
                print('No new boards to add')

    except Exception as e:
        error_message = f'Error saving boards for Monitor Bot: {str(e)}'
        create_slack_notification(message=error_message, is_error=True)

def process_token(token: Dict[str, Any], available_tokens: List[Dict[str, Any]], board_name: str) -> bool:
    """
    Process a single token, update database, and create alerts if necessary.

    Args:
        token (Dict[str, Any]): Token data from Monday.com.
        available_tokens (List[Dict[str, Any]]): List of available tokens from CoinGecko.
        board_name (str): Name of the board containing the token.

    Returns:
        bool: True if processing was successful, False otherwise.
    """
    
    token_name = token.get('column_name')
    monday_token_id = token.get('column_id')
    monday_token_values = token.get('column_values')

    print(f'\nToken: {token_name}')

    if not monday_token_values:
        print(f'No Monday values found: {monday_token_values}')
        return False
    
    token_data = extract_token_data(monday_token_values)
    
    if not validate_token_data(token_data, token_name):
        return False
    
    token_data['name'] = token_name
    token_data['monday_id'] = monday_token_id
    token_data['board_name'] = board_name

    token_id = save_token_to_database(token_data)

    # Check if token exists in CoinGecko
    key = (token_name.casefold(), token_data['symbol'].casefold())
    available_token = available_tokens_dict.get(key)

    if not available_token:
        print(f'No matched token found on Coingecko - token: {token_name}')
        return False

    token['gecko_id'] = available_token['id']
    print(f'Checking the price for {available_token["id"]}')
    price_data = check_price(coin=available_token['id'])

    if not price_data:
        print(f'{token_name} price was not found')
        return False

    token_price = price_data.get('current_price')
    token['token_price'] = token_price

    check_and_create_alerts(token, token_data, token_id, token_price, monday_token_id)

    return True

def extract_token_data(monday_token_values: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract important data from Monday.com token values.

    Args:
        monday_token_values (List[Dict[str, Any]]): List of token values from Monday.com.

    Returns:
        Dict[str, Any]: Extracted token data.
    """
    token_data = defaultdict(lambda: None)
    tp_values = {}

    for value in monday_token_values:
        column_name = value['column_name'].lower()
        column_value = value['column_value']
        
        if column_value:
            if column_name == 'code':
                token_data['symbol'] = column_value
            elif column_name == 'average buy price':
                token_data['average_buy_price'] = column_value
            elif column_name.startswith('tp'):
                tp_values[column_name.replace(' ', '')] = column_value

    token_data['tp_values'] = tp_values
    return token_data

def validate_token_data(token_data: Dict[str, Any], token_name: str) -> bool:
    """
    Validate that all required parameters are present in token data.

    Args:
        token_data (Dict[str, Any]): Extracted token data.
        token_name (str): Name of the token.

    Returns:
        bool: True if all required parameters are present, False otherwise.
    """
    required_params = ['symbol', 'average_buy_price']
    missing_params = [param for param in required_params if not token_data.get(param)]
    
    if not token_data['tp_values']:
        missing_params.append('tp_values')

    if missing_params:
        missing_params_str = ', '.join(missing_params)
        print(f"{token_name} does not have all required params: {missing_params_str}")
        return False
    
    return True

def save_token_to_database(token_data: Dict[str, Any]) -> int:
    """
    Save or update token data in the database.

    Args:
        token_data (Dict[str, Any]): Token data to be saved.

    Returns:
        int: ID of the saved token.
    """
    with Session() as session:
        existing_token = session.query(Token).filter_by(monday_id=token_data['monday_id']).first()
        if existing_token:
            update_existing_token(existing_token, token_data)
            token_id = existing_token.id
        else:
            new_token = create_new_token(token_data)
            session.add(new_token)
            session.flush()  # Ensure new_token gets an ID
            token_id = new_token.id
        session.commit()
    return token_id

def update_existing_token(existing_token: Token, token_data: Dict[str, Any]) -> None:
    """
    Update an existing token in the database.

    Args:
        existing_token (Token): Existing token object from the database.
        token_data (Dict[str, Any]): New token data to update.
    """
    existing_token.symbol = token_data['symbol']
    existing_token.name = token_data['name']
    existing_token.board_name = token_data['board_name']
    existing_token.average_buy_price = token_data['average_buy_price']
    existing_token.take_profit_1 = token_data['tp_values'].get('tp1')
    existing_token.take_profit_2 = token_data['tp_values'].get('tp2')
    existing_token.take_profit_3 = token_data['tp_values'].get('tp3')
    existing_token.take_profit_4 = token_data['tp_values'].get('tp4')
    existing_token.updated_at = datetime.now()

def create_new_token(token_data: Dict[str, Any]) -> Token:
    """
    Create a new token object for the database.

    Args:
        token_data (Dict[str, Any]): Token data for the new token.

    Returns:
        Token: New token object.
    """
    return Token(
        symbol=token_data['symbol'],
        name=token_data['name'],
        monday_id=token_data['monday_id'],
        board_name=token_data['board_name'],
        average_buy_price=token_data['average_buy_price'],
        take_profit_1=token_data['tp_values'].get('tp1'),
        take_profit_2=token_data['tp_values'].get('tp2'),
        take_profit_3=token_data['tp_values'].get('tp3'),
        take_profit_4=token_data['tp_values'].get('tp4'),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

def check_and_create_alerts(token: Dict[str, Any], token_data: Dict[str, Any], token_id: int, token_price: float, monday_token_id: int) -> None:
    """
    Check if any take profit levels have been hit and create alerts if necessary.

    Args:
        token (Dict[str, Any]): Token data.
        token_data (Dict[str, Any]): Extracted token data.
        token_id (int): ID of the token in the database.
        token_price (float): Current price of the token.
        monday_token_id (int): ID of the token in Monday.com.
    """
    message = None
    alert_type = None
    
    for tp_name, tp_price in token_data['tp_values'].items():
        is_tp_hit = check_target_price(current_price=token_price, token_name=token_data['name'], tp_name=tp_name, tp_price=tp_price)
        if is_tp_hit['success']:
            message = is_tp_hit['message']
            alert_type = is_tp_hit['type']
            break

    if message:
        create_alert(token_id, message, alert_type, monday_token_id)
        token['message'] = message

def create_alert(token_id: int, message: str, alert_type: str, monday_token_id: int) -> None:
    """
    Create a new alert in the database and send notifications.

    Args:
        token_id (int): ID of the token in the database.
        message (str): Alert message.
        alert_type (str): Type of the alert.
        monday_token_id (int): ID of the token in Monday.com.
    """
    try:
        with Session() as session:
            existing_alert = session.query(TokenAlert).filter_by(token_id=token_id, type=alert_type.casefold()).filter(TokenAlert.created_at >= date.today()).first()
          
            if not existing_alert:
                new_alert = TokenAlert(
                    token_id=token_id,
                    message=message.casefold(),
                    type=alert_type.casefold(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(new_alert)
                session.commit()
                create_notification(user_id=david_user_id, item_id=monday_token_id, value=message)
                write_new_update(item_id=monday_token_id, value=message)
                create_slack_notification(message=message)
            else:
                print(f"Alert already exists for token {token_id}: {message}")

    except Exception as e:
        print(f"Error saving alert for token {token_id}: {e}")
        create_slack_notification(message=f"Error saving alert for token {token_id}: {e}", is_error=True)