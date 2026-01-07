"""
Configuration centralisée du logging pour WaterScope
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_level=logging.INFO,
    log_to_file=True,
    log_to_console=True,
    log_dir='data/logs'
):
    """
    Configure le système de logging pour WaterScope
    
    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Écrire les logs dans un fichier
        log_to_console: Afficher les logs dans la console
        log_dir: Répertoire pour les fichiers de log
    
    Returns:
        Logger configuré
    """
    # Créer le dossier de logs
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Format des logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Créer le formatter
    formatter = logging.Formatter(log_format, date_format)
    
    # Récupérer le root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Supprimer les handlers existants
    root_logger.handlers = []
    
    # Handler console
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Handler fichier (avec rotation)
    if log_to_file:
        # Fichier de log avec date
        log_file = Path(log_dir) / f"waterscope_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Rotating file handler (max 10MB, garde 5 fichiers)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Logger de démarrage
    logger = logging.getLogger('waterscope')
    logger.info("Logging system initialized")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info(f"Log to console: {log_to_console}")
    logger.info(f"Log to file: {log_to_file}")
    
    return logger


# Logger par défaut pour l'application
def get_logger(name):
    """
    Récupère un logger pour un module spécifique
    
    Args:
        name: Nom du module (généralement __name__)
    
    Returns:
        Logger configuré
    """
    return logging.getLogger(name)


if __name__ == "__main__":
    # Test du système de logging
    logger = setup_logging(log_level=logging.DEBUG)
    
    logger.debug("Ceci est un message DEBUG")
    logger.info("Ceci est un message INFO")
    logger.warning("Ceci est un message WARNING")
    logger.error("Ceci est un message ERROR")
    logger.critical("Ceci est un message CRITICAL")
    
    print("\nLes logs ont été écrits dans data/logs/")