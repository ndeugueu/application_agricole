"""
Accounting & Tax Service
Double-entry bookkeeping with TVA tracking (19.25%)
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
import threading
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.database import create_db_engine, get_session_factory, get_db_session, Base
from shared.auth import get_current_user, require_roles, Roles
from shared.logging_config import configure_logging
from shared.events import EventPublisher, EventConsumer, EventEnvelope

import models
from pydantic import BaseModel, ConfigDict, Field

# Initialize
logger = configure_logging("accounting-service")
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_db_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)
Base.metadata.create_all(bind=engine)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
event_publisher = EventPublisher(RABBITMQ_URL, "accounting-service") if RABBITMQ_URL else None

app = FastAPI(
    title="Accounting & Tax Service",
    description="Double-entry bookkeeping with TVA tracking",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    with get_db_session(SessionFactory) as session:
        yield session


# ============================================
# Schemas
# ============================================

class AccountCreate(BaseModel):
    code: str
    name: str
    account_type: models.AccountType
    parent_account_id: Optional[UUID] = None
    description: Optional[str] = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    account_type: models.AccountType
    parent_account_id: Optional[UUID]
    description: Optional[str]
    is_active: int
    created_at: datetime


class LedgerEntryCreate(BaseModel):
    entry_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    entry_type: models.EntryType
    debit_account_id: UUID
    credit_account_id: UUID
    amount: int = Field(..., gt=0, description="Amount in FCFA cents")
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entry_date: str
    entry_type: models.EntryType
    debit_account_id: UUID
    credit_account_id: UUID
    amount: int
    reference_type: Optional[str]
    reference_id: Optional[UUID]
    description: Optional[str]
    fiscal_month: str
    fiscal_year: str
    is_reversed: int
    created_at: datetime


class TaxRecordCreate(BaseModel):
    tax_type: models.TaxType
    base_amount: int = Field(..., gt=0, description="Base amount HT in FCFA cents")
    tax_rate: int = Field(default=1925, description="Tax rate (1925 = 19.25%)")
    reference_type: str
    reference_id: UUID
    transaction_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    description: Optional[str] = None
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None


class TaxRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tax_type: models.TaxType
    base_amount: int
    tax_rate: int
    tax_amount: int
    reference_type: str
    reference_id: UUID
    transaction_date: str
    fiscal_month: str
    fiscal_year: str
    description: Optional[str]
    created_at: datetime


class MonthlyTVAReport(BaseModel):
    fiscal_month: str
    tva_collectee: int  # TVA collected (on sales)
    tva_deductible: int  # TVA deductible (on purchases)
    tva_net: int  # Net TVA (to pay or to recover)
    sales_count: int
    purchases_count: int


class TrialBalanceEntry(BaseModel):
    account_code: str
    account_name: str
    account_type: models.AccountType
    debit_total: int
    credit_total: int
    balance: int


# ============================================
# Chart of Accounts Endpoints
# ============================================

@app.post("/api/v1/accounts", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.COMPTABLE])),
    db: Session = Depends(get_db)
):
    """Create a new account in the chart of accounts"""
    # Check if code exists
    if db.query(models.Account).filter_by(code=account_data.code).first():
        raise HTTPException(status_code=400, detail="Account code already exists")

    # Verify parent account exists if specified
    if account_data.parent_account_id:
        parent = db.query(models.Account).filter_by(id=account_data.parent_account_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent account not found")

    account = models.Account(**account_data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)

    logger.info("Account created", account_id=str(account.id), code=account.code)
    return AccountResponse.model_validate(account)


@app.get("/api/v1/accounts", response_model=List[AccountResponse])
async def list_accounts(
    account_type: Optional[models.AccountType] = None,
    is_active: int = 1,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List accounts"""
    query = db.query(models.Account).filter_by(is_active=is_active)
    if account_type:
        query = query.filter_by(account_type=account_type)

    accounts = query.offset(skip).limit(limit).all()
    return [AccountResponse.model_validate(a) for a in accounts]


@app.get("/api/v1/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get account by ID"""
    account = db.query(models.Account).filter_by(id=account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse.model_validate(account)


# ============================================
# Ledger Entry Endpoints
# ============================================

@app.post("/api/v1/ledger-entries", response_model=LedgerEntryResponse, status_code=201)
async def create_ledger_entry(
    entry_data: LedgerEntryCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.COMPTABLE])),
    db: Session = Depends(get_db)
):
    """Create a ledger entry (append-only)"""
    # Verify accounts exist
    debit_account = db.query(models.Account).filter_by(id=entry_data.debit_account_id).first()
    credit_account = db.query(models.Account).filter_by(id=entry_data.credit_account_id).first()

    if not debit_account or not credit_account:
        raise HTTPException(status_code=404, detail="Debit or credit account not found")

    # Idempotency check
    if entry_data.idempotency_key:
        existing = db.query(models.LedgerEntry).filter_by(
            idempotency_key=entry_data.idempotency_key
        ).first()
        if existing:
            logger.warning("Duplicate ledger entry ignored", idempotency_key=entry_data.idempotency_key)
            return LedgerEntryResponse.model_validate(existing)

    # Calculate fiscal period
    entry_date = datetime.strptime(entry_data.entry_date, '%Y-%m-%d')
    fiscal_month = entry_date.strftime('%Y-%m')
    fiscal_year = entry_date.strftime('%Y')

    # Create entry
    entry = models.LedgerEntry(
        **entry_data.model_dump(exclude={'idempotency_key'}),
        fiscal_month=fiscal_month,
        fiscal_year=fiscal_year,
        user_id=UUID(current_user.user_id),
        idempotency_key=entry_data.idempotency_key
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Publish event
    if event_publisher:
        event_publisher.publish_event(
            "ledger.posted",
            {
                "entry_id": str(entry.id),
                "entry_type": entry.entry_type.value,
                "amount": entry.amount,
                "reference_type": entry.reference_type,
                "reference_id": str(entry.reference_id) if entry.reference_id else None,
                "fiscal_month": fiscal_month
            }
        )

    logger.info("Ledger entry created", entry_id=str(entry.id), amount=entry.amount)
    return LedgerEntryResponse.model_validate(entry)


@app.get("/api/v1/ledger-entries", response_model=List[LedgerEntryResponse])
async def list_ledger_entries(
    entry_type: Optional[models.EntryType] = None,
    fiscal_month: Optional[str] = Query(None, pattern=r'^\d{4}-\d{2}$'),
    reference_type: Optional[str] = None,
    reference_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List ledger entries"""
    query = db.query(models.LedgerEntry)

    if entry_type:
        query = query.filter_by(entry_type=entry_type)
    if fiscal_month:
        query = query.filter_by(fiscal_month=fiscal_month)
    if reference_type:
        query = query.filter_by(reference_type=reference_type)
    if reference_id:
        query = query.filter_by(reference_id=reference_id)

    entries = query.order_by(models.LedgerEntry.entry_date.desc()).offset(skip).limit(limit).all()
    return [LedgerEntryResponse.model_validate(e) for e in entries]


@app.post("/api/v1/ledger-entries/{entry_id}/reverse", response_model=LedgerEntryResponse, status_code=201)
async def reverse_ledger_entry(
    entry_id: UUID,
    notes: Optional[str] = None,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.COMPTABLE])),
    db: Session = Depends(get_db)
):
    """Reverse a ledger entry (create reversing entry)"""
    original_entry = db.query(models.LedgerEntry).filter_by(id=entry_id).first()
    if not original_entry:
        raise HTTPException(status_code=404, detail="Ledger entry not found")

    if original_entry.is_reversed:
        raise HTTPException(status_code=400, detail="Entry already reversed")

    # Create reversing entry (swap debit and credit)
    today = date.today().strftime('%Y-%m-%d')
    fiscal_month = date.today().strftime('%Y-%m')
    fiscal_year = date.today().strftime('%Y')

    reversing_entry = models.LedgerEntry(
        entry_date=today,
        entry_type=original_entry.entry_type,
        debit_account_id=original_entry.credit_account_id,  # Swapped
        credit_account_id=original_entry.debit_account_id,  # Swapped
        amount=original_entry.amount,
        reference_type=original_entry.reference_type,
        reference_id=original_entry.reference_id,
        description=f"Reversal of entry {str(entry_id)}",
        notes=notes or f"Reversing entry created on {today}",
        user_id=UUID(current_user.user_id),
        fiscal_month=fiscal_month,
        fiscal_year=fiscal_year,
        reverses_entry_id=entry_id
    )
    db.add(reversing_entry)

    # Mark original as reversed
    original_entry.is_reversed = 1

    db.commit()
    db.refresh(reversing_entry)

    logger.info("Ledger entry reversed", original_id=str(entry_id), reversing_id=str(reversing_entry.id))
    return LedgerEntryResponse.model_validate(reversing_entry)


# ============================================
# Tax (TVA) Endpoints
# ============================================

@app.post("/api/v1/tax-records", response_model=TaxRecordResponse, status_code=201)
async def create_tax_record(
    tax_data: TaxRecordCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.COMPTABLE])),
    db: Session = Depends(get_db)
):
    """Create a tax record (TVA)"""
    # Idempotency check
    if tax_data.idempotency_key:
        existing = db.query(models.TaxRecord).filter_by(
            idempotency_key=tax_data.idempotency_key
        ).first()
        if existing:
            logger.warning("Duplicate tax record ignored", idempotency_key=tax_data.idempotency_key)
            return TaxRecordResponse.model_validate(existing)

    # Calculate tax amount
    tax_amount = int((tax_data.base_amount * tax_data.tax_rate) / 10000)

    # Calculate fiscal period
    transaction_date = datetime.strptime(tax_data.transaction_date, '%Y-%m-%d')
    fiscal_month = transaction_date.strftime('%Y-%m')
    fiscal_year = transaction_date.strftime('%Y')

    # Create tax record
    tax_record = models.TaxRecord(
        **tax_data.model_dump(exclude={'idempotency_key'}),
        tax_amount=tax_amount,
        fiscal_month=fiscal_month,
        fiscal_year=fiscal_year,
        user_id=UUID(current_user.user_id),
        idempotency_key=tax_data.idempotency_key
    )
    db.add(tax_record)
    db.commit()
    db.refresh(tax_record)

    # Publish event
    if event_publisher:
        event_publisher.publish_event(
            f"tax.{tax_data.tax_type.value}",
            {
                "tax_id": str(tax_record.id),
                "tax_type": tax_record.tax_type.value,
                "base_amount": tax_record.base_amount,
                "tax_amount": tax_amount,
                "reference_type": tax_record.reference_type,
                "reference_id": str(tax_record.reference_id),
                "fiscal_month": fiscal_month
            }
        )

    logger.info("Tax record created", tax_id=str(tax_record.id), tax_amount=tax_amount)
    return TaxRecordResponse.model_validate(tax_record)


@app.get("/api/v1/tax-records", response_model=List[TaxRecordResponse])
async def list_tax_records(
    tax_type: Optional[models.TaxType] = None,
    fiscal_month: Optional[str] = Query(None, pattern=r'^\d{4}-\d{2}$'),
    reference_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List tax records"""
    query = db.query(models.TaxRecord)

    if tax_type:
        query = query.filter_by(tax_type=tax_type)
    if fiscal_month:
        query = query.filter_by(fiscal_month=fiscal_month)
    if reference_type:
        query = query.filter_by(reference_type=reference_type)

    records = query.order_by(models.TaxRecord.transaction_date.desc()).offset(skip).limit(limit).all()
    return [TaxRecordResponse.model_validate(r) for r in records]


# ============================================
# TVA Reports
# ============================================

@app.get("/api/v1/reports/tva/monthly", response_model=List[MonthlyTVAReport])
async def get_monthly_tva_report(
    fiscal_year: Optional[str] = Query(None, pattern=r'^\d{4}$'),
    current_user=Depends(require_roles([Roles.ADMIN, Roles.COMPTABLE, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Get monthly TVA report (collectée vs déductible)"""
    query = db.query(
        models.TaxRecord.fiscal_month,
        models.TaxRecord.tax_type,
        func.sum(models.TaxRecord.tax_amount).label('total_tax'),
        func.count(models.TaxRecord.id).label('record_count')
    )

    if fiscal_year:
        query = query.filter(models.TaxRecord.fiscal_year == fiscal_year)

    query = query.group_by(
        models.TaxRecord.fiscal_month,
        models.TaxRecord.tax_type
    ).order_by(models.TaxRecord.fiscal_month.desc())

    results = query.all()

    # Aggregate by month
    monthly_data = {}
    for row in results:
        month = row.fiscal_month
        if month not in monthly_data:
            monthly_data[month] = {
                'fiscal_month': month,
                'tva_collectee': 0,
                'tva_deductible': 0,
                'sales_count': 0,
                'purchases_count': 0
            }

        if row.tax_type == models.TaxType.TVA_COLLECTEE:
            monthly_data[month]['tva_collectee'] = int(row.total_tax)
            monthly_data[month]['sales_count'] = row.record_count
        elif row.tax_type == models.TaxType.TVA_DEDUCTIBLE:
            monthly_data[month]['tva_deductible'] = int(row.total_tax)
            monthly_data[month]['purchases_count'] = row.record_count

    # Calculate net TVA
    reports = []
    for month, data in sorted(monthly_data.items(), reverse=True):
        reports.append(MonthlyTVAReport(
            fiscal_month=data['fiscal_month'],
            tva_collectee=data['tva_collectee'],
            tva_deductible=data['tva_deductible'],
            tva_net=data['tva_collectee'] - data['tva_deductible'],
            sales_count=data['sales_count'],
            purchases_count=data['purchases_count']
        ))

    return reports


@app.get("/api/v1/reports/tva/monthly/{fiscal_month}", response_model=MonthlyTVAReport)
async def get_monthly_tva_report_for_month(
    fiscal_month: str,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.COMPTABLE, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Get TVA report for a specific month"""
    # Validate format
    try:
        datetime.strptime(fiscal_month, '%Y-%m')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid fiscal_month format. Use YYYY-MM")

    # Get TVA collectée
    tva_collectee = db.query(
        func.coalesce(func.sum(models.TaxRecord.tax_amount), 0),
        func.count(models.TaxRecord.id)
    ).filter(
        models.TaxRecord.fiscal_month == fiscal_month,
        models.TaxRecord.tax_type == models.TaxType.TVA_COLLECTEE
    ).first()

    # Get TVA déductible
    tva_deductible = db.query(
        func.coalesce(func.sum(models.TaxRecord.tax_amount), 0),
        func.count(models.TaxRecord.id)
    ).filter(
        models.TaxRecord.fiscal_month == fiscal_month,
        models.TaxRecord.tax_type == models.TaxType.TVA_DEDUCTIBLE
    ).first()

    collectee_amount = int(tva_collectee[0])
    deductible_amount = int(tva_deductible[0])

    return MonthlyTVAReport(
        fiscal_month=fiscal_month,
        tva_collectee=collectee_amount,
        tva_deductible=deductible_amount,
        tva_net=collectee_amount - deductible_amount,
        sales_count=tva_collectee[1],
        purchases_count=tva_deductible[1]
    )


@app.get("/api/v1/reports/trial-balance", response_model=List[TrialBalanceEntry])
async def get_trial_balance(
    fiscal_year: Optional[str] = Query(None, pattern=r'^\d{4}$'),
    fiscal_month: Optional[str] = Query(None, pattern=r'^\d{4}-\d{2}$'),
    current_user=Depends(require_roles([Roles.ADMIN, Roles.COMPTABLE, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Get trial balance (balance de vérification)"""
    # Query debit totals
    debit_query = db.query(
        models.Account.id,
        models.Account.code,
        models.Account.name,
        models.Account.account_type,
        func.coalesce(func.sum(models.LedgerEntry.amount), 0).label('debit_total')
    ).join(
        models.LedgerEntry,
        models.Account.id == models.LedgerEntry.debit_account_id
    ).filter(
        models.LedgerEntry.is_reversed == 0
    )

    if fiscal_year:
        debit_query = debit_query.filter(models.LedgerEntry.fiscal_year == fiscal_year)
    if fiscal_month:
        debit_query = debit_query.filter(models.LedgerEntry.fiscal_month == fiscal_month)

    debit_query = debit_query.group_by(
        models.Account.id,
        models.Account.code,
        models.Account.name,
        models.Account.account_type
    )

    # Query credit totals
    credit_query = db.query(
        models.Account.id,
        models.Account.code,
        models.Account.name,
        models.Account.account_type,
        func.coalesce(func.sum(models.LedgerEntry.amount), 0).label('credit_total')
    ).join(
        models.LedgerEntry,
        models.Account.id == models.LedgerEntry.credit_account_id
    ).filter(
        models.LedgerEntry.is_reversed == 0
    )

    if fiscal_year:
        credit_query = credit_query.filter(models.LedgerEntry.fiscal_year == fiscal_year)
    if fiscal_month:
        credit_query = credit_query.filter(models.LedgerEntry.fiscal_month == fiscal_month)

    credit_query = credit_query.group_by(
        models.Account.id,
        models.Account.code,
        models.Account.name,
        models.Account.account_type
    )

    # Combine results
    debit_results = {row.id: row for row in debit_query.all()}
    credit_results = {row.id: row for row in credit_query.all()}

    all_account_ids = set(debit_results.keys()) | set(credit_results.keys())

    trial_balance = []
    for account_id in all_account_ids:
        debit_row = debit_results.get(account_id)
        credit_row = credit_results.get(account_id)

        if debit_row:
            account_code = debit_row.code
            account_name = debit_row.name
            account_type = debit_row.account_type
            debit_total = int(debit_row.debit_total)
        else:
            account_code = credit_row.code
            account_name = credit_row.name
            account_type = credit_row.account_type
            debit_total = 0

        credit_total = int(credit_row.credit_total) if credit_row else 0

        trial_balance.append(TrialBalanceEntry(
            account_code=account_code,
            account_name=account_name,
            account_type=account_type,
            debit_total=debit_total,
            credit_total=credit_total,
            balance=debit_total - credit_total
        ))

    # Sort by account code
    trial_balance.sort(key=lambda x: x.account_code)
    return trial_balance


# ============================================
# Event Handlers
# ============================================

def handle_sale_created(event: EventEnvelope):
    """Handle sale.created event - create TVA collectée record"""
    logger.info("Handling sale.created event", event_id=event.event_id)

    with get_db_session(SessionFactory) as db:
        try:
            payload = event.payload
            sale_id = payload.get('sale_id')
            total_ht = payload.get('total_ht')  # Base amount without tax
            transaction_date = payload.get('sale_date')

            if not sale_id or not total_ht or not transaction_date:
                logger.warning("Missing required fields in sale.created event", event_id=event.event_id)
                return

            # Calculate tax
            tax_amount = int((total_ht * 1925) / 10000)  # 19.25%

            # Calculate fiscal period
            trans_date = datetime.strptime(transaction_date, '%Y-%m-%d')
            fiscal_month = trans_date.strftime('%Y-%m')
            fiscal_year = trans_date.strftime('%Y')

            # Create tax record
            tax_record = models.TaxRecord(
                tax_type=models.TaxType.TVA_COLLECTEE,
                base_amount=total_ht,
                tax_rate=1925,
                tax_amount=tax_amount,
                reference_type='sale',
                reference_id=UUID(sale_id),
                transaction_date=transaction_date,
                fiscal_month=fiscal_month,
                fiscal_year=fiscal_year,
                description=f"TVA collectée - Vente {sale_id}",
                idempotency_key=f"sale_{sale_id}_tva"
            )
            db.add(tax_record)
            db.commit()

            logger.info("TVA collectée created for sale", sale_id=sale_id, tax_amount=tax_amount)

        except Exception as e:
            logger.error("Error handling sale.created event", error=str(e), event_id=event.event_id)
            db.rollback()
            raise


def handle_purchase_received(event: EventEnvelope):
    """Handle purchase.received event - create TVA déductible record"""
    logger.info("Handling purchase.received event", event_id=event.event_id)

    with get_db_session(SessionFactory) as db:
        try:
            payload = event.payload
            purchase_id = payload.get('purchase_id')
            total_ht = payload.get('total_ht')
            transaction_date = payload.get('purchase_date')

            if not purchase_id or not total_ht or not transaction_date:
                logger.warning("Missing required fields in purchase.received event", event_id=event.event_id)
                return

            # Calculate tax
            tax_amount = int((total_ht * 1925) / 10000)  # 19.25%

            # Calculate fiscal period
            trans_date = datetime.strptime(transaction_date, '%Y-%m-%d')
            fiscal_month = trans_date.strftime('%Y-%m')
            fiscal_year = trans_date.strftime('%Y')

            # Create tax record
            tax_record = models.TaxRecord(
                tax_type=models.TaxType.TVA_DEDUCTIBLE,
                base_amount=total_ht,
                tax_rate=1925,
                tax_amount=tax_amount,
                reference_type='purchase',
                reference_id=UUID(purchase_id),
                transaction_date=transaction_date,
                fiscal_month=fiscal_month,
                fiscal_year=fiscal_year,
                description=f"TVA déductible - Achat {purchase_id}",
                idempotency_key=f"purchase_{purchase_id}_tva"
            )
            db.add(tax_record)
            db.commit()

            logger.info("TVA déductible created for purchase", purchase_id=purchase_id, tax_amount=tax_amount)

        except Exception as e:
            logger.error("Error handling purchase.received event", error=str(e), event_id=event.event_id)
            db.rollback()
            raise


# ============================================
# Startup & Shutdown
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize service"""
    logger.info("Accounting service starting up")
    if event_publisher:
        event_publisher.connect()

    # Setup event consumer
    if RABBITMQ_URL:
        consumer = EventConsumer(RABBITMQ_URL, "accounting-service", "accounting_queue")
        consumer.connect()
        consumer.register_handler("sale.created", handle_sale_created)
        consumer.register_handler("purchase.received", handle_purchase_received)
        app.state.accounting_consumer = consumer
        consumer_thread = threading.Thread(target=consumer.start_consuming, daemon=True)
        consumer_thread.start()
        app.state.accounting_consumer_thread = consumer_thread


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup"""
    logger.info("Accounting service shutting down")
    if event_publisher:
        event_publisher.close()
    if hasattr(app.state, "accounting_consumer"):
        app.state.accounting_consumer.stop_consuming()


# ============================================
# Health Check
# ============================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "accounting-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
