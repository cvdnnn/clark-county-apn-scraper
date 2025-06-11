"""CSV handling utilities for reading APNs and writing results."""

import csv
import logging
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd

from ..models.property import Property


class CSVHandler:
    """Handle CSV input/output operations for property scraping."""
    
    def __init__(self):
        """Initialize CSV handler with logging."""
        self.logger = logging.getLogger(__name__)
    
    def read_apns_from_csv(self, file_path: str, apn_column: str = 'APN') -> List[str]:
        """
        Read APNs from CSV file.
        
        Args:
            file_path: Path to input CSV file
            apn_column: Name of column containing APNs
            
        Returns:
            List of APN strings
        """
        apns = []
        
        if not os.path.exists(file_path):
            self.logger.error(f"Input file not found: {file_path}")
            return apns
        
        try:
            df = pd.read_csv(file_path)
            
            if apn_column not in df.columns:
                # Try common variations
                possible_columns = ['apn', 'APN', 'Apn', 'parcel', 'Parcel', 'PARCEL']
                found_column = None
                
                for col in possible_columns:
                    if col in df.columns:
                        found_column = col
                        break
                
                if found_column:
                    apn_column = found_column
                    self.logger.info(f"Using column '{apn_column}' for APNs")
                else:
                    self.logger.error(f"APN column '{apn_column}' not found in CSV. Available columns: {list(df.columns)}")
                    return apns
            
            # Extract APNs and clean them
            for _, row in df.iterrows():
                apn = str(row[apn_column]).strip()
                if apn and apn.lower() not in ['nan', 'none', '']:
                    apns.append(apn)
            
            self.logger.info(f"Read {len(apns)} APNs from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error reading CSV file {file_path}: {e}")
        
        return apns
    
    def write_properties_to_csv(self, properties: List[Property], output_path: str) -> bool:
        """
        Write property data to CSV file.
        
        Args:
            properties: List of Property objects
            output_path: Path for output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        if not properties:
            self.logger.warning("No properties to write")
            return False
        
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Convert properties to dictionaries
            data = [prop.to_dict() for prop in properties]
            
            # Write to CSV using pandas for consistent formatting
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            
            self.logger.info(f"Successfully wrote {len(properties)} properties to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing CSV file {output_path}: {e}")
            return False
    
    def append_property_to_csv(self, property_data: Property, output_path: str) -> bool:
        """
        Append single property to CSV file (for streaming results).
        
        Args:
            property_data: Property object to append
            output_path: Path for output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(output_path)
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Convert property to dictionary
            data = property_data.to_dict()
            
            # Write/append to CSV
            with open(output_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=data.keys())
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error appending to CSV file {output_path}: {e}")
            return False
    
    def validate_apn_format(self, apn: str) -> bool:
        """
        Validate APN format for Clark County.
        
        Args:
            apn: APN string to validate
            
        Returns:
            True if format appears valid, False otherwise
        """
        if not apn:
            return False
        
        # Clean APN for digit-only validation
        digits_only = ''.join(c for c in apn if c.isdigit())
        
        # Clark County APNs are typically 11 digits
        if len(digits_only) == 11:
            return True
        
        # Also accept properly formatted with dashes
        import re
        dash_pattern = r'^\d{3}-\d{2}-\d{3}-\d{3}$'
        if re.match(dash_pattern, apn.strip()):
            return True
        
        return False
    
    def format_apn(self, apn: str) -> str:
        """
        Format APN to standard Clark County format (XXX-XX-XXX-XXX).
        
        Args:
            apn: Raw APN string
            
        Returns:
            Formatted APN string
        """
        # Remove all non-digit characters
        digits_only = ''.join(c for c in apn if c.isdigit())
        
        # Format as XXX-XX-XXX-XXX if we have 11 digits
        if len(digits_only) == 11:
            return f"{digits_only[:3]}-{digits_only[3:5]}-{digits_only[5:8]}-{digits_only[8:11]}"
        
        # Return original if we can't format
        return apn