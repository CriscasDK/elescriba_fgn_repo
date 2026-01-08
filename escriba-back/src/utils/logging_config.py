"""Configuración centralizada de logging para el sistema."""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    name: str,
    level: str = "INFO",
    log_to_file: bool = True,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Configura logging para un módulo del sistema.

    Args:
        name: Nombre del logger (usualmente __name__)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Si True, también escribe a archivo
        log_dir: Directorio de logs (default: data/logs/)

    Returns:
        Logger configurado

    Examples:
        >>> logger = setup_logging(__name__)
        >>> logger.info("Mensaje informativo")
        >>> logger.error("Error detectado")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Evitar duplicar handlers
    if logger.handlers:
        return logger

    # Formato de mensajes
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (opcional)
    if log_to_file:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "data" / "logs"

        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name.replace('.', '_')}.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Logger por defecto para el sistema
default_logger = setup_logging("sistema_rag", level="INFO")
