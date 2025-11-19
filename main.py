import asyncio
import os
from aiohttp import web
from telethon import TelegramClient, events

from config import API_ID, API_HASH, BOT_TOKEN, GROUP_ID
from handlers.message_handler import handle_message
from handlers.grab_handler import handle_grab, button_handler
from handlers.command_handler import register_commands
from utils.logger import log_event
from database.db import init_db, add_ignored_admins
from handlers.command_menu import set_command_menu


# ================================
# FAKE WEB SERVER + SELF-PING
# ================================
async def index(request):
    return web.Response(text="Luci bot running")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", index)

    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"🌐 Web server running on port {port}")


async def self_ping_restart():
    """
    Every 5 minutes:
    - Ping the bot’s own Render URL
    - If fails → exit(1) → Render restarts automatically
    """
    render_url = "https://luci.onrender.com"

    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes

            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(render_url, timeout=10) as resp:
                    if resp.status != 200:
                        print("❌ Health check failed. Restarting...")
                        os._exit(1)

            print("✅ Self-ping OK")

        except Exception as e:
            print(f"⚠️ Ping error: {e}. Restarting...")
            os._exit(1)


# ================================
# TELEGRAM BOT MAIN
# ================================
async def main():
    bot = TelegramClient("bot", API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)

    # Start web server
    asyncio.create_task(start_web_server())

    # Start self-ping auto restart system
    asyncio.create_task(self_ping_restart())

    # DB init
    await init_db()
    await add_ignored_admins(bot, GROUP_ID)
    await set_command_menu(bot)

    await log_event(bot, "✅ Luci bot started & admins added to ignore list")

    # Message listeners
    @bot.on(events.NewMessage())
    async def message_listener(event):
        try:
            await handle_message(bot, event)
        except Exception as e:
            await log_event(bot, f"⚠️ Error in message handler: {e}")

    @bot.on(events.NewMessage(pattern=r"^/(grab|secure)"))
    async def grab_listener(event):
        try:
            await handle_grab(bot, event)
        except Exception as e:
            await log_event(bot, f"⚠️ Error in grab handler: {e}")

    register_commands(bot)
    bot.add_event_handler(button_handler)

    await log_event(bot, "🤖 Luci bot is running...")

    try:
        await bot.run_until_disconnected()
    except KeyboardInterrupt:
        await log_event(bot, "🛑 Bot stopped manually.")
    finally:
        await bot.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
