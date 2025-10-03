import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import json

# Load env.
load_dotenv()

# Access ENV stuff
EARTHDATA_TOKEN = os.getenv('TOKEN')

class TEMPODataFetcher:
    def __init__(self, token):
        # Initialize with Earthdata token
        """
        Args:
            token: Earthdata user token from profile
        """

        self.token = token
        self.cmr_base = "https://cmr.earthdata.nasa.gov/search"
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }

    def search_tempo_data(self, start_date, end_date, product_type="NO2_L3", limit=10):

        # Search for TEMPO data products using CMR API
        """
        Specify some data params.
        Args:
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            product_type: Type of TEMPO product (NO2_L3, HCHO_L3, O3TOT_L3, NO2_L2) 
        """

        # TEMPO product short names with version
        product_mapping = {
            "NO2_L3": "TEMPO_NO2_L3",   # Nitrogen Dioxide 
            "HCHO_L3": "TEMPO_HCHO_L3",  # Formaldehyde 
            "O3TOT_L3": "TEMPO_O3TOT_L3",   # Ozone Total Column
            "NO2_L2": "TEMPO_NO2_L2",   # Nitrogen Dioxide 
            "CLDO4_L3": "TEMPO_CLDO4_L3",   # Cloud data
        }
        
        short_name = product_mapping.get(product_type, "TEMPO_NO2_L3")
        
        # Build CMR query parameters
        params = {
            'short_name': short_name,
            'temporal': f'{start_date}T00:00:00Z,{end_date}T23:59:59Z',
            'page_size': limit,
            'sort_key': '-start_date'
        }
        
        print(f"Searching CMR for {short_name} data from {start_date} to {end_date}...")
        
        try:
            response = requests.get(
                f"{self.cmr_base}/granules.json",
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            granules = data.get('feed', {}).get('entry', [])
            print(f"Found {len(granules)} granules")
            
            return granules
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching CMR: {e}")
            return []
    
    def get_download_urls(self, granules):
        """
        Extract download URLs from granule metadata
        Args:
            granules: List of granule metadata from search_tempo_data()
        """
        urls = []
        
        for granule in granules:
            granule_id = granule.get('title', 'Unknown')
            links = granule.get('links', [])
            
            # Find data download links
            data_links = [
                link['href'] for link in links 
                if link.get('rel') == 'http://esipfed.org/ns/fedsearch/1.1/data#'
            ]
            
            if data_links:
                urls.append({
                    'granule_id': granule_id,
                    'time_start': granule.get('time_start', 'N/A'),
                    'time_end': granule.get('time_end', 'N/A'),
                    'size_mb': granule.get('granule_size', 'N/A'),
                    'urls': data_links
                })
        
        return urls
    
    def download_file(self, url, output_dir="./tempo_data"):
        """
        Download a single TEMPO data file using token authentication
        Args:
            url: Direct download URL
            output_dir: Directory to save the file
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filename = url.split('/')[-1]
        filepath = os.path.join(output_dir, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            print(f"File already exists: {filename}")
            return filepath
        
        print(f"Downloading {filename}...")
        
        try:
            # Create session + authentication
            session = requests.Session()
            session.headers.update(self.headers)
            
            response = session.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Download w progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)             
            
            print(f"\n✓ Downloaded: {filename}")
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error downloading {filename}: {e}")
            return None
    
    def download_multiple(self, file_info_list, output_dir="./tempo_data"):
        """
        Download multiple TEMPO files
        
        Args:
            file_info_list: List from get_download_urls()
            output_dir: Directory to save files
        """
        downloaded_files = []
        
        for info in file_info_list:
            print(f"\n--- Granule: {info['granule_id']} ---")
            print(f"Time: {info['time_start']} to {info['time_end']}")
            
            for url in info['urls']:
                filepath = self.download_file(url, output_dir)
                if filepath:
                    downloaded_files.append(filepath)
        
        return downloaded_files 

def main():
    print("=" * 70)
    print("Air Quality Data Fetcher - TEMPO & AirNow (Token-Based)")
    print("=" * 70)
    
    # Example 1: Fetch TEMPO satellite data
    print("\n--- TEMPO Satellite Data ---")
    if EARTHDATA_TOKEN:
        try:
            tempo = TEMPODataFetcher(EARTHDATA_TOKEN)
            
            # Search for data from last 3 days
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            
            # Search for Nitrogen Dioxide data
            granules = tempo.search_tempo_data(
                start_date=start_date,
                end_date=end_date,
                product_type="NO2_L3",  # Options: NO2_L3, HCHO_L3, O3TOT_L3
                limit=5
            )
            
            if granules:
                # Get download URLs
                file_info = tempo.get_download_urls(granules)
                
                print("\n--- Available Files ---")
                for i, info in enumerate(file_info[:3], 1):  # Show first 3
                    print(f"\n{i}. {info['granule_id']}")
                    print(f"   Time: {info['time_start']}")
                    print(f"   Size: {info['size_mb']} MB")
                    print(f"   URLs: {len(info['urls'])} file(s)")
                
                print("\n--- Downloading Files ---")
                downloaded = tempo.download_multiple(file_info[:2])  # Download first 2
                print(f"\nTotal files downloaded: {len(downloaded)}")
            else:
                print("No granules found for the specified date range")
        
        except Exception as e:
            print(f"Error fetching TEMPO data: {e}")
    else:
        print("EARTHDATA_TOKEN not found in .env file")
if __name__ == "__main__":
    main()



