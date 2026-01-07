"""
WaterScope Data Ingestion Service
Orchestrates the collection of water body surface area data
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


class IngestionService:
    """Main service for ingesting water body data"""
    
    def __init__(self, auth_manager, process_client, es_client):
        """
        Initialize ingestion service
        
        Args:
            auth_manager: SentinelHubAuth instance
            process_client: ProcessAPIClient instance
            es_client: WaterScopeESClient instance
        """
        self.auth = auth_manager
        self.process_client = process_client
        self.es = es_client
        
        print("Ingestion Service initialized")
    
    def load_waterbody_configs(self, config_path: str) -> List[Dict[str, Any]]:
        """
        Load water body configurations from JSON file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            List of water body configurations
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            configs = json.load(f)
        
        print(f"Loaded {len(configs)} water body configurations")
        return configs
    
    def ingest_waterbody(
        self,
        waterbody_config: Dict[str, Any],
        months_back: int = 1
    ) -> Dict[str, Any]:
        """
        Ingest data for a single water body
        
        Args:
            waterbody_config: Configuration dict with waterbody_id, name, geometry
            months_back: Number of months of historical data to fetch
            
        Returns:
            Summary of ingestion results
        """
        waterbody_id = waterbody_config['waterbody_id']
        waterbody_name = waterbody_config['name']
        geometry = waterbody_config['geometry']
        
        print(f"\n{'='*60}")
        print(f"Processing: {waterbody_name} ({waterbody_id})")
        print(f"{'='*60}")
        
        # Calculate time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        try:
            # Fetch data from Sentinel Hub
            result = self.process_client.calculate_water_surface_area(
                geometry=geometry,
                time_range=(start_date, end_date),
                waterbody_id=waterbody_id,
                waterbody_name=waterbody_name
            )
            
            # Store in Elasticsearch
            doc = {
                "waterbody_id": waterbody_id,
                "name": waterbody_name,
                "timestamp": datetime.now().isoformat(),
                "surface_area_hectares": 0.0,  # Will be calculated from response
                "data_source": "Sentinel-2",
                "geo_shape": geometry,
                "ingestion_date": datetime.now().isoformat()
            }
            
            doc_id = self.es.index_waterbody_stat(doc)
            
            print(f"Stored in Elasticsearch with ID: {doc_id}")
            
            return {
                "waterbody_id": waterbody_id,
                "status": "success",
                "document_id": doc_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error processing {waterbody_id}: {e}")
            return {
                "waterbody_id": waterbody_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def ingest_all(self, config_path: str, months_back: int = 1) -> Dict[str, Any]:
        """
        Ingest data for all water bodies in configuration
        
        Args:
            config_path: Path to configuration file
            months_back: Number of months of historical data to fetch
            
        Returns:
            Summary of all ingestion results
        """
        print("\n" + "="*60)
        print("WATERSCOPE DATA INGESTION")
        print("="*60)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load configurations
        waterbodies = self.load_waterbody_configs(config_path)
        
        # Process each water body
        results = []
        for config in waterbodies:
            result = self.ingest_waterbody(config, months_back)
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = len(results) - successful
        
        summary = {
            "total_waterbodies": len(results),
            "successful": successful,
            "failed": failed,
            "start_time": datetime.now().isoformat(),
            "results": results
        }
        
        print("\n" + "="*60)
        print("INGESTION SUMMARY")
        print("="*60)
        print(f"Total water bodies: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return summary


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    
    from sentinel_hub.auth import SentinelHubAuth
    from sentinel_hub.process_api import ProcessAPIClient
    from elasticsearch_client.client import WaterScopeESClient
    
    print("="*60)
    print("WaterScope Ingestion Service - Test Run")
    print("="*60)
    
    # Initialize components
    auth = SentinelHubAuth()
    process_client = ProcessAPIClient(auth)
    es_client = WaterScopeESClient()
    
    # Initialize service
    service = IngestionService(auth, process_client, es_client)
    
    # Test with a sample configuration
    print("\nTest mode: Processing sample water body...")
    
    test_config = {
        "waterbody_id": "lake_test_001",
        "name": "Test Lake",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [58.5, 45.0],
                [59.5, 45.0],
                [59.5, 46.0],
                [58.5, 46.0],
                [58.5, 45.0]
            ]]
        }
    }
    
    result = service.ingest_waterbody(test_config, months_back=1)
    
    print("\nTest Result:")
    print(json.dumps(result, indent=2))