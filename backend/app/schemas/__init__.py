from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# Ward Schemas
class WardBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ward_code: str
    ward_name: str
    zone: Optional[str] = None
    district: Optional[str] = None
    total_population: Optional[int] = 0
    total_males: Optional[int] = 0
    total_females: Optional[int] = 0
    elderly_percent: Optional[float] = 8.57
    outdoor_worker_density: Optional[float] = 0.0

class WardResponse(WardBase):
    id: int
    geometry: Optional[Dict[str, Any]] = None

class WardListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    wards: List[WardResponse]

class WardGeoJSONResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[Dict[str, Any]]

# Risk Schemas
class RiskScoreBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ward_code: str
    risk_category: str
    final_score: float
    heat_index: Optional[float] = None
    wbgt: Optional[float] = None
    demographic_multiplier: Optional[float] = None

class RiskScoreResponse(RiskScoreBase):
    id: int
    elderly_percent: Optional[float] = None
    outdoor_worker_density: Optional[float] = None
    breakdown: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

class RiskMapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    wards: List[RiskScoreResponse]

# Weather Schemas
class WeatherReadingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ward_code: str
    temperature_2m: Optional[float] = None
    relative_humidity_2m: Optional[float] = None
    precipitation: Optional[float] = None
    weathercode: Optional[int] = None
    heat_index: Optional[float] = None
    wbgt: Optional[float] = None

class WeatherReadingResponse(WeatherReadingBase):
    id: int
    recorded_at: Optional[datetime] = None

class WeatherForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ward_code: str
    current: Optional[WeatherReadingResponse] = None
    forecast: List[Dict[str, Any]] = []

# Alert Schemas
class AlertBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ward_code: str
    alert_channel: str
    message: str
    triggered_by: str

class AlertResponse(AlertBase):
    id: int
    alert_status: str
    external_id: Optional[str] = None
    sent_at: Optional[datetime] = None

class AlertTriggerRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ward_code: str
    risk_category: str
    message: str
    channel: str

class AlertLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    alerts: List[AlertResponse]

# Config Schemas
class ThresholdConfigBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    config_type: str
    low_threshold: float
    moderate_threshold: float
    high_threshold: float
    severe_threshold: float

class ThresholdConfigResponse(ThresholdConfigBase):
    id: int
    updated_at: Optional[datetime] = None

class AdvisoryTemplateBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    risk_category: str
    sms_text: str
    whatsapp_text: str

class AdvisoryTemplateResponse(AdvisoryTemplateBase):
    id: int

class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    service: str