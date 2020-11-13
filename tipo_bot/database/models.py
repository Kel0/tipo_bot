from sqlalchemy import Column, Integer, String

from .conf import base


class User(base):
    telegram_id = Column(Integer)
    first_name = Column(String(length=255))
    tipo_credentials = Column(
        String(length=1000), nullable=True
    )  # Zhambyl tipo service's account creds
