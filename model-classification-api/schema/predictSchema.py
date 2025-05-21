from pydantic import BaseModel, Field
from typing import Optional, Literal

class PredictionOutput(BaseModel):  # CamelCase for class names
    deviceId: str = Field(..., description="Device ID")
    stressPrediction: Literal["normal", "low", "medium", "high"] = Field(...)  # Consistent casing
    heartRate: Optional[int] = None
    timeStamp: int