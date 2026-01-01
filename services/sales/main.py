"""
Sales Service
Customer and sales management with event-driven stock/accounting integration
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4
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
logger = configure_logging("sales-service")
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_db_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)
Base.metadata.create_all(bind=engine)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
event_publisher = EventPublisher(RABBITMQ_URL, "sales-service") if RABBITMQ_URL else None

app = FastAPI(title="Sales Service", version="1.0.0")

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

class CustomerCreate(BaseModel):
    code: str
    name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    customer_type: Optional[str] = None
    tax_id: Optional[str] = None
    credit_limit: int = 0


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    phone_number: Optional[str]
    email: Optional[str]
    address: Optional[str]
    customer_type: Optional[str]
    tax_id: Optional[str]
    credit_limit: int
    current_balance: int
    is_active: int
    created_at: datetime


class SaleLineCreate(BaseModel):
    product_id: UUID
    product_code: str
    product_name: str
    quantity: Decimal = Field(gt=0)
    unit_price: int = Field(gt=0)
    tax_rate: Decimal = Field(default=Decimal("19.25"))


class SaleLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_code: str
    product_name: str
    quantity: Decimal
    unit_price: int
    line_total: int
    tax_rate: Decimal
    tax_amount: int


class SaleCreate(BaseModel):
    customer_id: UUID
    sale_date: str  # YYYY-MM-DD
    lines: List[SaleLineCreate]
    notes: Optional[str] = None
    delivery_address: Optional[str] = None
    idempotency_key: Optional[str] = None


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sale_number: str
    customer_id: UUID
    sale_date: str
    status: models.SaleStatus
    subtotal: int
    tax_amount: int
    total_amount: int
    notes: Optional[str]
    delivery_address: Optional[str]
    correlation_id: Optional[str]
    created_at: datetime
    lines: List[SaleLineResponse]


class PaymentCreate(BaseModel):
    sale_id: UUID
    payment_date: str  # YYYY-MM-DD
    payment_method: models.PaymentMethod
    amount: int = Field(gt=0)
    transaction_reference: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sale_id: UUID
    payment_date: str
    payment_method: models.PaymentMethod
    amount: int
    status: models.PaymentStatus
    transaction_reference: Optional[str]
    receipt_number: Optional[str]
    notes: Optional[str]
    created_at: datetime


# ============================================
# Customer Endpoints
# ============================================

@app.post("/api/v1/customers", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_data: CustomerCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Create a new customer"""
    # Check if code exists
    if db.query(models.Customer).filter_by(code=customer_data.code).first():
        raise HTTPException(status_code=400, detail="Customer code already exists")

    customer = models.Customer(**customer_data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)

    if event_publisher:
        event_publisher.publish_event(
            "customer.created",
            {"customer_id": str(customer.id), "code": customer.code, "name": customer.name}
        )

    logger.info("Customer created", customer_id=str(customer.id), code=customer.code)
    return CustomerResponse.model_validate(customer)


@app.get("/api/v1/customers", response_model=List[CustomerResponse])
async def list_customers(
    is_active: int = 1,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List customers"""
    query = db.query(models.Customer).filter_by(is_active=is_active)
    customers = query.offset(skip).limit(limit).all()
    return [CustomerResponse.model_validate(c) for c in customers]


@app.get("/api/v1/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer by ID"""
    customer = db.query(models.Customer).filter_by(id=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse.model_validate(customer)


# ============================================
# Sale Endpoints
# ============================================

def generate_sale_number(db: Session) -> str:
    """Generate unique sale number"""
    today = date.today()
    prefix = f"VTE-{today.strftime('%Y%m%d')}"

    # Get count of sales today
    count = db.query(func.count(models.Sale.id)).filter(
        models.Sale.sale_number.like(f"{prefix}%")
    ).scalar()

    return f"{prefix}-{count + 1:04d}"


def calculate_sale_totals(lines: List[SaleLineCreate]) -> tuple[int, int, int]:
    """Calculate sale subtotal, tax, and total"""
    subtotal = 0
    tax_amount = 0

    for line in lines:
        line_total = int(line.quantity * line.unit_price)
        subtotal += line_total

        # Calculate tax (19.25%)
        line_tax = int(line_total * float(line.tax_rate) / 100)
        tax_amount += line_tax

    total_amount = subtotal + tax_amount
    return subtotal, tax_amount, total_amount


@app.post("/api/v1/sales", response_model=SaleResponse, status_code=201)
async def create_sale(
    sale_data: SaleCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE, Roles.AGENT_TERRAIN])),
    db: Session = Depends(get_db)
):
    """
    Create a new sale (Saga pattern)
    1. Create sale with PENDING status
    2. Publish sale.created event
    3. Wait for stock.decremented and ledger.posted events
    4. Status updated to CONFIRMED or REJECTED by event handlers
    """
    # Validate customer exists
    customer = db.query(models.Customer).filter_by(id=sale_data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if not sale_data.lines:
        raise HTTPException(status_code=400, detail="Sale must have at least one line")

    # Idempotency check
    if sale_data.idempotency_key:
        existing = db.query(models.Sale).filter_by(
            idempotency_key=sale_data.idempotency_key
        ).first()
        if existing:
            logger.warning("Duplicate sale ignored", idempotency_key=sale_data.idempotency_key)
            db.refresh(existing)
            return SaleResponse.model_validate(existing)

    # Calculate totals
    subtotal, tax_amount, total_amount = calculate_sale_totals(sale_data.lines)

    # Generate sale number and correlation ID
    sale_number = generate_sale_number(db)
    correlation_id = str(uuid4())

    # Create sale
    sale = models.Sale(
        sale_number=sale_number,
        customer_id=sale_data.customer_id,
        sale_date=sale_data.sale_date,
        status=models.SaleStatus.PENDING,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        notes=sale_data.notes,
        delivery_address=sale_data.delivery_address,
        created_by_user_id=UUID(current_user.user_id),
        idempotency_key=sale_data.idempotency_key,
        correlation_id=correlation_id
    )
    db.add(sale)
    db.flush()

    # Create sale lines
    for line_data in sale_data.lines:
        line_total = int(line_data.quantity * line_data.unit_price)
        line_tax = int(line_total * float(line_data.tax_rate) / 100)

        line = models.SaleLine(
            sale_id=sale.id,
            product_id=line_data.product_id,
            product_code=line_data.product_code,
            product_name=line_data.product_name,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_total,
            tax_rate=line_data.tax_rate,
            tax_amount=line_tax
        )
        db.add(line)

    db.commit()
    db.refresh(sale)

    # Publish sale.created event (triggers stock decrement and ledger posting)
    if event_publisher:
        event_publisher.publish_event(
            "sale.created",
            {
                "sale_id": str(sale.id),
                "sale_number": sale.sale_number,
                "customer_id": str(sale.customer_id),
                "sale_date": sale.sale_date,
                "total_ht": sale.subtotal,
                "total_amount": sale.total_amount,
                "tax_amount": sale.tax_amount,
                "lines": [
                    {
                        "product_id": str(line.product_id),
                        "product_code": line.product_code,
                        "quantity": float(line.quantity),
                        "unit_price": line.unit_price,
                        "line_total": line.line_total,
                        "tax_amount": line.tax_amount
                    }
                    for line in sale.lines
                ]
            },
            correlation_id=correlation_id,
            idempotency_key=sale_data.idempotency_key
        )

    logger.info(
        "Sale created",
        sale_id=str(sale.id),
        sale_number=sale.sale_number,
        correlation_id=correlation_id,
        status="PENDING"
    )

    return SaleResponse.model_validate(sale)


@app.get("/api/v1/sales", response_model=List[SaleResponse])
async def list_sales(
    customer_id: Optional[UUID] = None,
    status: Optional[models.SaleStatus] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List sales with filters"""
    query = db.query(models.Sale)

    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if status:
        query = query.filter_by(status=status)
    if from_date:
        query = query.filter(models.Sale.sale_date >= from_date)
    if to_date:
        query = query.filter(models.Sale.sale_date <= to_date)

    sales = query.order_by(models.Sale.created_at.desc()).offset(skip).limit(limit).all()
    return [SaleResponse.model_validate(s) for s in sales]


@app.get("/api/v1/sales/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sale by ID"""
    sale = db.query(models.Sale).filter_by(id=sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return SaleResponse.model_validate(sale)


# ============================================
# Payment Endpoints
# ============================================

@app.post("/api/v1/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    payment_data: PaymentCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE, Roles.COMPTABLE])),
    db: Session = Depends(get_db)
):
    """Record a payment for a sale"""
    # Validate sale exists
    sale = db.query(models.Sale).filter_by(id=payment_data.sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    # Idempotency check
    if payment_data.idempotency_key:
        existing = db.query(models.Payment).filter_by(
            idempotency_key=payment_data.idempotency_key
        ).first()
        if existing:
            logger.warning("Duplicate payment ignored", idempotency_key=payment_data.idempotency_key)
            return PaymentResponse.model_validate(existing)

    # Create payment
    payment = models.Payment(
        sale_id=payment_data.sale_id,
        payment_date=payment_data.payment_date,
        payment_method=payment_data.payment_method,
        amount=payment_data.amount,
        status=models.PaymentStatus.COMPLETED,  # Simple flow - mark as completed
        transaction_reference=payment_data.transaction_reference,
        receipt_number=payment_data.receipt_number,
        notes=payment_data.notes,
        processed_by_user_id=UUID(current_user.user_id),
        idempotency_key=payment_data.idempotency_key
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Publish payment.recorded event
    if event_publisher:
        event_publisher.publish_event(
            "payment.recorded",
            {
                "payment_id": str(payment.id),
                "sale_id": str(payment.sale_id),
                "amount": payment.amount,
                "payment_method": payment.payment_method.value,
                "payment_date": payment.payment_date,
                "status": payment.status.value
            },
            correlation_id=sale.correlation_id,
            idempotency_key=payment_data.idempotency_key
        )

    logger.info(
        "Payment recorded",
        payment_id=str(payment.id),
        sale_id=str(payment.sale_id),
        amount=payment.amount,
        method=payment.payment_method.value
    )

    return PaymentResponse.model_validate(payment)


@app.get("/api/v1/payments", response_model=List[PaymentResponse])
async def list_payments(
    sale_id: Optional[UUID] = None,
    payment_method: Optional[models.PaymentMethod] = None,
    status: Optional[models.PaymentStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List payments with filters"""
    query = db.query(models.Payment)

    if sale_id:
        query = query.filter_by(sale_id=sale_id)
    if payment_method:
        query = query.filter_by(payment_method=payment_method)
    if status:
        query = query.filter_by(status=status)

    payments = query.order_by(models.Payment.created_at.desc()).offset(skip).limit(limit).all()
    return [PaymentResponse.model_validate(p) for p in payments]


# ============================================
# Event Handlers
# ============================================

def handle_stock_decremented(event: EventEnvelope):
    """Handle stock.decremented event - part of sale confirmation"""
    logger.info("Handling stock.decremented event", event_id=event.event_id)

    try:
        with get_db_session(SessionFactory) as db:
            # Find sale by correlation_id
            sale_id = event.payload.get("reference_id")
            if not sale_id:
                logger.warning("No reference_id in stock.decremented event")
                return

            sale = db.query(models.Sale).filter_by(id=UUID(sale_id)).first()
            if not sale:
                logger.warning("Sale not found", sale_id=sale_id)
                return

            # Check if we already received ledger.posted
            # For simplicity, we'll mark as CONFIRMED when we receive stock.decremented
            # In production, you might want to wait for both events
            if sale.status == models.SaleStatus.PENDING:
                sale.status = models.SaleStatus.CONFIRMED
                db.commit()

                logger.info(
                    "Sale confirmed after stock decrement",
                    sale_id=str(sale.id),
                    sale_number=sale.sale_number
                )
    except Exception as e:
        logger.error("Error handling stock.decremented event", error=str(e))
        raise


def handle_stock_failed(event: EventEnvelope):
    """Handle stock.failed event - insufficient stock"""
    logger.info("Handling stock.failed event", event_id=event.event_id)

    try:
        with get_db_session(SessionFactory) as db:
            sale_id = event.payload.get("reference_id")
            if not sale_id:
                logger.warning("No reference_id in stock.failed event")
                return

            sale = db.query(models.Sale).filter_by(id=UUID(sale_id)).first()
            if not sale:
                logger.warning("Sale not found", sale_id=sale_id)
                return

            if sale.status == models.SaleStatus.PENDING:
                sale.status = models.SaleStatus.REJECTED
                db.commit()

                logger.info(
                    "Sale rejected due to stock failure",
                    sale_id=str(sale.id),
                    sale_number=sale.sale_number,
                    reason=event.payload.get("reason")
                )
    except Exception as e:
        logger.error("Error handling stock.failed event", error=str(e))
        raise


def handle_ledger_posted(event: EventEnvelope):
    """Handle ledger.posted event - accounting entry created"""
    logger.info("Handling ledger.posted event", event_id=event.event_id)

    try:
        with get_db_session(SessionFactory) as db:
            # Extract sale reference from event
            reference_id = event.payload.get("reference_id")
            if not reference_id:
                logger.warning("No reference_id in ledger.posted event")
                return

            # Log for audit trail
            logger.info(
                "Ledger posted for sale",
                reference_id=reference_id,
                entry_id=event.payload.get("entry_id")
            )
    except Exception as e:
        logger.error("Error handling ledger.posted event", error=str(e))
        raise


# ============================================
# Startup/Shutdown
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize service"""
    logger.info("Sales service starting up")
    if event_publisher:
        event_publisher.connect()

    # Setup event consumer
    if RABBITMQ_URL:
        consumer = EventConsumer(RABBITMQ_URL, "sales-service", "sales_queue")
        consumer.connect()
        consumer.register_handler("stock.decremented", handle_stock_decremented)
        consumer.register_handler("stock.failed", handle_stock_failed)
        consumer.register_handler("ledger.posted", handle_ledger_posted)
        app.state.sales_consumer = consumer
        consumer_thread = threading.Thread(target=consumer.start_consuming, daemon=True)
        consumer_thread.start()
        app.state.sales_consumer_thread = consumer_thread


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup"""
    logger.info("Sales service shutting down")
    if event_publisher:
        event_publisher.close()
    if hasattr(app.state, "sales_consumer"):
        app.state.sales_consumer.stop_consuming()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sales-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
