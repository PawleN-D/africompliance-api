from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re

class TradeBloc(str, Enum):
    """Trade bloc classifications"""
    SADC = "SADC"
    EAC = "EAC"
    ECOWAS = "ECOWAS"
    COMESA = "COMESA"
    OTHER_AFRICA = "OTHER_AFRICA"
    REST_OF_WORLD = "REST_OF_WORLD"

class DocumentType(str, Enum):
    """Required trade documents"""
    COMMERCIAL_INVOICE = "Commercial Invoice"
    PACKING_LIST = "Packing List"
    BILL_OF_LADING = "Bill of Lading"
    CERTIFICATE_OF_ORIGIN = "Certificate of Origin"
    CUSTOMS_DECLARATION = "Customs Declaration (SAD 500)"
    IMPORT_PERMIT = "Import Permit"
    EXPORT_PERMIT = "Export Permit"
    PHYTOSANITARY = "Phytosanitary Certificate"
    HEALTH_CERTIFICATE = "Health Certificate"

class TradeTransaction(BaseModel):
    """Request for cross-border trade calculation"""
    item_description: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Description of goods being shipped",
        examples=["Electronic Components - Integrated Circuits"]
    )
    hs_code: str = Field(
        ...,
        description="Harmonized System Code (6-10 digits)",
        examples=["8542.31.90", "854231"]
    )
    value_zar: float = Field(
        ...,
        gt=0,
        description="Value of goods in South African Rand",
        examples=[50000.00]
    )
    quantity: Optional[float] = Field(
        None,
        gt=0,
        description="Quantity of goods",
        examples=[100.0]
    )
    unit_of_measure: Optional[str] = Field(
        None,
        description="Unit of measurement",
        examples=["KG", "UNITS", "LITRES"]
    )
    origin_country: str = Field(
        default="South Africa",
        description="Country of origin",
        examples=["South Africa"]
    )
    destination_country: str = Field(
        ...,
        min_length=2,
        description="Destination country",
        examples=["Namibia", "Botswana", "Nigeria", "Kenya"]
    )
    supplier_registration: Optional[str] = Field(
        None,
        description="Supplier's CIPC registration number",
        examples=["2019/123456/07"]
    )
    consignee_name: Optional[str] = Field(
        None,
        description="Name of consignee/buyer",
        examples=["ABC Importers Ltd"]
    )
    transport_mode: Optional[str] = Field(
        None,
        description="Mode of transport",
        examples=["Road", "Air", "Sea", "Rail"]
    )

    @field_validator('hs_code')
    @classmethod
    def validate_hs_code(cls, v: str) -> str:
        """Validate HS code format"""
        # Remove common separators
        cleaned = v.replace(".", "").replace("-", "").replace(" ", "")
        
        if not cleaned.isdigit():
            raise ValueError('HS code must contain only digits (separators like dots are allowed)')
        
        if not (4 <= len(cleaned) <= 10):
            raise ValueError('HS code must be between 4 and 10 digits')
        
        return v

    @field_validator('destination_country', 'origin_country')
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Normalize country names"""
        return v.strip().title()

class CalculationBreakdown(BaseModel):
    """Detailed breakdown of costs and duties"""
    base_value_zar: float = Field(..., description="Base value of goods")
    
    # VAT
    sa_vat_rate: float = Field(..., description="South African VAT rate")
    sa_vat_amount: float = Field(..., description="VAT amount in ZAR")
    
    # Duty
    customs_duty_rate: float = Field(..., description="Customs duty rate")
    customs_duty_amount: float = Field(..., description="Duty amount in ZAR")
    
    # Additional fees
    additional_fees: float = Field(
        default=0.0,
        description="Additional fees (storage, handling, etc.)"
    )
    
    # Totals
    subtotal_before_vat: float = Field(..., description="Subtotal before VAT")
    total_at_border: float = Field(..., description="Total cost including all charges")
    
    currency: str = Field(default="ZAR", description="Currency code")
    
    # Savings information
    duty_saved_via_trade_agreement: float = Field(
        default=0.0,
        description="Amount saved due to trade agreements"
    )

class ComplianceRequirement(BaseModel):
    """Required documents and compliance notes"""
    trade_bloc: TradeBloc = Field(..., description="Applicable trade bloc")
    trade_agreement: Optional[str] = Field(
        None,
        description="Applicable trade agreement",
        examples=["SADC Free Trade Area", "AfCFTA"]
    )
    
    # Documents
    required_documents: List[DocumentType] = Field(
        default_factory=list,
        description="List of required documents"
    )
    optional_documents: List[DocumentType] = Field(
        default_factory=list,
        description="Optional but recommended documents"
    )
    
    # Permits
    special_permits_required: List[str] = Field(
        default_factory=list,
        description="Special permits needed"
    )
    
    # Rules of Origin
    rules_of_origin_required: bool = Field(
        default=False,
        description="Whether rules of origin verification is required"
    )
    minimum_local_content_percent: Optional[float] = Field(
        None,
        description="Minimum local content required for preferential treatment"
    )
    
    # Timeline
    estimated_clearance_days: int = Field(
        ...,
        description="Estimated customs clearance time in days"
    )
    
    # Notes
    compliance_notes: List[str] = Field(
        default_factory=list,
        description="Important compliance notes"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings and potential issues"
    )

class TradeComplianceResponse(BaseModel):
    """Response for trade compliance calculation"""
    status: str = Field(default="success")
    transaction: TradeTransaction
    calculations: CalculationBreakdown
    compliance: ComplianceRequirement
    
    # Risk assessment
    risk_assessment: Optional[dict] = Field(
        None,
        description="Risk assessment if supplier registration provided"
    )
    
    # Metadata
    calculated_at: datetime
    request_id: str
    cache_hit: bool = Field(default=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "calculations": {
                    "base_value_zar": 50000.0,
                    "sa_vat_amount": 7500.0,
                    "customs_duty_amount": 0.0,
                    "total_at_border": 57500.0
                },
                "compliance": {
                    "trade_bloc": "SADC",
                    "required_documents": ["Commercial Invoice", "Certificate of Origin"],
                    "estimated_clearance_days": 2
                }
            }
        }