from services.slack.slack import client
from slack_sdk.errors import SlackApiError

# Sends a message to a Slack channel
def send_INFO_message_to_slack_channel(channel_id, title_message, sub_title, message):
        
        blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{title_message}*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*{sub_title}:*\n{message}"
                        }
                    ]
                },
                {
                "type": "divider"
                }
            ]
    
        try:
            result = client.chat_postMessage(
                channel=channel_id,
                text=title_message, 
                blocks=blocks
            )

            response = result['ok']
            ts = result['ts']
            print(f'Slack message timestamp:', ts)
           
            if response == True:
                return f'Message sent successfully to Slack channel {channel_id}', 200
            else:
                return response, 500

        except SlackApiError as e:
            print(f'Error sending this message: "{title_message}" to Slack channel, Reason:\n{str(e)}')
            return f'Error sending this message: "{title_message}" to Slack channel, Reason:\n{str(e)}', 500
        except Exception as e:
            print(f'Error sending message to slack: {str(e)}')
            return f'Error sending message to slack: {str(e)}', 500

#Deletes a message in Slack
def delete_messages_in_channel(ts_messages_list, channel_id="C06FTS38JRX"):
    try:
        for message in ts_messages_list:
            response = client.chat_delete(
                channel=channel_id,
                ts=message
            )
            if not response["ok"]:
                print(f"---Failed to delete message with timestamp {message}. Error: {response['error']}---")
            else:
                print(f"---Deleted message with timestamp {message}---")

        return 'All messages deleted in Slack', 200
    except Exception as e:
        print(f'---Error while deleting messages in Slack: {str(e)}---')
        return f'Error while deleting messages in Slack: {str(e)}', 500


# ________ Functions to format the message to send top 200 coins from coingecko, order by Market cap  ________
    
# Round a number to a given precision in decimal digits.
def format_number(number, decimal_places):
    formatted_number = round(number, decimal_places)
    return formatted_number

# First part of the entire message that will be send to slack: THE TITLE
def generate_initial_section(title="Top 100 Gainers"):
    return {
        "type": "rich_text",
        "elements": [
            {
                "type": "rich_text_list",
                "style": "bullet",
                "indent": 0,
                "border": 1,
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "text",
                                "text": title,
                                "style": {"bold": True}
                            }
                        ]
                    }
                ]
            }
        ]
    }


# Second part of the entire message: this part contains the details about a coin
def generate_coin_block(coin_data):
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*{str(coin_data['name']).capitalize()}*\n*Price:* ${format_number(coin_data['current_price'], 3)}\n*24h change:* {format_number(coin_data['price_change_percentage_24h'], 2)}%",
        },
        "accessory": {
            "type": "image",
            "image_url": coin_data["image"],
            "alt_text": coin_data["id"]
        }
    }



# ------ CREATE ROUTE FOR THIS BOT and ADD THIS INTO A NEW FILE CALLED get_200_coins_bot.py -----
def send_list_of_coins(coins, title="Top 100 Gainers", channel_id="C06F00A99C3", batch_size=20):
    try:
        blocks = []

        # Add the initial rich text section
        initial_section = generate_initial_section(title)
        blocks.append(initial_section)

        # Iterate through each batch of coins and add blocks
        for i in range(0, len(coins), batch_size):
            batch_coins = coins[i:i + batch_size]

            for coin_data in batch_coins:
                coin_block = generate_coin_block(coin_data)

                # Append the coin block to the blocks list
                blocks.append(coin_block)

                # Add a divider after each coin block
                blocks.append({"type": "divider"})


            # Save blocks to a text file (optional)
            with open(f'blocks_batch_{i // batch_size}.txt', 'w') as txt_file:
                for block in blocks:
                    txt_file.write(str(block))

            # Send the message with the current batch of blocks
            result = client.chat_postMessage(channel=channel_id, text=title, blocks=blocks)
            # print(f'Result for batch {i // batch_size}: {result}')
            print('\nTS:', result['ts'])
            response = result['ok']

            if not response:
                print(f'Slack API response indicated an error for batch {i // batch_size}: {result}')

            # Clear blocks for the next batch
            blocks = []

        return f'Messages sent successfully to Slack channel {channel_id}', 200

    except SlackApiError as e:
        print(f'Slack API error: {e.response["error"]}')
        return f'Slack API error: {e.response["error"]}', 500

    except Exception as e:
        print(f'Error sending list of coins to Slack: {str(e)}')
        return f'Error sending list of coins to Slack: {str(e)}', 500