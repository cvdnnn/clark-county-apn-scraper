"""High-performance web scraper for Clark County assessor data."""

import logging
import time
from typing import Optional, Tuple
from urllib.parse import urljoin, parse_qs, urlparse
import ssl

import requests
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ClarkCountyScraper:
    """High-performance scraper for Clark County property data."""
    
    BASE_URL = "https://maps.clarkcountynv.gov/assessor/AssessorParcelDetail/"
    SEARCH_URL = urljoin(BASE_URL, "pcl.aspx")
    
    def __init__(self, timeout: int = 10, max_retries: int = 3, verify_ssl: bool = False):
        """Initialize scraper with session and configuration."""
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        
        # Configure session for performance
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Configure SSL verification
        self.session.verify = verify_ssl
        
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=requests.adapters.Retry(
                total=max_retries,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.logger = logging.getLogger(__name__)
    
    def get_property_detail_url(self, apn: str) -> Optional[str]:
        """Submit APN search and get property detail URL."""
        try:
            # First, get the search page to extract form data
            search_response = self.session.get(self.SEARCH_URL, timeout=self.timeout)
            search_response.raise_for_status()
            
            soup = BeautifulSoup(search_response.content, 'lxml')
            
            # Extract form data
            form_data = {}
            
            # Get viewstate and other ASP.NET form fields
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            if viewstate:
                form_data['__VIEWSTATE'] = viewstate.get('value', '')
            
            viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            if viewstate_generator:
                form_data['__VIEWSTATEGENERATOR'] = viewstate_generator.get('value', '')
            
            event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
            if event_validation:
                form_data['__EVENTVALIDATION'] = event_validation.get('value', '')
            
            # Add APN and search parameters (using correct field names from debug)
            form_data.update({
                'tbParcel': apn,  # Changed from 'txtParcel' to 'tbParcel'
                'btnSubmit': 'Submit',
                'r1': 'pcl7'  # Radio button selection for instance
            })
            
            self.logger.debug(f"Submitting form data for APN {apn}: {form_data}")
            
            # Submit the form
            detail_response = self.session.post(
                self.SEARCH_URL,
                data=form_data,
                timeout=self.timeout,
                allow_redirects=True
            )
            detail_response.raise_for_status()
            
            self.logger.debug(f"Form submission response URL: {detail_response.url}")
            
            # Check if we got redirected to detail page
            if 'ParcelDetail.aspx' in detail_response.url:
                return detail_response.url
            
            # If not redirected, look for redirect URL in response
            detail_soup = BeautifulSoup(detail_response.content, 'lxml')
            
            # Look for JavaScript redirect or meta refresh
            script_tags = detail_soup.find_all('script')
            for script in script_tags:
                if script.string and 'location.href' in script.string:
                    # Extract URL from JavaScript redirect
                    import re
                    url_match = re.search(r'location\.href\s*=\s*["\']([^"\']+)["\']', script.string)
                    if url_match:
                        redirect_url = url_match.group(1)
                        if redirect_url.startswith('/'):
                            redirect_url = urljoin(self.BASE_URL, redirect_url)
                        self.logger.debug(f"Found JavaScript redirect: {redirect_url}")
                        return redirect_url
            
            # Look for form with auto-submit
            auto_form = detail_soup.find('form', {'id': 'aspnetForm'})
            if auto_form:
                action = auto_form.get('action', '')
                if action and 'ParcelDetail.aspx' in action:
                    if action.startswith('/'):
                        full_url = urljoin(self.BASE_URL, action)
                        self.logger.debug(f"Found form action redirect: {full_url}")
                        return full_url
                    return action
            
            # Check if there's an error message or no results found
            error_elements = detail_soup.find_all(text=lambda text: text and 
                any(phrase in text.lower() for phrase in ['not found', 'no results', 'invalid', 'error']))
            if error_elements:
                self.logger.warning(f"Search returned error for APN {apn}: {error_elements[0].strip()}")
            else:
                self.logger.warning(f"No detail page found for APN {apn} - may be invalid APN")
            
            return None
            
        except requests.RequestException as e:
            self.logger.error(f"Network error getting detail URL for APN {apn}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting detail URL for APN {apn}: {e}")
            return None
    
    def get_property_page_content(self, detail_url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse property detail page."""
        try:
            response = self.session.get(detail_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            return soup
            
        except requests.RequestException as e:
            self.logger.error(f"Network error fetching property page {detail_url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching property page {detail_url}: {e}")
            return None
    
    def scrape_property(self, apn: str) -> Tuple[Optional[BeautifulSoup], Optional[str]]:
        """
        Scrape property data for given APN.
        
        Returns:
            Tuple of (BeautifulSoup object, detail_url) or (None, None) on failure
        """
        start_time = time.time()
        
        try:
            # Get property detail URL
            detail_url = self.get_property_detail_url(apn)
            if not detail_url:
                return None, None
            
            # Get property page content
            soup = self.get_property_page_content(detail_url)
            if not soup:
                return None, None
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Scraped APN {apn} in {elapsed_time:.2f} seconds")
            
            return soup, detail_url
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Failed to scrape APN {apn} after {elapsed_time:.2f} seconds: {e}")
            return None, None
    
    def close(self):
        """Close the session."""
        self.session.close()