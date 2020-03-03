from db.models.base import BaseModel
from sqlalchemy import Column, UnicodeText, Integer, BigInteger, TIMESTAMP, VARCHAR, Boolean, ForeignKey
from sqlalchemy.orm import relationship


class Record(BaseModel):
    __tablename__ = 'record'
    id = Column(Integer, primary_key=True)
    ip_from = Column(VARCHAR(20), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    file = Column(UnicodeText, nullable=False)
    config = Column(UnicodeText, nullable=True)
    response_code = Column(Integer, nullable=False)
    bytes = Column(BigInteger, nullable=False)
    ref = Column(UnicodeText, nullable=False)
    app = Column(UnicodeText, nullable=False)
    forwarded_for = Column(UnicodeText, nullable=False)

    outer_request = Column(Boolean, nullable=False)
    country = Column(UnicodeText, nullable=True)
    city = Column(UnicodeText, nullable=True)
    company = Column(UnicodeText, nullable=True)

    model_id = Column(Integer, ForeignKey('model.id'), nullable=True)
    model = relationship('Model', back_populates='records')
