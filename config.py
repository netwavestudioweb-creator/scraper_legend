import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de la base de données
# Support de DATABASE_URL (ex: Render / Supabase / Neon / Heroku)
raw_db_url = os.getenv("DATABASE_URL")

if raw_db_url:
    # SQLAlchemy requiert 'postgresql://' et non 'postgres://'
    if raw_db_url.startswith("postgres://"):
        DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URL = raw_db_url
else:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "scraper_legende")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    if DB_PASSWORD:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        DATABASE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# URL de fallback pour développement local sans serveur PostgreSQL démarré
SQLITE_FALLBACK_URL = "sqlite:///scraper_legende.db"

# Paramètres de scraping éthique
SCRAPER_USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (compatible; ScraperLegende/2.0)"
)
SCRAPER_DELAY_SECONDS = float(os.getenv("SCRAPER_DELAY_SECONDS", "1.5"))
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "15"))

# Port du serveur Dashboard Flask
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
