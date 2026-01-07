"""
Scheduler Automatique pour WaterScope
Exécute l'ingestion mensuellement
"""

import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
import sys

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sentinel_hub.auth import SentinelHubAuth
from sentinel_hub.process_api import ProcessAPIClient
from elasticsearch_client.client import WaterScopeESClient
from ingestion.ingestion_service import IngestionService

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class WaterScopeScheduler:
    """Planificateur automatique pour l'ingestion de données"""
    
    def __init__(self, config_path: str):
        """
        Initialise le scheduler
        
        Args:
            config_path: Chemin vers la configuration des water bodies
        """
        self.config_path = config_path
        logger.info("Scheduler initialisé")
    
    def run_ingestion(self):
        """Exécute une itération d'ingestion complète"""
        logger.info("="*60)
        logger.info("DÉMARRAGE INGESTION PLANIFIÉE")
        logger.info("="*60)
        
        try:
            # Initialiser les composants
            logger.info("Initialisation des composants...")
            auth = SentinelHubAuth()
            process_client = ProcessAPIClient(auth)
            es_client = WaterScopeESClient()
            
            # Créer le service d'ingestion
            service = IngestionService(auth, process_client, es_client)
            
            # Lancer l'ingestion
            logger.info(f"Lancement de l'ingestion depuis {self.config_path}")
            summary = service.ingest_all(self.config_path, months_back=1)
            
            # Logger le résultat
            logger.info("="*60)
            logger.info("RÉSULTAT DE L'INGESTION")
            logger.info("="*60)
            logger.info(f"Total water bodies: {summary['total_waterbodies']}")
            logger.info(f"Succès: {summary['successful']}")
            logger.info(f"Échecs: {summary['failed']}")
            
            if summary['failed'] > 0:
                logger.warning("Certaines ingestions ont échoué :")
                for result in summary['results']:
                    if result['status'] == 'error':
                        logger.error(f"  - {result['waterbody_id']}: {result.get('error', 'Unknown error')}")
            
            logger.info("Ingestion terminée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ingestion : {e}", exc_info=True)
            raise
    
    def start_monthly_schedule(self):
        """
        Démarre le scheduler avec exécution mensuelle
        Exécute le 1er de chaque mois à 02:00
        """
        # Planifier l'exécution mensuelle
        schedule.every().month.at("02:00").do(self.run_ingestion)
        
        logger.info("Scheduler démarré - Exécution mensuelle le 1er à 02:00")
        logger.info("Appuyez sur Ctrl+C pour arrêter")
        
        # Boucle infinie
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier toutes les minutes
        except KeyboardInterrupt:
            logger.info("Scheduler arrêté par l'utilisateur")
    
    def start_daily_schedule_for_testing(self):
        """
        Version TEST : Exécution quotidienne à 14:00
        Utile pour tester sans attendre un mois
        """
        schedule.every().day.at("14:00").do(self.run_ingestion)
        
        logger.info("Scheduler TEST démarré - Exécution quotidienne à 14:00")
        logger.info("Appuyez sur Ctrl+C pour arrêter")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler arrêté par l'utilisateur")
    
    def run_once_now(self):
        """Exécute l'ingestion immédiatement (pour test)"""
        logger.info("Exécution immédiate de l'ingestion")
        self.run_ingestion()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WaterScope Scheduler")
    parser.add_argument(
        '--config',
        type=str,
        default='config/waterbodies_config.json',
        help='Chemin vers la configuration des water bodies'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['monthly', 'daily', 'now'],
        default='now',
        help='Mode d\'exécution: monthly (production), daily (test), now (exécution immédiate)'
    )
    
    args = parser.parse_args()
    
    # Créer le dossier de logs s'il n'existe pas
    Path('data/logs').mkdir(parents=True, exist_ok=True)
    
    # Créer le scheduler
    scheduler = WaterScopeScheduler(args.config)
    
    # Lancer selon le mode
    if args.mode == 'monthly':
        scheduler.start_monthly_schedule()
    elif args.mode == 'daily':
        scheduler.start_daily_schedule_for_testing()
    else:  # now
        scheduler.run_once_now()