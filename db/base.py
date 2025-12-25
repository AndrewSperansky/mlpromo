from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from db.naming import naming_convention

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)