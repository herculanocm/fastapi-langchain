from datetime import datetime
from zoneinfo import ZoneInfo

def now_sp() -> datetime:
    """Retorna o datetime atual em America/Sao_Paulo."""
    return datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)