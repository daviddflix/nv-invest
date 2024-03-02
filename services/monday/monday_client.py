import os 
from monday import MondayClient
from dotenv import load_dotenv
load_dotenv() 

MONDAY_API_KEY_NOVATIDE = os.getenv("MONDAY_API_KEY_NOVATIDE")

monday_client = MondayClient(MONDAY_API_KEY_NOVATIDE)
monday_url = "https://api.monday.com/v2"


