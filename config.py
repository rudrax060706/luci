import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID"))

TOTAL_MESSAGES_FOR_ROUND = 110
MIN_MESSAGES_REQUIRED = 10
MUTE_DURATION = 3600  # 1 hour

WELCOME_MESSAGE = (
    "👋 Hello {name}!\n\n"
    "I'm your **Auto-Mute Bot** 🤖\n"
    "I help keep the group active by muting users who camp and grab waifus/husbandos without chatting.\n\n"
    "💬 Stay active, chat more, and have fun!"
)