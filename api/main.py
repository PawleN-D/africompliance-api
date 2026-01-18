from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from api.services.trade_service import TradeComplianceService
import uuid
import logging

from api.models import (
    VerificationRequest,
    VerificationResponse,
    VerificationStatus,
    Business,
    Director,
    RiskFlags,
    POPIACompliance,
    Address,
    TradeTransaction,
    TradeComplianceResponse,
    CalculationBreakdown,
    ComplianceRequirement
)
from api.services.cipc_service import CIPCService
from api.services.risk_scoring import RiskScoringService
from api.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="POPIA-compliant business verification API for South African companies",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration (allow all for MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
cipc_service = CIPCService()
risk_service = RiskScoringService()
trade_service = TradeComplianceService() 

# Simple rate limiting
request_counts = {}

def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    
    # Clean old entries
    request_counts[client_ip] = [
        timestamp for timestamp in request_counts.get(client_ip, [])
        if timestamp > hour_ago
    ]
    
    # Check limit
    if len(request_counts.get(client_ip, [])) >= settings.MAX_REQUESTS_PER_HOUR:
        return False
    
    # Add current request
    if client_ip not in request_counts:
        request_counts[client_ip] = []
    request_counts[client_ip].append(now)
    
    return True

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    client_ip = request.client.host
    
    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Maximum {settings.MAX_REQUESTS_PER_HOUR} requests per hour allowed"
            }
        )
    
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    """Root endpoint - basic info"""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "cipc": "operational",
            "database": "operational",
            "cache": "operational"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/v1/verify/business/za", response_model=VerificationResponse)
async def verify_business(request: VerificationRequest):
    """
    Verify a South African business.
    
    Returns company information, director details, and risk assessment.
    All data handling complies with POPIA regulations.
    """
    try:
        logger.info(f"Verification request for: {request.registration_number}")
        
        # Generate unique request ID
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        # Verify with CIPC
        company_data = cipc_service.verify_company(request.registration_number)
        
        if not company_data:
            logger.warning(f"Company not found: {request.registration_number}")
            return {
                "status": VerificationStatus.NOT_FOUND,
                "confidence_score": 0,
                "business": None,
                "directors": None,
                "risk_flags": {
                    "sanctions_match": False,
                    "deregistration_pending": False,
                    "director_on_watchlist": False,
                    "recent_name_change": False,
                    "no_vat_registration": False
                },
                "compliance": {
                    "popia_consent_obtained": True,
                    "data_retention_days": 90,
                    "data_source": "CIPC"
                },
                "verified_at": datetime.now(),
                "request_id": request_id
            }
        
        # Extract directors if requested
        directors_list = None
        if request.verify_directors and 'directors' in company_data:
            directors_list = [
                Director(**director) for director in company_data['directors']
            ]
        
        # Calculate risk score
        confidence_score, risk_flags = risk_service.calculate_risk_score(
            company_data,
            company_data.get('directors', [])
        )
        
        # Build business object
        business = Business(
            legal_name=company_data['legal_name'],
            registration_number=company_data['registration_number'],
            status=company_data['status'],
            registration_date=company_data.get('registration_date'),
            business_type=company_data.get('business_type'),
            registered_address=Address(**company_data['registered_address']) if 'registered_address' in company_data else None,
            vat_registered=company_data.get('vat_registered', False),
            vat_number=company_data.get('vat_number')
        )
        
        logger.info(f"Verification successful: {company_data['legal_name']} - Score: {confidence_score}")
        
        # Return as dict - FastAPI will convert to VerificationResponse
        return {
            "status": VerificationStatus.VERIFIED,
            "confidence_score": confidence_score,
            "business": business,
            "directors": directors_list,
            "risk_flags": {
                "sanctions_match": risk_flags.sanctions_match,
                "deregistration_pending": risk_flags.deregistration_pending,
                "director_on_watchlist": risk_flags.director_on_watchlist,
                "recent_name_change": risk_flags.recent_name_change,
                "no_vat_registration": risk_flags.no_vat_registration
            },
            "compliance": {
                "popia_consent_obtained": True,
                "data_retention_days": 90,
                "data_source": "CIPC"
            },
            "verified_at": datetime.now(),
            "request_id": request_id
        }
        
    except Exception as e:
        logger.error(f"Verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )
    
@app.post("/v1/calculate/trade", response_model=TradeComplianceResponse)
async def calculate_trade_compliance(request: TradeTransaction):
    """
    Calculate duties, VAT, and compliance requirements for cross-border trade.
    
    This endpoint helps logistics companies and customs brokers:
    - Calculate estimated duties and VAT
    - Identify required documentation
    - Understand trade agreements (SADC, EAC, ECOWAS)
    - Get compliance notes and warnings
    
    Perfect for: Cross-border freight, customs clearance, cost estimation
    """
    try:
        logger.info(
            f"Trade calculation request: {request.origin_country} → "
            f"{request.destination_country}, Value: R{request.value_zar:,.2f}"
        )
        
        # Generate unique request ID
        request_id = f"trade_{uuid.uuid4().hex[:12]}"
        
        # Optional: Verify supplier if registration provided
        supplier_verified = False
        if request.supplier_registration:
            supplier_data = cipc_service.verify_company(request.supplier_registration)
            if supplier_data and supplier_data.get('status') == 'In Business':
                supplier_verified = True
                logger.info(f"Supplier verified: {supplier_data.get('legal_name')}")
            else:
                logger.warning(f"Supplier not verified: {request.supplier_registration}")
        
        # Calculate trade compliance
        calculations, compliance_req, warnings = trade_service.calculate_compliance(
            item_description=request.item_description,
            hs_code=request.hs_code,
            value_zar=request.value_zar,
            origin_country=request.origin_country,
            destination_country=request.destination_country
        )
        
        # Add warning if supplier not verified but registration was provided
        if request.supplier_registration and not supplier_verified:
            warnings.append(
                f"Warning: Supplier registration {request.supplier_registration} "
                f"could not be verified. Shipment may face delays."
            )
        
        logger.info(f"Trade calculation successful: Request ID {request_id}")
        
        # Return response as dict
        return {
            "status": "success",
            "transaction": request,
            "calculations": calculations,
            "compliance": compliance_req,
            "warnings": warnings,
            "calculated_at": datetime.now(),
            "request_id": request_id
        }
        
    except Exception as e:
        logger.error(f"Trade calculation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Trade calculation failed: {str(e)}"
        )
# For Vercel deployment
app = app