from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    JSON,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Opportunity(Base):
    """
    Modèle central pour toutes les opportunités d'affaires détectées multi-sources.
    Stocke le signal brut, les métadonnées de source, le score calculé,
    le statut d'analyse et le business case généré.
    """
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Métadonnées de source
    source = Column(String(50), nullable=False, index=True)  # ex: "hackernews", "producthunt", "reddit"
    category = Column(String(50), nullable=False, default="saas_tech", index=True)  # ex: "saas_tech", "b2b", "ia_tool"
    signal_type = Column(String(50), nullable=True, index=True)  # ex: "showcase", "pain_point", "feature_request"

    # Contenu détecté
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False)

    # Scoring & Priorisation
    score = Column(Float, default=0.0, nullable=False, index=True)

    # Workflow & Statut
    # Statuts: 'nouveau', 'qualifie', 'en_cours', 'rejete', 'business_case_genere'
    status = Column(String(50), default="nouveau", nullable=False, index=True)

    # Horodatage
    published_date = Column(DateTime, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Données brutes et Business Case généré
    raw_data = Column(JSON, nullable=True)
    business_case = Column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("source", "url", name="uq_opportunity_source_url"),
        Index("ix_source_detected_at", "source", "detected_at"),
    )

    def to_dict(self):
        """Retourne une représentation dictionnaire sérialisable."""
        return {
            "id": self.id,
            "source": self.source,
            "category": self.category,
            "signal_type": self.signal_type,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "score": round(self.score, 1) if self.score else 0.0,
            "status": self.status,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "raw_data": self.raw_data or {},
            "business_case": self.business_case or {},
        }

    def __repr__(self):
        return f"<Opportunity id={self.id} source={self.source} score={self.score} title={self.title[:35]}...>"


# Alias pour rétrocompatibilité avec d'éventuels scripts existants
ScrapedItem = Opportunity
