from mondayService import get_values_column, update_value, make_update_notification, make_update_over_price
from coingeckoService import check_price

david_id = 53919924
aman_id = 53919777
rajan_id = 53845740
kontopyrgou = 53889497

DEX_board_id = 1355568860
users_ids = [david_id, aman_id, rajan_id]

def activate_bot():

    response = get_values_column()
    if 'coins' in response:
        coins = response['coins']
        print('Updating prices...')
        for coin in coins:
            coin_value = coin['coin']
            price, price_change = check_price(coin_value)

            if price_change:
                for id in users_ids:
                    make_update_notification(user_id=id, item_id=coin['id'], value=price_change)
                    make_update_over_price(item_id=coin['id'], value=price_change)

            if price:
                update_value(board_id=coin['board_id'], item_id=coin['id'], column_id=coin['column_id'], value=price, item_name=coin['coin']) 
            else:
                update_value(board_id=coin['board_id'], item_id=coin['id'], column_id=coin['column_id'], value=0, item_name=coin['coin']) 
               
        return 'All coins updated', 200
    else:
        # make_update_over_price(user_id=david_id, item_id=DEX_board_id, value=response['error'])
        return response['error'], 500

