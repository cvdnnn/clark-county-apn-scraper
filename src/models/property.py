from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Property:
    """Data model for property information extracted from Clark County assessor."""
    
    # Core identifiers
    apn: str
    parcel_no: Optional[str] = None
    
    # Owner information
    owner: Optional[str] = None
    owner_2: Optional[str] = None
    
    # Mailing address (broken into separate lines)
    mailing_address_line1: Optional[str] = None
    mailing_address_line2: Optional[str] = None
    mailing_address_line3: Optional[str] = None
    mailing_address_line4: Optional[str] = None
    mailing_address_line5: Optional[str] = None
    
    # Property location
    location_address: Optional[str] = None
    city_unincorporated_town: Optional[str] = None
    
    # Assessor description
    assessor_description_line1: Optional[str] = None
    assessor_description_line2: Optional[str] = None
    assessor_description_line3: Optional[str] = None
    
    # Recording information
    recorded_document_no: Optional[str] = None
    recorded_date: Optional[str] = None
    vesting: Optional[str] = None
    comments: Optional[str] = None
    
    # Processing metadata
    status: str = "Pending"
    error_message: Optional[str] = None
    scraped_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert property to dictionary for CSV export."""
        return {
            'APN': self.apn,
            'Owner': self.owner,
            'Owner_2': self.owner_2,
            'Mailing_Address_Line1': self.mailing_address_line1,
            'Mailing_Address_Line2': self.mailing_address_line2,
            'Mailing_Address_Line3': self.mailing_address_line3,
            'Mailing_Address_Line4': self.mailing_address_line4,
            'Mailing_Address_Line5': self.mailing_address_line5,
            'Location_Address': self.location_address,
            'City_Unincorporated_Town': self.city_unincorporated_town
        }
    
    def mark_success(self, timestamp: Optional[str] = None) -> None:
        """Mark property as successfully scraped."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        self.status = f"Success - Scraped at {timestamp}"
        self.scraped_at = datetime.now().isoformat()
    
    def mark_error(self, error_msg: str = "Error") -> None:
        """Mark property as failed with error message."""
        self.status = f"Error: {error_msg}"
        self.error_message = error_msg
        self.scraped_at = datetime.now().isoformat()