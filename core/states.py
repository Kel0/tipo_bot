from aiogram.dispatcher.filters.state import State, StatesGroup


class TipoCredentialsState(StatesGroup):
    credentials = State()


class TipoHomeWork(StatesGroup):
    link = State()
