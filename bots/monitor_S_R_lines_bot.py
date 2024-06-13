from services.coingecko.coingecko import check_price, get_list_of_coins
from services.slack.actions import send_INFO_message_to_slack_channel
from services.monday.actions import get_all_boards, get_board_item_general, create_notification, write_new_update
from config import Session, Board, Token, TokenAlert
from datetime import datetime, date
from collections import defaultdict

david_user_id = 5391992
MONDAY_TP_ALERTS='C0753RC839P'

# Notifies to #monday-tp-alerts an Error
def log_and_notify_error(error_message,
                         title_message="NV Invest Monitor Bot has an error", 
                         sub_title="Response", 
                         SLACK_CHANNEL_ID=MONDAY_TP_ALERTS):
    print('--- Error message to send: ', error_message)
    # send_INFO_message_to_slack_channel(channel_id=SLACK_CHANNEL_ID, 
    #                                    title_message=title_message, 
    #                                    sub_title=sub_title,
    #                                    message=error_message)


# Notifies to #monday-tp-alerts when a TP is hit
def log_and_notify(message,
                         title_message="NV Invest Monitor Bot", 
                         sub_title="Notification", 
                         SLACK_CHANNEL_ID=MONDAY_TP_ALERTS):
    print('--- Message to send: ', message)
    # send_INFO_message_to_slack_channel(channel_id=SLACK_CHANNEL_ID, 
    #                                    title_message=title_message, 
    #                                    sub_title=sub_title,
    #                                    message=message)


# Function to check if a target price has been hit
def check_target_price(current_price, tp_name, tp_price, token_name):
    try:
        # Check if any required parameters are missing
        if not current_price or not tp_name or not tp_price:
            return {
                'error': "One or more required params are missing",
                'success': False
            }

        # Convert inputs to appropriate types
        current_price = float(current_price)
        formatted_tp_price = float(tp_price)

        # Check if the current price is equal to or has passed the target price
        if current_price > formatted_tp_price:
            return {
                'message': f"{str(token_name).upper()} price has crossed over {tp_name.upper()}: {tp_price}\nCurrent Price: {current_price}",
                'type': f'price has crossed over {tp_name}',
                'success': True
            }
        elif current_price == formatted_tp_price:
            return {
                'message': f"{str(token_name).upper()} price has touched {tp_name.upper()}: {tp_price}\nCurrent Price: {current_price}",
                'type': f'price has touched {tp_name}',
                'success': True
            }
        else:
            return {
                'error': f"The token price hasn't hit any Take Profit yet.\nCurrent Price: {current_price}",
                'success': False
            }
    except ValueError as e:
        return {'error': f'An error occurred while checking the take profit: {str(e)}', 'success': False}
    except Exception as e:
        return {'error': f'An unexpected error occurred: {str(e)}', 'success': False}



# Process each token
# Define the cache globally or in a higher scope
available_tokens_dict = None

def initialize_available_tokens_dict(available_tokens):
    global available_tokens_dict
    available_tokens_dict = {(t['name'].casefold(), t['symbol'].casefold()): t for t in available_tokens}

def process_token(token, available_tokens, board_name):
    global available_tokens_dict
    if available_tokens_dict is None:
        initialize_available_tokens_dict(available_tokens)
    
    token_name = token.get('column_name')
    monday_token_id = token.get('column_id')
    monday_token_values = token.get('column_values')

    if not monday_token_values:
        return

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

    if not token_data['symbol'] or not token_data['average_buy_price'] or not tp_values:
        print(f'{token_name} does not have all required params')
        return

    token_data['tp_values'] = tp_values
    token_data['name'] = token_name
    token_data['monday_id'] = monday_token_id
    token_data['board_name'] = board_name

    with Session() as session:
        existing_token = session.query(Token).filter_by(monday_id=monday_token_id).first()
        if existing_token:
            token_id = existing_token.id
            existing_token.symbol = token_data['symbol']
            existing_token.name = token_data['name']
            existing_token.board_name = token_data['board_name']
            existing_token.average_buy_price = token_data['average_buy_price']
            existing_token.take_profit_1 = tp_values.get('tp1')
            existing_token.take_profit_2 = tp_values.get('tp2')
            existing_token.take_profit_3 = tp_values.get('tp3')
            existing_token.take_profit_4 = tp_values.get('tp4')
            existing_token.updated_at = datetime.now()
        else:
            new_token = Token(
                symbol=token_data['symbol'],
                name=token_data['name'],
                monday_id=token_data['monday_id'],
                board_name=token_data['board_name'],
                average_buy_price=token_data['average_buy_price'],
                take_profit_1=tp_values.get('tp1'),
                take_profit_2=tp_values.get('tp2'),
                take_profit_3=tp_values.get('tp3'),
                take_profit_4=tp_values.get('tp4'),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(new_token)
            session.flush()  # Ensure new_token gets an ID
            token_id = new_token.id
        session.commit()

        key = (token_name.casefold(), token_data['symbol'].casefold())
        available_token = available_tokens_dict.get(key)

        if available_token:
            token['gecko_id'] = available_token['id']
            print(f'Checking the price for {available_token["id"]}')
            price_data = check_price(coin=available_token['id'])

            if not price_data:
                print(f'{token_name} price was not found')
                return

            token_price = price_data.get('current_price')
            token['token_price'] = token_price
            message = None
            type = None
            
            # Check if any TP has been touched
            for tp_name, tp_price in tp_values.items():
                is_tp_hit = check_target_price(current_price=token_price, token_name=token_name, tp_name=tp_name, tp_price=tp_price)
                if is_tp_hit['success']:
                    message = is_tp_hit['message']
                    type = is_tp_hit['type']
                    break

            if message:
                try:
                    existing_alert = session.query(TokenAlert).filter_by(token_id=token_id, type=type.casefold()).filter(TokenAlert.created_at >= date.today()).first()
                  
                    if not existing_alert:
                        new_alert = TokenAlert(
                            token_id=token_id,
                            message=message.casefold(),
                            type=type.casefold(),
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        session.add(new_alert)
                        session.commit()
                        create_notification(user_id=david_user_id, item_id=monday_token_id, value=message)
                        write_new_update(item_id=monday_token_id, value=message)
                        log_and_notify(message=message)
                        token['message'] = message
                    else:
                        print(f"Alert already exists for token {token_name}: {message}")

                except Exception as e:
                    print(f"Error saving alert for {token_name}: {e}")
                    log_and_notify_error(error_message=f"Error saving alert for {token_name}: {e}")


# Main function to monitor tokens
def monday_monitor_prices():
    response = {'error': None, 'data': None, 'message': None, 'success': False}

    try:
        # Fetch available tokens
        available_tokens, status = get_list_of_coins()
        if status != 200:
            response['error'] = 'Error asking for available tokens on CoinGecko'
            log_and_notify_error(error_message='Error asking for available tokens on CoinGecko')
            return response

        print('Available tokens', len(available_tokens))

        # Get all boards
        boards_data = get_all_boards(search_param='take')
        if not boards_data['success']:
            response['error'] = boards_data['error']
            log_and_notify_error(error_message=boards_data['error'])
            return response

        boards = boards_data['data']

        try:
            with Session() as session:
                # Fetch existing boards from the database
                existing_boards = session.query(Board.monday_board_id).all()
                existing_board_ids = {board_id for (board_id,) in existing_boards}

                # Filter out the boards that are already in the database
                boards_to_insert = [
                    {
                        'board_name': board['name'],
                        'monday_board_id': int(board['id']),
                        'board_kind': board['board_kind']
                    } for board in boards if int(board['id']) not in existing_board_ids
                ]

                if boards_to_insert:
                    # Perform bulk insert
                    session.bulk_insert_mappings(Board, boards_to_insert)
                    session.commit()
                    print(f'Inserted {len(boards_to_insert)} new boards into the database.')
                else:
                    print('No new boards to add')

        except Exception as e:
            response['error'] = f'Error saving boards for Monitor Bot: {str(e)}'
            log_and_notify_error(error_message=response['error'])
            return response

        board_ids = [board['id'] for board in boards]
        print('All found boards', len(board_ids))

        # Get board items
        board_items_data = get_board_item_general(board_ids=board_ids)
        if not board_items_data['success']:
            response['error'] = board_items_data['error']
            log_and_notify_error(error_message=board_items_data['error'])
            return response

        items = board_items_data['data']
        print('All found tokens', len(items))

        # Process each item in the board
        for item in items:
            board_name = item.get('board_name')
            data = item.get('data')

            print('\nProcessing board:', board_name)

            if data:
                for token in data:
                    process_token(token, available_tokens, board_name)       

        response['data'] = items
        response['success'] = True
        return response

    except Exception as e:
        error_message = f'Error monitoring tokens: {str(e)}'
        response['error'] = error_message
        log_and_notify_error(error_message=error_message)
        return response

