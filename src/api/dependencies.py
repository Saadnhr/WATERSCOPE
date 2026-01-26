"""
Dependencies for FastAPI application
"""

from functools import lru_cache
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sentinel_hub.auth import SentinelHubAuth
from sentinel_hub.process_api import ProcessAPIClient
from elasticsearch_client.client import WaterScopeESClient


@lru_cache()
def get_elasticsearch_client() -> WaterScopeESClient:
    """
    Get Elasticsearch client (cached)
    
    Returns:
        WaterScopeESClient instance
    """
    return WaterScopeESClient()


@lru_cache()
def get_sentinel_hub_auth() -> SentinelHubAuth:
    """
    Get Sentinel Hub auth manager (cached)
    
    Returns:
        SentinelHubAuth instance
    """
    return SentinelHubAuth()


@lru_cache()
def get_process_api_client() -> ProcessAPIClient:
    """
    Get Process API client (cached)
    
    Returns:
        ProcessAPIClient instance
    """
    auth = get_sentinel_hub_auth()
    return ProcessAPIClient(auth)


def get_es_client():
    """Dependency injection for Elasticsearch client"""
    return get_elasticsearch_client()


def get_sh_auth():
    """Dependency injection for Sentinel Hub auth"""
    return get_sentinel_hub_auth()


def get_process_client():
    """Dependency injection for Process API client"""
    return get_process_api_client()