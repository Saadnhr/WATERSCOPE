"""
Sentinel Hub Process API Client
Handles requests to the Statistical API for water surface area calculation
"""

import requests
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import json


class ProcessAPIClient:
    """Client for Sentinel Hub Process API"""
    
    PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
    
    def __init__(self, auth_manager):
        """
        Initialize Process API client
        
        Args:
            auth_manager: SentinelHubAuth instance for token management
        """
        self.auth = auth_manager
        print("Process API Client initialized")
    
    def calculate_water_surface_area(
        self,
        geometry: Dict[str, Any],
        time_range: Tuple[datetime, datetime],
        waterbody_id: str,
        waterbody_name: str = None
    ) -> Dict[str, Any]:
        """
        Calculate water surface area for a water body using NDWI
        
        Args:
            geometry: GeoJSON geometry (Polygon)
            time_range: Tuple of (start_date, end_date) as datetime objects
            waterbody_id: Unique identifier for the water body
            waterbody_name: Optional name of the water body
            
        Returns:
            Dict containing surface area statistics
        """
        print(f"\nCalculating water surface area for: {waterbody_id}")
        print(f"Time range: {time_range[0].date()} to {time_range[1].date()}")
        
        # Build request payload
        payload = self._build_payload(geometry, time_range)
        
        # Make request
        headers = {
            'Authorization': f'Bearer {self.auth.get_token()}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            print(f"Sending request to Sentinel Hub...")
            response = requests.post(
                self.PROCESS_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            print(f"Response status: {response.status_code}")
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            result = self._parse_response(data, waterbody_id, waterbody_name, time_range)
            
            print(f"Successfully calculated surface area")
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise Exception(f"Process API request failed: {e}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Process API request failed: {e}")
    
    def _build_payload(
        self,
        geometry: Dict[str, Any],
        time_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Build the JSON payload for Process API request"""
        
        start_date, end_date = time_range
        
        # Format dates as ISO strings
        time_from = start_date.strftime("%Y-%m-%dT00:00:00Z")
        time_to = end_date.strftime("%Y-%m-%dT23:59:59Z")
        
        payload = {
            "input": {
                "bounds": {
                    "geometry": geometry,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": time_from,
                                "to": time_to
                            },
                            "maxCloudCoverage": 20
                        }
                    }
                ]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/tiff"
                        }
                    }
                ]
            },
            "evalscript": self._get_ndwi_evalscript()
        }
        
        return payload
    
    def _get_ndwi_evalscript(self) -> str:
        """
        Get the evalscript for NDWI calculation
        
        NDWI = (GREEN - NIR) / (GREEN + NIR)
        NDWI = (B03 - B08) / (B03 + B08)
        
        Returns 1 for water pixels (NDWI > 0.2), 0 for non-water
        """
        evalscript = """
//VERSION=3

function setup() {
    return {
        input: [{
            bands: ["B03", "B08", "SCL"],
            units: "DN"
        }],
        output: {
            bands: 1,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(sample) {
    // Calculate NDWI
    let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08 + 0.0001);
    
    // Use SCL (Scene Classification Layer) to filter clouds
    // SCL values: 8=Cloud medium probability, 9=Cloud high probability, 3=Cloud shadows
    let isCloud = (sample.SCL == 8 || sample.SCL == 9 || sample.SCL == 3);
    
    if (isCloud) {
        return [0]; // Ignore cloudy pixels
    }
    
    // Return 1 for water (NDWI > 0.2), 0 for non-water
    return [ndwi > 0.2 ? 1 : 0];
}
"""
        return evalscript
    
    def _parse_response(
        self,
        data: Dict[str, Any],
        waterbody_id: str,
        waterbody_name: str,
        time_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Parse the API response and calculate surface area"""
        
        # Note: The actual response structure depends on whether we use
        # Statistical API or Process API. This is a simplified version.
        # In production, we'll need to adjust based on actual response format
        
        try:
            # For now, return a structure that matches our needs
            # We'll refine this once we test with real API responses
            
            result = {
                'waterbody_id': waterbody_id,
                'name': waterbody_name or waterbody_id,
                'time_range': {
                    'start': time_range[0].isoformat(),
                    'end': time_range[1].isoformat()
                },
                'data_source': 'Sentinel-2',
                'timestamp': datetime.now().isoformat(),
                'raw_response': data
            }
            
            return result
            
        except (KeyError, TypeError) as e:
            raise Exception(f"Failed to parse Process API response: {e}")


if __name__ == "__main__":
    from auth import SentinelHubAuth
    
    print("=" * 60)
    print("Test Process API Client")
    print("=" * 60)
    
    # Initialize
    auth = SentinelHubAuth()
    client = ProcessAPIClient(auth)
    
    # Example geometry (Lake Aral simplified)
    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [58.5, 45.0],
            [59.5, 45.0],
            [59.5, 46.0],
            [58.5, 46.0],
            [58.5, 45.0]
        ]]
    }
    
    # Time range: Last month
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        # Calculate surface area
        result = client.calculate_water_surface_area(
            geometry=geometry,
            time_range=(start_date, end_date),
            waterbody_id="lake_aral_test",
            waterbody_name="Lake Aral (Test)"
        )
        
        print("\nResult:")
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"\nError: {e}")