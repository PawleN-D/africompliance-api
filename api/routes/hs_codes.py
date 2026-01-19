from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from api.models import (
    HSCodeSearchRequest,
    HSCodeLookupRequest,
    HSCodeSearchResponse,
    HSCodeLookupResponse,
    HSCodeCategoriesResponse,
    HSCodeChapterResponse
)
from api.services.hs_code_service import HSCodeService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/hs-codes", tags=["HS Codes"])

# Initialize service
hs_code_service = HSCodeService()


@router.post("/search", response_model=HSCodeSearchResponse)
async def search_hs_codes(request: HSCodeSearchRequest):

    try:
        logger.info(f"HS code search: query='{request.query}', max={request.max_results}")
        
        # Search using service
        results = hs_code_service.search(
            query=request.query,
            max_results=request.max_results,
            category=request.category,
            chapter=request.chapter
        )
        
        # Extract unique categories from results
        categories_found = list(set(r.category for r in results))
        
        logger.info(f"Found {len(results)} HS codes for query '{request.query}'")
        
        return HSCodeSearchResponse(
            query=request.query,
            total_results=len(results),
            results=results,
            categories_found=sorted(categories_found)
        )
        
    except Exception as e:
        logger.error(f"HS code search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/lookup", response_model=HSCodeLookupResponse)
async def lookup_hs_code(request: HSCodeLookupRequest):

    try:
        logger.info(f"HS code lookup: {request.code}")
        
        # Lookup using service
        code_details = hs_code_service.lookup(request.code)
        
        if code_details:
            logger.info(f"Found HS code: {code_details.code}")
            return HSCodeLookupResponse(
                found=True,
                code_details=code_details
            )
        else:
            logger.warning(f"HS code not found: {request.code}")
            return HSCodeLookupResponse(
                found=False,
                code_details=None
            )
        
    except Exception as e:
        logger.error(f"HS code lookup error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Lookup failed: {str(e)}"
        )


@router.get("/categories", response_model=HSCodeCategoriesResponse)
async def get_categories():

    try:
        categories = hs_code_service.get_categories()
        
        return HSCodeCategoriesResponse(
            categories=categories,
            total_count=len(categories)
        )
        
    except Exception as e:
        logger.error(f"Get categories error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get categories: {str(e)}"
        )


@router.get("/chapter/{chapter}", response_model=HSCodeChapterResponse)
async def get_chapter_codes(chapter: str):

    try:
        logger.info(f"Getting codes for chapter: {chapter}")
        
        # Get codes
        codes = hs_code_service.get_by_chapter(chapter)
        
        # Get chapter description
        chapter_desc = hs_code_service.get_chapter_description(chapter)
        
        logger.info(f"Found {len(codes)} codes in chapter {chapter}")
        
        return HSCodeChapterResponse(
            chapter=chapter.zfill(2),  # Pad to 2 digits
            chapter_description=chapter_desc,
            codes=codes,
            total_count=len(codes)
        )
        
    except Exception as e:
        logger.error(f"Get chapter codes error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chapter codes: {str(e)}"
        )


@router.get("/popular")
async def get_popular_codes(
    limit: int = Query(default=20, ge=1, le=50, description="Number of codes to return")
):
    try:
        codes = hs_code_service.get_popular_codes(limit)
        
        return {
            "popular_codes": codes,
            "total_count": len(codes)
        }
        
    except Exception as e:
        logger.error(f"Get popular codes error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get popular codes: {str(e)}"
        )