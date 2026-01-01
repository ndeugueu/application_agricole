"""
Sales Service Database Models
Customers, Sales, Sale Lines, Payments (append-only pattern)
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


class SaleStatus(str, enum.Enum):
    """Sale status enumeration"""
    PENDING = "pending"              # Initial state, waiting for validation
    CONFIRMED = "confirmed"          # Stock decremented & ledger posted
    REJECTED = "rejected"            # Insufficient stock or other issue
    CANCELLED = "cancelled"          # Cancelled after creation


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration"""
    CASH = "cash"                    # Cash payment
    MOBILE_MONEY = "mobile_money"    # Mobile money (Orange Money, MTN, etc.)
    BANK_TRANSFER = "bank_transfer"  # Bank transfer
    CHECK = "check"                  # Check payment


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"              # Payment initiated
    COMPLETED = "completed"          # Payment confirmed
    FAILED = "failed"                # Payment failed


class Customer(Base, TimestampMixin):
    """Customer master data"""
    __tablename__ = 'customers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)

    # Contact information
    phone_number = Column(String(20))
    email = Column(String(100))
    address = Column(String(500))

    # Classification
    customer_type = Column(String(50))  # 'retail', 'wholesale', 'distributor', etc.
    tax_id = Column(String(50))  # Tax identification number

    # Credit management
    credit_limit = Column(Integer, default=0)  # Credit limit in FCFA cents
    current_balance = Column(Integer, default=0)  # Current balance in FCFA cents

    is_active = Column(Integer, default=1)

    # Relationships
    sales = relationship('Sale', back_populates='customer', cascade='all, delete-orphan')


class Sale(Base, TimestampMixin):
    """
    Sales header - append-only pattern
    Status changes are recorded through events, not updates
    """
    __tablename__ = 'sales'

    __table_args__ = (
        Index('idx_customer_sale', 'customer_id', 'created_at'),
        Index('idx_sale_status', 'status'),
        Index('idx_sale_date', 'sale_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)

    # Sale information
    sale_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    status = Column(SQLEnum(SaleStatus), nullable=False, default=SaleStatus.PENDING, index=True)

    # Amounts in FCFA cents (to avoid float issues)
    subtotal = Column(Integer, nullable=False)  # Sum of line totals before tax
    tax_amount = Column(Integer, nullable=False, default=0)  # TVA 19.25%
    total_amount = Column(Integer, nullable=False)  # Grand total

    # Metadata
    notes = Column(String(500))
    delivery_address = Column(String(500))
    created_by_user_id = Column(UUID(as_uuid=True))

    # Idempotency
    idempotency_key = Column(String(255), unique=True, index=True)

    # Correlation for event tracking
    correlation_id = Column(String(255), index=True)

    # Relationships
    customer = relationship('Customer', back_populates='sales')
    lines = relationship('SaleLine', back_populates='sale', cascade='all, delete-orphan')
    payments = relationship('Payment', back_populates='sale', cascade='all, delete-orphan')


class SaleLine(Base, TimestampMixin):
    """
    Sale line items - append-only
    Each line represents a product sold
    """
    __tablename__ = 'sale_lines'

    __table_args__ = (
        Index('idx_sale_product', 'sale_id', 'product_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey('sales.id', ondelete='CASCADE'), nullable=False)

    # Product reference (we don't FK to inventory to keep services decoupled)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_code = Column(String(50), nullable=False)
    product_name = Column(String(255), nullable=False)

    # Line details
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Integer, nullable=False)  # Price per unit in FCFA cents
    line_total = Column(Integer, nullable=False)  # quantity * unit_price

    # Tax details
    tax_rate = Column(Numeric(5, 2), default=19.25)  # 19.25% TVA
    tax_amount = Column(Integer, nullable=False, default=0)

    notes = Column(String(255))

    # Relationships
    sale = relationship('Sale', back_populates='lines')


class Payment(Base, TimestampMixin):
    """
    Payment records - append-only pattern
    CRITICAL: Never update or delete payments - this ensures audit trail
    """
    __tablename__ = 'payments'

    __table_args__ = (
        Index('idx_sale_payment', 'sale_id', 'payment_date'),
        Index('idx_payment_method', 'payment_method'),
        Index('idx_payment_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey('sales.id', ondelete='CASCADE'), nullable=False)

    # Payment details
    payment_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Amount in FCFA cents
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    # Method-specific references
    transaction_reference = Column(String(100))  # Mobile money transaction ID, check number, etc.
    receipt_number = Column(String(50))

    # Metadata
    notes = Column(String(500))
    processed_by_user_id = Column(UUID(as_uuid=True))

    # Idempotency
    idempotency_key = Column(String(255), unique=True, index=True)

    # Relationships
    sale = relationship('Sale', back_populates='payments')
