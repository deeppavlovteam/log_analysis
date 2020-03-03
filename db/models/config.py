from sqlalchemy import Column, Integer, UnicodeText, ARRAY

from db.models.base import BaseModel


class Config(BaseModel):
    __tablename__ = 'config'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    type = Column(UnicodeText, nullable=False)
    dp_version = Column(UnicodeText, nullable=False)
    files = Column(ARRAY(UnicodeText), nullable=False)
