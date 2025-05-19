import logging
import sys
from logging.handlers import RotatingFileHandler
from core.configs import settings # Para buscar configurações como LOG_LEVEL, LOG_FILE

def setup_logging():
    """
    Configura o sistema de logging para a aplicação.
    """
    # Determina o nível de log a partir das configurações, default para INFO
    log_level_str = settings.LOG_LEVEL.upper() if hasattr(settings, 'LOG_LEVEL') else "INFO"
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Formato do Log
    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    # Logger Raiz - Configurações básicas
    # É geralmente melhor configurar handlers específicos em vez de apenas o basicConfig
    # para maior controle, especialmente se você tiver múltiplos handlers.
    # logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    # Em vez disso, vamos configurar o logger raiz e adicionar handlers a ele.

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level) # Define o nível mínimo para o logger raiz

    # Handler para Console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level) # Nível para este handler específico
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(console_handler)

    # Handler para Arquivo com Rotação (opcional)
    if hasattr(settings, 'LOG_FILE') and settings.LOG_FILE:
        # Rotação: 5 arquivos de 10MB cada
        file_handler = RotatingFileHandler(
            settings.LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(log_level) # Nível para este handler específico
        if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            root_logger.addHandler(file_handler)

    # Silenciar loggers de bibliotecas muito verbosas, se necessário
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Exemplo

    # Log de inicialização
    initial_log = logging.getLogger(__name__)
    initial_log.info(f"Logging configurado. Nível de log: {log_level_str}")
    if hasattr(settings, 'LOG_FILE') and settings.LOG_FILE:
        initial_log.info(f"Logs de arquivo serão salvos em: {settings.LOG_FILE}")

# Para garantir que a configuração seja chamada apenas uma vez
_logging_configured = False

def ensure_logging_configured():
    global _logging_configured
    if not _logging_configured:
        setup_logging()
        _logging_configured = True