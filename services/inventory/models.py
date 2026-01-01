"""
Inventory Service Database Models
Products, Stock Movements (append-only pattern)
"""
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.database import Base, TimestampMixin


class ProductType(str, enum.Enum):
    """Product type enumeration"""
    INTRANT = "intrant"              # Agricultural inputs (seeds, fertilizers)
    ALIMENT = "aliment"              # Animal feed
    RECOLTE = "recolte"              # Harvested crops
    PRODUIT_TRANSFORME = "produit_transforme"  # Processed products
    AUTRE = "autre"


class MovementType(str, enum.Enum):
    """Stock movement type"""
    ENTREE = "entree"                # Stock in
    SORTIE = "sortie"                # Stock out
    AJUSTEMENT = "ajustement"        # Inventory adjustment
    RESERVATION = "reservation"      # Reserved stock
    LIBERATION = "liberation"        # Released reservation


class Product(Base, TimestampMixin):
    """Product catalog"""
    __tablename__ = 'products'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(500))
    product_type = Column(SQLEnum(ProductType), nullable=False, index=True)
    unit = Column(String(20), nullable=False)  # kg, liters, units, etc.

    # Stock thresholds
    min_stock_level = Column(Integer, default=0)
    max_stock_level = Column(Integer)

    # Pricing (in cents to avoid float issues)
    unit_cost = Column(Integer)  # Cost in FCFA cents
    unit_price = Column(Integer)  # Selling price in FCFA cents

    is_active = Column(Integer, default=1)

    # Relationships
    movements = relationship('StockMovement', back_populates='product', cascade='all, delete-orphan')


class StockMovement(Base, TimestampMixin):
    """
    Append-only stock movement log
    CRITICAL: Never update or delete movements - this ensures audit trail
    """
    __tablename__ = 'stock_movements'

    __table_args__ = (
        Index('idx_product_movement', 'product_id', 'movement_type'),
        Index('idx_movement_date', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    movement_type = Column(SQLEnum(MovementType), nullable=False, index=True)
    quantity = Column(Numeric(12, 3), nullable=False)  # Positive for IN, negative for OUT

    # Reference to source transaction
    reference_type = Column(String(50))  # 'purchase', 'sale', 'adjustment', 'harvest'
    reference_id = Column(UUID(as_uuid=True))  # ID of the source transaction

    # Additional metadata
    notes = Column(String(500))
    user_id = Column(UUID(as_uuid=True))  # Who created this movement
    location = Column(String(100))  # Warehouse, farm, etc.

    # Idempotency
    idempotency_key = Column(String(255), unique=True, index=True)

    # Relationships
    product = relationship('Product', back_populates='movements')
