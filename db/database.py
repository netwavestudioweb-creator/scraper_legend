import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from db.models import Base
from config import DATABASE_URL, SQLITE_FALLBACK_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _create_resilient_engine():
    """Tente de créer l'engine PostgreSQL, bascule sur SQLite si inaccessible en local."""
    try:
        engine_pg = create_engine(DATABASE_URL, pool_pre_ping=True)
        # Test rapide de connexion
        with engine_pg.connect() as conn:
            pass
        logger.info(f"✅ Connecté à PostgreSQL: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
        return engine_pg
    except Exception as e:
        logger.warning(f"⚠️ Impossible de joindre PostgreSQL ({e}). Bascule sur base locale SQLite ({SQLITE_FALLBACK_URL}).")
        return create_engine(SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})

engine = _create_resilient_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Crée les tables si elles n'existent pas encore."""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables de la base de données initialisées avec succès.")


def get_session():
    """Fournit une session SQLAlchemy."""
    return SessionLocal()


if __name__ == "__main__":
    init_db()
