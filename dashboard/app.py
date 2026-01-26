"""
WaterScope Dashboard - Flask Application - Version Corrigée
"""

from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from elasticsearch_client.client import WaterScopeESClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'waterscope-secret-key-2026'

# Configuration
API_BASE_URL = "http://localhost:8000"
ES_CLIENT = WaterScopeESClient()


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/waterbodies')
def get_waterbodies():
    """Get all waterbodies"""
    try:
        print("📊 Dashboard: Fetching waterbodies list...")
        response = requests.get(f"{API_BASE_URL}/api/waterbodies/", timeout=10)
        print(f"✅ Dashboard: Received {len(response.json())} waterbodies")
        return jsonify(response.json())
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard: Cannot connect to API")
        return jsonify({"error": "API not available"}), 503
    except Exception as e:
        print(f"❌ Dashboard: Error fetching waterbodies: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/waterbody/<waterbody_id>/latest')
def get_waterbody_latest(waterbody_id):
    """Get latest data for a waterbody"""
    try:
        print(f"📊 Dashboard: Fetching latest data for {waterbody_id}")
        response = requests.get(
            f"{API_BASE_URL}/api/waterbodies/{waterbody_id}/latest",
            timeout=10
        )
        data = response.json()
        print(f"✅ Dashboard: Received data for {waterbody_id}")
        return jsonify(data)
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard: Cannot connect to API")
        return jsonify({"error": "API not available"}), 503
    except Exception as e:
        print(f"❌ Dashboard: Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/waterbody/<waterbody_id>/timeseries')
def get_waterbody_timeseries(waterbody_id):
    """Get timeseries data for a waterbody"""
    try:
        months = request.args.get('months', 12, type=int)
        print(f"📊 Dashboard: Fetching timeseries for {waterbody_id} ({months} months)")
        
        response = requests.get(
            f"{API_BASE_URL}/api/waterbodies/{waterbody_id}/timeseries",
            params={'months_back': months},
            timeout=10
        )
        data = response.json()
        
        print(f"✅ Dashboard: Received {data.get('count', 0)} data points")
        return jsonify(data)
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard: Cannot connect to API")
        return jsonify({"error": "API not available"}), 503
    except Exception as e:
        print(f"❌ Dashboard: Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/drought-risk')
def get_drought_risk():
    """Get drought risk analysis for all waterbodies"""
    try:
        print("📊 Dashboard: Fetching drought risk analysis...")
        response = requests.get(
            f"{API_BASE_URL}/api/analytics/drought-risk",
            timeout=30
        )
        data = response.json()
        print(f"✅ Dashboard: Received {len(data)} risk analyses")
        return jsonify(data)
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard: Cannot connect to API")
        return jsonify([]), 503
    except Exception as e:
        print(f"❌ Dashboard: Error: {e}")
        return jsonify([]), 500


@app.route('/api/drought-risk/<waterbody_id>')
def get_drought_risk_single(waterbody_id):
    """Get drought risk analysis for a single waterbody"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/analytics/drought-risk/{waterbody_id}",
            timeout=10
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/trend/<waterbody_id>')
def get_trend(waterbody_id):
    """Get trend analysis for a waterbody"""
    try:
        months = request.args.get('months', 12, type=int)
        response = requests.get(
            f"{API_BASE_URL}/api/analytics/trend/{waterbody_id}",
            params={'months': months},
            timeout=10
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/comparison')
def get_comparison():
    """Compare all waterbodies"""
    try:
        print("📊 Dashboard: Fetching comparison data...")
        response = requests.get(
            f"{API_BASE_URL}/api/analytics/comparison",
            timeout=30
        )
        data = response.json()
        
        if 'waterbodies' in data:
            print(f"✅ Dashboard: Comparison data received - {len(data['waterbodies'])} waterbodies")
        else:
            print(f"⚠️ Dashboard: Comparison response: {data}")
        
        return jsonify(data)
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard: Cannot connect to API")
        return jsonify({"error": "API not available", "waterbodies": []}), 503
    except Exception as e:
        print(f"❌ Dashboard: Error in comparison: {e}")
        return jsonify({"error": str(e), "waterbodies": []}), 500


@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    try:
        print("📊 Dashboard: Fetching stats...")
        response = requests.get(
            f"{API_BASE_URL}/api/stats",
            timeout=10
        )
        data = response.json()
        print(f"✅ Dashboard: Stats - {data.get('total_documents', 0)} docs, {data.get('unique_waterbodies', 0)} waterbodies")
        return jsonify(data)
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard: Cannot connect to API")
        return jsonify({"error": "API not available"}), 503
    except Exception as e:
        print(f"❌ Dashboard: Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/health')
def health_check():
    """Health check"""
    try:
        # Check FastAPI
        api_response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        api_status = "healthy" if api_response.status_code == 200 else "unhealthy"
        
        # Check Elasticsearch directly
        es_health = ES_CLIENT.health_check()
        es_status = es_health['status']
        
        return jsonify({
            "dashboard": "healthy",
            "fastapi": api_status,
            "elasticsearch": es_status,
            "timestamp": datetime.now().isoformat()
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            "dashboard": "healthy",
            "fastapi": "offline",
            "elasticsearch": "unknown",
            "timestamp": datetime.now().isoformat(),
            "error": "FastAPI server not running. Start it with: uvicorn api_fixed:app --reload"
        }), 503
    except Exception as e:
        return jsonify({
            "dashboard": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌊 WaterScope Dashboard Starting...")
    print("="*60)
    print("📊 Dashboard: http://localhost:5000")
    print("🔌 API Backend: http://localhost:8000")
    print("📖 Make sure FastAPI is running: uvicorn api_fixed:app --reload")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )