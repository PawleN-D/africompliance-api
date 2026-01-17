import requests
from typing import Optional, Dict
import re
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CIPCService:
    """
    Service for verifying South African companies via CIPC.
    
    For MVP: Uses mock data for demos
    For Production: Will use official CIPC API
    """
    
    def __init__(self):
        self.base_url = "https://eservices.cipc.co.za"
        self.cache = {}  # In-memory cache
        self.cache_ttl = timedelta(days=90)  # POPIA-compliant retention
    
    def verify_company(self, registration_number: str) -> Optional[Dict]:
        """
        Verify a company by registration number.
        
        Args:
            registration_number: SA company reg number (e.g., 2019/123456/07)
            
        Returns:
            Dictionary with company data, or None if not found
        """
        # Check cache first
        cached = self._get_from_cache(registration_number)
        if cached:
            logger.info(f"Cache hit for {registration_number}")
            return cached
        
        # Validate registration number format
        if not self._is_valid_reg_number(registration_number):
            logger.warning(f"Invalid registration number format: {registration_number}")
            return None
        
        # For MVP: Generate realistic mock data
        # TODO: Replace with actual CIPC API call when you get access
        company_data = self._mock_cipc_lookup(registration_number)
        
        # Cache the result
        if company_data:
            self._add_to_cache(registration_number, company_data)
        
        return company_data
    
    def _is_valid_reg_number(self, reg_number: str) -> bool:
        """
        Validate SA company registration number format.
        
        Valid formats:
        - 2019/123456/07
        - K2019/123456/07 (close corporations)
        """
        pattern = r'^[K]?\d{4}/\d{6}/\d{2}$'
        return bool(re.match(pattern, reg_number))
    
    def _mock_cipc_lookup(self, registration_number: str) -> Dict:
        """
        Generate realistic mock data for demos.
        
        This mimics what the real CIPC API would return.
        
        TODO: Replace this entire function when you have CIPC API access
        """
        # Extract year from registration number
        year = registration_number[:4] if not registration_number.startswith('K') else registration_number[1:5]
        
        return {
            "legal_name": f"Demo Logistics (Pty) Ltd",
            "registration_number": registration_number,
            "status": "In Business",
            "registration_date": f"{year}-03-15",
            "business_type": "Private Company",
            "registered_address": {
                "street": "123 Main Road",
                "suburb": "Parow",
                "city": "Cape Town",
                "province": "Western Cape",
                "postal_code": "7500"
            },
            "vat_registered": True,
            "vat_number": f"4{registration_number[5:11]}",
            "directors": [
                {
                    "full_name": "Demo Director",
                    "id_number": "7801015009***",  # Masked for POPIA
                    "appointment_date": f"{year}-03-15",
                    "is_active": True
                }
            ]
        }
    
    def _get_from_cache(self, reg_number: str) -> Optional[Dict]:
        """Get cached company data if not expired."""
        if reg_number in self.cache:
            cached_item = self.cache[reg_number]
            if datetime.now() < cached_item['expires_at']:
                return cached_item['data']
            else:
                # Expired, remove from cache
                del self.cache[reg_number]
        return None
    
    def _add_to_cache(self, reg_number: str, data: Dict):
        """Add company data to cache with expiry."""
        self.cache[reg_number] = {
            'data': data,
            'expires_at': datetime.now() + self.cache_ttl
        }