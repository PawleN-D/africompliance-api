"""
HS Code (Harmonized System) Lookup Service

Provides search and lookup functionality for HS tariff codes.
Works 100% offline with no external dependencies.

Data Source: South African Revenue Service (SARS) Tariff Book
Last Updated: 2026-01-18
"""

from typing import List, Dict, Optional, Set
import json
import os
import logging
from functools import lru_cache

from api.models.hs_code import HSCodeDetails

logger = logging.getLogger(__name__)


class HSCodeService:
    """
    HS Code lookup and search service
    
    Features:
    - Fuzzy search by product description
    - Exact code lookup
    - Category and chapter filtering
    - Duty rate information
    - Compliance requirements
    """
    
    # Chapter descriptions for reference
    CHAPTER_DESCRIPTIONS = {
        "01": "Live animals",
        "02": "Meat and edible meat offal",
        "03": "Fish and crustaceans",
        "04": "Dairy produce; eggs; honey",
        "05": "Products of animal origin",
        "06": "Live trees and plants",
        "07": "Edible vegetables",
        "08": "Edible fruit and nuts",
        "09": "Coffee, tea, spices",
        "10": "Cereals",
        "22": "Beverages, spirits and vinegar",
        "24": "Tobacco",
        "27": "Mineral fuels, oils",
        "30": "Pharmaceutical products",
        "40": "Rubber and articles thereof",
        "62": "Articles of apparel (not knitted)",
        "71": "Precious stones, metals, jewelry",
        "72": "Iron and steel",
        "84": "Machinery and mechanical appliances",
        "85": "Electrical machinery and equipment",
        "87": "Vehicles",
        "90": "Optical, medical instruments"
    }
    
    def __init__(self, data_path: str = "api/data/hs_codes.json"):
        self.data_path = data_path
        self._codes: List[Dict] = []
        self._categories: Set[str] = set()
        self._load_data()
        
        logger.info(
            f"HSCodeService initialized with {len(self._codes)} codes "
            f"across {len(self._categories)} categories"
        )
    
    def _load_data(self):
        """Load HS codes from JSON file"""
        try:
            full_path = self.data_path
            
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    self._codes = json.load(f)
                
                # Extract unique categories
                self._categories = {code['category'] for code in self._codes}
                
                logger.info(f"Loaded {len(self._codes)} HS codes from {full_path}")
            else:
                logger.error(f"HS code data file not found: {full_path}")
                self._codes = []
        except Exception as e:
            logger.error(f"Error loading HS codes: {e}", exc_info=True)
            self._codes = []
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        category: Optional[str] = None,
        chapter: Optional[str] = None
    ) -> List[HSCodeDetails]:
        """
        Search HS codes by description
        
        Args:
            query: Search term (e.g., "wine", "electronics")
            max_results: Maximum results to return
            category: Filter by category
            chapter: Filter by chapter
            
        Returns:
            List of matching HS codes sorted by relevance
        """
        if not query or len(query) < 2:
            return []
        
        query_lower = query.lower().strip()
        query_words = query_lower.split()
        results = []
        
        for code_data in self._codes:
            # Apply filters
            if category and code_data['category'] != category:
                continue
            
            if chapter and code_data['chapter'] != chapter:
                continue
            
            # Calculate relevance score
            score = self._calculate_relevance(code_data, query_lower, query_words)
            
            if score > 0:
                hs_code = HSCodeDetails(
                    code=code_data['code'],
                    description=code_data['description'],
                    category=code_data['category'],
                    chapter=code_data['chapter'],
                    section=code_data['section'],
                    duty_rate_general=code_data['duty_rate_general'],
                    vat_applicable=code_data['vat_applicable'],
                    special_permits=code_data['special_permits'],
                    common_destinations=code_data['common_destinations'],
                    notes=code_data.get('notes'),
                    relevance_score=score
                )
                results.append(hs_code)
        
        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:max_results]
    
    def _calculate_relevance(
        self,
        code_data: Dict,
        query_lower: str,
        query_words: List[str]
    ) -> float:
        """
        Calculate relevance score for search result
        
        Scoring algorithm:
        - Exact phrase match in description: 50 points
        - Word boundary match: +20 points
        - Category match: 15 points
        - Each word match in description: 10 points
        - Word match in notes: 5 points
        """
        score = 0.0
        
        description_lower = code_data['description'].lower()
        category_lower = code_data['category'].lower()
        notes_lower = code_data.get('notes', '').lower()
        
        # Exact phrase match
        if query_lower in description_lower:
            score += 50.0
            
            # Bonus for word boundary match (not partial word)
            if f" {query_lower} " in f" {description_lower} " or \
               description_lower.startswith(query_lower) or \
               description_lower.endswith(query_lower):
                score += 20.0
        
        # Category match
        if query_lower in category_lower:
            score += 15.0
        
        # Individual word matches
        for word in query_words:
            if len(word) >= 3:  # Only score words 3+ chars
                if word in description_lower:
                    score += 10.0
                if word in notes_lower:
                    score += 5.0
        
        return score
    
    def lookup(self, code: str) -> Optional[HSCodeDetails]:
        """
        Exact lookup by HS code
        
        Args:
            code: HS code (e.g., "8542.31", "854231")
            
        Returns:
            HS code details or None if not found
        """
        # Normalize code (remove dots, spaces, dashes)
        normalized = self._normalize_code(code)
        
        for code_data in self._codes:
            code_normalized = self._normalize_code(code_data['code'])
            
            # Match exact code or prefix
            if code_normalized == normalized or code_normalized.startswith(normalized):
                return HSCodeDetails(
                    code=code_data['code'],
                    description=code_data['description'],
                    category=code_data['category'],
                    chapter=code_data['chapter'],
                    section=code_data['section'],
                    duty_rate_general=code_data['duty_rate_general'],
                    vat_applicable=code_data['vat_applicable'],
                    special_permits=code_data['special_permits'],
                    common_destinations=code_data['common_destinations'],
                    notes=code_data.get('notes'),
                    relevance_score=100.0
                )
        
        return None
    
    @staticmethod
    def _normalize_code(code: str) -> str:
        """Normalize HS code for comparison"""
        return code.replace(".", "").replace(" ", "").replace("-", "").upper()
    
    def get_categories(self) -> List[str]:
        """Get list of all available categories"""
        return sorted(list(self._categories))
    
    def get_by_chapter(self, chapter: str) -> List[HSCodeDetails]:
        """
        Get all codes in a specific chapter
        
        Args:
            chapter: Chapter number (e.g., "22", "85")
            
        Returns:
            List of HS codes in that chapter
        """
        results = []
        
        # Normalize chapter (pad to 2 digits)
        chapter_normalized = chapter.zfill(2)
        
        for code_data in self._codes:
            if code_data['chapter'] == chapter_normalized:
                results.append(HSCodeDetails(
                    code=code_data['code'],
                    description=code_data['description'],
                    category=code_data['category'],
                    chapter=code_data['chapter'],
                    section=code_data['section'],
                    duty_rate_general=code_data['duty_rate_general'],
                    vat_applicable=code_data['vat_applicable'],
                    special_permits=code_data['special_permits'],
                    common_destinations=code_data['common_destinations'],
                    notes=code_data.get('notes')
                ))
        
        return results
    
    def get_chapter_description(self, chapter: str) -> str:
        """Get description for a chapter"""
        chapter_normalized = chapter.zfill(2)
        return self.CHAPTER_DESCRIPTIONS.get(
            chapter_normalized,
            f"Chapter {chapter_normalized}"
        )
    
    @lru_cache(maxsize=100)
    def get_popular_codes(self, limit: int = 20) -> List[HSCodeDetails]:
        """
        Get most commonly used HS codes
        
        Based on export volume (simulated for now)
        """
        # For MVP, return a curated list of common exports
        common_codes = [
            "2204.21",  # Wine
            "7102.31",  # Diamonds
            "8703.23",  # Motor cars
            "0805.10",  # Oranges
            "8542.31",  # Electronics
            "6203.42",  # Clothing
            "2709.00",  # Petroleum
            "7108.13",  # Gold
        ]
        
        results = []
        for code in common_codes[:limit]:
            hs_code = self.lookup(code)
            if hs_code:
                results.append(hs_code)
        
        return results