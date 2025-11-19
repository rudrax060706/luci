import asyncio
from telethon import TelegramClient, events
from config import API_ID, API_HASH, BOT_TOKEN, GROUP_ID
from handlers.message_handler import handle_message
from handlers.grab_handler import handle_grab, button_handler
from handlers.command_handler import register_commands
from utils.logger import log_event
from database.db import init_db, add_ignored_admins
from handlers.command_menu import set_command_menu

async def main():
    bot = TelegramClient("bot", API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)

    # Initialize DB and ignored admins
    await init_db()
    await add_ignored_admins(bot, GROUP_ID)
    await set_command_menu(bot)
    
    await log_event(bot, "✅ Bot started successfully and admins added to ignored list")

    # Listen for normal messages
    @bot.on(events.NewMessage())
    async def message_listener(event):
        try:
            await handle_message(bot, event)
        except Exception as e:
            await log_event(bot, f"⚠️ Error in message handler: {e}")

    # Listen for /grab or /secure commands
    @bot.on(events.NewMessage(pattern=r"^/(grab|secure)"))
    async def grab_listener(event):
        try:
            await handle_grab(bot, event)
        except Exception as e:
            await log_event(bot, f"⚠️ Error in grab handler: {e}")

    # Register other command handlers (e.g., /start)
    register_commands(bot)

    # Add callback button handler (for unmute/decline)
    bot.add_event_handler(button_handler)

    await log_event(bot, "🤖 Bot is running... Press Ctrl+C to stop.")

    try:
        await bot.run_until_disconnected()
    except KeyboardInterrupt:
        await log_event(bot, "🛑 Bot stopped manually.")
    finally:
        await bot.disconnect()


if __name__ == "__main__":
    asyncio.run(main())