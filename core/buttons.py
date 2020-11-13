from typing import List

from .custom_exceptions import NoCallbackData

from aiogram.types import (  # isort:skip
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


class Buttons:
    def init_inline(self, buttons: List[dict], *args, **kwargs) -> InlineKeyboardMarkup:
        """
        Initialize inline buttons by self.buttons variable
        :return:
        """
        if buttons[0].get("callback_data") is None:
            raise NoCallbackData("Buttons have no callback data")

        inline_buttons: List[InlineKeyboardButton] = [
            InlineKeyboardButton(
                text=button["name"], callback_data=button["callback_data"]
            )
            for button in buttons
        ]
        return InlineKeyboardMarkup(*args, **kwargs).add(*inline_buttons)

    def init_cancel_button(self) -> ReplyKeyboardMarkup:
        button_cancel = KeyboardButton(text="Cancel ❌")

        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(button_cancel)
        return kb
