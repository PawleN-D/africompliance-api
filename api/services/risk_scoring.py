from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path so we can import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import RiskFlags
import logging

logger = logging.getLogger(__name__)

class RiskScoringService:
    """
    Assess risk based on company data.
    
    Scoring logic:
    - Start with score of 100 (perfect)
    - Deduct points for each risk factor found
    """
    
    def calculate_risk_score(
        self, 
        company_data: Dict, 
        directors: List[Dict]
    ) -> Tuple[int, RiskFlags]:
        """
        Calculate confidence score (0-100) and identify risk flags.
        
        Args:
            company_data: Dictionary with company information
            directors: List of director dictionaries
            
        Returns:
            Tuple of (confidence_score, risk_flags)
        """
        score = 100
        flags = RiskFlags()
        
        # Check 1: Company status
        status = company_data.get('status', '').lower()
        if status != 'in business':
            score -= 50
            if 'deregistration' in status or 'deregister' in status:
                flags.deregistration_pending = True
                logger.warning(f"Company deregistration pending: {company_data.get('legal_name')}")
        
        # Check 2: VAT registration
        if not company_data.get('vat_registered'):
            score -= 10
            flags.no_vat_registration = True
            logger.info(f"Company not VAT registered: {company_data.get('legal_name')}")
        
        # Check 3: Company age (very new = higher risk)
        reg_date = company_data.get('registration_date')
        if reg_date:
            try:
                from datetime import datetime
                reg_datetime = datetime.fromisoformat(reg_date)
                days_old = (datetime.now() - reg_datetime).days
                
                if days_old < 90:  # Less than 3 months old
                    score -= 15
                    logger.info(f"New company (<90 days): {company_data.get('legal_name')}")
                    
            except Exception as e:
                logger.error(f"Error parsing registration date: {e}")
        
        # Check 4: Directors (sanctions and watchlists)
        for director in directors:
            if self._check_sanctions(director):
                score -= 30
                flags.sanctions_match = True
                logger.warning(f"Sanctions match for director: {director.get('full_name')}")
                
            if self._check_watchlist(director):
                score -= 20
                flags.director_on_watchlist = True
                logger.warning(f"Watchlist match for director: {director.get('full_name')}")
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        logger.info(f"Risk score calculated: {score} for {company_data.get('legal_name')}")
        
        return score, flags
    
    def _check_sanctions(self, director: Dict) -> bool:
        """
        Check if director is on sanctions lists.
        
        TODO: Integrate with:
        - UN Sanctions List
        - OFAC SDN List
        - EU Sanctions List
        - South African sanctions
        """
        # For MVP: Always returns False
        # In production, this would check against actual databases
        return False
    
    def _check_watchlist(self, director: Dict) -> bool:
        """
        Check if director is on fraud watchlists.
        
        TODO: Integrate with:
        - TPN fraud database
        - Credit bureau data
        - Court records
        """
        # For MVP: Always returns False
        return False