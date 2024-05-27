from services.coingecko.coingecko import check_price, get_list_of_coins
from services.slack.actions import send_INFO_message_to_slack_channel
from services.monday.actions import get_all_boards, get_board_item_general, create_notification, write_new_update

david_user_id = 53919924

# Notifies to #monday-tp-alerts an Error
def log_and_notify_error(error_message,
                         title_message="NV Invest Bot has an error", 
                         sub_title="Response", 
                         SLACK_CHANNEL_ID='C0753RC839P'):
    # print('--- Error message to send: ', error_message)
    send_INFO_message_to_slack_channel(channel_id=SLACK_CHANNEL_ID, 
                                       title_message=title_message, 
                                       sub_title=sub_title,
                                       message=error_message)


# Notifies to #monday-tp-alerts when a TP is hit
def log_and_notify(message,
                         title_message="NV Invest Bot", 
                         sub_title="Notification", 
                         SLACK_CHANNEL_ID='C0753RC839P'):
    # print('--- Message to send: ', message)
    send_INFO_message_to_slack_channel(channel_id=SLACK_CHANNEL_ID, 
                                       title_message=title_message, 
                                       sub_title=sub_title,
                                       message=message)


# Function to check if a target price has been hit
def check_target_price(current_price, tp_name, tp_price):
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
        if current_price >= formatted_tp_price:
            return {
                'message': f"The token price has hit {tp_name.upper()}: {tp_price}\nCurrent Price: {current_price}",
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

        print('Getting all available tokens, found:', len(available_tokens))

        # Get all boards
        boards_data = get_all_boards(search_param='take')
        if not boards_data['success']:
            response['error'] = boards_data['error']
            log_and_notify_error(error_message=boards_data['error'])
            return response

        boards = boards_data['data']
        board_ids = [board['id'] for board in boards]

        print('Getting all boards - found:', len(board_ids))

        # Get board items
        board_items_data = get_board_item_general(board_ids=board_ids)
        if not board_items_data['success']:
            response['error'] = board_items_data['error']
            log_and_notify_error(error_message=board_items_data['error'])
            return response

        items = board_items_data['data']
        print('Getting all items, found:', len(items))

        # Process each item in the board
        for item in items:
            board_name = item.get('board_name')
            data = item.get('data')

            print('\nProcessing this board:', board_name)

            if data:
                for token in data:
                    process_token(token, available_tokens)

        response['data'] = items
        response['success'] = True
        return response

    except Exception as e:
        error_message = f'Error monitoring tokens: {str(e)}'
        response['error'] = error_message
        log_and_notify_error(error_message=error_message)
        return response


# Process each token
def process_token(token, available_tokens):
    """
    Process each token to check its price and compare it with target prices.

    Args:
        token (dict): The token data containing 'column_name', 'column_id', and 'column_values'.
        available_tokens (list): List of available tokens with their details.

    """
    token_name = token.get('column_name')
    monday_token_id = token.get('column_id')
    monday_token_values = token.get('column_values')

    if not monday_token_values:
        return

    token_symbol = None
    tp_values = {}

    for value in monday_token_values:
        column_name = str(value['column_name']).casefold()
        column_value = value['column_value']

        if column_name == 'code' and column_value:
            token_symbol = column_value
        elif column_name.startswith('tp'):
            tp_values[column_name.replace(' ', '')] = column_value

    if token_symbol:
        for available_token in available_tokens:
            if (token_name.casefold() == available_token['name'].casefold() and
                    token_symbol.casefold() == available_token['symbol'].casefold()):

                token['gecko_id'] = available_token['id']
                print(f'Checking the price for {available_token["id"]}')
                price_data = check_price(coin=available_token['id'])

                if price_data:
                    token_price = price_data.get('current_price')
                    token['token_price'] = token_price
                    message = None

                    for tp_name, tp_price in tp_values.items():
                        is_tp_hit = check_target_price(current_price=token_price, tp_name=tp_name, tp_price=tp_price)
                        if is_tp_hit['success']:
                            message = is_tp_hit['message']
                            break

                    if message:
                        create_notification(user_id=david_user_id, item_id=monday_token_id, value=message)
                        write_new_update(item_id=monday_token_id, value=message)
                        log_and_notify(message=message)
                        token['message'] = message














# def monday_monitor_prices():

#     response = {'error': None, 'data': None, 'message': None, 'success': False}
#     print('--Starting monitoring prices--')

#     try:
#         # Fetch available tokens
#         available_tokens, status = get_list_of_coins()
#         if status != 200:
#             response['error'] = 'Error asking for available tokens on CoinGecko'
#             return response

#         print('Getting all available tokens, found:', len(available_tokens))

#         # Get all boards
#         boards_data = get_all_boards(search_param='take')
#         if not boards_data['success']:
#             response['error'] = boards_data['error']
#             log_and_notify_error(error_message=boards_data['error'])
#             return response

#         boards = boards_data['data']
#         board_ids = [board['id'] for board in boards]

#         print('Getting all boards - found:', len(board_ids))

#         # Get board items
#         board_items_data = get_board_item_general(board_ids=board_ids)
#         if not board_items_data['success']:
#             response['error'] = board_items_data['error']
#             log_and_notify_error(error_message=board_items_data['error'])
#             return response

#         items = board_items_data['data']
#         print('Getting all items, found:', len(items))

#         # Process each item in the board
#         for item in items:
#             board_name = item.get('board_name')
#             data = item.get('data')
            
#             print('\nProcessing this board: ', board_name)
           
#             if data:
#                 for token in data:
#                     token_name = token.get('column_name')
#                     monday_token_id = token.get('column_id') 
#                     monday_token_values = token.get('column_values')
#                     token_symbol = None
#                     tp_values = {}
#                     percentage_threshold = 2

        
#                     if monday_token_values:
#                         for value in monday_token_values:
#                             if str(value['column_name']).casefold() == 'code' and value['column_value']:
#                                 token_symbol = value['column_value']

#                             tp_column = str(value['column_name']).casefold().replace(' ', '')
                            
#                             if tp_column.startswith('tp'):
#                                 tp_values[tp_column] = value['column_value']
    
#                     # Match token_name and token_symbol with available tokens
#                     if token_symbol:
#                         for available_token in available_tokens:
#                             if (token_name.casefold() == available_token['name'].casefold() and 
#                                 token_symbol.casefold() == available_token['symbol'].casefold()):
#                                 # Add gecko_id to token
#                                 token['gecko_id'] = available_token['id']
#                                 print(f'checking the price for {available_token['id']}')
#                                 price_data = check_price(coin=available_token['id'])
#                                 if price_data:
#                                     token_price = price_data.get('current_price')
#                                     token['token_price']=token_price
#                                     message = None
#                                     if token_price:
#                                         # Check each target price
#                                         for tp_name, tp_price in tp_values.items():
#                                             is_tp_hit = check_target_price(current_price=token_price,
#                                                                tp_name=tp_name,
#                                                                 tp_price=tp_price,
#                                                                 percentage_threshold=percentage_threshold)

#                                             if is_tp_hit['success']:
#                                                 message = is_tp_hit['message']
                                                
#                                             else:
#                                                 # print(f'Token {token_name} had an error: {is_tp_hit['error']}')
#                                                 log_and_notify_error(error_message=is_tp_hit['error'])
                                    
#                                     token['message']=message
#                                     if message:
#                                         create_notification(user_id=david_user_id,
#                                                             item_id=monday_token_id,
#                                                             value=message
#                                                             )
#                                         write_new_update(item_id=monday_token_id,
#                                                          value=message
#                                                          )
                                

#         response['data'] = items
#         response['success'] = True
#         return response

#     except Exception as e:
#         error_message = f'Error monitoring tokens: {str(e)}'
#         response['error'] = error_message
#         log_and_notify_error(error_message=error_message)
#         return response
