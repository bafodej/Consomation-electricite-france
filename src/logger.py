"""
Configuration du logging applicatif structuré
RNCP C20: Assurer le monitoring et la supervision de l'application
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import json


class JSONFormatter(logging.Formatter):
    """Formateur pour logs en JSON structuré"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id

        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint

        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(log_level=logging.INFO, log_dir="logs"):
    """
    Configure le logging applicatif avec sortie console et fichiers

    Args:
        log_level: Niveau de log (INFO, DEBUG, WARNING, ERROR)
        log_dir: Répertoire pour les fichiers de logs
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Retirer les handlers existants
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Handler console (format lisible)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Handler fichier général (format JSON)
    app_log_file = log_path / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(app_log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # Handler fichier erreurs uniquement
    error_log_file = log_path / f"error_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)

    # Réduire le niveau de logging des librairies tierces
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    root_logger.info("Logging configuré avec succès", extra={
        'log_dir': str(log_path),
        'log_level': logging.getLevelName(log_level)
    })

    return root_logger


def get_logger(name):
    """
    Récupère un logger nommé

    Args:
        name: Nom du logger (généralement __name__)

    Returns:
        Logger configuré
    """
    return logging.getLogger(name)
