"""
WaterScope API - Version Minimale Sans Dépendances
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from datetime import datetime
from elasticsearch import Elasticsearch

app = FastAPI(
    title="WaterScope API - Minimal",
    description="API Minimale pour Dashboard",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Elasticsearch client simple
es = Elasticsearch(
    "http://localhost:9200",
    verify_certs=False,
    ssl_show_warn=False
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/api/health")
async def health():
    """Health check simple"""
    try:
        es_ping = es.ping()
        return {
            "status": "healthy" if es_ping else "degraded",
            "elasticsearch": "connected" if es_ping else "disconnected",
            "sentinel_hub": "not_checked",
            "timestamp": datetime.now().isoformat()
        }
    except:
        return {
            "status": "degraded",
            "elasticsearch": "error",
            "sentinel_hub": "not_checked",
            "timestamp": datetime.now().isoformat()
        }


@app.get("/api/waterbodies/")
async def list_waterbodies():
    """Liste des lacs"""
    try:
        query = {
            "size": 0,
            "aggs": {
                "waterbodies": {
                    "terms": {"field": "waterbody_id.keyword", "size": 100}
                }
            }
        }
        response = es.search(index="waterbody_stats", body=query)
        return [b['key'] for b in response['aggregations']['waterbodies']['buckets']]
    except Exception as e:
        return []


@app.get("/api/waterbodies/{waterbody_id}/latest")
async def get_latest(waterbody_id: str):
    """Dernières données"""
    try:
        query = {
            "query": {"term": {"waterbody_id.keyword": waterbody_id}},
            "sort": [{"timestamp": "desc"}],
            "size": 1
        }
        response = es.search(index="waterbody_stats", body=query)
        if response['hits']['hits']:
            return response['hits']['hits'][0]['_source']
        return {"error": "not found"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/waterbodies/{waterbody_id}/timeseries")
async def get_timeseries(waterbody_id: str, months_back: int = 12):
    """Série temporelle"""
    try:
        query = {
            "query": {"term": {"waterbody_id.keyword": waterbody_id}},
            "sort": [{"timestamp": "asc"}],
            "size": 100
        }
        response = es.search(index="waterbody_stats", body=query)
        
        hits = response['hits']['hits']
        if not hits:
            return {
                "waterbody_id": waterbody_id,
                "name": waterbody_id,
                "data_points": [],
                "count": 0
            }
        
        name = hits[0]['_source'].get('name', waterbody_id)
        data_points = [
            {
                "timestamp": h['_source']['timestamp'],
                "surface_area_hectares": h['_source']['surface_area_hectares']
            }
            for h in hits
        ]
        
        return {
            "waterbody_id": waterbody_id,
            "name": name,
            "start_date": data_points[0]['timestamp'] if data_points else None,
            "end_date": data_points[-1]['timestamp'] if data_points else None,
            "data_points": data_points,
            "count": len(data_points)
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/analytics/comparison")
async def comparison():
    """Comparaison des lacs"""
    try:
        waterbodies_query = {
            "size": 0,
            "aggs": {
                "waterbodies": {
                    "terms": {"field": "waterbody_id.keyword", "size": 100}
                }
            }
        }
        wb_response = es.search(index="waterbody_stats", body=waterbodies_query)
        waterbody_ids = [b['key'] for b in wb_response['aggregations']['waterbodies']['buckets']]
        
        waterbodies = []
        for wid in waterbody_ids:
            latest_query = {
                "query": {"term": {"waterbody_id.keyword": wid}},
                "sort": [{"timestamp": "desc"}],
                "size": 1
            }
            latest_response = es.search(index="waterbody_stats", body=latest_query)
            if latest_response['hits']['hits']:
                data = latest_response['hits']['hits'][0]['_source']
                waterbodies.append({
                    "waterbody_id": wid,
                    "name": data.get('name', wid),
                    "surface_area_hectares": data['surface_area_hectares'],
                    "timestamp": data['timestamp']
                })
        
        return {
            "total_waterbodies": len(waterbodies),
            "waterbodies": sorted(waterbodies, key=lambda x: x['surface_area_hectares'], reverse=True),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "waterbodies": []}


@app.get("/api/analytics/drought-risk")
async def drought_risk():
    """Analyse risque sécheresse"""
    try:
        waterbodies_query = {
            "size": 0,
            "aggs": {
                "waterbodies": {
                    "terms": {"field": "waterbody_id.keyword", "size": 100}
                }
            }
        }
        wb_response = es.search(index="waterbody_stats", body=waterbodies_query)
        waterbody_ids = [b['key'] for b in wb_response['aggregations']['waterbodies']['buckets']]
        
        analyses = []
        for wid in waterbody_ids:
            query = {
                "query": {"term": {"waterbody_id.keyword": wid}},
                "sort": [{"timestamp": "asc"}],
                "size": 100
            }
            response = es.search(index="waterbody_stats", body=query)
            hits = response['hits']['hits']
            
            if len(hits) < 2:
                continue
            
            name = hits[0]['_source'].get('name', wid)
            areas = [h['_source']['surface_area_hectares'] for h in hits]
            
            current = areas[-1]
            baseline = sum(areas) / len(areas)
            change = ((current - baseline) / baseline) * 100
            
            if change >= -5:
                risk = "LOW"
            elif change >= -15:
                risk = "MEDIUM"
            elif change >= -30:
                risk = "HIGH"
            else:
                risk = "CRITICAL"
            
            mid = len(areas) // 2
            recent_avg = sum(areas[mid:]) / len(areas[mid:])
            older_avg = sum(areas[:mid]) / len(areas[:mid])
            
            if recent_avg > older_avg * 1.02:
                trend = "INCREASING"
            elif recent_avg < older_avg * 0.98:
                trend = "DECLINING"
            else:
                trend = "STABLE"
            
            analyses.append({
                "waterbody_id": wid,
                "name": name,
                "current_area_hectares": round(current, 2),
                "baseline_area_hectares": round(baseline, 2),
                "percentage_change": round(change, 2),
                "risk_level": risk,
                "trend": trend,
                "last_updated": hits[-1]['_source']['timestamp']
            })
        
        return sorted(analyses, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x['risk_level'], 999))
    except Exception as e:
        return []


@app.get("/api/stats")
async def stats():
    """Statistiques"""
    try:
        count = es.count(index="waterbody_stats")
        
        agg_query = {
            "size": 0,
            "aggs": {
                "unique": {"cardinality": {"field": "waterbody_id.keyword"}},
                "oldest": {"min": {"field": "timestamp"}},
                "newest": {"max": {"field": "timestamp"}}
            }
        }
        response = es.search(index="waterbody_stats", body=agg_query)
        
        return {
            "total_documents": count['count'],
            "unique_waterbodies": response['aggregations']['unique']['value'],
            "oldest_measurement": response['aggregations']['oldest'].get('value_as_string', 'N/A'),
            "newest_measurement": response['aggregations']['newest'].get('value_as_string', 'N/A'),
            "elasticsearch_status": "connected",
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("\n🌊 WaterScope API Minimale")
    print("📖 http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)