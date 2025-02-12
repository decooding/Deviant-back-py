from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)
    description = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
