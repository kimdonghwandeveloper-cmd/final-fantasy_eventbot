from datetime import datetime
from sqlalchemy import Column, String, DateTime
from final_fantasy_eventbot.database import Base

class EventRecord(Base):
    __tablename__ = "event_records"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
