"""
Waterbodies Routes - /api/waterbodies
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from api.models.schemas import (
    WaterbodyConfig,
    WaterbodyData,
    TimeseriesResponse,
    TimeseriesPoint,
    ErrorResponse
)
from api.dependencies import get_es_client
from elasticsearch_client.client import WaterScopeESClient

router = APIRouter(prefix="/api/waterbodies", tags=["Waterbodies"])


@router.get(
    "/",
    response_model=List[str],
    summary="List all waterbody IDs",
    description="Get a list of all available waterbody IDs in the system"
)
async def list_waterbodies(
    es_client: WaterScopeESClient = Depends(get_es_client)
):
    """
    List all unique waterbody IDs that have data in the system.
    
    Returns:
        List of waterbody IDs
    """
    try:
        # Aggregation pour obtenir tous les waterbody_id uniques
        query = {
            "size": 0,
            "aggs": {
                "waterbodies": {
                    "terms": {
                        "field": "waterbody_id.keyword",
                        "size": 1000
                    }
                }
            }
        }
        
        response = es_client.es.search(index="waterbody_stats", body=query)
        
        waterbody_ids = [
            bucket['key'] 
            for bucket in response['aggregations']['waterbodies']['buckets']
        ]
        
        return waterbody_ids
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching waterbodies: {str(e)}")


@router.get(
    "/{waterbody_id}/latest",
    response_model=WaterbodyData,
    summary="Get latest data for a waterbody",
    description="Retrieve the most recent measurement for a specific waterbody"
)
async def get_latest_data(
    waterbody_id: str,
    es_client: WaterScopeESClient = Depends(get_es_client)
):
    """
    Get the latest measurement for a specific waterbody.
    
    Args:
        waterbody_id: ID of the waterbody
        
    Returns:
        Latest waterbody data
    """
    try:
        query = {
            "query": {
                "term": {"waterbody_id.keyword": waterbody_id}
            },
            "sort": [{"timestamp": "desc"}],
            "size": 1
        }
        
        response = es_client.es.search(index="waterbody_stats", body=query)
        
        if not response['hits']['hits']:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for waterbody '{waterbody_id}'"
            )
        
        data = response['hits']['hits'][0]['_source']
        return WaterbodyData(**data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@router.get(
    "/{waterbody_id}/timeseries",
    response_model=TimeseriesResponse,
    summary="Get time series data",
    description="Retrieve historical time series data for a waterbody"
)
async def get_timeseries(
    waterbody_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    months_back: Optional[int] = Query(12, ge=1, le=60, description="Months of history if dates not provided"),
    es_client: WaterScopeESClient = Depends(get_es_client)
):
    """
    Get time series data for a waterbody.
    
    Args:
        waterbody_id: ID of the waterbody
        start_date: Start date (optional, defaults to months_back)
        end_date: End date (optional, defaults to now)
        months_back: Number of months to retrieve if dates not specified
        
    Returns:
        Time series data with all measurements
    """
    try:
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30 * months_back)
        
        # Fetch data
        results = es_client.get_waterbody_timeseries(
            waterbody_id=waterbody_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for waterbody '{waterbody_id}' in the specified period"
            )
        
        # Extract name
        name = results[0].get('name', waterbody_id)
        
        # Build response
        data_points = [
            TimeseriesPoint(
                timestamp=datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')),
                surface_area_hectares=r['surface_area_hectares']
            )
            for r in results
        ]
        
        return TimeseriesResponse(
            waterbody_id=waterbody_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            data_points=data_points,
            count=len(data_points)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timeseries: {str(e)}")


@router.get(
    "/{waterbody_id}/surface-area",
    response_model=dict,
    summary="Get current surface area",
    description="Get the current surface area with statistics"
)
async def get_surface_area(
    waterbody_id: str,
    es_client: WaterScopeESClient = Depends(get_es_client)
):
    """
    Get current surface area and statistics for a waterbody.
    
    Args:
        waterbody_id: ID of the waterbody
        
    Returns:
        Surface area statistics
    """
    try:
        # Get latest
        latest_query = {
            "query": {"term": {"waterbody_id.keyword": waterbody_id}},
            "sort": [{"timestamp": "desc"}],
            "size": 1
        }
        
        latest_response = es_client.es.search(index="waterbody_stats", body=latest_query)
        
        if not latest_response['hits']['hits']:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for waterbody '{waterbody_id}'"
            )
        
        latest_data = latest_response['hits']['hits'][0]['_source']
        
        # Get statistics (last 12 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        stats_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"waterbody_id.keyword": waterbody_id}},
                        {"range": {"timestamp": {"gte": start_date.isoformat(), "lte": end_date.isoformat()}}}
                    ]
                }
            },
            "aggs": {
                "stats": {
                    "stats": {"field": "surface_area_hectares"}
                }
            }
        }
        
        stats_response = es_client.es.search(index="waterbody_stats", body=stats_query)
        stats = stats_response['aggregations']['stats']
        
        return {
            "waterbody_id": waterbody_id,
            "name": latest_data.get('name', waterbody_id),
            "current_area_hectares": latest_data['surface_area_hectares'],
            "last_updated": latest_data['timestamp'],
            "statistics_12months": {
                "min": stats['min'],
                "max": stats['max'],
                "avg": stats['avg'],
                "count": stats['count']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching surface area: {str(e)}")