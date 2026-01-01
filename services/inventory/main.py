"""
Inventory Service
Stock management with append-only movements pattern
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
import threading
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.database import create_db_engine, get_session_factory, get_db_session, Base
from shared.auth import get_current_user, require_roles, Roles
from shared.logging_config import configure_logging
from shared.events import EventPublisher, EventConsumer, EventEnvelope

import models
from pydantic import BaseModel, ConfigDict
from datetime import datetime

# Initialize
logger = configure_logging("inventory-service")
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_db_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)
Base.metadata.create_all(bind=engine)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
event_publisher = EventPublisher(RABBITMQ_URL, "inventory-service") if RABBITMQ_URL else None

app = FastAPI(title="Inventory Service", version="1.0.0")

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

class ProductCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    product_type: models.ProductType
    unit: str
    min_stock_level: int = 0
    max_stock_level: Optional[int] = None
    unit_cost: Optional[int] = None
    unit_price: Optional[int] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str]
    product_type: models.ProductType
    unit: str
    min_stock_level: int
    max_stock_level: Optional[int]
    unit_cost: Optional[int]
    unit_price: Optional[int]
    is_active: int
    created_at: datetime


class StockMovementCreate(BaseModel):
    product_id: UUID
    movement_type: models.MovementType
    quantity: Decimal
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    idempotency_key: Optional[str] = None


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    movement_type: models.MovementType
    quantity: Decimal
    reference_type: Optional[str]
    reference_id: Optional[UUID]
    notes: Optional[str]
    location: Optional[str]
    created_at: datetime


class StockLevel(BaseModel):
    product_id: UUID
    product_code: str
    product_name: str
    current_stock: Decimal
    unit: str
    min_stock_level: int
    is_below_minimum: bool


# ============================================
# Product Endpoints
# ============================================

@app.post("/api/v1/products", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Create a new product"""
    # Check if code exists
    if db.query(models.Product).filter_by(code=product_data.code).first():
        raise HTTPException(status_code=400, detail="Product code already exists")

    product = models.Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    if event_publisher:
        event_publisher.publish_event(
            "product.created",
            {"product_id": str(product.id), "code": product.code, "name": product.name}
        )

    logger.info("Product created", product_id=str(product.id), code=product.code)
    return ProductResponse.model_validate(product)


@app.get("/api/v1/products", response_model=List[ProductResponse])
async def list_products(
    product_type: Optional[models.ProductType] = None,
    is_active: int = 1,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List products"""
    query = db.query(models.Product).filter_by(is_active=is_active)
    if product_type:
        query = query.filter_by(product_type=product_type)

    products = query.offset(skip).limit(limit).all()
    return [ProductResponse.model_validate(p) for p in products]


@app.get("/api/v1/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get product by ID"""
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)


# ============================================
# Stock Movement Endpoints
# ============================================

@app.post("/api/v1/stock-movements", response_model=StockMovementResponse, status_code=201)
async def create_stock_movement(
    movement_data: StockMovementCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE, Roles.AGENT_TERRAIN])),
    db: Session = Depends(get_db)
):
    """Create a stock movement (append-only)"""
    # Check product exists
    product = db.query(models.Product).filter_by(id=movement_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Idempotency check
    if movement_data.idempotency_key:
        existing = db.query(models.StockMovement).filter_by(
            idempotency_key=movement_data.idempotency_key
        ).first()
        if existing:
            logger.warning("Duplicate movement ignored", idempotency_key=movement_data.idempotency_key)
            return StockMovementResponse.model_validate(existing)

    # Create movement
    movement = models.StockMovement(
        **movement_data.model_dump(),
        user_id=UUID(current_user.user_id)
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)

    # Publish event
    if event_publisher:
        event_publisher.publish_event(
            f"stock.{movement_data.movement_type.value}",
            {
                "movement_id": str(movement.id),
                "product_id": str(movement.product_id),
                "quantity": float(movement.quantity),
                "reference_type": movement.reference_type,
                "reference_id": str(movement.reference_id) if movement.reference_id else None
            }
        )

    logger.info("Stock movement created", movement_id=str(movement.id), product_id=str(product.id))
    return StockMovementResponse.model_validate(movement)


@app.get("/api/v1/stock-movements", response_model=List[StockMovementResponse])
async def list_stock_movements(
    product_id: Optional[UUID] = None,
    movement_type: Optional[models.MovementType] = None,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List stock movements"""
    query = db.query(models.StockMovement)
    if product_id:
        query = query.filter_by(product_id=product_id)
    if movement_type:
        query = query.filter_by(movement_type=movement_type)

    movements = query.order_by(models.StockMovement.created_at.desc()).offset(skip).limit(limit).all()
    return [StockMovementResponse.model_validate(m) for m in movements]


# ============================================
# Stock Level Queries
# ============================================

@app.get("/api/v1/stock-levels", response_model=List[StockLevel])
async def get_stock_levels(
    product_type: Optional[models.ProductType] = None,
    below_minimum: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current stock levels for all products"""
    # Query to calculate current stock from movements
    query = db.query(
        models.Product.id,
        models.Product.code,
        models.Product.name,
        models.Product.unit,
        models.Product.min_stock_level,
        func.coalesce(func.sum(models.StockMovement.quantity), 0).label('current_stock')
    ).outerjoin(
        models.StockMovement,
        models.Product.id == models.StockMovement.product_id
    ).filter(
        models.Product.is_active == 1
    )

    if product_type:
        query = query.filter(models.Product.product_type == product_type)

    query = query.group_by(
        models.Product.id,
        models.Product.code,
        models.Product.name,
        models.Product.unit,
        models.Product.min_stock_level
    )

    results = query.all()

    stock_levels = []
    for row in results:
        is_below = row.current_stock < row.min_stock_level
        if below_minimum and not is_below:
            continue

        stock_levels.append(StockLevel(
            product_id=row.id,
            product_code=row.code,
            product_name=row.name,
            current_stock=Decimal(str(row.current_stock)),
            unit=row.unit,
            min_stock_level=row.min_stock_level,
            is_below_minimum=is_below
        ))

    return stock_levels


@app.get("/api/v1/stock-levels/{product_id}", response_model=StockLevel)
async def get_product_stock_level(
    product_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get stock level for a specific product"""
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    current_stock = db.query(
        func.coalesce(func.sum(models.StockMovement.quantity), 0)
    ).filter(
        models.StockMovement.product_id == product_id
    ).scalar()

    return StockLevel(
        product_id=product.id,
        product_code=product.code,
        product_name=product.name,
        current_stock=Decimal(str(current_stock)),
        unit=product.unit,
        min_stock_level=product.min_stock_level,
        is_below_minimum=current_stock < product.min_stock_level
    )


# ============================================
# Event Handlers
# ============================================

def handle_sale_created(event: EventEnvelope):
    """Handle sale.created event - decrement stock"""
    logger.info("Handling sale.created event", event_id=event.event_id)
    payload = event.payload
    sale_id = payload.get("sale_id")
    lines = payload.get("lines", [])

    if not sale_id or not lines:
        logger.warning("Missing sale_id or lines in sale.created event", event_id=event.event_id)
        return

    with get_db_session(SessionFactory) as db:
        # Validate stock availability
        for line in lines:
            product_id_str = line.get("product_id")
            quantity_raw = line.get("quantity")

            if not product_id_str or quantity_raw is None:
                logger.warning("Missing product info in sale.created event", sale_id=sale_id)
                return

            product_id = UUID(product_id_str)
            quantity = Decimal(str(quantity_raw))
            if quantity <= 0:
                logger.warning("Invalid quantity in sale.created event", sale_id=sale_id, quantity=quantity_raw)
                return

            product = db.query(models.Product).filter_by(id=product_id).first()
            if not product:
                if event_publisher:
                    event_publisher.publish_event(
                        "stock.failed",
                        {"reference_id": sale_id, "reason": "product_not_found", "product_id": product_id_str}
                    )
                return

            current_stock = db.query(
                func.coalesce(func.sum(models.StockMovement.quantity), 0)
            ).filter(
                models.StockMovement.product_id == product_id
            ).scalar()

            if Decimal(str(current_stock)) < quantity:
                if event_publisher:
                    event_publisher.publish_event(
                        "stock.failed",
                        {"reference_id": sale_id, "reason": "insufficient_stock", "product_id": product_id_str}
                    )
                return

        # Create stock movements
        movement_ids = []
        for line in lines:
            product_id = UUID(line["product_id"])
            quantity = Decimal(str(line["quantity"]))
            idempotency_key = f"sale_{sale_id}_{product_id}"

            existing = db.query(models.StockMovement).filter_by(idempotency_key=idempotency_key).first()
            if existing:
                movement_ids.append(str(existing.id))
                continue

            movement = models.StockMovement(
                product_id=product_id,
                movement_type=models.MovementType.SORTIE,
                quantity=-abs(quantity),
                reference_type="sale",
                reference_id=UUID(sale_id),
                notes="Auto-decrement from sale",
                idempotency_key=idempotency_key
            )
            db.add(movement)
            db.flush()
            movement_ids.append(str(movement.id))

        db.commit()

    if event_publisher:
        event_publisher.publish_event(
            "stock.decremented",
            {"reference_id": sale_id, "sale_id": sale_id, "movement_ids": movement_ids}
        )


@app.on_event("startup")
async def startup_event():
    """Initialize service"""
    logger.info("Inventory service starting up")
    if event_publisher:
        event_publisher.connect()

    # Setup event consumer
    if RABBITMQ_URL:
        consumer = EventConsumer(RABBITMQ_URL, "inventory-service", "inventory_queue")
        consumer.connect()
        consumer.register_handler("sale.created", handle_sale_created)
        app.state.inventory_consumer = consumer
        consumer_thread = threading.Thread(target=consumer.start_consuming, daemon=True)
        consumer_thread.start()
        app.state.inventory_consumer_thread = consumer_thread


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup"""
    logger.info("Inventory service shutting down")
    if event_publisher:
        event_publisher.close()
    if hasattr(app.state, "inventory_consumer"):
        app.state.inventory_consumer.stop_consuming()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "inventory-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
