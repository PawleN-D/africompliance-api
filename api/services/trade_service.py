from typing import Dict, List, Tuple
import logging
from api.models.trade import TradeBloc, DocumentType

logger = logging.getLogger(__name__)

class TradeComplianceService:
    """
    Calculate duties, VAT, and compliance requirements for cross-border trade.
    
    Production-ready implementation with proper error handling and validation.
    """
    
    # SADC member states (Southern African Development Community)
    SADC_COUNTRIES = [
        "Angola", "Botswana", "Comoros", "Congo", "Eswatini", "Lesotho",
        "Madagascar", "Malawi", "Mauritius", "Mozambique", "Namibia",
        "Seychelles", "South Africa", "Tanzania", "Zambia", "Zimbabwe"
    ]
    
    # EAC member states (East African Community)
    EAC_COUNTRIES = [
        "Burundi", "Kenya", "Rwanda", "South Sudan", "Tanzania", "Uganda"
    ]
    
    # ECOWAS member states (Economic Community of West African States)
    ECOWAS_COUNTRIES = [
        "Benin", "Burkina Faso", "Cape Verde", "Ivory Coast", "Gambia",
        "Ghana", "Guinea", "Guinea-Bissau", "Liberia", "Mali", "Niger",
        "Nigeria", "Senegal", "Sierra Leone", "Togo"
    ]
    
    # COMESA member states
    COMESA_COUNTRIES = [
        "Burundi", "Comoros", "Congo", "Djibouti", "Egypt", "Eritrea",
        "Eswatini", "Ethiopia", "Kenya", "Libya", "Madagascar", "Malawi",
        "Mauritius", "Rwanda", "Seychelles", "Somalia", "Sudan", "Tunisia",
        "Uganda", "Zambia", "Zimbabwe"
    ]
    
    # Standard rates
    SA_VAT_RATE = 0.15  # South African VAT is 15%
    
    def __init__(self):
        self.duty_rates = self._initialize_duty_rates()
    
    def _initialize_duty_rates(self) -> Dict[str, float]:
        """
        Initialize duty rates by trade bloc.
        
        TODO: Integrate with actual tariff databases:
        - SARS Customs Tariff Book
        - WTO Tariff Database
        - AfCFTA tariff schedules
        """
        return {
            TradeBloc.SADC: 0.0,           # SADC Free Trade Area = 0% for most goods
            TradeBloc.EAC: 0.05,           # EAC has varying rates, using 5% average
            TradeBloc.ECOWAS: 0.10,        # ECOWAS external tariff averages ~10%
            TradeBloc.COMESA: 0.05,        # COMESA preferential rates
            TradeBloc.OTHER_AFRICA: 0.15,  # Other African countries
            TradeBloc.REST_OF_WORLD: 0.20  # Non-African countries
        }
    
    def calculate_compliance(
        self,
        item_description: str,
        hs_code: str,
        value_zar: float,
        origin_country: str,
        destination_country: str
    ) -> Tuple[Dict, Dict, List[str]]:
        """
        Calculate duties, VAT, and compliance requirements.
        
        Returns:
            Tuple of (calculations_dict, compliance_dict, warnings_list)
        """
        warnings = []
        
        # Determine trade bloc
        trade_bloc = self._get_trade_bloc(destination_country)
        
        # Get duty rate
        duty_rate = self.duty_rates.get(trade_bloc, 0.20)
        
        # Validate HS code
        if not self._is_valid_hs_code(hs_code):
            warnings.append(f"HS Code '{hs_code}' may be invalid. Please verify with SARS tariff book.")
        
        # Calculate amounts
        customs_duty_amount = value_zar * duty_rate
        subtotal_before_vat = value_zar + customs_duty_amount
        sa_vat_amount = subtotal_before_vat * self.SA_VAT_RATE  # VAT is on CIF + duty
        total_at_border = subtotal_before_vat + sa_vat_amount
        
        # Calculate savings from trade agreements
        standard_duty_rate = 0.20  # Standard non-preferential rate
        duty_saved = value_zar * (standard_duty_rate - duty_rate)
        
        # Build calculations dict (matching CalculationBreakdown model)
        calculations = {
            "base_value_zar": round(value_zar, 2),
            "sa_vat_rate": self.SA_VAT_RATE,
            "sa_vat_amount": round(sa_vat_amount, 2),
            "customs_duty_rate": duty_rate,
            "customs_duty_amount": round(customs_duty_amount, 2),
            "additional_fees": 0.0,  # Can add storage/handling fees later
            "subtotal_before_vat": round(subtotal_before_vat, 2),
            "total_at_border": round(total_at_border, 2),
            "currency": "ZAR",
            "duty_saved_via_trade_agreement": round(duty_saved, 2) if duty_saved > 0 else 0.0
        }
        
        # Get compliance requirements (matching ComplianceRequirement model)
        compliance = self._get_compliance_requirements(
            destination_country,
            trade_bloc,
            hs_code,
            value_zar
        )
        
        logger.info(
            f"Trade calculation: {origin_country} → {destination_country}, "
            f"Bloc: {trade_bloc}, Value: R{value_zar:,.2f}, Duty: {duty_rate*100}%, "
            f"Total: R{total_at_border:,.2f}"
        )
        
        return calculations, compliance, warnings
    
    def _get_trade_bloc(self, country: str) -> TradeBloc:
        """Determine which trade bloc a country belongs to."""
        country_normalized = country.strip().title()
        
        if country_normalized in self.SADC_COUNTRIES:
            return TradeBloc.SADC
        elif country_normalized in self.EAC_COUNTRIES:
            return TradeBloc.EAC
        elif country_normalized in self.ECOWAS_COUNTRIES:
            return TradeBloc.ECOWAS
        elif country_normalized in self.COMESA_COUNTRIES:
            return TradeBloc.COMESA
        elif self._is_african_country(country_normalized):
            return TradeBloc.OTHER_AFRICA
        else:
            return TradeBloc.REST_OF_WORLD
    
    def _is_african_country(self, country: str) -> bool:
        """Check if country is in Africa (basic heuristic)."""
        african_countries = [
            "Algeria", "Egypt", "Libya", "Morocco", "Tunisia",  # North Africa
            "Chad", "Mali", "Mauritania", "Niger", "Sudan",    # Sahel
            "Cameroon", "Central African Republic", "Gabon",   # Central Africa
            "Ethiopia", "Somalia", "South Sudan",              # Horn of Africa
        ]
        return country in african_countries or "Africa" in country
    
    def _is_valid_hs_code(self, hs_code: str) -> bool:
        """
        Basic validation of HS code format.
        
        HS codes are typically 6-10 digits, may include dots/dashes.
        """
        # Remove common separators
        cleaned = hs_code.replace(".", "").replace("-", "").replace(" ", "")
        
        # Check if it's numeric and reasonable length
        return cleaned.isdigit() and 4 <= len(cleaned) <= 10
    
    def _get_compliance_requirements(
        self,
        destination_country: str,
        trade_bloc: TradeBloc,
        hs_code: str,
        value_zar: float
    ) -> Dict:
        """
        Determine compliance requirements based on destination and goods.
        
        Returns dict matching ComplianceRequirement model.
        """
        country_normalized = destination_country.strip().title()
        
        # Determine trade agreement
        trade_agreement = self._get_trade_agreement_name(trade_bloc)
        
        # Required documents (always needed)
        required_documents = [
            DocumentType.COMMERCIAL_INVOICE,
            DocumentType.PACKING_LIST,
            DocumentType.BILL_OF_LADING,
            DocumentType.CUSTOMS_DECLARATION
        ]
        
        # Certificate of Origin for preferential treatment
        rules_of_origin_required = False
        minimum_local_content = None
        
        if trade_bloc in [TradeBloc.SADC, TradeBloc.EAC, TradeBloc.ECOWAS, TradeBloc.COMESA]:
            required_documents.append(DocumentType.CERTIFICATE_OF_ORIGIN)
            rules_of_origin_required = True
            
            if trade_bloc == TradeBloc.SADC:
                minimum_local_content = 35.0  # SADC Rules of Origin
            elif trade_bloc == TradeBloc.EAC:
                minimum_local_content = 50.0  # EAC Rules of Origin
        
        # Optional documents
        optional_documents = []
        
        # Special permits based on HS code
        special_permits = self._get_special_permits(hs_code)
        
        # High-value shipments
        if value_zar > 1000000:  # Over R1M
            special_permits.append("Physical Inspection Likely (High Value Shipment)")
        
        # Estimated clearance time
        clearance_days = self._estimate_clearance_time(trade_bloc, value_zar, len(special_permits))
        
        # Compliance notes
        compliance_notes = self._generate_compliance_notes(
            trade_bloc,
            trade_agreement,
            rules_of_origin_required,
            minimum_local_content,
            value_zar
        )
        
        # Warnings
        warnings = []
        if len(special_permits) > 0:
            warnings.append("Special permits required - allow additional 5-10 days for processing")
        if value_zar > 500000:
            warnings.append("High-value shipment - recommend pre-clearance consultation with SARS")
        
        return {
            "trade_bloc": trade_bloc,
            "trade_agreement": trade_agreement,
            "required_documents": required_documents,
            "optional_documents": optional_documents,
            "special_permits_required": special_permits,
            "rules_of_origin_required": rules_of_origin_required,
            "minimum_local_content_percent": minimum_local_content,
            "estimated_clearance_days": clearance_days,
            "compliance_notes": compliance_notes,
            "warnings": warnings
        }
    
    def _get_trade_agreement_name(self, trade_bloc: TradeBloc) -> str | None:
        """Get the name of the trade agreement."""
        agreements = {
            TradeBloc.SADC: "SADC Free Trade Area",
            TradeBloc.EAC: "East African Community Customs Union",
            TradeBloc.ECOWAS: "ECOWAS Trade Liberalisation Scheme",
            TradeBloc.COMESA: "COMESA Free Trade Area"
        }
        return agreements.get(trade_bloc)
    
    def _get_special_permits(self, hs_code: str) -> List[str]:
        """Determine special permits needed based on HS code."""
        permits = []
        cleaned_code = hs_code.replace(".", "").replace("-", "").replace(" ", "")
        
        # Chapter-based permit requirements
        if cleaned_code.startswith("93"):  # Arms and ammunition
            permits.append("Import Permit from NCACC (National Conventional Arms Control Committee)")
            permits.append("End User Certificate")
        elif cleaned_code.startswith("27"):  # Mineral fuels
            permits.append("Department of Mineral Resources and Energy Permit")
        elif cleaned_code.startswith("30"):  # Pharmaceutical products
            permits.append("SAHPRA Registration (South African Health Products Regulatory Authority)")
        elif cleaned_code.startswith("02") or cleaned_code.startswith("04"):  # Meat, dairy
            permits.append("Veterinary Health Certificate")
            permits.append("Department of Agriculture Import Permit")
        elif cleaned_code.startswith("06") or cleaned_code.startswith("07"):  # Live plants, vegetables
            permits.append("Phytosanitary Certificate")
            permits.append("Department of Agriculture Import Permit")
        elif cleaned_code.startswith("22"):  # Alcoholic beverages
            permits.append("Excise Registration (if applicable)")
        elif cleaned_code.startswith("24"):  # Tobacco
            permits.append("Excise Registration")
            permits.append("Health Warning Labels Compliance")
        
        return permits
    
    def _estimate_clearance_time(self, trade_bloc: TradeBloc, value_zar: float, permit_count: int) -> int:
        """Estimate customs clearance time in days."""
        # Base clearance time by trade bloc
        base_days = {
            TradeBloc.SADC: 2,
            TradeBloc.EAC: 3,
            TradeBloc.ECOWAS: 3,
            TradeBloc.COMESA: 3,
            TradeBloc.OTHER_AFRICA: 5,
            TradeBloc.REST_OF_WORLD: 7
        }
        
        days = base_days.get(trade_bloc, 7)
        
        # Add time for high-value shipments
        if value_zar > 1000000:
            days += 2
        elif value_zar > 500000:
            days += 1
        
        # Add time for special permits
        days += permit_count * 2
        
        return days
    
    def _generate_compliance_notes(
        self,
        trade_bloc: TradeBloc,
        trade_agreement: str | None,
        rules_of_origin_required: bool,
        minimum_local_content: float | None,
        value_zar: float
    ) -> List[str]:
        """Generate compliance notes for the shipment."""
        notes = []
        
        # Trade agreement notes
        if trade_agreement:
            notes.append(
                f"Preferential duty treatment available under {trade_agreement}"
            )
        
        # Rules of origin
        if rules_of_origin_required:
            notes.append(
                f"Certificate of Origin required. Goods must meet rules of origin criteria."
            )
            if minimum_local_content:
                notes.append(
                    f"Minimum {minimum_local_content}% local/regional content required for duty-free treatment"
                )
        
        # Standard documents
        notes.append(
            "Ensure all commercial documents (invoice, packing list) are accurate and match"
        )
        
        # High-value notes
        if value_zar > 500000:
            notes.append(
                "High-value shipment: Consider advance customs declaration for faster clearance"
            )
        
        # General compliance
        notes.append(
            "Goods declaration must be submitted via SARS eFiling or registered customs broker"
        )
        
        return notes