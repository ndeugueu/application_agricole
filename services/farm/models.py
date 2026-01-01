"""
Farm Service Database Models
Farms, Plots (parcelles), Seasons/Campaigns, Crop Types
"""
from sqlalchemy import Column, String, Numeric, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.database import Base, TimestampMixin


class Farm(Base, TimestampMixin):
    """Farm/Exploitation model (Ferme)"""
    __tablename__ = 'farms'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(500))
    location = Column(String(255))  # Physical address or GPS coordinates
    total_area = Column(Numeric(12, 2))  # Total area in hectares
    owner_name = Column(String(255))
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    plots = relationship('Plot', back_populates='farm', cascade='all, delete-orphan')
    seasons = relationship('Season', back_populates='farm', cascade='all, delete-orphan')


class CropType(Base, TimestampMixin):
    """Crop type reference data (Type de culture)"""
    __tablename__ = 'crop_types'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(500))
    category = Column(String(100))  # e.g., "cereals", "vegetables", "fruits", "cash_crops"
    typical_yield_per_ha = Column(Numeric(12, 2))  # Average yield in kg/ha or tons/ha
    typical_cycle_days = Column(Integer)  # Typical growing cycle in days
    unit = Column(String(20), nullable=False, default="kg")  # kg, tons, units
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    plots = relationship('Plot', back_populates='crop_type')


class Plot(Base, TimestampMixin):
    """Plot/Parcelle - a subdivision of a farm for specific crops"""
    __tablename__ = 'plots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)  # Unique within farm
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    area = Column(Numeric(12, 2), nullable=False)  # Area in hectares
    soil_type = Column(String(100))  # e.g., "clay", "sandy", "loam"
    irrigation_available = Column(Boolean, default=False)

    # Current crop information
    crop_type_id = Column(UUID(as_uuid=True), ForeignKey('crop_types.id', ondelete='SET NULL'), index=True)
    current_season_id = Column(UUID(as_uuid=True), ForeignKey('seasons.id', ondelete='SET NULL'))

    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    farm = relationship('Farm', back_populates='plots')
    crop_type = relationship('CropType', back_populates='plots')
    current_season = relationship('Season', foreign_keys=[current_season_id])


class Season(Base, TimestampMixin):
    """Season/Campaign (Campagne/Saison) - a growing cycle"""
    __tablename__ = 'seasons'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Saison 2025-A", "Campagne Maïs 2025"
    code = Column(String(50), nullable=False, index=True)  # Unique identifier
    description = Column(String(500))
    year = Column(Integer, nullable=False, index=True)
    season_number = Column(Integer)  # 1, 2, 3 for multiple seasons per year
    start_date = Column(String(50))  # ISO date string YYYY-MM-DD
    end_date = Column(String(50))  # ISO date string YYYY-MM-DD
    status = Column(String(50), default="planned", nullable=False)  # planned, active, completed, cancelled
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    farm = relationship('Farm', back_populates='seasons')
