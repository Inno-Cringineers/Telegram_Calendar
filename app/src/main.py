import asyncio
import logging
from bot.bot import setup_bot
from bot.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():

    config = load_config()
    
    bot = await setup_bot(config)
    
    try:
        logger.info("Starting Telegram Calendar bot")
        await bot.start_polling()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        logger.info("Stopping bot")
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())