from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.db.session import Base
import datetime

class Ward(Base):
    __tablename__ = "wards"
    id = Column(Integer, primary_key=True, index=True)
    ward_code = Column(String, unique=True, index=True)
    ward_name = Column(String, nullable=False)
    zone = Column(String)
    district = Column(String)
    geometry = Column(Text)
    total_population = Column(Integer, default=0)
    total_males = Column(Integer, default=0)
    total_females = Column(Integer, default=0)
    sc_population = Column(Integer, default=0)
    st_population = Column(Integer, default=0)
    elderly_percent = Column(Float, default=8.57)
    outdoor_worker_density = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WeatherReading(Base):
    __tablename__ = "weather_readings"
    id = Column(Integer, primary_key=True, index=True)
    ward_code = Column(String, index=True)
    temperature_2m = Column(Float)
    relative_humidity_2m = Column(Float)
    precipitation = Column(Float)
    weathercode = Column(Integer)
    heat_index = Column(Float)
    wbgt = Column(Float)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    ward_code = Column(String, index=True)
    risk_category = Column(String)
    final_score = Column(Float)
    heat_index = Column(Float)
    wbgt = Column(Float)
    elderly_percent = Column(Float)
    outdoor_worker_density = Column(Float)
    demographic_multiplier = Column(Float)
    breakdown = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    ward_code = Column(String, index=True)
    alert_channel = Column(String)
    alert_status = Column(String, default="pending")
    external_id = Column(String)
    message = Column(Text)
    triggered_by = Column(String)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)

class ThresholdConfig(Base):
    __tablename__ = "threshold_configs"
    id = Column(Integer, primary_key=True, index=True)
    config_type = Column(String, unique=True)
    low_threshold = Column(Float)
    moderate_threshold = Column(Float)
    high_threshold = Column(Float)
    severe_threshold = Column(Float)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class AdvisoryTemplate(Base):
    __tablename__ = "advisory_templates"
    id = Column(Integer, primary_key=True, index=True)
    risk_category = Column(String, unique=True)
    sms_text = Column(Text)
    whatsapp_text = Column(Text)

__all__ = ["Ward", "WeatherReading", "RiskScore", "Alert", "ThresholdConfig", "AdvisoryTemplate"]
