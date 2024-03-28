import json
from datetime import date
from sqlalchemy import Date, cast
from config import session, Coin, Alert, Board
from services.slack.actions import send_INFO_message_to_slack_channel
from services.monday.actions import (get_board_items, 
                           change_column_value, 
                           create_notification, calculate_profit,
                           write_new_update)

from services.coingecko.coingecko import (check_price, 
                              calculate_percentage_change_over_buy_price, 
                              percentage_variation_daily, 
                              percentage_variation_week)

david_user_id = 53919924
aman_user_id = 53919777
rajan_user_id = 53845740
kontopyrgou_user_id = 53889497
DEX_board_id = 1355568860

users_ids = [aman_user_id, kontopyrgou_user_id]

# Notifies to #Logs channel in Slack
def log_and_notify_error(error_message, title_message="Error executing NV Invest Bot", sub_title="Response", SLACK_CHANNEL_ID="C06FTS38JRX"):
    send_INFO_message_to_slack_channel(channel_id=SLACK_CHANNEL_ID, 
                                       title_message=title_message, 
                                       sub_title=sub_title,
                                       message=error_message)


# Validates each coin against CoinGecko list of coins, if coin is valid, then it's added to the DB
def validate_and_save_coins(coins, users_ids):
    # Load Coingecko data once
    with open('coingecko_coins.json', 'r', encoding='utf-8') as file:
        coingecko_data = json.load(file)

    not_saved_coins = ""

    for coin in coins:
        coin_name = coin['coin_name']
        coin_id = coin['coin_id']
        buy_price = coin['buy_price']
        coin_symbol = coin['coin_symbol']
        total_quantity_value = coin['total_quantity_value']
        board_id = coin['board_id']
        board_name = coin['board_name']
        valuation_price_column_id = coin['column_ids']['valuation_price_column_id']
        percentage_change_column_id = coin['column_ids']['percentage_change_column_id']
        projected_value_column_id = coin['column_ids']['projected_value_column_id']

        # Check if the coin is already in the database
        existing_coin = session.query(Coin).filter_by(coin_id=coin_id).first()

        coin['coingecko_coin_id'] = None

        if not existing_coin or (existing_coin and not existing_coin.is_valid):
            # Search for Coingecko ID
            for coingecko_coin in coingecko_data:
                valid_coin_name = coingecko_coin['name'].casefold().strip()
                valid_coin_symbol = coingecko_coin['symbol'].casefold().strip()
                valid_coin_id = coingecko_coin['id'].casefold().strip()

                if valid_coin_name == coin_name and valid_coin_symbol == coin_symbol:
                    coin['coingecko_coin_id'] = valid_coin_id
                    break
                elif valid_coin_symbol == coin_symbol:
                    coin['coingecko_coin_id'] = valid_coin_id

            if coin['coingecko_coin_id']:
                # Add the coin to the database
                new_coin = Coin(
                    coin_id=coin_id,
                    coin_name=coin_name,
                    coin_symbol=coin_symbol,
                    coingecko_coin_id=coin['coingecko_coin_id'],
                    is_valid=True,
                    buy_price=buy_price,
                    total_quantity_value=total_quantity_value,
                    board_id=board_id,
                    board_name=board_name,
                    valuation_price_column_id=valuation_price_column_id,
                    percentage_change_column_id=percentage_change_column_id,
                    projected_value_column_id=projected_value_column_id
                )
                session.add(new_coin)
                session.commit()
                print(f"{coin_name.capitalize()} was added to the DB")
            else:
                not_saved_coins += f"{coin_name} ({coin_symbol}),\n "
                print(f"No Coingecko ID found for: {coin_name} ({coin_symbol})")
                # Notify users
                for user_id in users_ids:
                    create_notification(user_id=user_id, item_id=coin_id,
                                         value=f"No Coingecko ID found for: {coin_name} ({coin_symbol.upper()})")
        else:
            # Check if any values have changed, update the database entry if needed
            if (
                existing_coin.total_quantity_value != str(total_quantity_value) or
                existing_coin.buy_price != str(buy_price)
            ):  
                existing_coin.total_quantity_value = total_quantity_value
                existing_coin.buy_price = buy_price
                session.commit()
                print(f"{coin_name.capitalize()} in the DB was updated")
            else:
                print(f"{coin_name} already exists and it's valid")
    
    print('not_saved_coins: ', not_saved_coins if len(not_saved_coins) > 0 else "None")
    # Notify which coins cound't be added to the DB
    if len(not_saved_coins) > 0:
        for user_id in users_ids:
            create_notification(user_id=user_id, item_id=DEX_board_id, value=f'These coins could not be added, due to they were not found on CoinGecko: {not_saved_coins}')
    
    return 'All valid coin added to the DB'


def activate_nv_invest_bot():

    all_boards = session.query(Board).all()
    board_ids = [board.monday_board_id for board in all_boards]

    try:
        coins_item = get_board_items(board_ids=board_ids)
        
        if not coins_item:
            print("--- Error while getting items from Monday boards ---")
            log_and_notify_error(error_message="Error while getting items from Monday boards")
            return 'Error while getting items from Monday boards'
        
        validate_and_save_coins(coins=coins_item, users_ids=users_ids)

        # Gets all the coins saved in the DB
        all_coins = session.query(Coin).order_by(Coin.created_at).all()
        coins_item = [coin.as_dict() for coin in all_coins]

        # Add the coin to the database and check the price of the coin, and other...
        for coin in coins_item:
            coin_name = coin['coin_name']
            buy_price = coin['buy_price']
            coin_id = coin['coin_id']
            coingecko_coin_id = coin['coingecko_coin_id']
            board_id = coin['board_id']
            valuation_price_column_id = coin['valuation_price_column_id']
            percentage_change_column_id = coin['percentage_change_column_id']
            projected_value_column_id = coin['projected_value_column_id']
            coin_symbol = coin['coin_symbol']
            total_quantity_value = coin['total_quantity_value']

            print(f"\n---{str(coin_name).upper()}---")
            
            price = check_price(coingecko_coin_id)
            
            if not price:
                print(f'---No price for {coin_name}---')
                for user_id in users_ids:
                    create_notification(user_id=user_id, item_id=coin_id, value=f'No price was found for: {coin_name} ({coin_symbol.upper()})')
                continue
           
            current_price = price['current_price']
            price_change_daily = price['price_change_daily']
            price_change_weekly = price['price_change_weekly']

            # --- calculate the profit of coin ----
            profit = calculate_profit(current_price=current_price, 
                                      buy_price=buy_price, 
                                      total_quantity=total_quantity_value)

            if profit['status'] == True:
                change_column_value(board_id=board_id, 
                                    item_id=coin_id, 
                                    column_id=projected_value_column_id, 
                                    value=profit['message']) 
                print(f'---Profit column updated for {coin_name}, profit: {profit["message"]}---')
            else:
                print(f'---No profit for {coin_name}---')
                for user_id in users_ids:
                    create_notification(user_id=user_id, item_id=coin_id, 
                                        value=f"Can't calculate the profit for {coin_name} ({coin_symbol.upper()}) - {profit['message']}")

            # --- calculate the percentages of the Daily, Weekly and Buy Price compared to the current ----
            buy_price_percentage = calculate_percentage_change_over_buy_price(buy_price=buy_price, 
                                                                    current_price=current_price, 
                                                                    coin=coin_name)
            daily_percentage = percentage_variation_daily(coin=coin_name, 
                                                price_change_daily=price_change_daily)
            
            weekly_percentage = percentage_variation_week(coin=coin_name, 
                                                price_change_weekly=price_change_weekly)
        
            
            if buy_price_percentage['status'] == True:
                percentage_change = buy_price_percentage['percentage_change']
                if percentage_change:
                    change_column_value(board_id=board_id, 
                                        item_id=coin_id, 
                                        column_id=percentage_change_column_id, 
                                        value=percentage_change) 
                    print(f'% change column updated for {coin_name}, % change: {percentage_change}')
                else:
                    print(f'No % change for {coin_name}')
                  
                existing_alert_buy_price = session.query(Alert).\
                            filter_by(alert_type=buy_price_percentage['alert_type'], coin_id=coin_id).\
                            filter(cast(Alert.created_at, Date) == date.today()).\
                            first()

                # If alert does not exist during the day, then it's fired.
                if not existing_alert_buy_price:
                    # Writes a new update in Monday.com
                    write_new_update(item_id=id, value=buy_price_percentage['alert_message'])

                    # Saves the alert to the DB
                    new_alert = Alert(alert_message = buy_price_percentage['alert_message'],
                                        alert_type = buy_price_percentage['alert_type'],
                                        coin_id = coin_id)
                    session.add(new_alert)
                    session.commit()

                    # creates a notification for all the users that are in the list
                    for user_id in users_ids:
                        create_notification(user_id=user_id, item_id=coin_id, value=buy_price_percentage['alert_message'])  
            else:
                print(f"{coin_name} buy price response: ", buy_price_percentage['message'])

            if not daily_percentage:
                print(f'No daily percentage for {coin_name}')
            
            if daily_percentage:
                existing_alert_daily = session.query(Alert).\
                                filter_by(alert_type=daily_percentage['alert_type'], coin_id=coin_id).\
                                filter(cast(Alert.created_at, Date) == date.today()).\
                                first()
             
                # IF alert does not exist during the day, then it's fired.
                if not existing_alert_daily:

                    # Writes a new update in Monday.com
                    write_new_update(item_id=coin_id, value=daily_percentage['alert_message'])

                    # Saves the alert to the DB
                    new_alert = Alert(alert_message = daily_percentage['alert_message'],
                                        alert_type = daily_percentage['alert_type'],
                                        coin_id = coin_id)
                    session.add(new_alert)
                    session.commit()

                    # creates a notification for all the users that are in the list
                    for user_id in users_ids:
                        create_notification(user_id=user_id, item_id=id, value=daily_percentage['alert_message'])  
            
            
            if not weekly_percentage:
                print(f'No weekly percentage for {coin_name}')
            
            if weekly_percentage:
                existing_alert_weekly = session.query(Alert).\
                                    filter_by(alert_type=weekly_percentage['alert_type'], coin_id=coin_id).\
                                    filter(cast(Alert.created_at, Date) == date.today()).\
                                    first()

                # IF alert does not exist during the day, then it's fired.
                if not existing_alert_weekly:

                    # Writes a new update in Monday.com
                    write_new_update(item_id=coin_id, value=weekly_percentage['alert_message'])
                    
                    # Saves the alert to the DB
                    new_alert = Alert(alert_message = weekly_percentage['alert_message'],
                                        alert_type = weekly_percentage['alert_type'],
                                        coin_id = coin_id)
                    session.add(new_alert)
                    session.commit()
                    
                    # creates a notification for all the users that are in the list
                    for user_id in users_ids:
                        create_notification(user_id=user_id, item_id=coin_id, value=weekly_percentage['alert_message'])      

            # Makes the update fo the price in the desired column
            if current_price:
                change_column_value(board_id=board_id, item_id=coin_id, column_id=valuation_price_column_id, value=current_price) 
            else:
                print(f'No current price for {coin_name}')
                change_column_value(board_id=board_id, item_id=coin_id, column_id=valuation_price_column_id, value="0") 
        
        return 'All coins updated', 200
        
    except Exception as e:
        log_and_notify_error(error_message=f"Main error: {str(e)}")
        return f'Error executing NV Invest BOT {str(e)}', 500











# __________________________ OLD CODE _______________________________-

# def activate_nv_invest_bot():

#     all_boards = session.query(Board).all()
#     board_ids = [board.monday_board_id for board in all_boards]

#     try:
#         coins_item = get_board_items(board_ids=board_ids)
#         print("------")
        
#         if not coins_item:
#             print("--- Error while getting items from Monday boards ---")
#             log_and_notify_error(error_message="Error while getting items from Monday boards")
#             return 'Error while getting items from Monday boards'
        
#         # Load Coingecko data once
#         with open('coingecko_coins.json', 'r', encoding='utf-8') as file:
#             coingecko_data = json.load(file)
        
#         # Verification if the coins are findable in Coingecko
#         for coin in coins_item:
#             coin_name = coin['coin_name']
#             coin_id = coin['coin_id']
#             coin_symbol = coin['coin_symbol']
        
#             coin['coingecko_coin_id'] = None  # Default value
           
#             for coingecko_coin in coingecko_data:
#                 valid_coin_name = coingecko_coin['name'].casefold().strip()
#                 valid_coin_symbol = coingecko_coin['symbol'].casefold().strip()
#                 valid_coin_id = coingecko_coin['id'].casefold().strip()

#                 if valid_coin_name == coin_name and valid_coin_symbol == coin_symbol:
#                     coin['coingecko_coin_id'] = valid_coin_id
#                     break
#                 elif valid_coin_symbol == coin_symbol:
#                     coin['coingecko_coin_id'] = valid_coin_id
            
#              # Check if Coingecko ID is still None after the loop
#             if coin['coingecko_coin_id'] is None:
#                 print(f"No Coingecko ID found for: {coin_name} ({coin_symbol})")
#                 # creates a notification for all the users that are in the list
#                 for user_id in users_ids:
#                     create_notification(user_id=user_id, item_id=coin_id, value=f"No Coingecko ID found for: {coin_name} ({coin_symbol})")  
         
#         # Add the coin to the database and check the price of the coin, and other...
#         for coin in coins_item:
#             coin_name = coin['coin_name']
#             buy_price = coin['buy_price']
#             coin_id = coin['coin_id']
#             coingecko_coin_id = coin['coingecko_coin_id']
#             board_id = coin['board_id']
#             valuation_price_column_id = coin['column_ids']['valuation_price_column_id']
#             percentage_change_column_id = coin['column_ids']['percentage_change_column_id']
#             projected_value_column_id = coin['column_ids']['projected_value_column_id']
#             coin_symbol = coin['coin_symbol']
#             total_quantity_value = coin['total_quantity_value']

#             existing_coin = session.query(Coin).filter_by(coin_id=coin_id).first()
        
#             if not existing_coin:
#                 new_coin = Coin(coin_id = coin_id,
#                 coin_name = coin_name,
#                 coingecko_coin_id = coingecko_coin_id,
#                 buy_price = buy_price
#                 )
#                 session.add(new_coin)
#                 session.commit()
#             elif existing_coin.buy_price != buy_price:
#                 # Coin exists, but buy_price has changed, update the existing record
#                 existing_coin.buy_price = buy_price
#                 session.commit()
#                 # creates a notification for all the users that are in the list
#                 for user_id in users_ids:
#                     create_notification(user_id=user_id, item_id=coin_id, value=f'Buy price was updated for {str(coin_name).capitalize()} to ${buy_price}')  

#             if not coingecko_coin_id:
#                 print(f"{coin_name.capitalize()} doesn't have coingecko_coin_id: {coingecko_coin_id}")
#                 continue
            
#             price = check_price(coingecko_coin_id)
#             # print(f'---Price for {coin_name} ({coin_symbol}):', price)
            
#             if not price:
#                 print(f'---No price for {coin_name}---')
#                 for user_id in users_ids:
#                     create_notification(user_id=user_id, item_id=coin_id, value=f'No price was found for {str(coin_name).capitalize()}')
#                 continue

#             current_price = price['current_price']
#             price_change_daily = price['price_change_daily']
#             price_change_weekly = price['price_change_weekly']

#             # --- calculate the profit of coin ----
#             profit = calculate_profit(current_price=current_price, 
#                                       buy_price=buy_price, 
#                                       total_quantity=total_quantity_value)

#             if profit:
#                 change_column_value(board_id=board_id, 
#                                     item_id=coin_id, 
#                                     column_id=projected_value_column_id, 
#                                     value=profit) 
#                 print(f'---Profit column updated for {coin_name}, profit: {profit}---')
#             else:
#                 print(f'---No profit for {coin_name}---')

#             # --- calculate the percentages of the Daily, Weekly and Buy Price compared to the current ----
#             buy_price_percentage = calculate_percentage_change_over_buy_price(buy_price=buy_price, 
#                                                                     current_price=current_price, 
#                                                                     coin=coin_name)
#             daily_percentage = percentage_variation_daily(coin=coin_name, 
#                                                 price_change_daily=price_change_daily)
            
#             weekly_percentage = percentage_variation_week(coin=coin_name, 
#                                                 price_change_weekly=price_change_weekly)
#             if not buy_price_percentage:
#                 print(f'No buy price percentage for {coin_name}')

#             if buy_price_percentage:
#                 percentage_change = buy_price_percentage['percentage_change']
#                 if percentage_change:
#                     change_column_value(board_id=board_id, 
#                                         item_id=coin_id, 
#                                         column_id=percentage_change_column_id, 
#                                         value=percentage_change) 
#                     print(f'% change column updated for {coin_name}, % change: {percentage_change}')
#                 else:
#                     print(f'No % change for {coin_name}')
                  
#                 existing_alert_buy_price = session.query(Alert).\
#                             filter_by(alert_type=buy_price_percentage['alert_type'], coin_id=coin_id).\
#                             filter(cast(Alert.created_at, Date) == date.today()).\
#                             first()

#                 # If alert does not exist during the day, then it's fired.
#                 if not existing_alert_buy_price:
#                     # Writes a new update in Monday.com
#                     # write_new_update(item_id=id, value=buy_price_percentage['alert_message'])

#                     # Saves the alert to the DB
#                     new_alert = Alert(alert_message = buy_price_percentage['alert_message'],
#                                         alert_type = buy_price_percentage['alert_type'],
#                                         coin_id = coin_id)
#                     session.add(new_alert)
#                     session.commit()

#                     # creates a notification for all the users that are in the list
#                     for user_id in users_ids:
#                         create_notification(user_id=user_id, item_id=coin_id, value=buy_price_percentage['alert_message'])  
            
#             if not daily_percentage:
#                 print(f'No daily percentage for {coin_name}')
            
#             if daily_percentage:
#                 existing_alert_daily = session.query(Alert).\
#                                 filter_by(alert_type=daily_percentage['alert_type'], coin_id=coin_id).\
#                                 filter(cast(Alert.created_at, Date) == date.today()).\
#                                 first()
             
#                 # IF alert does not exist during the day, then it's fired.
#                 if not existing_alert_daily:

#                     # Writes a new update in Monday.com
#                     # write_new_update(item_id=coin_id, value=daily_percentage['alert_message'])

#                     # Saves the alert to the DB
#                     new_alert = Alert(alert_message = daily_percentage['alert_message'],
#                                         alert_type = daily_percentage['alert_type'],
#                                         coin_id = coin_id)
#                     session.add(new_alert)
#                     session.commit()

#                     # creates a notification for all the users that are in the list
#                     for user_id in users_ids:
#                         create_notification(user_id=user_id, item_id=id, value=daily_percentage['alert_message'])  
            
            
#             if not weekly_percentage:
#                 print(f'No weekly percentage for {coin_name}')
            
#             if weekly_percentage:
#                 existing_alert_weekly = session.query(Alert).\
#                                     filter_by(alert_type=weekly_percentage['alert_type'], coin_id=coin_id).\
#                                     filter(cast(Alert.created_at, Date) == date.today()).\
#                                     first()

#                 # IF alert does not exist during the day, then it's fired.
#                 if not existing_alert_weekly:

#                     # Writes a new update in Monday.com
#                     # write_new_update(item_id=coin_id, value=weekly_percentage['alert_message'])
                    
#                     # Saves the alert to the DB
#                     new_alert = Alert(alert_message = weekly_percentage['alert_message'],
#                                         alert_type = weekly_percentage['alert_type'],
#                                         coin_id = coin_id)
#                     session.add(new_alert)
#                     session.commit()
                    
#                     # creates a notification for all the users that are in the list
#                     for user_id in users_ids:
#                         create_notification(user_id=user_id, item_id=coin_id, value=weekly_percentage['alert_message'])      

#             # Makes the update fo the price in the desired column
#             if current_price:
#                 change_column_value(board_id=board_id, item_id=coin_id, column_id=valuation_price_column_id, value=current_price) 
#             else:
#                 print(f'No current price for {coin_name}')
#                 change_column_value(board_id=board_id, item_id=coin_id, column_id=valuation_price_column_id, value="0") 
        
#         return 'All coins updated', 200
        
#     except Exception as e:
#         log_and_notify_error(error_message=str(e))
#         return f'Error executing NV Invest BOT {str(e)}', 500


# board_ids = {
    # 'KuCoin Master Sheet': {'board_id': 1362987416},
    # 'NV OKX Master Sheet': {'board_id': 1364995332},
    # 'Bybit Sepia Wallet Master Sheet': {'board_id': 1365577256},
    # 'OKX Sepia International Wallet Master Sheet': {'board_id': 1365552286},
    # 'OKX Sepia Wallet Master Sheet': {'board_id': 1365759185},
    # 'Rabby Wallet Master Sheet': {'board_id': 1368448935},
    # 'Rajan Metamask Wallet Master Sheet': {'board_id': 1367129332},
    # 'Metamask Avalanche Wallet Master Sheet': {'board_id': 1366240359},
    # 'Metamask BNB Wallet Master Sheet': {'board_id': 1366234172},
    # 'Metamask Polygon Wallet Master Sheet': {'board_id': 1366238676},
    # 'Metamask Optimism Wallet Master Sheet': {'board_id': 1366282633},
    # 'Keplr Wallet Master Sheet': {'board_id': 1366947918},
    # 'HashPack Wallet Master Sheet': {'board_id': 1368425094},
    # 'Doge Labs Wallet Master Sheet': {'board_id': 1411047183},
    # 'Solflare Wallet Master Sheet': {'board_id': 1411045630},
    # 'NinjaVault Wallet Master Sheet': {'board_id': 1411045311},
    # 'Xeggex Wallet Master Sheet': {'board_id': 1414949166},
    # 'Sepia BingX Wallet Master Sheet': {'board_id': 1414983307},
    # 'NV Web3 OKX Wallet Master Sheet': {'board_id': 1414986083},
    # 'Rabby Mantle Wallet Master Sheet': {'board_id': 1397034863},
    # 'Rabby Ethereum Wallet Master Sheet': {'board_id': 1366177225},
    # 'Rabby Eigen Layer Testnet Wallet Master Sheet': {'board_id': 1410677412},
    # }