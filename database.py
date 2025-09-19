import os
import logging
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, Boolean, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class VibrationData(Base):
    """
    Database model for storing vibration sensor data
    """
    __tablename__ = "vibration_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    sensor_id = Column(String, nullable=False, default="sensor_1", index=True)
    raw_magnitude = Column(Float, nullable=False)
    processed_magnitude = Column(Float, nullable=False)
    x_axis = Column(Float, nullable=False)
    y_axis = Column(Float, nullable=False)
    z_axis = Column(Float, nullable=False)
    alert = Column(Boolean, nullable=False, default=False)
    threshold_used = Column(Float, nullable=False)
    sensitivity_level = Column(String, nullable=False)
    filter_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AlertHistory(Base):
    """
    Database model for storing alert history
    """
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    sensor_id = Column(String, nullable=False, default="sensor_1", index=True)
    message = Column(String, nullable=False)
    magnitude = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String, nullable=False, default="medium")
    acknowledged = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Create database tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database and create tables"""
    try:
        # Test database connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        # Create tables
        create_tables()
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def get_db_session():
    """Get a database session for direct use"""
    return SessionLocal()