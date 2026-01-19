"""
Data models for AfriCompliance API
"""

from .common import (
    ResponseStatus,
    Address,
    POPIACompliance
)

from .verification import (
    VerificationStatus,
    Director,
    RiskFlags,
    Business,
    VerificationRequest,
    VerificationResponse
)

from .trade import (
    TradeBloc,
    DocumentType,
    TradeTransaction,
    CalculationBreakdown,
    ComplianceRequirement,
    TradeComplianceResponse
)

from .hs_code import (
    HSCodeSection,
    HSCodeSearchRequest,
    HSCodeLookupRequest,
    HSCodeDetails,
    HSCodeSearchResponse,
    HSCodeLookupResponse,
    HSCodeCategoriesResponse,
    HSCodeChapterResponse
)

from .document import (
    DocumentCategory,
    DocumentRequirement,
    DocumentInfo,
    DocumentChecklistRequest,
    DocumentChecklistResponse,
    DocumentTemplateRequest,
    DocumentTemplate
)

__all__ = [
    # Common
    "ResponseStatus",
    "Address",
    "POPIACompliance",
    
    # Verification
    "VerificationStatus",
    "Director",
    "RiskFlags",
    "Business",
    "VerificationRequest",
    "VerificationResponse",
    
    # Trade
    "TradeBloc",
    "DocumentType",
    "TradeTransaction",
    "CalculationBreakdown",
    "ComplianceRequirement",
    "TradeComplianceResponse",

    # HS Code
    "HSCodeSection",
    "HSCodeSearchRequest",
    "HSCodeLookupRequest",
    "HSCodeDetails",
    "HSCodeSearchResponse",
    "HSCodeLookupResponse",
    "HSCodeCategoriesResponse",
    "HSCodeChapterResponse",

    # Document
    "DocumentCategory",
    "DocumentRequirement",
    "DocumentInfo",
    "DocumentChecklistRequest",
    "DocumentChecklistResponse",
    "DocumentTemplateRequest",
    "DocumentTemplate",
]