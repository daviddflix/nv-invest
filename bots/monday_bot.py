from config import session, Coin, Alert
from datetime import date
from sqlalchemy import Date, cast
from services.monday.monday import (get_values_column, 
                           update_value, 
                           make_update_notification, 
                           make_update_over_price)

from services.coingecko.coingecko import (check_price, 
                              calculate_percentage_change_over_buy_price, 
                              percentage_variation_by_day, 
                              percentage_variation_week)

david_id = 53919924
aman_id = 53919777
rajan_id = 53845740
kontopyrgou = 53889497

DEX_board_id = 1355568860
users_ids = [david_id]

def activate_nv_invest_bot():

    try:
        response = get_values_column()
        if 'coins' in response:
            coins = response['coins']
            print('Updating prices...')
            for coin in coins:
                coin_name = coin['coin']
                buy_price = coin['buy_price']
                id = coin['id']
                board_name = coin['board_name']
                board_id = coin['board_id']
                column_id = coin['column_id']

                existing_coin = session.query(Coin).filter_by(coin_id=id).first()
            
                if not existing_coin:
                    new_coin = Coin(coin_id = id,
                    coin_name = coin_name,
                    column_id = column_id,
                    board_name = board_name,
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
                        make_update_notification(user_id=user_id, item_id=id, value=f'Buy price was updated for {coin_name} to ${buy_price}')  

                price = check_price(coin_name)
                print(f'Price for {coin_name}:', price)
                
                if not price:
                    make_update_notification(user_id=david_id, item_id=DEX_board_id, value=f'No price was found for {coin_name}')
                    continue

                current_price = price['current_price']
                price_change_daily = price['price_change_daily']
                price_change_weekly = price['price_change_weekly']


                buy_price_percentage = calculate_percentage_change_over_buy_price(buy_price=buy_price, 
                                                                        current_price=current_price, 
                                                                        coin=coin_name)
                daily_percentage = percentage_variation_by_day(coin=coin_name, 
                                                    percentage_change=price_change_daily)
                
                weekly_percentage = percentage_variation_week(coin=coin_name, 
                                                    percentage_change=price_change_weekly)

                if buy_price_percentage:
                    existing_alert_buy_price = session.query(Alert).\
                                filter_by(alert_type=buy_price_percentage['alert_type'], coin_id=id).\
                                filter(cast(Alert.created_at, Date) == date.today()).\
                                first()

                    # If alert does not exist during the day, then it's fired.
                    if not existing_alert_buy_price:

                        # Makes the update in Monday.con in each coin.
                        make_update_over_price(item_id=id, value=buy_price_percentage['alert_message'])

                        # Saves the alert to the DB
                        new_alert = Alert(alert_message = buy_price_percentage['alert_message'],
                                            alert_type = buy_price_percentage['alert_type'],
                                            coin_id = id)
                        session.add(new_alert)
                        session.commit()

                        # creates a notification for all the users that are in the list
                        for user_id in users_ids:
                            make_update_notification(user_id=user_id, item_id=id, value=buy_price_percentage['alert_message'])  

                if daily_percentage:
                    existing_alert_daily = session.query(Alert).\
                                    filter_by(alert_type=daily_percentage['alert_type'], coin_id=id).\
                                    filter(cast(Alert.created_at, Date) == date.today()).\
                                    first()

                    # IF alert does not exist during the day, then it's fired.
                    if not existing_alert_daily:

                        # Makes the update in Monday.com in each coin.
                        make_update_over_price(item_id=id, value=daily_percentage['alert_message'])

                        # Saves the alert to the DB
                        new_alert = Alert(alert_message = daily_percentage['alert_message'],
                                            alert_type = daily_percentage['alert_type'],
                                            coin_id = id)
                        session.add(new_alert)
                        session.commit()

                        # creates a notification for all the users that are in the list
                        for user_id in users_ids:
                            make_update_notification(user_id=user_id, item_id=id, value=daily_percentage['alert_message'])  

                if weekly_percentage:
                    existing_alert_weekly = session.query(Alert).\
                                        filter_by(alert_type=weekly_percentage['alert_type'], coin_id=id).\
                                        filter(cast(Alert.created_at, Date) == date.today()).\
                                        first()

                    # IF alert does not exist during the day, then it's fired.
                    if not existing_alert_weekly:

                        # Makes the update in Monday.con in each coin when it's clicked.
                        make_update_over_price(item_id=id, value=weekly_percentage['alert_message'])
                        
                        # Saves the alert to the DB
                        new_alert = Alert(alert_message = weekly_percentage['alert_message'],
                                            alert_type = weekly_percentage['alert_type'],
                                            coin_id = id)
                        session.add(new_alert)
                        session.commit()
                        
                        # creates a notification for all the users that are in the list
                        for user_id in users_ids:
                            make_update_notification(user_id=user_id, item_id=id, value=weekly_percentage['alert_message'])      

                # Makes the update fo the price in the desired column
                if current_price:
                    update_value(board_id=board_id, item_id=id, column_id=column_id, value=current_price, item_name=coin_name) 
                else:
                    update_value(board_id=board_id, item_id=id, column_id=column_id, value=0, item_name=coin_name) 
            
            return 'All coins updated', 200
        else:
            make_update_notification(user_id=david_id, item_id=DEX_board_id, value=f'{response['error']}')
            return response['error'], 500
        
    except Exception as e:
        make_update_notification(user_id=david_id, item_id=DEX_board_id, value=str(e))
        return f'Error executing NV Invest BOT {str(e)}', 500


activate_nv_invest_bot()
