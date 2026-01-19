from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class HSCodeSection(str, Enum):
    I = "I - Live Animals & Animal Products"
    II = "II - Vegetable Products"
    III = "III - Animal/Vegetable Fats & Oils"
    IV = "IV - Food Products, Beverages & Tobacco"
    V = "V - Mineral Products"
    VI = "VI - Chemical Products"
    VII = "VII - Plastics & Rubber"
    VIII = "VIII - Raw Hides, Skins, Leather"
    IX = "IX - Wood & Wood Products"
    X = "X - Pulp, Paper & Paperboard"
    XI = "XI - Textiles & Textile Articles"
    XII = "XII - Footwear, Headgear"
    XIII = "XIII - Stone, Cement, Ceramics, Glass"
    XIV = "XIV - Precious Stones, Metals, Jewelry"
    XV = "XV - Base Metals & Articles"
    XVI = "XVI - Machinery & Mechanical Appliances"
    XVII = "XVII - Vehicles & Transport Equipment"
    XVIII = "XVIII - Precision Instruments"
    XIX = "XIX - Arms & Ammunition"
    XX = "XX - Miscellaneous Manufactured Articles"
    XXI = "XXI - Works of Art, Collectors' Pieces"


class HSCodeSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Search query (product description)",
        examples=["wine", "electronic circuits", "clothing", "mining equipment"]
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return"
    )
    category: Optional[str] = Field(
        None,
        description="Filter by category",
        examples=["Food Products & Beverages", "Electrical Machinery & Equipment"]
    )
    chapter: Optional[str] = Field(
        None,
        description="Filter by chapter (2 digits)",
        examples=["22", "85", "87"]
    )


class HSCodeLookupRequest(BaseModel):
    code: str = Field(
        ...,
        min_length=4,
        max_length=10,
        description="HS code to lookup",
        examples=["8542.31", "2204.21", "854231"]
    )


class HSCodeDetails(BaseModel):
    code: str = Field(..., description="HS code", examples=["8542.31"])
    description: str = Field(..., description="Product description")
    category: str = Field(..., description="Product category")
    chapter: str = Field(..., description="HS chapter (2 digits)")
    section: str = Field(..., description="HS section")
    
    duty_rate_general: float = Field(
        ...,
        ge=0,
        le=1,
        description="General duty rate (0.0 - 1.0)"
    )
    vat_applicable: bool = Field(..., description="Whether VAT applies")
    
    special_permits: List[str] = Field(
        default_factory=list,
        description="Required permits and certificates"
    )

    common_destinations: List[str] = Field(
        default_factory=list,
        description="Common export destinations"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes and guidance"
    )
    
    relevance_score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Search relevance score"
    )


class HSCodeSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[HSCodeDetails]
    categories_found: List[str] = Field(
        default_factory=list,
        description="Categories present in results"
    )


class HSCodeLookupResponse(BaseModel):
    found: bool
    code_details: Optional[HSCodeDetails] = None


class HSCodeCategoriesResponse(BaseModel):

    categories: List[str]
    total_count: int


class HSCodeChapterResponse(BaseModel):
    chapter: str
    chapter_description: str
    codes: List[HSCodeDetails]
    total_count: int