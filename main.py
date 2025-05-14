from WebSite.data import db_session

db_session.global_init("WebSite/db/database.db")

import threading
import asyncio

from WebSite.server import app
from TelegramBot.bot import start_bot


def run_web():
    app.run(port=5000, host='localhost', use_reloader=False)


async def run_bot():
    await start_bot()


def main():
    web_thread = threading.Thread(target=run_web, daemon=False)
    web_thread.start()

    asyncio.run(run_bot())


if __name__ == '__main__':
    main()
