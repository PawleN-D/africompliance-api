"""
Trade Document Models

For generating required document checklists for cross-border shipments.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DocumentCategory(str, Enum):
    """
    Categories of trade documents
    
    Purpose: Group documents by their function for easier organization
    """
    COMMERCIAL = "Commercial Documentation"       # Invoices, packing lists
    CUSTOMS = "Customs & Clearance"              # Customs declarations
    TRANSPORT = "Transport & Logistics"           # Bills of lading, waybills
    COMPLIANCE = "Compliance & Permits"           # Certificates, permits
    FINANCIAL = "Financial & Payment"             # Insurance, payment proof


class DocumentRequirement(str, Enum):
    """
    Whether a document is required or optional
    
    Purpose: Help logistics teams prioritize document collection
    """
    REQUIRED = "required"
    OPTIONAL = "optional"
    RECOMMENDED = "recommended"
    CONDITIONAL = "conditional"  # Required under certain conditions


class DocumentInfo(BaseModel):
    """
    Information about a single trade document
    
    This represents one document in a checklist
    """
    name: str = Field(
        ...,
        description="Document name",
        examples=["Commercial Invoice", "Certificate of Origin"]
    )
    
    category: DocumentCategory = Field(
        ...,
        description="Document category"
    )
    
    requirement_level: DocumentRequirement = Field(
        ...,
        description="Is this document required or optional?"
    )
    
    description: str = Field(
        ...,
        description="What this document is and why it's needed",
        examples=["Detailed invoice showing goods, values, and payment terms"]
    )
    
    issuer: str = Field(
        ...,
        description="Who issues/provides this document",
        examples=["Exporter", "Customs Broker", "Chamber of Commerce"]
    )
    
    validity_days: Optional[int] = Field(
        None,
        description="How long the document remains valid (if applicable)",
        examples=[180, 90, 30]
    )
    
    notes: Optional[str] = Field(
        None,
        description="Additional guidance or warnings",
        examples=["Must be on company letterhead", "Requires notarization"]
    )
    
    estimated_cost_zar: Optional[float] = Field(
        None,
        ge=0,
        description="Estimated cost to obtain this document in ZAR",
        examples=[500.0, 1500.0]
    )
    
    processing_time_days: Optional[int] = Field(
        None,
        ge=0,
        description="Estimated time to obtain this document",
        examples=[1, 5, 14]
    )


class DocumentChecklistRequest(BaseModel):
    """
    Request for generating a document checklist
    
    Purpose: Client sends shipment details, API returns required documents
    """
    destination_country: str = Field(
        ...,
        min_length=2,
        description="Destination country name",
        examples=["Namibia", "Nigeria", "United Kingdom"]
    )
    
    hs_code: str = Field(
        ...,
        min_length=4,
        max_length=10,
        description="HS code of goods being shipped",
        examples=["2204.21", "8542.31", "0805.10"]
    )
    
    value_zar: float = Field(
        ...,
        gt=0,
        description="Total shipment value in ZAR",
        examples=[50000.0, 500000.0]
    )
    
    trade_bloc: Optional[str] = Field(
        None,
        description="Trade bloc (if known)",
        examples=["SADC", "EAC", "ECOWAS"]
    )
    
    transport_mode: Optional[str] = Field(
        None,
        description="Mode of transport",
        examples=["Air", "Sea", "Road", "Rail"]
    )
    
    include_cost_estimates: bool = Field(
        default=False,
        description="Include estimated costs for documents"
    )


class DocumentChecklistResponse(BaseModel):
    """
    Response containing complete document checklist
    
    Purpose: Provide organized list of all documents needed
    """
    # Request context
    destination_country: str
    hs_code: str
    value_zar: float
    trade_bloc: Optional[str] = None
    
    # Document lists (organized by requirement level)
    required_documents: List[DocumentInfo] = Field(
        default_factory=list,
        description="Documents that MUST be provided"
    )
    
    optional_documents: List[DocumentInfo] = Field(
        default_factory=list,
        description="Documents that are recommended but not mandatory"
    )
    
    permits_and_certificates: List[DocumentInfo] = Field(
        default_factory=list,
        description="Special permits and certificates required"
    )
    
    # Summary information
    total_required: int = Field(
        ...,
        description="Total number of required documents"
    )
    
    total_optional: int = Field(
        ...,
        description="Total number of optional documents"
    )
    
    estimated_total_cost_zar: Optional[float] = Field(
        None,
        description="Total estimated cost for all documents"
    )
    
    estimated_processing_days: Optional[int] = Field(
        None,
        description="Estimated days to collect all documents"
    )
    
    warnings: List[str] = Field(
        default_factory=list,
        description="Important warnings or compliance notes"
    )
    
    tips: List[str] = Field(
        default_factory=list,
        description="Helpful tips for this shipment"
    )


class DocumentTemplateRequest(BaseModel):
    """
    Request for a document template/example
    
    Purpose: Help users understand what a document should look like
    """
    document_name: str = Field(
        ...,
        description="Name of document",
        examples=["Commercial Invoice", "Packing List"]
    )


class DocumentTemplate(BaseModel):
    """
    Template information for a document
    
    Purpose: Provide guidance on document format
    """
    document_name: str
    required_fields: List[str] = Field(
        default_factory=list,
        description="Fields that must be included"
    )
    optional_fields: List[str] = Field(
        default_factory=list,
        description="Fields that are optional"
    )
    sample_url: Optional[str] = Field(
        None,
        description="URL to sample document (if available)"
    )
    format_notes: Optional[str] = Field(
        None,
        description="Notes on formatting requirements"
    )