import pymysql
import sqlalchemy
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker

from settings import DB_LINK


class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + "s"

    __table_args__ = {"mysql_engine": "InnoDB"}
    __mapper_args__ = {"always_refresh": True}

    id = Column(Integer, primary_key=True, autoincrement=True)


pymysql.install_as_MySQLdb()
engine: sqlalchemy.engine.base.Engine = create_engine(
    DB_LINK, pool_recycle=3600, pool_pre_ping=True
)
session: sqlalchemy.orm.session.sessionmaker = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

base = declarative_base(cls=Base)
