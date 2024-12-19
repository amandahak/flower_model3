from pydantic import BaseModel

class Prediction(BaseModel):
    label: int
    confidence: float
    prediction: str
    version: int
    version_iso: str
