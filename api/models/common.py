from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ResponseStatus(str, Enum):
    """Standard response status"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PENDING = "pending"

class Address(BaseModel):
    """Physical address"""
    street: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = Field(default="South Africa")

    class Config:
        json_schema_extra = {
            "example": {
                "street": "123 Main Road",
                "suburb": "Parow",
                "city": "Cape Town",
                "province": "Western Cape",
                "postal_code": "7500",
                "country": "South Africa"
            }
        }

class POPIACompliance(BaseModel):
    """POPIA compliance metadata"""
    data_masked: bool = Field(
        default=True,
        description="Whether PII has been masked"
    )
    retention_days: int = Field(
        default=90,
        description="Data retention period in days"
    )
    purpose: str = Field(
        default="Business verification and compliance checking",
        description="Purpose of data processing"
    )
    legal_basis: str = Field(
        default="Legitimate interest - fraud prevention",
        description="Legal basis for processing"
    )