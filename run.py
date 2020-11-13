import json
import logging.config

from tipo_bot.bot import dp

from aiogram import executor


def setup_logging(path: str = "logging.json") -> None:
    with open(path, "rt") as f:
        config = json.load(f)
    logging.config.dictConfig(config)


if __name__ == '__main__':
    setup_logging()
    executor.start_polling(dp, skip_updates=True)
