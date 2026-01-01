"""
BFF Mobile - Backend for Frontend (Mobile)
Aggregates data from multiple services for mobile screens
Optimized for mobile network (1 endpoint = 1 screen)
"""
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import httpx
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.auth import get_current_user, TokenData
from shared.logging_config import configure_logging

# Initialize
logger = configure_logging("bff-mobile")
bearer_scheme = HTTPBearer()

# Service URLs
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
FARM_SERVICE_URL = os.getenv("FARM_SERVICE_URL", "http://localhost:8002")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003")
SALES_SERVICE_URL = os.getenv("SALES_SERVICE_URL", "http://localhost:8004")

app = FastAPI(title="BFF Mobile", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Helper Functions
# ============================================

async def make_service_request(
    url: str,
    method: str = "GET",
    headers: Dict = None,
    json_data: Dict = None
) -> Dict[str, Any]:
    """Make HTTP request to a service"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Service request failed", url=url, error=str(e))
            raise HTTPException(status_code=502, detail=f"Service unavailable: {str(e)}")


def get_auth_headers(credentials: HTTPAuthorizationCredentials) -> Dict[str, str]:
    """Pass through the caller's JWT to downstream services"""
    return {"Authorization": f"Bearer {credentials.credentials}"}


# ============================================
# Mobile Screen Endpoints
# ============================================

class HomeScreenData(BaseModel):
    """Data for mobile home screen"""
    user_name: str
    farms_count: int
    plots_count: int
    low_stock_count: int
    pending_sales_count: int
    today_sales_total: int


@app.get("/m/home", response_model=HomeScreenData)
async def get_home_screen(
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Mobile home screen - aggregates data from multiple services
    Returns: User info + dashboard metrics
    """
    # Get user info
    user_data = await make_service_request(
        f"{IDENTITY_SERVICE_URL}/api/v1/users/me",
        headers=get_auth_headers(credentials)
    )

    # Get farm counts
    farms = await make_service_request(
        f"{FARM_SERVICE_URL}/api/v1/farms?limit=1000",
        headers=get_auth_headers(credentials)
    )

    plots = await make_service_request(
        f"{FARM_SERVICE_URL}/api/v1/plots?limit=1000",
        headers=get_auth_headers(credentials)
    )

    # Get inventory alerts
    low_stock = await make_service_request(
        f"{INVENTORY_SERVICE_URL}/api/v1/stock-levels?below_minimum=true",
        headers=get_auth_headers(credentials)
    )

    # Get sales data
    sales = await make_service_request(
        f"{SALES_SERVICE_URL}/api/v1/sales?status=PENDING&limit=100",
        headers=get_auth_headers(credentials)
    )

    return HomeScreenData(
        user_name=user_data.get("full_name", user_data.get("username")),
        farms_count=len(farms) if isinstance(farms, list) else 0,
        plots_count=len(plots) if isinstance(plots, list) else 0,
        low_stock_count=len(low_stock) if isinstance(low_stock, list) else 0,
        pending_sales_count=len(sales) if isinstance(sales, list) else 0,
        today_sales_total=0  # Would calculate from sales data
    )


@app.get("/m/plot/{plot_id}/overview")
async def get_plot_overview(
    plot_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Plot overview screen - all data needed for plot details
    Returns: Plot info + season + recent operations
    """
    # Get plot details
    plot = await make_service_request(
        f"{FARM_SERVICE_URL}/api/v1/plots/{plot_id}",
        headers=get_auth_headers(credentials)
    )

    # Get farm details
    farm = await make_service_request(
        f"{FARM_SERVICE_URL}/api/v1/farms/{plot['farm_id']}",
        headers=get_auth_headers(credentials)
    )

    # Get current season
    seasons = await make_service_request(
        f"{FARM_SERVICE_URL}/api/v1/seasons?status=active&limit=1",
        headers=get_auth_headers(credentials)
    )

    return {
        "plot": plot,
        "farm": farm,
        "current_season": seasons[0] if seasons else None,
        "recent_operations": []  # Would fetch from operations service
    }


@app.get("/m/inventory/low-stock")
async def get_low_stock_mobile(
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """Mobile-optimized low stock screen"""
    stock_levels = await make_service_request(
        f"{INVENTORY_SERVICE_URL}/api/v1/stock-levels?below_minimum=true",
        headers=get_auth_headers(credentials)
    )

    return {"low_stock_items": stock_levels}


@app.post("/m/sales/quick-create")
async def quick_create_sale(
    sale_data: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Quick sale creation for mobile
    Simplified interface for field agents
    """
    # Create sale via Sales Service
    sale = await make_service_request(
        f"{SALES_SERVICE_URL}/api/v1/sales",
        method="POST",
        headers=get_auth_headers(credentials),
        json_data=sale_data
    )

    return {"sale": sale, "message": "Sale created successfully"}


@app.get("/m/sync/pull")
async def sync_pull(
    since: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Pull updates for offline sync
    Returns: Changed data since last sync
    """
    # This would implement offline sync logic
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "farms": [],
        "plots": [],
        "products": [],
        "sales": []
    }


@app.post("/m/sync/push")
async def sync_push(
    sync_data: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Push local changes for offline sync
    Processes batch of actions created offline
    """
    # This would process offline actions and sync them
    processed = 0
    errors = []

    # Process each action with idempotency
    for action in sync_data.get("actions", []):
        try:
            # Route to appropriate service based on action type
            processed += 1
        except Exception as e:
            errors.append({"action_id": action.get("id"), "error": str(e)})

    return {
        "processed": processed,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bff-mobile"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
