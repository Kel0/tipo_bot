import json
import logging
import os
import re
from typing import Dict, List, Optional, TypeVar, Union

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from requests import Session as requests_session
from sqlalchemy.orm import Session

from .database.conf import session
from .database.models import User
from .services.scraper import Auth, SiteEvents

logger = logging.getLogger(__name__)

T = TypeVar("T")
ls: Session


def validate_creds(creds_string: str) -> bool:
    symbols = re.findall(r"(?!@|\.|\:)[\W]", creds_string)
    if len(symbols) > 0:
        return False
    return True


async def log_in_tipo_account(email: str, pwd: str) -> Optional[requests_session]:
    auth = Auth()
    return auth.login(username=email, password=pwd)


async def get_or_create_user(telegram_id: int, first_name: str) -> User:
    ls = session()
    user: List[User]

    user = ls.query(User).filter(User.telegram_id == telegram_id).all()

    if len(user) > 0:
        return user[0]

    ls.add(User(telegram_id=telegram_id, first_name=first_name))
    ls.commit()
    user = ls.query(User).filter(User.telegram_id == telegram_id).all()

    return user[0]


async def update_users_tipo_creds(
    telegram_id: int, credentials: Dict[str, str]
) -> bool:
    ls = session()

    try:
        ls.query(User).filter(User.telegram_id == telegram_id).update(
            {User.tipo_credentials: json.dumps(credentials)}
        )
        ls.commit()
        return True
    except Exception as e_info:
        logger.info(e_info)
        return False


async def check_for_session(
    bot: Bot,
    user: User,
    buttons: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup],
    telegram_id: int,
) -> Optional[requests_session]:

    _session = None
    if user.tipo_credentials is not None:
        creds = json.loads(user.tipo_credentials)
        _session = await log_in_tipo_account(email=creds["email"], pwd=creds["pwd"])

        if _session is None:
            return None

        # Check for valid
        try:
            site_events = SiteEvents(login_session=_session)
            site_events.get_todays_schedule()
        except AttributeError:
            await bot.send_message(
                telegram_id,
                "Account has incorrect TIPO credentials...",
                reply_markup=buttons,
            )
            return None

    elif user.tipo_credentials is None:
        await bot.send_message(
            telegram_id,
            "You have not inserted account credentials",
            reply_markup=buttons,
        )
        return None

    return _session


def remove_file_from_storage(path: str) -> None:
    os.remove(path)
