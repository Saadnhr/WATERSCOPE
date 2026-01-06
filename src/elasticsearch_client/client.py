"""
Elasticsearch Client for WaterScope
"""

from elasticsearch import Elasticsearch
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class WaterScopeESClient:
    """Elasticsearch client for waterbody statistics"""
    
    INDEX_NAME = "waterbody_stats"
    
    def __init__(self, host: Optional[str] = None):
        self.host = host or os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
        self.es = Elasticsearch([self.host])
        
        # Check connection
        if not self.es.ping():
            raise Exception(f"Cannot connect to Elasticsearch at {self.host}")
        
        print(f"✅ Connected to Elasticsearch at {self.host}")
        
        # Create index if it doesn't exist
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Create the waterbody_stats index if it doesn't exist"""
        if not self.es.indices.exists(index=self.INDEX_NAME):
            mapping = {
                "mappings": {
                    "properties": {
                        "waterbody_id": {"type": "keyword"},
                        "name": {"type": "text"},
                        "timestamp": {"type": "date"},
                        "surface_area_hectares": {"type": "float"},
                        "data_source": {"type": "keyword"},
                        "cloud_cover_percentage": {"type": "float"},
                        "geo_shape": {"type": "geo_shape"}
                    }
                }
            }
            
            self.es.indices.create(index=self.INDEX_NAME, body=mapping)
            print(f"✅ Created index: {self.INDEX_NAME}")
        else:
            print(f"✅ Index {self.INDEX_NAME} already exists")
    
    def index_waterbody_stat(self, document: Dict[str, Any]) -> str:
        """Index a single waterbody statistic document"""
        response = self.es.index(
            index=self.INDEX_NAME,
            document=document
        )
        return response['_id']
    
    def get_waterbody_timeseries(
        self,
        waterbody_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get time-series data for a specific waterbody"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"waterbody_id": waterbody_id}},
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_date.isoformat(),
                                    "lte": end_date.isoformat()
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [{"timestamp": "asc"}],
            "size": 1000
        }
        
        response = self.es.search(index=self.INDEX_NAME, body=query)
        
        return [hit['_source'] for hit in response['hits']['hits']]
    
    def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch cluster health"""
        health = self.es.cluster.health()
        
        return {
            "status": health['status'],
            "number_of_nodes": health['number_of_nodes'],
            "active_shards": health['active_shards'],
            "index_exists": self.es.indices.exists(index=self.INDEX_NAME)
        }


if __name__ == "__main__":
    # Test the client
    client = WaterScopeESClient()
    
    # Check health
    health = client.health_check()
    print(f"Elasticsearch Health: {health}")
    
    # Index a test document
    doc = {
        "waterbody_id": "lake_test_001",
        "name": "Test Lake",
        "timestamp": "2024-01-01T00:00:00Z",
        "surface_area_hectares": 1050.8,
        "data_source": "Sentinel-2",
        "cloud_cover_percentage": 10.2
    }
    
    doc_id = client.index_waterbody_stat(doc)
    print(f"✅ Indexed test document with ID: {doc_id}")