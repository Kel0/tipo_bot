import json
import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

import core.resources as dialog
from core.buttons import Buttons
from core.states import TipoCredentialsState
from settings import BOT_API_TOKEN

from .services.scraper import SiteEvents
from .services.utils import get_today_date

from .utils import (  # isort:skip
    get_or_create_user,
    remove_file_from_storage,
    check_for_session,
    update_users_tipo_creds,
    validate_creds,
)

bot = Bot(token=BOT_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

buttons_constructor = Buttons()


@dp.message_handler(state="*", commands="cancel")
@dp.message_handler(Text(contains="cancel", ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply(
        "Cancelled.", reply_markup=types.ReplyKeyboardRemove(), reply=False
    )


@dp.callback_query_handler(lambda c: c.data.lower() in "cancel", state="*")
async def process_callback_query(
    callback_query: types.CallbackQuery, state: FSMContext
):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await bot.send_message(
        callback_query.from_user.id,
        "Cancelled.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await get_or_create_user(
        telegram_id=message.from_user.id, first_name=message.from_user.first_name
    )

    buttons = buttons_constructor.init_inline(buttons=dialog.command_buttons)
    await message.reply(
        md.text(dialog.welcome_message.format(name=message.from_user.first_name)),
        reply_markup=buttons,
    )


@dp.callback_query_handler(lambda c: c.data == "get_account")
async def process_callback_get_account(callback_query: types.CallbackQuery):
    buttons = buttons_constructor.init_inline(buttons=dialog.command_buttons)
    await bot.answer_callback_query(callback_query.id)

    await bot.send_chat_action(callback_query.from_user.id, "Typing")
    user = await get_or_create_user(
        telegram_id=callback_query.from_user.id,
        first_name=callback_query.from_user.first_name,
    )
    await bot.send_message(
        callback_query.from_user.id,
        dialog.account_info.format(
            name=user.first_name,
            telegram_id=user.telegram_id,
            tipo_email=(
                json.loads(user.tipo_credentials)["email"]
                if user.tipo_credentials is not None
                else "No creds."
            ),
        ),
        reply_markup=buttons,
    )


@dp.callback_query_handler(lambda c: c.data == "get_schedule")
async def process_callback_get_schedule(callback_query: types.CallbackQuery):
    buttons = buttons_constructor.init_inline(buttons=dialog.command_buttons)
    await bot.answer_callback_query(callback_query.id)

    reply_text = [md.text(f"{get_today_date()}")]

    await bot.send_chat_action(callback_query.from_user.id, "Typing")
    user = await get_or_create_user(
        telegram_id=callback_query.from_user.id,
        first_name=callback_query.from_user.first_name,
    )
    session = await check_for_session(
        bot=bot, user=user, buttons=buttons, telegram_id=callback_query.from_user.id
    )
    if session is None:
        return

    site_events = SiteEvents(login_session=session)
    schedule = site_events.get_todays_schedule()

    if schedule is None:
        await bot.send_message(
            callback_query.from_user.id, "No schedule", reply_markup=buttons
        )
        return

    for subj in schedule:
        reply_text.append(
            md.text(
                dialog.schedule_text.format(
                    time=subj["time"],
                    name=subj["name"],
                    subject=subj["subject"],
                    lecture=subj["lecture"],
                    format=subj["format"],
                    link=md.hlink("Lesson url", subj["link"])
                    if subj["link"] is not None
                    else "Has no distance lesson link",
                )
            )
        )

    reply_text = md.text(*reply_text, sep="\n")

    await bot.send_message(
        callback_query.from_user.id,
        reply_text,
        reply_markup=buttons,
        parse_mode=types.message.ParseMode.HTML,
    )


@dp.callback_query_handler(lambda c: c.data == "visit_lesson")
async def process_callback_visit_lesson(callback_query: types.CallbackQuery):
    buttons = buttons_constructor.init_inline(buttons=dialog.command_buttons)
    await bot.answer_callback_query(callback_query.id)

    await bot.send_chat_action(callback_query.from_user.id, "Typing")
    user = await get_or_create_user(
        telegram_id=callback_query.from_user.id,
        first_name=callback_query.from_user.first_name,
    )
    session = await check_for_session(
        bot=bot, user=user, buttons=buttons, telegram_id=callback_query.from_user.id
    )
    if session is None:
        return

    site_events = SiteEvents(login_session=session)
    visited_lessons: list = site_events.go_to_lesson()

    reply_text = []

    for visited_lesson in visited_lessons:
        reply_text.append(
            md.text(
                dialog.visit_lessons.format(
                    lesson_name=visited_lesson["subject"],
                    link=md.hlink("Lesson url", visited_lesson["link"]),
                )
            )
        )

    await bot.send_message(
        callback_query.from_user.id,
        md.text(*reply_text, sep="\n"),
        reply_markup=buttons,
        parse_mode=types.message.ParseMode.HTML,
    )


@dp.callback_query_handler(lambda c: c.data == "get_class_work")
async def process_callback_get_class_work(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    buttons = buttons_constructor.init_inline(buttons=dialog.command_buttons)

    await bot.send_chat_action(callback_query.from_user.id, "Typing")
    user = await get_or_create_user(
        telegram_id=callback_query.from_user.id,
        first_name=callback_query.from_user.first_name,
    )
    session = await check_for_session(
        bot=bot, user=user, buttons=buttons, telegram_id=callback_query.from_user.id
    )
    if session is None:
        return

    site_events = SiteEvents(login_session=session)
    class_work_links = site_events.scrape_subjects("class")

    reply_buttons = buttons_constructor.init_inline(
        row_width=2,
        buttons=[
            {"name": button["subject"], "callback_data": f"classwork__{button['link']}"}
            for button in class_work_links
        ],
    )

    await bot.send_message(
        callback_query.from_user.id,
        "Choose subject(class work)",
        reply_markup=reply_buttons,
    )


@dp.callback_query_handler(lambda c: "classwork__" in c.data)
async def process_classword_link(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    buttons = buttons_constructor.init_inline(buttons=dialog.command_buttons)

    await bot.send_chat_action(callback_query.from_user.id, "Typing")
    user = await get_or_create_user(
        telegram_id=callback_query.from_user.id,
        first_name=callback_query.from_user.first_name,
    )
    session = await check_for_session(
        bot=bot, user=user, buttons=buttons, telegram_id=callback_query.from_user.id
    )
    if session is None:
        return

    site_events = SiteEvents(login_session=session)
    subject_link = callback_query.data.split("__")[-1]

    result = site_events.scrape_class_works_of_subject(link=subject_link)

    if result is None:
        await bot.send_message(
            callback_query.from_user.id, dialog.no_type_works.format(type_="class")
        )
        return

    await bot.send_message(
        callback_query.from_user.id,
        dialog.cw_desc.format(
            desc=result["desc"],
            teacher=result["teacher"],
            group=result["group"],
            date=result["date"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            subject=result["subject"],
        ),
    )

    if result["type"] == "paste":
        await bot.send_message(callback_query.from_user.id, result["file"])

    elif result["type"] == "file":
        if result["file"] is not None:
            file = types.InputFile(result["file"], filename=result["filename"])
            await bot.send_document(callback_query.from_user.id, document=file)

            remove_file_from_storage(result["file"])


@dp.callback_query_handler(lambda c: c.data == "get_home_work")
async def process_callback_get_home_work(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    buttons = buttons_constructor.init_inline(buttons=dialog.command_buttons)

    await bot.send_chat_action(callback_query.from_user.id, "Typing")
    user = await get_or_create_user(
        telegram_id=callback_query.from_user.id,
        first_name=callback_query.from_user.first_name,
    )
    session = await check_for_session(
        bot=bot, user=user, buttons=buttons, telegram_id=callback_query.from_user.id
    )
    if session is None:
        return

    site_events = SiteEvents(login_session=session)
    home_work_links = site_events.scrape_subjects("home")

    reply_buttons = buttons_constructor.init_inline(
        row_width=2,
        buttons=[
            {"name": button["subject"], "callback_data": f"homework__{button['link']}"}
            for button in home_work_links
        ],
    )

    await bot.send_message(
        callback_query.from_user.id,
        "Choose subject(home work)",
        reply_markup=reply_buttons,
    )


@dp.callback_query_handler(lambda c: "homework__" in c.data)
async def process_homework_link(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    buttons = buttons_constructor.init_inline(buttons=dialog.command_buttons)

    await bot.send_chat_action(callback_query.from_user.id, "Typing")
    user = await get_or_create_user(
        telegram_id=callback_query.from_user.id,
        first_name=callback_query.from_user.first_name,
    )
    session = await check_for_session(
        bot=bot, user=user, buttons=buttons, telegram_id=callback_query.from_user.id
    )
    if session is None:
        return

    site_events = SiteEvents(login_session=session)
    subject_link = callback_query.data.split("__")[-1]

    result = site_events.scrape_home_works_of_subject(link=subject_link)

    if result is None:
        await bot.send_message(
            callback_query.from_user.id, dialog.no_type_works.format(type_="home")
        )
        return

    await bot.send_message(
        callback_query.from_user.id,
        dialog.hw_desc.format(
            name=result["name"],
            desc=result["desc"],
            teacher=result["teacher"],
            deadline=result["deadline"],
            date=result["created_at"],
        ),
    )

    if result["file"] is not None:
        file = types.InputFile(result["file"], filename=result["filename"])
        await bot.send_document(callback_query.from_user.id, document=file)

        remove_file_from_storage(result["file"])


@dp.callback_query_handler(lambda c: c.data == "set_account")
async def process_callback_set_account(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    await TipoCredentialsState.credentials.set()
    await bot.send_message(
        callback_query.from_user.id,
        md.text(dialog.creds_format.format(format="email:password")),
        reply_markup=buttons_constructor.init_cancel_button(),
    )


@dp.message_handler(state=TipoCredentialsState.credentials)
async def process_credentials(message: types.Message, state: FSMContext):
    buttons = buttons_constructor.init_inline(buttons=dialog.command_buttons)

    await bot.send_chat_action(message.from_user.id, "Typing")
    async with state.proxy() as data:
        if (
            not validate_creds(message.text)
            or ":" not in message.text
            and "Cancel" not in message.text
        ):
            await message.reply(
                "Not correct credentials format, try again", reply_markup=buttons
            )
            await state.finish()
            return

        credentials = message.text.split(":")
        data["credentials"] = {"email": credentials[0], "pwd": credentials[1]}
        status = await update_users_tipo_creds(
            telegram_id=message.from_user.id, credentials=data["credentials"]
        )

    if status:
        await message.reply(
            "Success, credentials have been updated!", reply_markup=buttons
        )
    elif not status:
        await message.reply("Fail. Something went wrong", reply_markup=buttons)

    await state.finish()
