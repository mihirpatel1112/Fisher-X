# THIS WILL DOWNLOAD AN HOURLY OR SO SNAPSHOT DEPENDING ON THE DATE SET AS
# Contains: Temperature, humidity, wind, pressure, radiation for xx HOURS
import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
EARTHDATA_USERNAME = os.getenv('EARTHDATA_USERNAME')
EARTHDATA_PASSWORD = os.getenv('EARTHDATA_PASSWORD')

class SessionWithHeaderRedirection(requests.Session):
    """Handle NASA Earthdata redirects properly"""
    AUTH_HOST = 'urs.earthdata.nasa.gov'
    
    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)
    
    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url
        
        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)
            
            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != self.AUTH_HOST and \
                    original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']

def download_nldas_data(date, hour):
    """
    Download NLDAS weather data
    
    Args:
        date: Date string YYYYMMDD (e.g., "20250930")
        hour: Hour string 0000-2300 (e.g., "1200")
    """
    dt = datetime.strptime(date, "%Y%m%d")
    year = dt.year
    doy = dt.strftime("%j")
    
    base_url = "https://data.gesdisc.earthdata.nasa.gov/data/NLDAS"
    filename = f"NLDAS_FORA0125_H.A{date}.{hour}.020.nc"
    url = f"{base_url}/NLDAS_FORA0125_H.2.0/{year}/{doy}/{filename}"
    
    # Create authenticated session
    session = SessionWithHeaderRedirection(EARTHDATA_USERNAME, EARTHDATA_PASSWORD)
    
    print(f"Downloading {filename}...")
    
    try:
        response = session.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"Downloaded: {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Example
download_nldas_data("20250930", "1200")
