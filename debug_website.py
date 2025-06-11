"""Debug script to analyze Clark County website structure."""

import requests
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def analyze_website():
    """Analyze the Clark County assessor website structure."""
    
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    url = "https://maps.clarkcountynv.gov/assessor/AssessorParcelDetail/pcl.aspx"
    
    try:
        print(f"Fetching: {url}")
        response = session.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find forms
        forms = soup.find_all('form')
        print(f"\nFound {len(forms)} forms:")
        
        for i, form in enumerate(forms):
            print(f"\nForm {i+1}:")
            print(f"  Action: {form.get('action', 'No action')}")
            print(f"  Method: {form.get('method', 'GET')}")
            print(f"  ID: {form.get('id', 'No ID')}")
            
            # Find input fields
            inputs = form.find_all('input')
            print(f"  Inputs ({len(inputs)}):")
            for inp in inputs[:10]:  # Show first 10 inputs
                print(f"    - {inp.get('name', 'No name')}: {inp.get('type', 'text')} = '{inp.get('value', '')[:50]}'")
            
            if len(inputs) > 10:
                print(f"    ... and {len(inputs) - 10} more inputs")
        
        # Look for specific elements
        parcel_input = soup.find('input', {'name': lambda x: x and 'parcel' in x.lower()})
        if parcel_input:
            print(f"\nFound parcel input: {parcel_input}")
        
        # Look for submit buttons
        submit_buttons = soup.find_all(['input', 'button'], {'type': 'submit'})
        print(f"\nSubmit buttons ({len(submit_buttons)}):")
        for btn in submit_buttons:
            print(f"  - {btn.get('name', 'No name')}: '{btn.get('value', btn.get_text())}'")
        
        print(f"\nPage title: {soup.title.get_text() if soup.title else 'No title'}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_website()