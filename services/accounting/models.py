"""
Accounting & Tax Service Database Models
Ledger entries (append-only), Tax records, Chart of accounts
"""
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.database import Base, TimestampMixin


class AccountType(str, enum.Enum):
    """Chart of accounts - account types"""
    ACTIF = "actif"                    # Assets
    PASSIF = "passif"                  # Liabilities
    CAPITAUX_PROPRES = "capitaux_propres"  # Equity
    PRODUIT = "produit"                # Revenue
    CHARGE = "charge"                  # Expenses


class EntryType(str, enum.Enum):
    """Ledger entry type"""
    VENTE = "vente"                    # Sale transaction
    ACHAT = "achat"                    # Purchase transaction
    PAIEMENT = "paiement"              # Payment
    AJUSTEMENT = "ajustement"          # Manual adjustment
    TVA = "tva"                        # TVA entry
    STOCK = "stock"                    # Stock valuation


class TaxType(str, enum.Enum):
    """Tax type"""
    TVA_COLLECTEE = "tva_collectee"    # VAT collected (on sales)
    TVA_DEDUCTIBLE = "tva_deductible"  # VAT deductible (on purchases)


class Account(Base, TimestampMixin):
    """Chart of accounts"""
    __tablename__ = 'accounts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False, index=True)
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'))
    description = Column(String(500))
    is_active = Column(Integer, default=1)

    # Relationships
    parent_account = relationship('Account', remote_side=[id], backref='sub_accounts')
    ledger_entries_debit = relationship('LedgerEntry', foreign_keys='LedgerEntry.debit_account_id', back_populates='debit_account')
    ledger_entries_credit = relationship('LedgerEntry', foreign_keys='LedgerEntry.credit_account_id', back_populates='credit_account')


class LedgerEntry(Base, TimestampMixin):
    """
    Append-only journal entries (double-entry bookkeeping)
    CRITICAL: Never update or delete entries - corrections are done via reversing entries
    """
    __tablename__ = 'ledger_entries'

    __table_args__ = (
        Index('idx_ledger_date', 'entry_date'),
        Index('idx_ledger_type', 'entry_type'),
        Index('idx_ledger_reference', 'reference_type', 'reference_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD for easy queries
    entry_type = Column(SQLEnum(EntryType), nullable=False, index=True)

    # Double-entry: debit and credit accounts
    debit_account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=False)
    credit_account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=False)

    # Amount in FCFA cents (avoid float precision issues)
    amount = Column(Integer, nullable=False)

    # Reference to source transaction
    reference_type = Column(String(50))  # 'sale', 'purchase', 'payment', 'adjustment'
    reference_id = Column(UUID(as_uuid=True))

    # Additional metadata
    description = Column(String(500))
    notes = Column(String(1000))
    user_id = Column(UUID(as_uuid=True))  # Who created this entry
    fiscal_month = Column(String(7), nullable=False, index=True)  # YYYY-MM for monthly reports
    fiscal_year = Column(String(4), nullable=False, index=True)   # YYYY

    # Idempotency
    idempotency_key = Column(String(255), unique=True, index=True)

    # Reversal tracking (if this entry corrects/reverses another)
    reverses_entry_id = Column(UUID(as_uuid=True), ForeignKey('ledger_entries.id'))
    is_reversed = Column(Integer, default=0)  # 1 if this entry has been reversed

    # Relationships
    debit_account = relationship('Account', foreign_keys=[debit_account_id], back_populates='ledger_entries_debit')
    credit_account = relationship('Account', foreign_keys=[credit_account_id], back_populates='ledger_entries_credit')
    reverses_entry = relationship('LedgerEntry', remote_side=[id], backref='reversing_entries')


class TaxRecord(Base, TimestampMixin):
    """
    TVA tracking (19.25% for agricultural products in FCFA zone)
    Append-only pattern for audit trail
    """
    __tablename__ = 'tax_records'

    __table_args__ = (
        Index('idx_tax_period', 'fiscal_month'),
        Index('idx_tax_type', 'tax_type'),
        Index('idx_tax_reference', 'reference_type', 'reference_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tax_type = Column(SQLEnum(TaxType), nullable=False, index=True)

    # Base amount (HT - hors taxes) in FCFA cents
    base_amount = Column(Integer, nullable=False)

    # Tax rate (stored as integer: 1925 = 19.25%)
    tax_rate = Column(Integer, nullable=False, default=1925)

    # Tax amount in FCFA cents
    tax_amount = Column(Integer, nullable=False)

    # Reference to source transaction
    reference_type = Column(String(50), nullable=False)  # 'sale', 'purchase'
    reference_id = Column(UUID(as_uuid=True), nullable=False)

    # Fiscal period
    transaction_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    fiscal_month = Column(String(7), nullable=False, index=True)  # YYYY-MM
    fiscal_year = Column(String(4), nullable=False, index=True)   # YYYY

    # Additional metadata
    description = Column(String(500))
    notes = Column(String(1000))
    user_id = Column(UUID(as_uuid=True))

    # Idempotency
    idempotency_key = Column(String(255), unique=True, index=True)

    # Linked ledger entry (if applicable)
    ledger_entry_id = Column(UUID(as_uuid=True), ForeignKey('ledger_entries.id'))

    # Relationships
    ledger_entry = relationship('LedgerEntry', backref='tax_records')
