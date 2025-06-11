"""Data parser for extracting property information from HTML content."""

import logging
import re
from typing import Optional, List
from bs4 import BeautifulSoup
from datetime import datetime

from ..models.property import Property


class PropertyDataParser:
    """Parser for extracting property data from Clark County assessor HTML."""
    
    def __init__(self):
        """Initialize parser with logging."""
        self.logger = logging.getLogger(__name__)
    
    def parse_property_data(self, soup: BeautifulSoup, apn: str) -> Property:
        """
        Parse property data from BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object of property detail page
            apn: APN being processed
            
        Returns:
            Property object with extracted data
        """
        property_data = Property(apn=apn)
        
        try:
            # Extract all data sections using exact element IDs from website
            self._extract_parcel_info(soup, property_data)
            self._extract_owner_info(soup, property_data)
            self._extract_mailing_address(soup, property_data)
            self._extract_location_info(soup, property_data)
            self._extract_assessor_description(soup, property_data)
            self._extract_recording_info(soup, property_data)
            self._extract_vesting_comments(soup, property_data)
            
            # Mark as successful if we got core data
            if any([property_data.owner, property_data.location_address, property_data.assessor_description_line1]):
                property_data.mark_success()
                self.logger.debug(f"Successfully parsed data for APN {apn}")
            else:
                property_data.mark_error("No data found")
                self.logger.warning(f"No data extracted for APN {apn}")
                
        except Exception as e:
            self.logger.error(f"Error parsing property data for APN {apn}: {e}")
            property_data.mark_error(f"Parse error: {str(e)}")
        
        return property_data
    
    def _extract_parcel_info(self, soup: BeautifulSoup, property_data: Property) -> None:
        """Extract parcel number from lblParcel element."""
        parcel_element = soup.find('span', {'id': 'lblParcel'})
        if parcel_element:
            parcel_text = parcel_element.get_text(strip=True)
            if parcel_text:
                property_data.parcel_no = parcel_text
                self.logger.debug(f"Found parcel number: {parcel_text}")
    
    def _extract_owner_info(self, soup: BeautifulSoup, property_data: Property) -> None:
        """Extract owner information from lblOwner1 element with <br> handling."""
        owner_element = soup.find('span', {'id': 'lblOwner1'})
        if owner_element:
            # Get the raw HTML to preserve <br> tags for proper splitting
            owner_html = str(owner_element)
            
            # Split on <br> or <br/> tags to separate multiple owners
            owner_parts = re.split(r'<br\s*/?>', owner_html, flags=re.IGNORECASE)
            
            # Clean up the parts and extract text
            cleaned_owners = []
            for part in owner_parts:
                part_soup = BeautifulSoup(part, 'lxml')
                clean_text = part_soup.get_text(strip=True)
                
                # Skip empty parts and HTML artifacts
                if clean_text and clean_text not in ['span', '']:
                    import html
                    clean_text = html.unescape(clean_text)
                    cleaned_owners.append(clean_text)
            
            # Assign owners
            if len(cleaned_owners) >= 1:
                property_data.owner = cleaned_owners[0]
                self.logger.debug(f"Found owner: {cleaned_owners[0]}")
                
            if len(cleaned_owners) >= 2:
                property_data.owner_2 = cleaned_owners[1]
                self.logger.debug(f"Found owner_2: {cleaned_owners[1]}")
    
    def _extract_mailing_address(self, soup: BeautifulSoup, property_data: Property) -> None:
        """Extract mailing address from lblAddr1 through lblAddr5 elements."""
        address_fields = [
            ('lblAddr1', 'mailing_address_line1'),
            ('lblAddr2', 'mailing_address_line2'),
            ('lblAddr3', 'mailing_address_line3'),
            ('lblAddr4', 'mailing_address_line4'),
            ('lblAddr5', 'mailing_address_line5')
        ]
        
        for label_id, field_name in address_fields:
            addr_element = soup.find('span', {'id': label_id})
            if addr_element:
                addr_text = addr_element.get_text(strip=True)
                if addr_text:
                    setattr(property_data, field_name, addr_text)
                    self.logger.debug(f"Found {field_name}: {addr_text}")
    
    def _extract_location_info(self, soup: BeautifulSoup, property_data: Property) -> None:
        """Extract location address from lblLocation and city from lblTown."""
        # Extract location address
        location_element = soup.find('span', {'id': 'lblLocation'})
        if location_element:
            location_text = location_element.get_text(strip=True)
            if location_text:
                property_data.location_address = location_text
                self.logger.debug(f"Found location address: {location_text}")
        
        # Extract city/unincorporated town
        town_element = soup.find('span', {'id': 'lblTown'})
        if town_element:
            town_text = town_element.get_text(strip=True)
            if town_text:
                property_data.city_unincorporated_town = town_text
                self.logger.debug(f"Found city/town: {town_text}")
    
    def _extract_assessor_description(self, soup: BeautifulSoup, property_data: Property) -> None:
        """Extract assessor description from lblDesc1, lblDesc2, lblDesc3 elements."""
        desc_fields = [
            ('lblDesc1', 'assessor_description_line1'),
            ('lblDesc2', 'assessor_description_line2'),
            ('lblDesc3', 'assessor_description_line3')
        ]
        
        for label_id, field_name in desc_fields:
            desc_element = soup.find('span', {'id': label_id})
            if desc_element:
                desc_text = desc_element.get_text(strip=True)
                if desc_text:
                    setattr(property_data, field_name, desc_text)
                    self.logger.debug(f"Found {field_name}: {desc_text}")
    
    def _extract_recording_info(self, soup: BeautifulSoup, property_data: Property) -> None:
        """Extract recording document number from lblRecDoc and date from lblRecDate."""
        # Extract document number
        doc_element = soup.find('span', {'id': 'lblRecDoc'})
        if doc_element:
            doc_text = doc_element.get_text(strip=True)
            if doc_text:
                property_data.recorded_document_no = doc_text
                self.logger.debug(f"Found document number: {doc_text}")
        
        # Extract recorded date
        date_element = soup.find('span', {'id': 'lblRecDate'})
        if date_element:
            date_text = date_element.get_text(strip=True)
            if date_text:
                property_data.recorded_date = date_text
                self.logger.debug(f"Found recorded date: {date_text}")
    
    def _extract_vesting_comments(self, soup: BeautifulSoup, property_data: Property) -> None:
        """Extract vesting from lblVest and comments from litComments."""
        # Extract vesting
        vesting_element = soup.find('span', {'id': 'lblVest'})
        if vesting_element:
            vesting_text = vesting_element.get_text(strip=True)
            if vesting_text:
                property_data.vesting = vesting_text
                self.logger.debug(f"Found vesting: {vesting_text}")
        
        # Extract comments
        comments_element = soup.find('span', {'id': 'litComments'})
        if comments_element:
            comments_text = comments_element.get_text(strip=True)
            if comments_text:
                property_data.comments = comments_text
                self.logger.debug(f"Found comments: {comments_text}")
    
    def _format_date(self, date_text: str) -> str:
        """Format date text to consistent format."""
        if not date_text:
            return date_text
            
        # Try to parse various date formats and convert to "MMM DD YYYY"
        try:
            # Handle format like "20250226:00938" -> "Feb 26 2025"
            if ':' in date_text and len(date_text.split(':')[0]) == 8:
                date_part = date_text.split(':')[0]
                year = date_part[:4]
                month = date_part[4:6]
                day = date_part[6:8]
                
                from datetime import datetime
                parsed_date = datetime(int(year), int(month), int(day))
                return parsed_date.strftime("%b %-d %Y")
            
            # Handle other common formats
            # Add more date parsing logic as needed based on actual data formats
            
        except Exception as e:
            self.logger.debug(f"Could not parse date format '{date_text}': {e}")
        
        return date_text  # Return original if parsing fails