"""
Document Checklist API Routes

Endpoints for generating trade document checklists.
"""

from fastapi import APIRouter, HTTPException
import logging

from api.models import (
    DocumentChecklistRequest,
    DocumentChecklistResponse
)
from api.services.document_service import DocumentService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/documents", tags=["Documents"])

# Initialize service
document_service = DocumentService()


@router.post("/checklist", response_model=DocumentChecklistResponse)
async def generate_document_checklist(request: DocumentChecklistRequest):

    try:
        logger.info(
            f"Document checklist request: {request.destination_country}, "
            f"HS: {request.hs_code}, Value: R{request.value_zar:,.0f}"
        )
        
        # Generate checklist using service
        checklist = document_service.generate_checklist(
            destination_country=request.destination_country,
            hs_code=request.hs_code,
            value_zar=request.value_zar,
            trade_bloc=request.trade_bloc,
            transport_mode=request.transport_mode
        )
        
        # Add request context to response
        response_data = {
            "destination_country": request.destination_country,
            "hs_code": request.hs_code,
            "value_zar": request.value_zar,
            "trade_bloc": request.trade_bloc,
            **checklist
        }
        
        logger.info(
            f"Generated checklist: {response_data['total_required']} required, "
            f"{response_data['total_optional']} optional, "
            f"{len(response_data['permits_and_certificates'])} permits"
        )
        
        return DocumentChecklistResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Document checklist error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate checklist: {str(e)}"
        )


@router.get("/info/{document_name}")
async def get_document_info(document_name: str):
    """
    **Note:**
    This is a placeholder - full implementation would query a document database
    """
    try:
        # For MVP, return basic info
        # In production, this would query a comprehensive document database
        
        common_docs = {
            "certificate of origin": {
                "name": "Certificate of Origin",
                "description": "Certifies the country of origin for preferential duty treatment",
                "issuer": "SABS or Chamber of Commerce",
                "processing_time_days": 3,
                "cost_zar": 300.0,
                "validity_days": 180,
                "notes": "Required for SADC/EAC/ECOWAS preferential treatment"
            },
            "commercial invoice": {
                "name": "Commercial Invoice",
                "description": "Detailed invoice of goods being shipped",
                "issuer": "Exporter",
                "processing_time_days": 1,
                "cost_zar": 0.0,
                "validity_days": None,
                "notes": "Must be on company letterhead with authorized signature"
            },
            "phytosanitary certificate": {
                "name": "Phytosanitary Certificate",
                "description": "Certifies plant products are pest-free",
                "issuer": "Department of Agriculture",
                "processing_time_days": 5,
                "cost_zar": 500.0,
                "validity_days": 14,
                "notes": "Required for all plant and plant product exports"
            }
        }
        
        doc_key = document_name.lower()
        
        if doc_key in common_docs:
            return common_docs[doc_key]
        else:
            return {
                "name": document_name,
                "description": "Document information not available in database",
                "note": "Contact customs broker for specific requirements"
            }
        
    except Exception as e:
        logger.error(f"Get document info error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document info: {str(e)}"
        )