"""
Pydantic Schemas for WaterScope API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class WaterbodyConfig(BaseModel):
    """Schema for waterbody configuration"""
    waterbody_id: str = Field(..., description="Unique identifier for the waterbody")
    name: str = Field(..., description="Name of the waterbody")
    region: Optional[str] = Field(None, description="Geographic region")
    country: Optional[str] = Field(None, description="Country")
    description: Optional[str] = Field(None, description="Description of the waterbody")
    
    class Config:
        json_schema_extra = {
            "example": {
                "waterbody_id": "lake_aral_001",
                "name": "Lake Aral",
                "region": "Central Asia",
                "country": "Kazakhstan/Uzbekistan",
                "description": "Large endorheic lake in Central Asia"
            }
        }


class WaterbodyData(BaseModel):
    """Schema for waterbody measurement data"""
    waterbody_id: str
    name: str
    timestamp: datetime
    surface_area_hectares: float = Field(..., description="Surface area in hectares")
    data_source: str = Field(default="Sentinel-2")
    cloud_cover_percentage: Optional[float] = Field(None, ge=0, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "waterbody_id": "lake_aral_001",
                "name": "Lake Aral",
                "timestamp": "2026-01-07T00:00:00Z",
                "surface_area_hectares": 1050.8,
                "data_source": "Sentinel-2",
                "cloud_cover_percentage": 5.2
            }
        }


class TimeseriesPoint(BaseModel):
    """Schema for a single point in time series"""
    timestamp: datetime
    surface_area_hectares: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-07T00:00:00Z",
                "surface_area_hectares": 1050.8
            }
        }


class TimeseriesResponse(BaseModel):
    """Schema for timeseries response"""
    waterbody_id: str
    name: str
    start_date: datetime
    end_date: datetime
    data_points: List[TimeseriesPoint]
    count: int = Field(..., description="Number of data points")
    
    class Config:
        json_schema_extra = {
            "example": {
                "waterbody_id": "lake_aral_001",
                "name": "Lake Aral",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2026-01-07T00:00:00Z",
                "data_points": [
                    {"timestamp": "2024-01-01T00:00:00Z", "surface_area_hectares": 1100.0},
                    {"timestamp": "2024-06-01T00:00:00Z", "surface_area_hectares": 1050.0}
                ],
                "count": 2
            }
        }


class DroughtRiskAnalysis(BaseModel):
    """Schema for drought risk analysis"""
    waterbody_id: str
    name: str
    current_area_hectares: float
    baseline_area_hectares: float = Field(..., description="Average area over last 12 months")
    percentage_change: float = Field(..., description="Percentage change from baseline")
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH, CRITICAL")
    trend: str = Field(..., description="Trend: STABLE, DECLINING, INCREASING")
    last_updated: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "waterbody_id": "lake_aral_001",
                "name": "Lake Aral",
                "current_area_hectares": 950.0,
                "baseline_area_hectares": 1050.0,
                "percentage_change": -9.52,
                "risk_level": "MEDIUM",
                "trend": "DECLINING",
                "last_updated": "2026-01-07T00:00:00Z"
            }
        }


class TrendAnalysis(BaseModel):
    """Schema for trend analysis"""
    waterbody_id: str
    name: str
    period_months: int
    start_area_hectares: float
    end_area_hectares: float
    total_change_hectares: float
    percentage_change: float
    average_monthly_change: float
    trend_direction: str = Field(..., description="UP, DOWN, STABLE")
    
    class Config:
        json_schema_extra = {
            "example": {
                "waterbody_id": "lake_aral_001",
                "name": "Lake Aral",
                "period_months": 12,
                "start_area_hectares": 1100.0,
                "end_area_hectares": 950.0,
                "total_change_hectares": -150.0,
                "percentage_change": -13.64,
                "average_monthly_change": -12.5,
                "trend_direction": "DOWN"
            }
        }


class IngestionRequest(BaseModel):
    """Schema for triggering ingestion"""
    waterbody_ids: Optional[List[str]] = Field(None, description="Specific waterbody IDs to ingest (empty = all)")
    months_back: int = Field(1, ge=1, le=12, description="Number of months of data to retrieve")
    
    class Config:
        json_schema_extra = {
            "example": {
                "waterbody_ids": ["lake_aral_001", "lake_chad_001"],
                "months_back": 1
            }
        }


class IngestionResponse(BaseModel):
    """Schema for ingestion response"""
    status: str
    message: str
    total_waterbodies: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "message": "Ingestion completed successfully",
                "total_waterbodies": 2,
                "successful": 2,
                "failed": 0,
                "results": [
                    {"waterbody_id": "lake_aral_001", "status": "success"},
                    {"waterbody_id": "lake_chad_001", "status": "success"}
                ],
                "timestamp": "2026-01-08T10:30:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    elasticsearch: str
    sentinel_hub: str
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "elasticsearch": "connected",
                "sentinel_hub": "authenticated",
                "timestamp": "2026-01-08T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "WaterbodyNotFound",
                "detail": "Waterbody with ID 'invalid_id' not found",
                "timestamp": "2026-01-08T10:30:00Z"
            }
        }