from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=True)

    hashed_api_key = Column(String, unique=True, index=True, nullable=False)

    tier = Column(String, default="basic", nullable=False)  # basic | pro | enterprise
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    monthly_quota = Column(Integer, default=1000, nullable=False)
    requests_used_this_month = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
