"""
Analytics Routes - /api/analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from api.models.schemas import (
    DroughtRiskAnalysis,
    TrendAnalysis
)
from api.dependencies import get_es_client
from elasticsearch_client.client import WaterScopeESClient

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get(
    "/drought-risk",
    response_model=List[DroughtRiskAnalysis],
    summary="Analyze drought risk",
    description="Calculate drought risk for all waterbodies based on recent trends"
)
async def analyze_drought_risk(
    threshold_percentage: float = Query(-10.0, description="Percentage decline threshold for risk"),
    es_client: WaterScopeESClient = Depends(get_es_client)
):
    """
    Analyze drought risk for all waterbodies.
    
    Calculates risk based on percentage change from 12-month baseline.
    
    Risk Levels:
    - LOW: < 5% decline
    - MEDIUM: 5-15% decline
    - HIGH: 15-30% decline
    - CRITICAL: > 30% decline
    
    Args:
        threshold_percentage: Percentage decline threshold for risk (default: -10%)
        
    Returns:
        List of drought risk analyses for all waterbodies
    """
    try:
        # Get all waterbody IDs
        agg_query = {
            "size": 0,
            "aggs": {
                "waterbodies": {
                    "terms": {"field": "waterbody_id.keyword", "size": 1000}
                }
            }
        }
        
        response = es_client.es.search(index="waterbody_stats", body=agg_query)
        waterbody_ids = [b['key'] for b in response['aggregations']['waterbodies']['buckets']]
        
        analyses = []
        
        for waterbody_id in waterbody_ids:
            try:
                analysis = await calculate_single_drought_risk(waterbody_id, es_client)
                if analysis:
                    analyses.append(analysis)
            except Exception as e:
                print(f"Error analyzing {waterbody_id}: {e}")
                continue
        
        # Sort by risk level (CRITICAL first)
        risk_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        analyses.sort(key=lambda x: risk_order.get(x.risk_level, 999))
        
        return analyses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing drought risk: {str(e)}")


async def calculate_single_drought_risk(
    waterbody_id: str,
    es_client: WaterScopeESClient
) -> DroughtRiskAnalysis:
    """Calculate drought risk for a single waterbody"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Get all data for last 12 months
    results = es_client.get_waterbody_timeseries(
        waterbody_id=waterbody_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not results or len(results) < 2:
        return None
    
    # Sort by date
    results.sort(key=lambda x: x['timestamp'])
    
    name = results[0].get('name', waterbody_id)
    
    # Current area (most recent)
    current_area = results[-1]['surface_area_hectares']
    last_updated = datetime.fromisoformat(results[-1]['timestamp'].replace('Z', '+00:00'))
    
    # Baseline (average of all measurements)
    baseline_area = sum(r['surface_area_hectares'] for r in results) / len(results)
    
    # Calculate change
    percentage_change = ((current_area - baseline_area) / baseline_area) * 100
    
    # Determine risk level
    if percentage_change >= -5:
        risk_level = "LOW"
    elif percentage_change >= -15:
        risk_level = "MEDIUM"
    elif percentage_change >= -30:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"
    
    # Determine trend (last 3 months vs previous 3 months)
    mid_point = len(results) // 2
    recent_avg = sum(r['surface_area_hectares'] for r in results[mid_point:]) / max(len(results[mid_point:]), 1)
    older_avg = sum(r['surface_area_hectares'] for r in results[:mid_point]) / max(len(results[:mid_point]), 1)
    
    if recent_avg > older_avg * 1.02:
        trend = "INCREASING"
    elif recent_avg < older_avg * 0.98:
        trend = "DECLINING"
    else:
        trend = "STABLE"
    
    return DroughtRiskAnalysis(
        waterbody_id=waterbody_id,
        name=name,
        current_area_hectares=round(current_area, 2),
        baseline_area_hectares=round(baseline_area, 2),
        percentage_change=round(percentage_change, 2),
        risk_level=risk_level,
        trend=trend,
        last_updated=last_updated
    )


@router.get(
    "/drought-risk/{waterbody_id}",
    response_model=DroughtRiskAnalysis,
    summary="Analyze drought risk for specific waterbody",
    description="Calculate drought risk for a single waterbody"
)
async def analyze_drought_risk_single(
    waterbody_id: str,
    es_client: WaterScopeESClient = Depends(get_es_client)
):
    """
    Analyze drought risk for a specific waterbody.
    
    Args:
        waterbody_id: ID of the waterbody
        
    Returns:
        Drought risk analysis
    """
    try:
        analysis = await calculate_single_drought_risk(waterbody_id, es_client)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for waterbody '{waterbody_id}'"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing drought risk: {str(e)}")


@router.get(
    "/trend/{waterbody_id}",
    response_model=TrendAnalysis,
    summary="Analyze trend",
    description="Calculate trend for a waterbody over a specified period"
)
async def analyze_trend(
    waterbody_id: str,
    months: int = Query(12, ge=3, le=60, description="Number of months to analyze"),
    es_client: WaterScopeESClient = Depends(get_es_client)
):
    """
    Analyze trend for a waterbody.
    
    Args:
        waterbody_id: ID of the waterbody
        months: Number of months to analyze (default: 12)
        
    Returns:
        Trend analysis with direction and statistics
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)
        
        # Get data
        results = es_client.get_waterbody_timeseries(
            waterbody_id=waterbody_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not results or len(results) < 2:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for waterbody '{waterbody_id}'"
            )
        
        # Sort by date
        results.sort(key=lambda x: x['timestamp'])
        
        name = results[0].get('name', waterbody_id)
        
        # Start and end areas
        start_area = results[0]['surface_area_hectares']
        end_area = results[-1]['surface_area_hectares']
        
        # Calculate changes
        total_change = end_area - start_area
        percentage_change = (total_change / start_area) * 100
        average_monthly_change = total_change / months
        
        # Determine trend direction
        if percentage_change > 2:
            trend_direction = "UP"
        elif percentage_change < -2:
            trend_direction = "DOWN"
        else:
            trend_direction = "STABLE"
        
        return TrendAnalysis(
            waterbody_id=waterbody_id,
            name=name,
            period_months=months,
            start_area_hectares=round(start_area, 2),
            end_area_hectares=round(end_area, 2),
            total_change_hectares=round(total_change, 2),
            percentage_change=round(percentage_change, 2),
            average_monthly_change=round(average_monthly_change, 2),
            trend_direction=trend_direction
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing trend: {str(e)}")


@router.get(
    "/comparison",
    response_model=dict,
    summary="Compare waterbodies",
    description="Compare current surface areas of all waterbodies"
)
async def compare_waterbodies(
    es_client: WaterScopeESClient = Depends(get_es_client)
):
    """
    Compare current surface areas of all waterbodies.
    
    Returns:
        Comparison data for all waterbodies
    """
    try:
        # Get all waterbody IDs
        agg_query = {
            "size": 0,
            "aggs": {
                "waterbodies": {
                    "terms": {"field": "waterbody_id.keyword", "size": 1000}
                }
            }
        }
        
        response = es_client.es.search(index="waterbody_stats", body=agg_query)
        waterbody_ids = [b['key'] for b in response['aggregations']['waterbodies']['buckets']]
        
        comparisons = []
        
        for waterbody_id in waterbody_ids:
            # Get latest data
            latest_query = {
                "query": {"term": {"waterbody_id.keyword": waterbody_id}},
                "sort": [{"timestamp": "desc"}],
                "size": 1
            }
            
            latest_response = es_client.es.search(index="waterbody_stats", body=latest_query)
            
            if latest_response['hits']['hits']:
                data = latest_response['hits']['hits'][0]['_source']
                comparisons.append({
                    "waterbody_id": waterbody_id,
                    "name": data.get('name', waterbody_id),
                    "surface_area_hectares": data['surface_area_hectares'],
                    "timestamp": data['timestamp']
                })
        
        # Sort by surface area (largest first)
        comparisons.sort(key=lambda x: x['surface_area_hectares'], reverse=True)
        
        return {
            "total_waterbodies": len(comparisons),
            "waterbodies": comparisons,
            "total_surface_area_hectares": sum(w['surface_area_hectares'] for w in comparisons),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing waterbodies: {str(e)}")