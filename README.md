# 🌊 WaterScope - Inland Water Body Dynamics Monitor

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Elasticsearch 8.11](https://img.shields.io/badge/elasticsearch-8.11-yellow.svg)](https://www.elastic.co/)
[![Tests](https://img.shields.io/badge/tests-24%20passed-green.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-77%25-brightgreen.svg)](htmlcov/)

**Projet B3 - IPSA Paris**  
*Surveillance automatisée des masses d'eau par données satellite Sentinel-2*

Auteur : Saad Nhari | Janvier 2026

---

## 📖 Description

WaterScope surveille automatiquement l'évolution des lacs et réservoirs en utilisant des images satellite Sentinel-2 gratuites. Le système calcule la surface en eau via l'indice NDWI (Normalized Difference Water Index) et stocke les résultats dans Elasticsearch pour analyse dans Kibana.

**🎯 Objectif :** Détecter les variations de surface des masses d'eau pour identifier les sécheresses et analyser les tendances climatiques.

---

## 🚀 Quick Start (5 minutes)

```powershell
# 1. Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# 2. Démarrer Docker
docker-compose up -d

# 3. Attendre 30 secondes, puis vérifier
curl http://localhost:9200

# 4. Lancer l'ingestion
python scripts\test_full_pipeline.py

# 5. Ouvrir Kibana
start http://localhost:5601
```

---

## 🛠️ Installation Complète

### Prérequis
- ✅ Docker Desktop installé et démarré
- ✅ Python 3.11 ou supérieur
- ✅ Compte Copernicus Data Space (gratuit : https://dataspace.copernicus.eu/)

### Étape 1 : Environnement Python

```powershell
# Naviguer vers le dossier du projet
cd "C:\Users\...\WATERSCOPE"

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activer l'environnement (Windows CMD)
venv\Scripts\activate.bat

# Vérifier l'activation (doit afficher le chemin de venv)
where python
```

### Étape 2 : Installer les Dépendances

```powershell
# Installer toutes les dépendances
pip install -r requirements.txt

# Vérifier que tout est bien installé
pip list

# Vérifier version Elasticsearch (DOIT être 8.11.1)
pip show elasticsearch
```

### Étape 3 : Configuration

```powershell
# Créer le fichier .env à la racine
New-Item -ItemType File -Path ".env"

# Ouvrir .env avec un éditeur
notepad .env
```

**Contenu du .env :**
```env
COPERNICUS_USERNAME=ton_email@ipsa.fr
COPERNICUS_PASSWORD=ton_mot_de_passe
ELASTICSEARCH_HOST=http://localhost:9200
KIBANA_HOST=http://localhost:5601
PYTHONPATH=./src
```

### Étape 4 : Démarrer Docker

```powershell
# Démarrer Elasticsearch + Kibana
docker-compose up -d

# Vérifier que les conteneurs tournent
docker ps

# Devrait afficher :
# waterscope_elasticsearch (port 9200)
# waterscope_kibana (port 5601)

# Attendre 30-60 secondes que tout démarre
Start-Sleep -Seconds 30

# Vérifier Elasticsearch
curl http://localhost:9200

# Devrait retourner du JSON avec "You Know, for Search"
```

### Étape 5 : Test Initial

```powershell
# Tester l'authentification
python src\sentinel_hub\auth.py

# Devrait afficher : "Token obtained successfully!"

# Tester Elasticsearch
python src\elasticsearch_client\client.py

# Devrait afficher : "Connected to Elasticsearch"
```

### Étape 6 : Première Ingestion

```powershell
# Lancer le pipeline complet
python scripts\test_full_pipeline.py

# Devrait afficher :
# Processing: Lake Aral (lake_aral_001) ✅
# Processing: Lake Chad (lake_chad_001) ✅
# Processing: Lake Mead (lake_mead_001) ✅
# Total: 3 | Successful: 3 | Failed: 0
```

### Étape 7 : Vérification dans Kibana

```powershell
# Ouvrir Kibana dans le navigateur
start http://localhost:5601

# Vérifier le nombre de documents
curl http://localhost:9200/waterbody_stats/_count

# Devrait retourner : {"count": 3, ...}
```

**Dans Kibana :**
1. Menu ☰ → Management → Stack Management
2. Data → Index Patterns → Create index pattern
3. Name: `waterbody_stats*`
4. Time field: `timestamp`
5. Create
6. Menu ☰ → Analytics → Discover
7. Changer time range en haut à droite : "Last 1 year"
8. Voir les 3 documents !

---

## 🎮 Commandes Essentielles

### 🔧 Gestion de l'Environnement

```powershell
# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# Désactiver l'environnement
deactivate

# Réinstaller les dépendances
pip install -r requirements.txt

# Mettre à jour une dépendance spécifique
pip install --upgrade requests

# Lister les packages installés
pip list

# Voir les packages obsolètes
pip list --outdated
```

### 🐳 Gestion Docker

```powershell
# Démarrer les services
docker-compose up -d

# Arrêter les services
docker-compose down

# Redémarrer les services
docker-compose restart

# Voir les conteneurs en cours
docker ps

# Voir tous les conteneurs (y compris arrêtés)
docker ps -a

# Voir les logs d'Elasticsearch
docker logs waterscope_elasticsearch

# Voir les logs de Kibana
docker logs waterscope_kibana

# Suivre les logs en temps réel
docker-compose logs -f

# Supprimer tout (y compris données!)
docker-compose down -v
```

### 🧪 Tests

```powershell
# Lancer TOUS les tests
pytest tests/ -v

# Tests avec coverage
pytest tests/ -v --cov=src

# Coverage avec rapport détaillé
pytest tests/ -v --cov=src --cov-report=term-missing

# Générer rapport HTML
pytest tests/ -v --cov=src --cov-report=html

# Ouvrir le rapport dans le navigateur
start htmlcov/index.html

# Tests d'un module spécifique
pytest tests/test_sentinel_hub/test_auth.py -v
pytest tests/test_sentinel_hub/test_process_api.py -v
pytest tests/test_elasticsearch/test_client.py -v

# Tests sans intégration
pytest tests/ -v -m "not integration"

# Test d'une fonction spécifique
pytest tests/test_auth.py::TestSentinelHubAuth::test_init_avec_credentials -v
```

### 🚀 Exécution du Pipeline

```powershell
# Pipeline complet (tous les lacs)
python scripts\test_full_pipeline.py

# Tester uniquement l'authentification
python src\sentinel_hub\auth.py

# Tester uniquement le Process API
python src\sentinel_hub\process_api.py

# Tester uniquement Elasticsearch
python src\elasticsearch_client\client.py

# Tester le service d'ingestion
python src\ingestion\ingestion_service.py
```

### ⏰ Scheduler Automatique

```powershell
# Exécution immédiate (pour tester)
python src\ingestion\scheduler.py --mode now

# Exécution quotidienne à 14:00 (développement)
python src\ingestion\scheduler.py --mode daily

# Exécution mensuelle le 1er à 02:00 (production)
python src\ingestion\scheduler.py --mode monthly

# Avec fichier de config personnalisé
python src\ingestion\scheduler.py --config config/custom_lakes.json --mode now
```

### 🔍 Vérifications Elasticsearch

```powershell
# Santé du cluster
curl http://localhost:9200/_cluster/health

# Compter les documents
curl http://localhost:9200/waterbody_stats/_count

# Voir tous les documents (10 premiers)
curl http://localhost:9200/waterbody_stats/_search

# Voir le mapping de l'index
curl http://localhost:9200/waterbody_stats/_mapping

# Liste de tous les indices
curl http://localhost:9200/_cat/indices?v

# Statistiques de l'index
curl http://localhost:9200/waterbody_stats/_stats

# Supprimer l'index (ATTENTION: perte de données!)
curl -X DELETE http://localhost:9200/waterbody_stats
```

### 📊 Kibana

```powershell
# Ouvrir Kibana
start http://localhost:5601

# Ouvrir directement Discover
start http://localhost:5601/app/discover

# Ouvrir Stack Management
start http://localhost:5601/app/management
```

### 🐛 Debugging

```powershell
# Voir les logs du scheduler (si exécuté)
type data\logs\scheduler.log

# Nettoyer les fichiers cache Python
Get-ChildItem -Path . -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force

# Vérifier les processus Python en cours
Get-Process python

# Tuer un processus Python
Stop-Process -Name python

# Entrer dans le conteneur Elasticsearch
docker exec -it waterscope_elasticsearch bash

# Voir l'utilisation des ressources Docker
docker stats
```

### 📁 Gestion de Fichiers

```powershell
# Voir l'arborescence du projet
tree /F

# Créer les dossiers manquants
mkdir docs\screenshots
mkdir data\logs

# Compter les lignes de code
Get-ChildItem -Path src -Recurse -Filter *.py | Get-Content | Measure-Object -Line

# Compter les fichiers Python
Get-ChildItem -Path src -Recurse -Filter *.py | Measure-Object
```

---

## 🎯 Scénarios d'Usage

### Scénario 1 : Premier Démarrage du Jour

```powershell
# 1. Activer l'environnement
.\venv\Scripts\Activate.ps1

# 2. Démarrer Docker (si pas déjà fait)
docker-compose up -d

# 3. Vérifier que tout fonctionne
curl http://localhost:9200

# 4. Lancer les tests
pytest tests/ -v

# 5. Tu es prêt à travailler!
```

### Scénario 2 : Ajouter un Nouveau Lac

```powershell
# 1. Éditer le fichier de configuration
code config\waterbodies_config.json

# Ajouter :
# {
#   "waterbody_id": "lake_custom_001",
#   "name": "Mon Lac",
#   "geometry": { ... },
#   ...
# }

# 2. Lancer l'ingestion
python scripts\test_full_pipeline.py

# 3. Vérifier dans Kibana
start http://localhost:5601
```

### Scénario 3 : Tout Réinitialiser

```powershell
# 1. Arrêter Docker
docker-compose down -v

# 2. Supprimer l'environnement virtuel
Remove-Item -Recurse -Force venv

# 3. Recréer tout
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker-compose up -d
Start-Sleep -Seconds 30
python scripts\test_full_pipeline.py
```

### Scénario 4 : Avant de Rendre le Projet

```powershell
# 1. Lancer tous les tests
pytest tests/ -v --cov=src --cov-report=html

# 2. Vérifier le coverage (doit être >60%)
start htmlcov/index.html

# 3. Lancer le pipeline
python scripts\test_full_pipeline.py

# 4. Vérifier Kibana
start http://localhost:5601

# 5. Prendre les captures d'écran

# 6. Générer le PDF du rapport
# (Dans VS Code avec extension Markdown PDF)
```

---

## 🧪 Tests

**Résultats actuels :**
- ✅ 24 tests passés (8 auth + 10 process_api + 6 elasticsearch)
- ✅ Coverage : 77% (objectif >60%)
- ✅ 0 échecs

```powershell
# Suite de tests complète
pytest tests/ -v --cov=src --cov-report=html
```

---

## 📊 Résultats

**Pipeline d'ingestion :**
- ✅ 3 lacs configurés (Lake Aral, Lake Chad, Lake Mead)
- ✅ Données indexées dans Elasticsearch
- ✅ Visualisations disponibles dans Kibana
- ✅ Temps d'exécution : ~15 secondes par run

**Métriques de performance :**
- Tests unitaires : 24/24 ✅
- Coverage : 77%
- Authentification OAuth2 : Fonctionnelle
- Calcul NDWI : Validé avec seuil 0.2
- Filtrage nuages : SCL 8, 9, 3

---

## 📁 Structure du Projet

```
WATERSCOPE/
├── src/                           # Code source principal
│   ├── sentinel_hub/              # Authentification + Process API
│   │   ├── auth.py                # OAuth2 token management
│   │   └── process_api.py         # NDWI calculation client
│   ├── elasticsearch_client/      # Client Elasticsearch
│   │   └── client.py              # CRUD + time-series queries
│   ├── ingestion/                 # Service d'ingestion
│   │   ├── ingestion_service.py   # Orchestration
│   │   └── scheduler.py           # Planification automatique
│   └── utils/                     # Utilitaires
│       └── logging_config.py      # Configuration logging
│
├── tests/                         # Tests unitaires (Pytest)
│   ├── test_sentinel_hub/         # 18 tests
│   │   ├── test_auth.py
│   │   └── test_process_api.py
│   └── test_elasticsearch/        # 6 tests
│       └── test_client.py
│
├── config/                        # Configuration
│   └── waterbodies_config.json    # Définition des lacs
│
├── docs/                          # Documentation
│   ├── technology_familiarization_report.md  # 40+ pages
│   └── screenshots/               # Captures Kibana
│
├── scripts/                       # Scripts utilitaires
│   └── test_full_pipeline.py      # Test intégration E2E
│
├── docker-compose.yml             # Infrastructure Docker
├── requirements.txt               # Dépendances Python
├── pytest.ini                     # Configuration tests
├── .env                           # Credentials (non commité)
├── .gitignore                     # Fichiers à ignorer
└── README.md                      # Ce fichier
```

---

## 🎮 Usage Avancé

### Ajouter un Nouveau Lac

Éditer `config/waterbodies_config.json` :

```json
{
  "waterbody_id": "lake_custom_001",
  "name": "Mon Lac Personnalisé",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
  },
  "region": "Europe",
  "country": "France",
  "description": "Description du lac"
}
```

Puis :
```powershell
python scripts\test_full_pipeline.py
```

### Requêtes Elasticsearch Personnalisées

```powershell
# PowerShell - Chercher par waterbody_id
$body = '{"query":{"term":{"waterbody_id":"lake_aral_001"}}}'
Invoke-WebRequest -Uri "http://localhost:9200/waterbody_stats/_search" -Method POST -ContentType "application/json" -Body $body

# Chercher dans une période
$body = '{"query":{"range":{"timestamp":{"gte":"2024-01-01","lte":"2026-12-31"}}}}'
Invoke-WebRequest -Uri "http://localhost:9200/waterbody_stats/_search" -Method POST -ContentType "application/json" -Body $body
```

---

## 📈 Données Produites

**Index Elasticsearch :** `waterbody_stats`

**Structure des documents :**
```json
{
  "waterbody_id": "lake_aral_001",
  "name": "Lake Aral",
  "timestamp": "2026-01-07T00:00:00Z",
  "surface_area_hectares": 1050.8,
  "data_source": "Sentinel-2",
  "cloud_cover_percentage": 5.2,
  "geo_shape": {
    "type": "Polygon",
    "coordinates": [[[58.5, 45.0], ...]]
  }
}
```

---

## 🛠️ Dépannage

### Problème : Elasticsearch ne démarre pas

```powershell
# Voir les logs
docker logs waterscope_elasticsearch

# Solution 1: Augmenter la mémoire Docker
# Docker Desktop → Settings → Resources → Memory → 4GB → Apply

# Solution 2: Redémarrer Docker
docker-compose down
docker-compose up -d
```

### Problème : Erreur 401 Authentification

```powershell
# Vérifier le .env
type .env

# Tester l'authentification
python src\sentinel_hub\auth.py

# Si erreur: vérifier credentials sur https://dataspace.copernicus.eu/
```

### Problème : Pas de données dans Kibana

```powershell
# 1. Vérifier le nombre de documents
curl http://localhost:9200/waterbody_stats/_count

# 2. Si count = 0, lancer l'ingestion
python scripts\test_full_pipeline.py

# 3. Dans Kibana, changer time range à "Last 1 year"
```

### Problème : Tests échouent

```powershell
# Réinstaller elasticsearch à la bonne version
pip uninstall elasticsearch
pip install elasticsearch==8.11.1

# Relancer les tests
pytest tests/ -v
```

### Problème : "Cannot connect to Elasticsearch"

```powershell
# Vérifier qu'Elasticsearch tourne
docker ps

# Vérifier qu'il répond
curl http://localhost:9200

# Redémarrer si nécessaire
docker-compose restart elasticsearch
Start-Sleep -Seconds 30
curl http://localhost:9200
```

---

## 🔧 Configuration

### Variables d'Environnement (.env)

```env
# Copernicus Data Space Credentials
COPERNICUS_USERNAME=your_email@example.com
COPERNICUS_PASSWORD=your_password

# Elasticsearch
ELASTICSEARCH_HOST=http://localhost:9200
KIBANA_HOST=http://localhost:5601

# Python
PYTHONPATH=./src
```

### Docker Compose

Services déployés :
- **Elasticsearch** : Port 9200, 512MB RAM
- **Kibana** : Port 5601

---

## 📚 Documentation

- [📄 Rapport Technique Complet](docs/technology_familiarization_report.md) - 40 pages
- [📊 Coverage Report](htmlcov/index.html) - Généré par pytest-cov
- [🧪 Tests](tests/) - 24 tests unitaires
- [📸 Screenshots Kibana](docs/screenshots/) - 5 captures

---

## 🔮 Roadmap

### Phase 1 : Infrastructure & Ingestion (Semaines 1-4) ✅
- [x] Setup Docker (Elasticsearch + Kibana)
- [x] Authentification Sentinel Hub
- [x] Client Process API (NDWI)
- [x] Stockage Elasticsearch
- [x] Tests unitaires (24 tests, 77% coverage)
- [x] Documentation technique

### Phase 2 : API REST (Semaines 5-6) ⏳
- [ ] API FastAPI
- [ ] Endpoints `/waterbodies/{id}/surface-area`
- [ ] Endpoints `/analytics/drought-risk`
- [ ] Documentation Swagger

### Phase 3 : Dashboard Web (Semaines 7-8) ⏳
- [ ] Interface web (Streamlit ou React)
- [ ] Graphiques interactifs
- [ ] Alertes automatiques

---

## 🧠 Architecture

```
┌─────────────────────────────────────────┐
│     Sentinel-2 Satellite Data           │
│     (Images tous les 5 jours)           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Copernicus Data Space / Sentinel Hub  │
│   • Stockage images satellite           │
│   • Process API (calculs cloud)         │
└──────────────┬──────────────────────────┘
               │ HTTPS REST API
               ▼
┌─────────────────────────────────────────┐
│   Python WaterScope Application         │
│   • auth.py - OAuth2 token              │
│   • process_api.py - NDWI calculation   │
│   • ingestion_service.py - Orchestration│
└──────────────┬──────────────────────────┘
               │ JSON documents
               ▼
┌─────────────────────────────────────────┐
│          Elasticsearch                  │
│   Index: waterbody_stats                │
│   • Time-series storage                 │
│   • Queries & Aggregations              │
└──────────────┬──────────────────────────┘
               │ Visualization
               ▼
┌─────────────────────────────────────────┐
│             Kibana                      │
│   • Dashboards                          │
│   • Time-series charts                  │
│   • Discover interface                  │
└─────────────────────────────────────────┘
```

---

## 🔬 Méthodologie NDWI

### Principe Scientifique

Le **NDWI (Normalized Difference Water Index)** exploite les propriétés spectrales de l'eau :

**Formule :**
```
NDWI = (B03 - B08) / (B03 + B08)
```

**Où :**
- **B03** = Bande verte (560 nm) - Réfléchie par l'eau
- **B08** = Proche infrarouge (842 nm) - Absorbée par l'eau

**Interprétation :**
- `NDWI > 0.2` → Eau
- `NDWI ≤ 0.2` → Terre/Végétation

### Filtrage des Nuages

Utilisation de **SCL (Scene Classification Layer)** :
- SCL = 3 : Ombre de nuage
- SCL = 8 : Nuage (probabilité moyenne)
- SCL = 9 : Nuage (probabilité haute)

---

## ✅ Checklist Quotidienne

```powershell
# Matin
.\venv\Scripts\Activate.ps1
docker-compose up -d
curl http://localhost:9200

# Développement
pytest tests/ -v
python scripts\test_full_pipeline.py

# Fin de journée
pytest tests/ -v --cov=src --cov-report=term
docker-compose logs > logs_$(Get-Date -Format "yyyyMMdd").txt
```

---

## 👨‍💻 Auteur

**Saad Nhari**  
B3 - IPSA Paris  
Projet de fin d'études - Janvier 2026

📧 saad64547@gmail.com

---

## 🙏 Remerciements

- **ESA Copernicus** pour les données Sentinel-2 gratuites
- **Anthropic Claude** pour l'assistance technique
- **IPSA Paris** pour l'encadrement académique
- **Elastic** pour Elasticsearch et Kibana open-source

---

## 📄 License

Projet académique réalisé dans le cadre du cursus B3 à IPSA Paris.

© 2026 IPSA Paris - Tous droits réservés pour usage académique.

---

## 🔗 Liens Utiles

- [Documentation Copernicus](https://documentation.dataspace.copernicus.eu/)
- [Sentinel Hub Process API](https://docs.sentinel-hub.com/api/latest/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/index.html)
- [Kibana Guide](https://www.elastic.co/guide/en/kibana/8.11/index.html)
- [NDWI Scientific Paper](https://doi.org/10.1080/01431169608948714) - McFeeters (1996)

---

**Version :** 1.0.0 (Phase 1 complétée)  
**Dernière mise à jour :** 8 Janvier 2026  
**Status :** ✅ Production Ready (Phase 1)