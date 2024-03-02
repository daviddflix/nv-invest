import json
from datetime import date
from sqlalchemy import Date, cast
from config import session, Coin, Alert
from services.slack.actions import send_INFO_message_to_slack_channel
from services.monday.actions import (get_board_items, 
                           change_column_value, 
                           create_notification, 
                           write_new_update)

from services.coingecko.coingecko import (check_price, 
                              calculate_percentage_change_over_buy_price, 
                              percentage_variation_daily, 
                              percentage_variation_week)

david_user_id = 53919924
aman__user_id = 53919777
rajan_user_id = 53845740
kontopyrgou_user_id = 53889497
DEX_board_id = 1355568860

users_ids = [david_user_id, aman__user_id, rajan_user_id, kontopyrgou_user_id]

def activate_nv_invest_bot():

    board_ids = {
    'CEX Balance Sheet': {'board_id': 1355564217},
    'DEX Balance Sheet': {'board_id': 1355568860},
    'KuCoin Master Sheet': {'board_id': 1362987416},
    'NV OKX Master Sheet': {'board_id': 1364995332},
    'Bybit Sepia Wallet Master Sheet': {'board_id': 1365577256},
    'OKX Sepia International Wallet Master Sheet': {'board_id': 1365552286},
    'OKX Sepia Wallet Master Sheet': {'board_id': 1365759185},
    'Rabby Wallet Master Sheet': {'board_id': 1368448935},
    'Rajan Metamask Wallet Master Sheet': {'board_id': 1367129332},
    'Metamask Avalanche Wallet Master Sheet': {'board_id': 1366240359},
    'Metamask BNB Wallet Master Sheet': {'board_id': 1366234172},
    'Metamask Polygon Wallet Master Sheet': {'board_id': 1366238676},
    'Metamask Optimism Wallet Master Sheet': {'board_id': 1366282633},
    'Keplr Wallet Master Sheet': {'board_id': 1366947918},
    'HashPack Wallet Master Sheet': {'board_id': 1368425094},
    'Doge Labs Wallet Master Sheet': {'board_id': 1411047183},
    'Solflare Wallet Master Sheet': {'board_id': 1411045630},
    'NinjaVault Wallet Master Sheet': {'board_id': 1411045311},
    }

    try:
        coins_item = get_board_items(board_ids=board_ids)
        
        if not coins_item:
            send_INFO_message_to_slack_channel(channel_id="C06FTS38JRX", 
                                               title_message="Erro in Monday.com", 
                                               sub_title="Response",
                                               message="Error while getting items from Monday boards")
        
        # Load Coingecko data once
        with open('coingecko_coins.json', 'r', encoding='utf-8') as file:
            coingecko_data = json.load(file)
        
        # Verification if the coins are findable in Coingecko
        for coin in coins_item:
            coin_name = coin['coin_name']
            coin_id = coin['coin_id']
            coin_symbol = coin['coin_symbol']
        
            coin['coingecko_coin_id'] = None  # Default value

            for coingecko_coin in coingecko_data:
                valid_coin_name = coingecko_coin['name'].casefold().strip()
                valid_coin_symbol = coingecko_coin['symbol'].casefold().strip()
                valid_coin_id = coingecko_coin['id'].casefold().strip()

                if valid_coin_name == coin_name and valid_coin_symbol == coin_symbol:
                    coin['coingecko_coin_id'] = valid_coin_id
                    break
                elif valid_coin_symbol == coin_symbol:
                    coin['coingecko_coin_id'] = valid_coin_id
            
            # Check if Coingecko ID is still None after the loop
            if coin['coingecko_coin_id'] is None:
                print(f"No Coingecko ID found for: {coin_name} ({coin_symbol})")
                # creates a notification for all the users that are in the list
                for user_id in users_ids:
                    create_notification(user_id=user_id, item_id=coin_id, value=f"No Coingecko ID found for: {coin_name} ({coin_symbol})")  
            

        for coin in coins_item:
            coin_name = coin['coin_name']
            buy_price = coin['buy_price']
            coin_id = coin['coin_id']
            board_name = coin['board_name']
            coingecko_coin_id = coin['coingecko_coin_id']
            board_id = coin['board_id']
            valuation_price_column_id = coin['valuation_price_column_id']
            coin_symbol = coin['coin_symbol']

            existing_coin = session.query(Coin).filter_by(coin_id=coin_id).first()
        
            if not existing_coin:
                new_coin = Coin(coin_id = coin_id,
                coin_name = coin_name,
                column_id = valuation_price_column_id,
                board_name = board_name,
                coingecko_coin_id = coingecko_coin_id,
                board_id = board_id,
                buy_price = buy_price
                )
                session.add(new_coin)
                session.commit()
            elif existing_coin.buy_price != buy_price:
                # Coin exists, but buy_price has changed, update the existing record
                existing_coin.buy_price = buy_price
                session.commit()
                # creates a notification for all the users that are in the list
                for user_id in users_ids:
                    create_notification(user_id=user_id, item_id=coin_id, value=f'Buy price was updated for {str(coin_name).capitalize()} to ${buy_price}')  

            if not coingecko_coin_id:
                continue
            
            price = check_price(coingecko_coin_id)
            print(f'Price for {coin_name} ({coin_symbol}):', price)
            
            if not price:
                for user_id in users_ids:
                    create_notification(user_id=user_id, item_id=coin_id, value=f'No price was found for {str(coin_name).capitalize()}')
                continue

            current_price = price['current_price']
            price_change_daily = price['price_change_daily']
            price_change_weekly = price['price_change_weekly']


            buy_price_percentage = calculate_percentage_change_over_buy_price(buy_price=buy_price, 
                                                                    current_price=current_price, 
                                                                    coin=coin_name)
            daily_percentage = percentage_variation_daily(coin=coin_name, 
                                                price_change_daily=price_change_daily)
            
            weekly_percentage = percentage_variation_week(coin=coin_name, 
                                                price_change_weekly=price_change_weekly)

            if buy_price_percentage:
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
                change_column_value(board_id=board_id, item_id=coin_id, column_id=valuation_price_column_id, value="0") 
        
        return 'All coins updated', 200
        
    except Exception as e:
        send_INFO_message_to_slack_channel(channel_id="C06FTS38JRX", 
                                            title_message="Error executing NV Invest Bot", 
                                            sub_title="Response",
                                            message={str(e)})
        return f'Error executing NV Invest BOT {str(e)}', 500


activate_nv_invest_bot()