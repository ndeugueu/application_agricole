"""
Farm Service
Farm structure management: Farms, Plots, Seasons, Crop Types
"""
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.database import create_db_engine, get_session_factory, get_db_session, Base
from shared.auth import get_current_user, require_roles, Roles
from shared.logging_config import configure_logging
from shared.events import EventPublisher

import models
from pydantic import BaseModel, ConfigDict

# Initialize logging
logger = configure_logging("farm-service")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_db_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)

# Create tables (dev only; prefer migrations in prod)
if os.getenv("AUTO_CREATE_DB", "true").lower() == "true":
    Base.metadata.create_all(bind=engine)

# Event publisher
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
event_publisher = EventPublisher(RABBITMQ_URL, "farm-service") if RABBITMQ_URL else None

# FastAPI app
app = FastAPI(
    title="Farm Service",
    description="Farm structure management microservice",
    version="1.0.0"
)


# Dependency to get database session
def get_db():
    with get_db_session(SessionFactory) as session:
        yield session


# ============================================
# Schemas
# ============================================

class FarmCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    location: Optional[str] = None
    total_area: Optional[Decimal] = None
    owner_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    total_area: Optional[Decimal] = None
    owner_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: Optional[bool] = None


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    description: Optional[str]
    location: Optional[str]
    total_area: Optional[Decimal]
    owner_name: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    is_active: bool
    created_at: datetime


class PlotCreate(BaseModel):
    farm_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    area: Decimal
    soil_type: Optional[str] = None
    irrigation_available: bool = False
    crop_type_id: Optional[UUID] = None
    current_season_id: Optional[UUID] = None


class PlotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    area: Optional[Decimal] = None
    soil_type: Optional[str] = None
    irrigation_available: Optional[bool] = None
    crop_type_id: Optional[UUID] = None
    current_season_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class PlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    code: str
    name: str
    description: Optional[str]
    area: Decimal
    soil_type: Optional[str]
    irrigation_available: bool
    crop_type_id: Optional[UUID]
    current_season_id: Optional[UUID]
    is_active: bool
    created_at: datetime


class SeasonCreate(BaseModel):
    farm_id: UUID
    name: str
    code: str
    description: Optional[str] = None
    year: int
    season_number: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "planned"


class SeasonUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class SeasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    name: str
    code: str
    description: Optional[str]
    year: int
    season_number: Optional[int]
    start_date: Optional[str]
    end_date: Optional[str]
    status: str
    is_active: bool
    created_at: datetime


class CropTypeCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    typical_yield_per_ha: Optional[Decimal] = None
    typical_cycle_days: Optional[int] = None
    unit: str = "kg"


class CropTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    typical_yield_per_ha: Optional[Decimal] = None
    typical_cycle_days: Optional[int] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None


class CropTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str]
    category: Optional[str]
    typical_yield_per_ha: Optional[Decimal]
    typical_cycle_days: Optional[int]
    unit: str
    is_active: bool
    created_at: datetime


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Farm service starting up")
    if event_publisher:
        event_publisher.connect()

    # Create default crop types
    with get_db_session(SessionFactory) as db:
        create_default_crop_types(db)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Farm service shutting down")
    if event_publisher:
        event_publisher.close()


def create_default_crop_types(db: Session):
    """Create default crop types reference data"""
    default_crops = [
        {
            "code": "MAIS",
            "name": "Maïs",
            "category": "cereals",
            "typical_yield_per_ha": Decimal("3000"),
            "typical_cycle_days": 120,
            "unit": "kg"
        },
        {
            "code": "RIZ",
            "name": "Riz",
            "category": "cereals",
            "typical_yield_per_ha": Decimal("4000"),
            "typical_cycle_days": 150,
            "unit": "kg"
        },
        {
            "code": "TOMATE",
            "name": "Tomate",
            "category": "vegetables",
            "typical_yield_per_ha": Decimal("25000"),
            "typical_cycle_days": 90,
            "unit": "kg"
        },
        {
            "code": "MANIOC",
            "name": "Manioc",
            "category": "tubers",
            "typical_yield_per_ha": Decimal("15000"),
            "typical_cycle_days": 300,
            "unit": "kg"
        },
        {
            "code": "HARICOT",
            "name": "Haricot",
            "category": "legumes",
            "typical_yield_per_ha": Decimal("1500"),
            "typical_cycle_days": 75,
            "unit": "kg"
        },
    ]

    for crop_data in default_crops:
        existing = db.query(models.CropType).filter_by(code=crop_data["code"]).first()
        if not existing:
            crop = models.CropType(**crop_data)
            db.add(crop)

    db.commit()


# ============================================
# Farm Endpoints
# ============================================

@app.post("/api/v1/farms", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Create a new farm"""
    # Check if code already exists
    if db.query(models.Farm).filter_by(code=farm_data.code).first():
        raise HTTPException(status_code=400, detail="Farm code already exists")

    farm = models.Farm(**farm_data.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)

    # Publish event
    if event_publisher:
        event_publisher.publish_event(
            "farm.created",
            {"farm_id": str(farm.id), "code": farm.code, "name": farm.name}
        )

    logger.info("Farm created", farm_id=str(farm.id), code=farm.code)
    return FarmResponse.model_validate(farm)


@app.get("/api/v1/farms", response_model=List[FarmResponse])
async def list_farms(
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all farms"""
    query = db.query(models.Farm).filter_by(is_active=is_active)
    farms = query.offset(skip).limit(limit).all()
    return [FarmResponse.model_validate(farm) for farm in farms]


@app.get("/api/v1/farms/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get farm by ID"""
    farm = db.query(models.Farm).filter_by(id=farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return FarmResponse.model_validate(farm)


@app.put("/api/v1/farms/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: UUID,
    farm_data: FarmUpdate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Update a farm"""
    farm = db.query(models.Farm).filter_by(id=farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Update fields
    update_data = farm_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(farm, field, value)

    db.commit()
    db.refresh(farm)

    logger.info("Farm updated", farm_id=str(farm.id))
    return FarmResponse.model_validate(farm)


@app.delete("/api/v1/farms/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farm(
    farm_id: UUID,
    current_user=Depends(require_roles([Roles.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a farm (soft delete)"""
    farm = db.query(models.Farm).filter_by(id=farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm.is_active = False
    db.commit()

    logger.info("Farm deleted", farm_id=str(farm.id))
    return None


# ============================================
# Plot Endpoints
# ============================================

@app.post("/api/v1/plots", response_model=PlotResponse, status_code=status.HTTP_201_CREATED)
async def create_plot(
    plot_data: PlotCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE, Roles.AGENT_TERRAIN])),
    db: Session = Depends(get_db)
):
    """Create a new plot"""
    # Verify farm exists
    farm = db.query(models.Farm).filter_by(id=plot_data.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Check if code exists for this farm
    existing = db.query(models.Plot).filter_by(
        farm_id=plot_data.farm_id,
        code=plot_data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plot code already exists for this farm")

    plot = models.Plot(**plot_data.model_dump())
    db.add(plot)
    db.commit()
    db.refresh(plot)

    # Publish event
    if event_publisher:
        event_publisher.publish_event(
            "plot.created",
            {
                "plot_id": str(plot.id),
                "farm_id": str(plot.farm_id),
                "code": plot.code,
                "name": plot.name,
                "area": float(plot.area)
            }
        )

    logger.info("Plot created", plot_id=str(plot.id), farm_id=str(farm.id))
    return PlotResponse.model_validate(plot)


@app.get("/api/v1/plots", response_model=List[PlotResponse])
async def list_plots(
    farm_id: Optional[UUID] = None,
    crop_type_id: Optional[UUID] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List plots"""
    query = db.query(models.Plot).filter_by(is_active=is_active)

    if farm_id:
        query = query.filter_by(farm_id=farm_id)
    if crop_type_id:
        query = query.filter_by(crop_type_id=crop_type_id)

    plots = query.offset(skip).limit(limit).all()
    return [PlotResponse.model_validate(plot) for plot in plots]


@app.get("/api/v1/plots/{plot_id}", response_model=PlotResponse)
async def get_plot(
    plot_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get plot by ID"""
    plot = db.query(models.Plot).filter_by(id=plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    return PlotResponse.model_validate(plot)


@app.put("/api/v1/plots/{plot_id}", response_model=PlotResponse)
async def update_plot(
    plot_id: UUID,
    plot_data: PlotUpdate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE, Roles.AGENT_TERRAIN])),
    db: Session = Depends(get_db)
):
    """Update a plot"""
    plot = db.query(models.Plot).filter_by(id=plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    # Update fields
    update_data = plot_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plot, field, value)

    db.commit()
    db.refresh(plot)

    logger.info("Plot updated", plot_id=str(plot.id))
    return PlotResponse.model_validate(plot)


@app.delete("/api/v1/plots/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plot(
    plot_id: UUID,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Delete a plot (soft delete)"""
    plot = db.query(models.Plot).filter_by(id=plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    plot.is_active = False
    db.commit()

    logger.info("Plot deleted", plot_id=str(plot.id))
    return None


# ============================================
# Season/Campaign Endpoints
# ============================================

@app.post("/api/v1/seasons", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
async def create_season(
    season_data: SeasonCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Create a new season/campaign"""
    # Verify farm exists
    farm = db.query(models.Farm).filter_by(id=season_data.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Check if code exists for this farm
    existing = db.query(models.Season).filter_by(
        farm_id=season_data.farm_id,
        code=season_data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Season code already exists for this farm")

    season = models.Season(**season_data.model_dump())
    db.add(season)
    db.commit()
    db.refresh(season)

    # Publish event
    if event_publisher:
        event_publisher.publish_event(
            "season.created",
            {
                "season_id": str(season.id),
                "farm_id": str(season.farm_id),
                "code": season.code,
                "name": season.name,
                "year": season.year
            }
        )

    logger.info("Season created", season_id=str(season.id), farm_id=str(farm.id))
    return SeasonResponse.model_validate(season)


@app.get("/api/v1/seasons", response_model=List[SeasonResponse])
async def list_seasons(
    farm_id: Optional[UUID] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List seasons"""
    query = db.query(models.Season).filter_by(is_active=is_active)

    if farm_id:
        query = query.filter_by(farm_id=farm_id)
    if year:
        query = query.filter_by(year=year)
    if status:
        query = query.filter_by(status=status)

    seasons = query.offset(skip).limit(limit).all()
    return [SeasonResponse.model_validate(season) for season in seasons]


@app.get("/api/v1/seasons/{season_id}", response_model=SeasonResponse)
async def get_season(
    season_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get season by ID"""
    season = db.query(models.Season).filter_by(id=season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    return SeasonResponse.model_validate(season)


@app.put("/api/v1/seasons/{season_id}", response_model=SeasonResponse)
async def update_season(
    season_id: UUID,
    season_data: SeasonUpdate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Update a season"""
    season = db.query(models.Season).filter_by(id=season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # Update fields
    update_data = season_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(season, field, value)

    db.commit()
    db.refresh(season)

    logger.info("Season updated", season_id=str(season.id))
    return SeasonResponse.model_validate(season)


@app.delete("/api/v1/seasons/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_season(
    season_id: UUID,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Delete a season (soft delete)"""
    season = db.query(models.Season).filter_by(id=season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    season.is_active = False
    db.commit()

    logger.info("Season deleted", season_id=str(season.id))
    return None


# ============================================
# Crop Type Endpoints
# ============================================

@app.post("/api/v1/crop-types", response_model=CropTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_crop_type(
    crop_data: CropTypeCreate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Create a new crop type"""
    # Check if code already exists
    if db.query(models.CropType).filter_by(code=crop_data.code).first():
        raise HTTPException(status_code=400, detail="Crop type code already exists")

    crop_type = models.CropType(**crop_data.model_dump())
    db.add(crop_type)
    db.commit()
    db.refresh(crop_type)

    logger.info("Crop type created", crop_type_id=str(crop_type.id), code=crop_type.code)
    return CropTypeResponse.model_validate(crop_type)


@app.get("/api/v1/crop-types", response_model=List[CropTypeResponse])
async def list_crop_types(
    category: Optional[str] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List crop types"""
    query = db.query(models.CropType).filter_by(is_active=is_active)

    if category:
        query = query.filter_by(category=category)

    crop_types = query.offset(skip).limit(limit).all()
    return [CropTypeResponse.model_validate(ct) for ct in crop_types]


@app.get("/api/v1/crop-types/{crop_type_id}", response_model=CropTypeResponse)
async def get_crop_type(
    crop_type_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get crop type by ID"""
    crop_type = db.query(models.CropType).filter_by(id=crop_type_id).first()
    if not crop_type:
        raise HTTPException(status_code=404, detail="Crop type not found")
    return CropTypeResponse.model_validate(crop_type)


@app.put("/api/v1/crop-types/{crop_type_id}", response_model=CropTypeResponse)
async def update_crop_type(
    crop_type_id: UUID,
    crop_data: CropTypeUpdate,
    current_user=Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Update a crop type"""
    crop_type = db.query(models.CropType).filter_by(id=crop_type_id).first()
    if not crop_type:
        raise HTTPException(status_code=404, detail="Crop type not found")

    # Update fields
    update_data = crop_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(crop_type, field, value)

    db.commit()
    db.refresh(crop_type)

    logger.info("Crop type updated", crop_type_id=str(crop_type.id))
    return CropTypeResponse.model_validate(crop_type)


@app.delete("/api/v1/crop-types/{crop_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crop_type(
    crop_type_id: UUID,
    current_user=Depends(require_roles([Roles.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a crop type (soft delete)"""
    crop_type = db.query(models.CropType).filter_by(id=crop_type_id).first()
    if not crop_type:
        raise HTTPException(status_code=404, detail="Crop type not found")

    crop_type.is_active = False
    db.commit()

    logger.info("Crop type deleted", crop_type_id=str(crop_type.id))
    return None


# ============================================
# Health Check
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "farm-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
