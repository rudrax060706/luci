from datetime import datetime
from config import LOG_GROUP_ID

async def log_event(bot, text: str):
    """Send log messages to the log group instead of writing to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {text}"
    print(log_message)

    try:
        await bot.send_message(LOG_GROUP_ID, log_message)
    except Exception as e:
        print(f"⚠️ Failed to send log to log group: {e}")