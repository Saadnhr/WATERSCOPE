"""
WaterScope API - Version Corrigée avec bon mapping
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from datetime import datetime
from elasticsearch import Elasticsearch

app = FastAPI(
    title="WaterScope API - Fixed",
    description="API Corrigée pour Dashboard",
    version="1.0.1"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Elasticsearch client
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
    """Health check"""
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
    """Liste des lacs - CORRIGÉ"""
    try:
        # Essayer d'abord avec .keyword
        query = {
            "size": 0,
            "aggs": {
                "waterbodies": {
                    "terms": {"field": "waterbody_id.keyword", "size": 100}
                }
            }
        }
        
        try:
            response = es.search(index="waterbody_stats", body=query)
            if response['aggregations']['waterbodies']['buckets']:
                return [b['key'] for b in response['aggregations']['waterbodies']['buckets']]
        except:
            pass
        
        # Sinon, sans .keyword
        query = {
            "size": 0,
            "aggs": {
                "waterbodies": {
                    "terms": {"field": "waterbody_id", "size": 100}
                }
            }
        }
        
        try:
            response = es.search(index="waterbody_stats", body=query)
            if response['aggregations']['waterbodies']['buckets']:
                return [b['key'] for b in response['aggregations']['waterbodies']['buckets']]
        except:
            pass
        
        # Dernière solution : récupérer tous les docs et extraire les IDs uniques
        all_docs = es.search(index="waterbody_stats", body={"size": 100})
        unique_ids = list(set([
            hit['_source'].get('waterbody_id') 
            for hit in all_docs['hits']['hits'] 
            if 'waterbody_id' in hit['_source']
        ]))
        return unique_ids
        
    except Exception as e:
        print(f"Error listing waterbodies: {e}")
        return []


@app.get("/api/waterbodies/{waterbody_id}/latest")
async def get_latest(waterbody_id: str):
    """Dernières données"""
    try:
        # Essayer avec .keyword
        query = {
            "query": {"term": {"waterbody_id.keyword": waterbody_id}},
            "sort": [{"timestamp": "desc"}],
            "size": 1
        }
        
        response = es.search(index="waterbody_stats", body=query)
        
        # Si pas de résultat, essayer sans .keyword
        if not response['hits']['hits']:
            query = {
                "query": {"term": {"waterbody_id": waterbody_id}},
                "sort": [{"timestamp": "desc"}],
                "size": 1
            }
            response = es.search(index="waterbody_stats", body=query)
        
        # Si toujours pas de résultat, match query
        if not response['hits']['hits']:
            query = {
                "query": {"match": {"waterbody_id": waterbody_id}},
                "sort": [{"timestamp": "desc"}],
                "size": 1
            }
            response = es.search(index="waterbody_stats", body=query)
        
        if response['hits']['hits']:
            return response['hits']['hits'][0]['_source']
        return {"error": "not found"}
    except Exception as e:
        print(f"Error getting latest: {e}")
        return {"error": str(e)}


@app.get("/api/waterbodies/{waterbody_id}/timeseries")
async def get_timeseries(waterbody_id: str, months_back: int = 12):
    """Série temporelle"""
    try:
        # Essayer plusieurs méthodes
        queries = [
            {"query": {"term": {"waterbody_id.keyword": waterbody_id}}},
            {"query": {"term": {"waterbody_id": waterbody_id}}},
            {"query": {"match": {"waterbody_id": waterbody_id}}}
        ]
        
        hits = []
        for q in queries:
            q["sort"] = [{"timestamp": "asc"}]
            q["size"] = 100
            response = es.search(index="waterbody_stats", body=q)
            if response['hits']['hits']:
                hits = response['hits']['hits']
                break
        
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
        print(f"Error getting timeseries: {e}")
        return {"error": str(e)}


@app.get("/api/analytics/comparison")
async def comparison():
    """Comparaison des lacs"""
    try:
        # Obtenir tous les IDs
        waterbody_ids = await list_waterbodies()
        
        waterbodies = []
        for wid in waterbody_ids:
            latest = await get_latest(wid)
            if 'error' not in latest:
                waterbodies.append({
                    "waterbody_id": wid,
                    "name": latest.get('name', wid),
                    "surface_area_hectares": latest['surface_area_hectares'],
                    "timestamp": latest['timestamp']
                })
        
        return {
            "total_waterbodies": len(waterbodies),
            "waterbodies": sorted(waterbodies, key=lambda x: x['surface_area_hectares'], reverse=True),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error in comparison: {e}")
        return {"error": str(e), "waterbodies": []}


@app.get("/api/analytics/drought-risk")
async def drought_risk():
    """Analyse risque sécheresse"""
    try:
        waterbody_ids = await list_waterbodies()
        
        analyses = []
        for wid in waterbody_ids:
            timeseries = await get_timeseries(wid, 12)
            
            if timeseries.get('count', 0) < 2:
                continue
            
            data_points = timeseries['data_points']
            name = timeseries['name']
            areas = [p['surface_area_hectares'] for p in data_points]
            
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
                "last_updated": data_points[-1]['timestamp']
            })
        
        return sorted(analyses, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x['risk_level'], 999))
    except Exception as e:
        print(f"Error in drought risk: {e}")
        return []


@app.get("/api/stats")
async def stats():
    """Statistiques"""
    try:
        count = es.count(index="waterbody_stats")
        waterbody_ids = await list_waterbodies()
        
        agg_query = {
            "size": 0,
            "aggs": {
                "oldest": {"min": {"field": "timestamp"}},
                "newest": {"max": {"field": "timestamp"}}
            }
        }
        response = es.search(index="waterbody_stats", body=agg_query)
        
        return {
            "total_documents": count['count'],
            "unique_waterbodies": len(waterbody_ids),
            "oldest_measurement": response['aggregations']['oldest'].get('value_as_string', 'N/A'),
            "newest_measurement": response['aggregations']['newest'].get('value_as_string', 'N/A'),
            "elasticsearch_status": "connected",
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error in stats: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("\n🌊 WaterScope API - Version Corrigée")
    print("📖 http://localhost:8000/docs\n")
    uvicorn.run("api_fixed:app", host="0.0.0.0", port=8000, reload=True)