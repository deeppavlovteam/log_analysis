from sqlalchemy import Column, Integer, UnicodeText, ForeignKey, TIMESTAMP, VARCHAR
from sqlalchemy.orm import relationship

from db.models.base import BaseModel


class Model(BaseModel):
    __tablename__ = 'model'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=True)
    type = Column(UnicodeText, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    ip = Column(VARCHAR(20), nullable=False)
    country = Column(UnicodeText, nullable=True)
    # model we refer to with some files necessary for this model
    base_model = Column(Integer, ForeignKey('model.id'), nullable=True)
    records = relationship('Record', back_populates='model', lazy='dynamic')
