# polylastic = '4.697e-05'
# sats = '6.07663e-07'
# value = format(float(sats), '.12f')
# print(value)
# print(type(value))
# import json

def percentage_change_daily_or_weekly(current_price, starting_price, time_period, percentage_threshold):
    percentage_change = ((current_price - starting_price) / starting_price) * 100

    if time_period == 'daily':
        gap = 5
        alert_type = 'day'
    elif time_period == 'weekly':
        gap = 10
        alert_type = 'week'
    else:
        raise ValueError("Invalid time period. Use 'daily' or 'weekly'.")

    if abs(percentage_change) >= percentage_threshold:
        num_alerts = int(abs(percentage_change) // gap)
        direction = 'increased' if percentage_change > 0 else 'decreased'

        for alert_num in range(1, num_alerts + 1):
            alert_percentage = alert_num * gap
            message = f'Arbitrum has {direction} in price by {alert_percentage}% since the start of the {alert_type}.'
            print(message)

# Example usage:
starting_price = 0.1116  # Replace with the actual starting price
current_price = 0.129964  # Replace with the actual current price

# Daily alerts with 5% threshold
percentage_change_daily_or_weekly(current_price, starting_price, 'daily', 5)

# Weekly alerts with 10% threshold
percentage_change_daily_or_weekly(current_price, starting_price, 'weekly', 10)
