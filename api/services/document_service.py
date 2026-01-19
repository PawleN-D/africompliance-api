from typing import List, Dict, Optional
from enum import Enum
import logging

from api.models.document import (
    DocumentInfo,
    DocumentCategory,
    DocumentRequirement
)

logger = logging.getLogger(__name__)


class DocumentService:
    
    def __init__(self):
        logger.info("DocumentService initialized")
    
    def generate_checklist(
        self,
        destination_country: str,
        hs_code: str,
        value_zar: float,
        trade_bloc: Optional[str] = None,
        transport_mode: Optional[str] = None
    ) -> Dict:
        # Start with empty lists
        documents = []
        
        documents.extend(self._get_standard_documents())
        
        if trade_bloc:
            documents.extend(self._get_trade_bloc_documents(trade_bloc))

        documents.extend(self._get_hs_code_documents(hs_code))

        documents.extend(self._get_value_based_documents(value_zar))
        
        if transport_mode:
            documents.extend(self._get_transport_documents(transport_mode))
 
        checklist = self._organize_documents(documents)
        

        checklist['warnings'] = self._generate_warnings(
            hs_code, value_zar, trade_bloc
        )
        checklist['tips'] = self._generate_tips(
            destination_country, trade_bloc
        )
        
        # Step 8: Calculate totals
        checklist['total_required'] = len(checklist['required_documents'])
        checklist['total_optional'] = len(checklist['optional_documents'])
        
        logger.info(
            f"Generated checklist for {destination_country}: "
            f"{checklist['total_required']} required, "
            f"{checklist['total_optional']} optional"
        )
        
        return checklist
    
    def _get_standard_documents(self) -> List[DocumentInfo]:
 
        return [
            DocumentInfo(
                name="Commercial Invoice",
                category=DocumentCategory.COMMERCIAL,
                requirement_level=DocumentRequirement.REQUIRED,
                description=(
                    "Detailed invoice showing description of goods, quantity, "
                    "unit price, total value, payment terms, and Incoterms"
                ),
                issuer="Exporter/Seller",
                validity_days=None,  # No expiry
                notes="Must be on company letterhead with authorized signature",
                estimated_cost_zar=0.0,  # Free (you create it)
                processing_time_days=1
            ),
            
            DocumentInfo(
                name="Packing List",
                category=DocumentCategory.COMMERCIAL,
                requirement_level=DocumentRequirement.REQUIRED,
                description=(
                    "Detailed list of package contents including weights, "
                    "dimensions, and packaging type"
                ),
                issuer="Exporter/Seller",
                validity_days=None,
                notes="Must match commercial invoice exactly",
                estimated_cost_zar=0.0,
                processing_time_days=1
            ),
            
            DocumentInfo(
                name="Bill of Lading / Airway Bill",
                category=DocumentCategory.TRANSPORT,
                requirement_level=DocumentRequirement.REQUIRED,
                description=(
                    "Transport document serving as receipt for goods and "
                    "contract of carriage"
                ),
                issuer="Shipping Line / Airline / Freight Forwarder",
                validity_days=None,
                notes="Original required for sea freight, copy acceptable for air",
                estimated_cost_zar=500.0,  # Typical freight forwarder fee
                processing_time_days=1
            ),
            
            DocumentInfo(
                name="Customs Declaration (SAD 500)",
                category=DocumentCategory.CUSTOMS,
                requirement_level=DocumentRequirement.REQUIRED,
                description=(
                    "South African customs declaration form for export"
                ),
                issuer="Customs Broker / Exporter (if registered)",
                validity_days=None,
                notes="Must be submitted electronically via SARS eFiling",
                estimated_cost_zar=800.0,  # Typical broker fee
                processing_time_days=1
            ),
        ]
    
    def _get_trade_bloc_documents(self, trade_bloc: str) -> List[DocumentInfo]:

        documents = []
        
        # Check if it's a trade bloc we recognize
        if trade_bloc.upper() in ["SADC", "EAC", "ECOWAS", "COMESA"]:
            
            # Certificate of Origin is THE key document for preferential treatment
            documents.append(
                DocumentInfo(
                    name="Certificate of Origin",
                    category=DocumentCategory.COMPLIANCE,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description=(
                        f"Certifies that goods originate from South Africa "
                        f"for {trade_bloc} preferential duty treatment"
                    ),
                    issuer="South African Bureau of Standards (SABS) or Chamber of Commerce",
                    validity_days=180,  # Valid for 6 months
                    notes=(
                        f"Goods must meet {trade_bloc} Rules of Origin criteria. "
                        f"Typically requires 35-50% local/regional content."
                    ),
                    estimated_cost_zar=300.0,  # SABS/Chamber fee
                    processing_time_days=3
                )
            )
            
            # SADC-specific additional documents
            if trade_bloc.upper() == "SADC":
                documents.append(
                    DocumentInfo(
                        name="SADC Certificate of Origin (Form A)",
                        category=DocumentCategory.COMPLIANCE,
                        requirement_level=DocumentRequirement.REQUIRED,
                        description="Specific SADC format certificate",
                        issuer="SABS or Designated Authority",
                        validity_days=180,
                        notes="Must be endorsed by authorized signatory",
                        estimated_cost_zar=300.0,
                        processing_time_days=3
                    )
                )
        
        return documents
    
    def _get_hs_code_documents(self, hs_code: str) -> List[DocumentInfo]:
 
        documents = []

        cleaned_code = hs_code.replace(".", "").replace("-", "").replace(" ", "")
        
        # Get chapter (first 2 digits)
        # Example: "2204.21" -> "22" (Beverages)
        #          "8542.31" -> "85" (Electronics)
        chapter = cleaned_code[:2]
        
        # Food & Agriculture (Chapters 01-24)
        if chapter in [f"{i:02d}" for i in range(1, 25)]:
            documents.append(
                DocumentInfo(
                    name="Phytosanitary Certificate",
                    category=DocumentCategory.COMPLIANCE,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description=(
                        "Certifies that plants/plant products are free from "
                        "pests and diseases"
                    ),
                    issuer="Department of Agriculture, Land Reform and Rural Development",
                    validity_days=14,  # Very short validity!
                    notes="Must be issued within 14 days of export",
                    estimated_cost_zar=500.0,
                    processing_time_days=5
                )
            )
            
            # Meat & Dairy need extra certification
            if chapter in ["02", "04"]:  # Meat, Dairy
                documents.append(
                    DocumentInfo(
                        name="Veterinary Health Certificate",
                        category=DocumentCategory.COMPLIANCE,
                        requirement_level=DocumentRequirement.REQUIRED,
                        description="Certifies animal products are disease-free",
                        issuer="State Veterinarian",
                        validity_days=30,
                        notes="Required for all animal products",
                        estimated_cost_zar=800.0,
                        processing_time_days=7
                    )
                )
        
        # Pharmaceuticals (Chapter 30)
        if chapter == "30":
            documents.append(
                DocumentInfo(
                    name="SAHPRA Registration Certificate",
                    category=DocumentCategory.COMPLIANCE,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description=(
                        "South African Health Products Regulatory Authority "
                        "approval for pharmaceutical products"
                    ),
                    issuer="SAHPRA",
                    validity_days=None,  # Ongoing registration
                    notes=(
                        "Products must be registered before export. "
                        "Initial registration takes 6-12 months."
                    ),
                    estimated_cost_zar=15000.0,  # Very expensive!
                    processing_time_days=180  # 6 months minimum
                )
            )
        
        # Chemicals (Chapters 28-38)
        if chapter in [f"{i:02d}" for i in range(28, 39)]:
            documents.append(
                DocumentInfo(
                    name="Material Safety Data Sheet (MSDS)",
                    category=DocumentCategory.COMPLIANCE,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description="Chemical safety and handling information",
                    issuer="Manufacturer",
                    validity_days=None,
                    notes="Must be in English and destination country language",
                    estimated_cost_zar=0.0,  # Manufacturer provides
                    processing_time_days=1
                )
            )
        
        # Alcoholic Beverages (Chapter 22)
        if chapter == "22":
            documents.append(
                DocumentInfo(
                    name="Excise Clearance Certificate",
                    category=DocumentCategory.COMPLIANCE,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description="SARS clearance for alcoholic beverage export",
                    issuer="SARS (South African Revenue Service)",
                    validity_days=30,
                    notes="Required for all alcoholic products",
                    estimated_cost_zar=500.0,
                    processing_time_days=7
                )
            )
        
        # Tobacco (Chapter 24)
        if chapter == "24":
            documents.append(
                DocumentInfo(
                    name="Tobacco Products Control Certificate",
                    category=DocumentCategory.COMPLIANCE,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description="Compliance with health warning requirements",
                    issuer="Department of Health",
                    validity_days=None,
                    notes="Packaging must comply with destination country regulations",
                    estimated_cost_zar=1000.0,
                    processing_time_days=14
                )
            )
        
        # Diamonds & Precious Stones (Chapter 71)
        # Why: Conflict diamonds, money laundering, theft
        if chapter == "71":
            documents.append(
                DocumentInfo(
                    name="Kimberley Process Certificate",
                    category=DocumentCategory.COMPLIANCE,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description=(
                        "Certifies diamonds are conflict-free and legally mined"
                    ),
                    issuer="South African Diamond & Precious Metals Regulator (SADPMR)",
                    validity_days=90,
                    notes="MANDATORY for ALL diamond exports - no exceptions",
                    estimated_cost_zar=2000.0,
                    processing_time_days=10
                )
            )
        
        # Gold & Precious Metals (Chapter 71)
        if chapter == "71" and ("7108" in hs_code or "7109" in hs_code):
            documents.append(
                DocumentInfo(
                    name="South African Reserve Bank (SARB) Export Permit",
                    category=DocumentCategory.COMPLIANCE,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description="Central bank approval for precious metal export",
                    issuer="SARB Financial Surveillance Department",
                    validity_days=60,
                    notes="Strict foreign exchange control regulations apply",
                    estimated_cost_zar=1500.0,
                    processing_time_days=14
                )
            )
        
        return documents
    
    def _get_value_based_documents(self, value_zar: float) -> List[DocumentInfo]:
        documents = []
        
        # High-value shipments (>R500k)
        if value_zar > 500000:
            documents.append(
                DocumentInfo(
                    name="Cargo Insurance Certificate",
                    category=DocumentCategory.FINANCIAL,
                    requirement_level=DocumentRequirement.RECOMMENDED,  # Not mandatory but smart
                    description=(
                        "Insurance coverage for goods in transit"
                    ),
                    issuer="Insurance Company / Freight Forwarder",
                    validity_days=None,  # Covers specific shipment
                    notes=(
                        f"Recommended for shipment value R{value_zar:,.0f}. "
                        "Typically costs 0.5-1% of shipment value."
                    ),
                    estimated_cost_zar=value_zar * 0.007,  # 0.7% of value
                    processing_time_days=1
                )
            )
        
        # Very high-value shipments (>R1M)
        if value_zar > 1000000:
            documents.append(
                DocumentInfo(
                    name="Pre-Clearance Valuation Letter",
                    category=DocumentCategory.CUSTOMS,
                    requirement_level=DocumentRequirement.RECOMMENDED,
                    description=(
                        "Advance ruling from SARS on customs valuation to "
                        "avoid delays at clearance"
                    ),
                    issuer="SARS Customs Valuation Unit",
                    validity_days=90,
                    notes=(
                        "Highly recommended for high-value shipments to avoid "
                        "delays. Physical inspection likely."
                    ),
                    estimated_cost_zar=2000.0,
                    processing_time_days=21  # Can take 3 weeks
                )
            )
        
        return documents
    
    def _get_transport_documents(self, transport_mode: str) -> List[DocumentInfo]:

        documents = []
        
        mode_lower = transport_mode.lower()
        
        # Air freight specific
        if "air" in mode_lower:
            documents.append(
                DocumentInfo(
                    name="Air Waybill (AWB)",
                    category=DocumentCategory.TRANSPORT,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description="Air transport document and cargo receipt",
                    issuer="Airline or Freight Forwarder",
                    validity_days=None,
                    notes="Non-negotiable document (unlike sea bill of lading)",
                    estimated_cost_zar=300.0,
                    processing_time_days=1
                )
            )
        
        # Road freight specific (important for SADC)
        if "road" in mode_lower:
            documents.append(
                DocumentInfo(
                    name="CMR (Convention Marchandises Routières)",
                    category=DocumentCategory.TRANSPORT,
                    requirement_level=DocumentRequirement.REQUIRED,
                    description="International road transport consignment note",
                    issuer="Road Carrier / Transporter",
                    validity_days=None,
                    notes="Standard document for road freight in Southern Africa",
                    estimated_cost_zar=150.0,
                    processing_time_days=1
                )
            )
        
        return documents
    
    def _organize_documents(self, documents: List[DocumentInfo]) -> Dict:

        required = []
        optional = []
        permits = []
        
        seen_names = set()
        
        for doc in documents:

            if doc.name in seen_names:
                continue
            
            seen_names.add(doc.name)

            if "permit" in doc.name.lower() or "certificate" in doc.name.lower():
                if doc.requirement_level == DocumentRequirement.REQUIRED:
                    permits.append(doc)
            elif doc.requirement_level == DocumentRequirement.REQUIRED:
                required.append(doc)
            else:
                optional.append(doc)
        
        return {
            'required_documents': required,
            'optional_documents': optional,
            'permits_and_certificates': permits
        }
    
    def _generate_warnings(
        self,
        hs_code: str,
        value_zar: float,
        trade_bloc: Optional[str]
    ) -> List[str]:
        warnings = []
        
        # High-value warning
        if value_zar > 1000000:
            warnings.append(
                "⚠️ High-value shipment (>R1M): Expect physical inspection by customs. "
                "Allow extra 2-3 days for clearance."
            )
        
        # Trade bloc warning
        if trade_bloc:
            warnings.append(
                f"⚠️ {trade_bloc} preferential treatment ONLY applies if Certificate of Origin "
                "is provided. Without it, standard duties apply."
            )
        
        # Product-specific warnings
        chapter = hs_code.replace(".", "")[:2]
        
        if chapter in ["02", "04"]:  # Perishables
            warnings.append(
                "⚠️ Perishable goods: All health certificates must be obtained "
                "BEFORE shipping. Short validity periods (14-30 days)."
            )
        
        if chapter == "71":  # Precious goods
            warnings.append(
                "⚠️ Precious stones/metals: Strict export controls apply. "
                "Missing permits = criminal offense. Allow 14+ days for approvals."
            )
        
        if chapter == "30":  # Pharma
            warnings.append(
                "⚠️ Pharmaceutical products: Registration process can take 6-12 months. "
                "Plan well in advance."
            )
        
        return warnings
    
    def _generate_tips(
        self,
        destination_country: str,
        trade_bloc: Optional[str]
    ) -> List[str]:
        tips = []
        
        tips.append(
            "💡 Tip: Start collecting documents 2-3 weeks before shipment date"
        )
        
        tips.append(
            "💡 Tip: Keep digital and physical copies of ALL documents"
        )
        
        if trade_bloc:
            tips.append(
                f"💡 Tip: For {trade_bloc} shipments, ensure your goods meet rules of origin "
                "BEFORE applying for Certificate of Origin"
            )
        
        tips.append(
            "💡 Tip: Use a registered customs broker for faster clearance and compliance"
        )
        
        if "Nigeria" in destination_country or "Kenya" in destination_country:
            tips.append(
                f"💡 Tip: {destination_country} has strict import regulations. "
                "Contact destination customs in advance for specific requirements."
            )
        
        return tips