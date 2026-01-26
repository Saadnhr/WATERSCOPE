"""
Sentinel Hub Process API Client - MODIFIED VERSION
Handles requests to Process API for NDWI calculation
CHANGE: NDWI threshold lowered from 0.2 to 0.0 for better water detection
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .auth import SentinelHubAuth


class ProcessAPIClient:
    """Client for Sentinel Hub Process API"""
    
    PROCESS_API_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
    
    def __init__(self, auth: SentinelHubAuth):
        """
        Initialize Process API client
        
        Args:
            auth: SentinelHubAuth instance for authentication
        """
        self.auth = auth
        print("Process API Client initialized")
    
    def calculate_water_surface(
        self,
        waterbody_id: str,
        geometry: Dict[str, Any],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        months_back: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate water surface area using NDWI
        
        Args:
            waterbody_id: Unique identifier for the water body
            geometry: GeoJSON geometry of the water body
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            months_back: Number of months to look back if dates not provided
            
        Returns:
            Dictionary with calculation results including surface area
        """
        print(f"\nCalculating water surface area for: {waterbody_id}")
        
        # Set date range
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start = datetime.now() - timedelta(days=30 * months_back)
            start_date = start.strftime("%Y-%m-%d")
        
        print(f"Time range: {start_date} to {end_date}")
        
        # Build request
        request_payload = self._build_request_payload(
            geometry=geometry,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get authentication token
        token = self.auth.get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/tar"
        }
        
        # Send request
        print("Sending request to Sentinel Hub...")
        response = requests.post(
            self.PROCESS_API_URL,
            json=request_payload,
            headers=headers,
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            raise Exception(
                f"Process API request failed: {response.status_code} - {response.text}"
            )
        
        # Calculate surface area from response
        result = self._process_response(response.content, geometry)
        
        print("Successfully calculated surface area")
        
        return {
            "waterbody_id": waterbody_id,
            "surface_area_hectares": result["surface_area_hectares"],
            "timestamp": datetime.now().isoformat(),
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }
    
    def _build_request_payload(
        self,
        geometry: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Build Process API request payload
        
        Args:
            geometry: GeoJSON geometry
            start_date: Start date
            end_date: End date
            
        Returns:
            Request payload dictionary
        """
        
        # NDWI calculation script - THRESHOLD LOWERED TO 0.0
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
                    sampleType: "UINT8"
                }
            };
        }
        
        function evaluatePixel(sample) {
            // Scene Classification Layer filtering
            // 3 = cloud shadows, 8 = cloud medium probability, 9 = cloud high probability
            if (sample.SCL === 3 || sample.SCL === 8 || sample.SCL === 9) {
                return [0];  // Return 0 for clouds/shadows
            }
            
            // Calculate NDWI and create binary water mask
            let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
            
            // MODIFIED: Threshold lowered from 0.2 to 0.0
            // This captures turbid water and winter conditions better
            return [ndwi > 0.0 ? 1 : 0];
        }
        """
        
        payload = {
            "input": {
                "bounds": {
                    "geometry": geometry,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{start_date}T00:00:00Z",
                            "to": f"{end_date}T23:59:59Z"
                        },
                        "maxCloudCoverage": 30
                    }
                }]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [{
                    "identifier": "default",
                    "format": {
                        "type": "image/tiff"
                    }
                }]
            },
            "evalscript": evalscript
        }
        
        return payload
    
    def _process_response(
        self,
        response_content: bytes,
        geometry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process the response from Process API
        
        Args:
            response_content: Raw response content (TIFF image)
            geometry: Original geometry for reference
            
        Returns:
            Dictionary with surface area calculation
        """
        try:
            # Import libraries for image processing
            from io import BytesIO
            import tarfile
            import numpy as np
            from PIL import Image
            
            # Extract TIFF from tar archive
            tar_buffer = BytesIO(response_content)
            with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
                # Find the TIFF file
                tiff_member = None
                for member in tar.getmembers():
                    if member.name.endswith('.tif') or member.name.endswith('.tiff'):
                        tiff_member = member
                        break
                
                if not tiff_member:
                    raise Exception("No TIFF file found in response")
                
                # Extract and read the TIFF
                tiff_file = tar.extractfile(tiff_member)
                img = Image.open(tiff_file)
                
                # Convert to numpy array
                img_array = np.array(img)
                
                # Count water pixels (value = 1)
                water_pixels = np.sum(img_array == 1)
                total_pixels = img_array.size
                
                # DEBUG: See what Sentinel Hub actually returns
                print(f"\n🔍 DEBUG IMAGE ANALYSIS:")
                print(f"   Image shape: {img_array.shape}")
                print(f"   Unique pixel values: {np.unique(img_array)}")
                print(f"   Water pixels (value=1): {water_pixels}")
                print(f"   Total pixels: {total_pixels}")
                if img_array.size > 0:
                    value_counts = np.bincount(img_array.flatten())
                    for val, count in enumerate(value_counts):
                        if count > 0:
                            print(f"   Value {val}: {count} pixels ({100*count/total_pixels:.2f}%)")
                
                # Calculate area
                # Get bounding box dimensions from geometry
                coords = geometry['coordinates'][0]
                
                # Calculate approximate area of bounding box
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                
                lon_range = max(lons) - min(lons)
                lat_range = max(lats) - min(lats)
                
                # Approximate conversion (degrees to km at mid-latitude)
                avg_lat = sum(lats) / len(lats)
                km_per_deg_lon = 111.32 * np.cos(np.radians(avg_lat))
                km_per_deg_lat = 111.32
                
                area_km2 = (lon_range * km_per_deg_lon) * (lat_range * km_per_deg_lat)
                
                # Calculate water surface area
                water_fraction = water_pixels / total_pixels if total_pixels > 0 else 0
                water_area_km2 = area_km2 * water_fraction
                water_area_hectares = water_area_km2 * 100  # Convert km² to hectares
                
                return {
                    "surface_area_hectares": round(water_area_hectares, 2),
                    "water_pixels": int(water_pixels),
                    "total_pixels": int(total_pixels),
                    "water_fraction": round(water_fraction, 4)
                }
                
        except Exception as e:
            print(f"Error processing response: {e}")
            # Return 0 if processing fails
            return {
                "surface_area_hectares": 0.0,
                "water_pixels": 0,
                "total_pixels": 0,
                "water_fraction": 0.0,
                "error": str(e)
            }