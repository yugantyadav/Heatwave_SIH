from pydantic import BaseModel, ConfigDict, field_validator, PlainSerializer
from typing import Annotated, Optional, List, Dict, Any
from datetime import datetime, timezone
import json


def _utc_iso(value):
    """Render naive datetimes as explicit UTC ISO-8601.

    The ORM defaults (``datetime.utcnow``) produce strings with no offset.
    Per the ES spec a datetime without an offset is parsed by browsers as
    *local* time, so a naive UTC stamp rendered in India showed 5h30m early.
    Emitting a trailing ``Z`` makes the instant unambiguous everywhere.
    """
    if isinstance(value, datetime):
        aware = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        return aware.astimezone(timezone.utc).isoformat()
    return value


UtcDateTime = Annotated[datetime, PlainSerializer(_utc_iso, return_type=str, when_used="json")]

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

    @field_validator("geometry", mode="before")
    @classmethod
    def parse_geometry(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

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
    created_at: Optional[UtcDateTime] = None

    @field_validator("breakdown", mode="before")
    @classmethod
    def parse_breakdown(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

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
    recorded_at: Optional[UtcDateTime] = None

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
    sent_at: Optional[UtcDateTime] = None

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
    low_threshold: Optional[float] = None
    moderate_threshold: Optional[float] = None
    high_threshold: Optional[float] = None
    severe_threshold: Optional[float] = None

class ThresholdConfigResponse(ThresholdConfigBase):
    id: int
    updated_at: Optional[UtcDateTime] = None

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