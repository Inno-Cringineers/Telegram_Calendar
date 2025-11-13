from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from bot.database import Base

class Event(Base):
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    source = Column(Text, nullable=False)