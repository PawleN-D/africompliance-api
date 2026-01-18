from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re

from .common import Address, POPIACompliance

class VerificationStatus(str, Enum):
    """Status of verification request"""
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"
    NOT_FOUND = "not_found"

class Director(BaseModel):
    """Company director information (POPIA compliant)"""
    full_name: str = Field(..., description="Director's full name")
    id_number: Optional[str] = Field(
        None,
        description="Masked ID number (POPIA compliant)",
        examples=["7801015009***"]
    )
    appointment_date: Optional[str] = Field(
        None,
        description="Date appointed as director",
        examples=["2019-03-15"]
    )
    is_active: bool = Field(
        default=True,
        description="Whether director is currently active"
    )
    designation: Optional[str] = Field(
        None,
        description="Director's designation",
        examples=["Managing Director", "Executive Director"]
    )

    @field_validator('id_number')
    @classmethod
    def validate_masked_id(cls, v: Optional[str]) -> Optional[str]:
        """Ensure ID numbers are masked for POPIA compliance"""
        if v and not v.endswith('***'):
            # Auto-mask if not already masked
            return f"{v[:10]}***" if len(v) >= 10 else f"{v}***"
        return v

class RiskFlags(BaseModel):
    """Risk indicators for business entity"""
    sanctions_match: bool = Field(
        default=False,
        description="Entity matches international sanctions lists"
    )
    deregistration_pending: bool = Field(
        default=False,
        description="Company deregistration is pending"
    )
    director_on_watchlist: bool = Field(
        default=False,
        description="One or more directors on fraud watchlist"
    )
    recent_name_change: bool = Field(
        default=False,
        description="Company name changed in last 90 days"
    )
    no_vat_registration: bool = Field(
        default=False,
        description="Company is not VAT registered"
    )
    dormant_company: bool = Field(
        default=False,
        description="Company shows no recent activity"
    )
    high_risk_industry: bool = Field(
        default=False,
        description="Company operates in high-risk industry"
    )

    def has_critical_flags(self) -> bool:
        """Check if any critical risk flags are raised"""
        return self.sanctions_match or self.deregistration_pending or self.director_on_watchlist

    def risk_level(self) -> str:
        """Calculate overall risk level"""
        critical_count = sum([
            self.sanctions_match,
            self.deregistration_pending,
            self.director_on_watchlist
        ])
        warning_count = sum([
            self.recent_name_change,
            self.no_vat_registration,
            self.dormant_company,
            self.high_risk_industry
        ])
        
        if critical_count > 0:
            return "CRITICAL"
        elif warning_count >= 2:
            return "HIGH"
        elif warning_count == 1:
            return "MEDIUM"
        return "LOW"

class Business(BaseModel):
    """Company information from CIPC"""
    legal_name: str = Field(..., description="Registered legal name")
    registration_number: str = Field(
        ...,
        description="CIPC registration number",
        examples=["2019/123456/07"]
    )
    status: str = Field(..., description="Company status", examples=["In Business"])
    registration_date: Optional[str] = Field(
        None,
        description="Date of registration",
        examples=["2019-03-15"]
    )
    business_type: Optional[str] = Field(
        None,
        description="Type of business entity",
        examples=["Private Company", "Close Corporation"]
    )
    registered_address: Optional[Address] = None
    vat_registered: bool = Field(
        default=False,
        description="Whether company is VAT registered"
    )
    vat_number: Optional[str] = Field(
        None,
        description="VAT registration number",
        examples=["4123456789"]
    )
    industry_classification: Optional[str] = Field(
        None,
        description="SIC code or industry classification",
        examples=["62010"]
    )

class VerificationRequest(BaseModel):
    """Request to verify a South African business"""
    registration_number: str = Field(
        ...,
        description="SA company registration number",
        examples=["2019/123456/07", "K2019/123456/07"]
    )
    vat_number: Optional[str] = Field(
        None,
        description="VAT number for cross-validation",
        examples=["4123456789"]
    )
    verify_directors: bool = Field(
        default=True,
        description="Include director information in response"
    )
    check_sanctions: bool = Field(
        default=True,
        description="Check entity against sanctions lists"
    )
    customer_reference: Optional[str] = Field(
        None,
        description="Your internal reference for this verification",
        examples=["SHIPMENT-2024-001"]
    )

    @field_validator('registration_number')
    @classmethod
    def validate_registration_format(cls, v: str) -> str:
        """Validate SA company registration number format"""
        # Remove whitespace
        v = v.strip()
        
        # Valid formats: 2019/123456/07 or K2019/123456/07
        pattern = r'^[K]?\d{4}/\d{6}/\d{2}$'
        if not re.match(pattern, v):
            raise ValueError(
                'Invalid registration number format. Expected: YYYY/NNNNNN/NN or KYYYY/NNNNNN/NN'
            )
        return v

    @field_validator('vat_number')
    @classmethod
    def validate_vat_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate VAT number format"""
        if v is None:
            return v
        
        # Remove whitespace
        v = v.strip()
        
        # SA VAT numbers are 10 digits starting with 4
        if not re.match(r'^4\d{9}$', v):
            raise ValueError('Invalid VAT number format. Expected: 10 digits starting with 4')
        return v

class VerificationResponse(BaseModel):
    """Response from business verification"""
    status: VerificationStatus
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score (0-100)"
    )
    risk_level: str = Field(
        ...,
        description="Overall risk level",
        examples=["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    )
    business: Optional[Business] = None
    directors: Optional[List[Director]] = None
    risk_flags: RiskFlags
    popia_compliance: POPIACompliance
    data_source: str = Field(
        default="CIPC",
        description="Primary data source"
    )
    verified_at: datetime
    request_id: str = Field(..., description="Unique request identifier")
    cache_hit: bool = Field(
        default=False,
        description="Whether result was served from cache"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "verified",
                "confidence_score": 95,
                "risk_level": "LOW",
                "business": {
                    "legal_name": "Example Logistics (Pty) Ltd",
                    "registration_number": "2019/123456/07",
                    "status": "In Business",
                    "vat_registered": True
                },
                "risk_flags": {
                    "sanctions_match": False,
                    "deregistration_pending": False
                },
                "verified_at": "2026-01-17T14:30:00Z",
                "request_id": "req_abc123"
            }
        }