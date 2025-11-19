from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommand, BotCommandScopeDefault

async def set_command_menu(bot):
    """Sets the bot's command menu (like in / commands list)."""
    commands = [
        BotCommand("start", "Start the bot and see basic info"),
        BotCommand("help", "Show available commands and usage guide"),
        BotCommand("ignore", "Add a user to ignored list (owner only)"),
        BotCommand("stats", "View your message stats"),
    ]

    # ✅ Fixed: Added required scope and lang_code arguments
    await bot(
        SetBotCommandsRequest(
            scope=BotCommandScopeDefault(),
            lang_code="",
            commands=commands
        )
    )

    print("✅ Command menu successfully set for the bot!")