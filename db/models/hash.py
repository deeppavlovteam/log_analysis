from db.models.base import BaseModel
from sqlalchemy import Column, Integer, CHAR


class Hash(BaseModel):
    __tablename__ = 'hash'
    id = Column(Integer, primary_key=True)
    hash = Column(CHAR(32), nullable=False, unique=True)
