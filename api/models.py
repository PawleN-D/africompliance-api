from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class VerificationStatus(str, Enum):
    """Status of the verification request"""
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"
    NOT_FOUND = "not_found"

class Address(BaseModel):
    """Company registered address"""
    street: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None

class Director(BaseModel):
    """Company director information"""
    full_name: str
    id_number: Optional[str] = None  # Masked for POPIA: 7801015009***
    appointment_date: Optional[str] = None
    is_active: bool = True

class RiskFlags(BaseModel):
    """Risk indicators for the company"""
    sanctions_match: bool = False
    deregistration_pending: bool = False
    director_on_watchlist: bool = False
    recent_name_change: bool = False
    no_vat_registration: bool = False

class ComplianceInfo(BaseModel):
    """POPIA compliance information"""
    popia_consent_obtained: bool = True
    data_retention_days: int = 90
    data_source: str = "CIPC"

class Business(BaseModel):
    """Company information"""
    legal_name: str
    registration_number: str
    status: str
    registration_date: Optional[str] = None
    business_type: Optional[str] = None
    registered_address: Optional[Address] = None
    vat_registered: bool = False
    vat_number: Optional[str] = None

class VerificationRequest(BaseModel):
    """Request to verify a company"""
    registration_number: str = Field(
        ..., 
        description="SA company registration number (e.g., 2019/123456/07)",
        example="2019/123456/07"
    )
    vat_number: Optional[str] = Field(
        None,
        description="VAT number for additional verification",
        example="4123456789"
    )
    verify_directors: bool = Field(
        default=True,
        description="Include director information"
    )
    customer_reference: Optional[str] = Field(
        None,
        description="Your internal reference for this check"
    )

class VerificationResponse(BaseModel):
    """Response from verification"""
    status: VerificationStatus
    confidence_score: int = Field(..., ge=0, le=100)
    business: Optional[Business] = None
    directors: Optional[List[Director]] = None
    risk_flags: RiskFlags
    compliance: ComplianceInfo
    verified_at: datetime
    request_id: str