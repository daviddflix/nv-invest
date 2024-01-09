from mondayService import get_values_column, update_value, make_update_notification, make_update_over_price
from coingeckoService import check_price

david_id = 53919924
aman_id = 53919777
rajan_id = 53845740
kontopyrgou = 53889497

DEX_board_id = 1355568860
users_ids = [david_id]

def activate_bot():

    response = get_values_column()
    if 'coins' in response:
        coins = response['coins']
        print('Updating prices...')
        for coin in coins:
            coin_value = coin['coin']
            buy_price = coin['buy_price']
            current_price, percentage_variation_daily, percentage_variation_weekly, percentage_variation_over_buy_price = check_price(coin_value, buy_price)

            if percentage_variation_over_buy_price:
                # make_update_over_price(item_id=coin['id'], value=percentage_variation_over_buy_price)
                for id in users_ids:
                    make_update_notification(user_id=id, item_id=coin['id'], value=percentage_variation_over_buy_price)  

            if percentage_variation_daily:
                # make_update_over_price(item_id=coin['id'], value=percentage_variation_daily)
                for id in users_ids:
                    make_update_notification(user_id=id, item_id=coin['id'], value=percentage_variation_daily)  

            if percentage_variation_weekly:
                # make_update_over_price(item_id=coin['id'], value=percentage_variation_weekly)
                for id in users_ids:
                    make_update_notification(user_id=id, item_id=coin['id'], value=percentage_variation_weekly)      

            if current_price:
                update_value(board_id=coin['board_id'], item_id=coin['id'], column_id=coin['column_id'], value=current_price, item_name=coin['coin']) 
            else:
                update_value(board_id=coin['board_id'], item_id=coin['id'], column_id=coin['column_id'], value=0, item_name=coin['coin']) 
               
        return 'All coins updated', 200
    else:
        # make_update_over_price(user_id=david_id, item_id=DEX_board_id, value=response['error'])
        return response['error'], 500

activate_bot()