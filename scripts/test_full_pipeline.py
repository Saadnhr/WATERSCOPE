"""
Script pour tester le pipeline complet avec plusieurs water bodies
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sentinel_hub.auth import SentinelHubAuth
from sentinel_hub.process_api import ProcessAPIClient
from elasticsearch_client.client import WaterScopeESClient
from ingestion.ingestion_service import IngestionService

print("="*60)
print("TEST PIPELINE COMPLET")
print("="*60)

# Initialize components
print("\n1. Initialisation des composants...")
auth = SentinelHubAuth()
process_client = ProcessAPIClient(auth)
es_client = WaterScopeESClient()

# Initialize service
service = IngestionService(auth, process_client, es_client)

# Run ingestion for all configured waterbodies
print("\n2. Lancement de l'ingestion...")
config_path = "config/waterbodies_config.json"

try:
    summary = service.ingest_all(config_path, months_back=1)
    
    print("\n" + "="*60)
    print("RESULTAT FINAL")
    print("="*60)
    print(f"Total: {summary['total_waterbodies']}")
    print(f"Succes: {summary['successful']}")
    print(f"Echecs: {summary['failed']}")
    
except FileNotFoundError:
    print(f"\nERREUR: Fichier de config non trouve: {config_path}")
    print("Assure-toi d'avoir copie waterbodies_config.json dans le dossier config/")
except Exception as e:
    print(f"\nERREUR: {e}")