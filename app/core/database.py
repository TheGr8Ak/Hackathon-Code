"""
Database models and connection setup for Hospital AI System
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
import os
from enum import Enum

Base = declarative_base()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hospital_ai:hospital_ai_pass@localhost:5432/hospital_ai_db")
# Convert to async URL
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create engines
engine = create_engine(DATABASE_URL)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionType(str, Enum):
    AUTONOMOUS = "AUTONOMOUS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class AgentAction(Base):
    """Audit trail for all agent actions"""
    __tablename__ = "agent_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    action_payload = Column(JSON, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True)
    execution_type = Column(SQLEnum(ExecutionType), nullable=False, default=ExecutionType.PENDING)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    result = Column(JSON, nullable=True)
    approved_by = Column(String(100), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Forecast(Base):
    """Patient load forecasts from Watchtower agent"""
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(DateTime, nullable=False, index=True)
    predicted_load = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    confidence_interval_lower = Column(Integer, nullable=True)
    confidence_interval_upper = Column(Integer, nullable=True)
    drivers_json = Column(JSON, nullable=True)
    actual_load = Column(Integer, nullable=True)
    error_pct = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Inventory(Base):
    """Hospital inventory tracking"""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    current_quantity = Column(Integer, nullable=False, default=0)
    required_quantity = Column(Integer, nullable=False, default=0)
    unit = Column(String(50), nullable=False, default="units")
    reorder_threshold = Column(Integer, nullable=False, default=10)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    supplier_name = Column(String(200), nullable=True)
    supplier_contact = Column(String(100), nullable=True)


class PatientAdvisory(Base):
    """Patient advisories sent by Press Secretary agent"""
    __tablename__ = "patient_advisories"
    
    id = Column(Integer, primary_key=True, index=True)
    advisory_type = Column(String(100), nullable=False, index=True)
    message_content = Column(Text, nullable=False)
    recipient_count = Column(Integer, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    complaint_count = Column(Integer, default=0, nullable=False)
    success_status = Column(Boolean, default=True, nullable=False)
    action_id = Column(Integer, nullable=True)  # Reference to agent_actions.id
    verification_result = Column(JSON, nullable=True)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        yield session


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

