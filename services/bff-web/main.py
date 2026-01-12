"""
BFF Web - Backend for Frontend (Web Admin)
Aggregates data from multiple services for web dashboards
Optimized for admin/back-office use
"""
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
import httpx
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.auth import get_current_user, require_roles, TokenData, Roles
from shared.logging_config import configure_logging

# Initialize
logger = configure_logging("bff-web")
bearer_scheme = HTTPBearer()

# Service URLs
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
FARM_SERVICE_URL = os.getenv("FARM_SERVICE_URL", "http://localhost:8002")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003")
SALES_SERVICE_URL = os.getenv("SALES_SERVICE_URL", "http://localhost:8004")
ACCOUNTING_SERVICE_URL = os.getenv("ACCOUNTING_SERVICE_URL", "http://localhost:8005")
REPORTING_SERVICE_URL = os.getenv("REPORTING_SERVICE_URL", "http://localhost:8006")

app = FastAPI(title="BFF Web", version="1.0.0")


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
    async with httpx.AsyncClient(timeout=15.0) as client:
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
# Dashboard Endpoints
# ============================================

class DashboardData(BaseModel):
    """Complete dashboard data"""
    summary: Dict[str, Any]
    recent_sales: List[Dict[str, Any]]
    low_stock_items: List[Dict[str, Any]]
    tva_summary: Dict[str, Any]
    sales_chart: List[Dict[str, Any]]


@app.get("/w/dashboard", response_model=DashboardData)
async def get_dashboard(
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Complete web dashboard with aggregated data from all services
    """
    # Get dashboard summary from reporting service
    try:
        summary = await make_service_request(
            f"{REPORTING_SERVICE_URL}/api/v1/dashboard",
            headers=get_auth_headers(credentials)
        )
    except:
        summary = {"sales_today": 0, "sales_month": 0, "inventory_value": 0}

    # Get recent sales
    try:
        sales = await make_service_request(
            f"{SALES_SERVICE_URL}/api/v1/sales?limit=10",
            headers=get_auth_headers(credentials)
        )
        recent_sales = sales if isinstance(sales, list) else []
    except:
        recent_sales = []

    # Get low stock items
    try:
        low_stock = await make_service_request(
            f"{INVENTORY_SERVICE_URL}/api/v1/stock-levels?below_minimum=true&limit=10",
            headers=get_auth_headers(credentials)
        )
        low_stock_items = low_stock if isinstance(low_stock, list) else []
    except:
        low_stock_items = []

    # Get TVA summary (current month)
    try:
        tva_data = await make_service_request(
            f"{ACCOUNTING_SERVICE_URL}/api/v1/reports/tva/monthly",
            headers=get_auth_headers(credentials)
        )
        current_month = datetime.now().strftime("%Y%m")
        tva_summary = next((t for t in tva_data if t.get("fiscal_month") == current_month), {})
    except:
        tva_summary = {}

    return DashboardData(
        summary=summary,
        recent_sales=recent_sales,
        low_stock_items=low_stock_items,
        tva_summary=tva_summary,
        sales_chart=[]  # Would calculate from sales data
    )


@app.get("/w/inventory/overview")
async def get_inventory_overview(
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Inventory overview for web admin
    Returns: Stock levels + alerts + valuation
    """
    # Get all stock levels
    stock_levels = await make_service_request(
        f"{INVENTORY_SERVICE_URL}/api/v1/stock-levels",
        headers=get_auth_headers(credentials)
    )

    # Get recent movements
    movements = await make_service_request(
        f"{INVENTORY_SERVICE_URL}/api/v1/stock-movements?limit=50",
        headers=get_auth_headers(credentials)
    )

    # Calculate inventory value
    total_value = 0
    if isinstance(stock_levels, list):
        for item in stock_levels:
            # Would multiply stock by unit cost
            total_value += 0

    return {
        "stock_levels": stock_levels,
        "recent_movements": movements,
        "total_value": total_value,
        "alerts_count": len([s for s in stock_levels if s.get("is_below_minimum")]) if isinstance(stock_levels, list) else 0
    }


@app.get("/w/sales/analytics")
async def get_sales_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: TokenData = Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE, Roles.COMPTABLE])),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Sales analytics for web admin
    Returns: Sales trends, top customers, top products
    """
    # Build query params
    params = {}
    if start_date:
        params["from_date"] = start_date.isoformat()
    if end_date:
        params["to_date"] = end_date.isoformat()

    # Get sales data
    sales = await make_service_request(
        f"{SALES_SERVICE_URL}/api/v1/sales?" + "&".join([f"{k}={v}" for k, v in params.items()]),
        headers=get_auth_headers(credentials)
    )

    # Analyze sales data
    total_sales = len(sales) if isinstance(sales, list) else 0
    total_amount = sum([s.get("total_amount", 0) for s in sales]) if isinstance(sales, list) else 0

    return {
        "total_sales": total_sales,
        "total_amount": total_amount,
        "average_sale": total_amount / total_sales if total_sales > 0 else 0,
        "sales_by_day": [],  # Would group by date
        "top_customers": [],  # Would aggregate by customer
        "top_products": []   # Would aggregate by product
    }


@app.get("/w/accounting/overview")
async def get_accounting_overview(
    current_user: TokenData = Depends(require_roles([Roles.ADMIN, Roles.COMPTABLE])),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Accounting overview for web admin
    Returns: Trial balance + TVA + recent entries
    """
    # Get trial balance
    try:
        trial_balance = await make_service_request(
            f"{ACCOUNTING_SERVICE_URL}/api/v1/reports/trial-balance",
            headers=get_auth_headers(credentials)
        )
    except:
        trial_balance = []

    # Get TVA reports
    try:
        tva_reports = await make_service_request(
            f"{ACCOUNTING_SERVICE_URL}/api/v1/reports/tva/monthly",
            headers=get_auth_headers(credentials)
        )
    except:
        tva_reports = []

    # Get recent ledger entries
    try:
        ledger_entries = await make_service_request(
            f"{ACCOUNTING_SERVICE_URL}/api/v1/ledger-entries?limit=20",
            headers=get_auth_headers(credentials)
        )
    except:
        ledger_entries = []

    return {
        "trial_balance": trial_balance,
        "tva_reports": tva_reports,
        "recent_entries": ledger_entries
    }


@app.get("/w/farms/overview")
async def get_farms_overview(
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Farms and plots overview for web admin
    """
    # Get all farms
    farms = await make_service_request(
        f"{FARM_SERVICE_URL}/api/v1/farms",
        headers=get_auth_headers(credentials)
    )

    # Get all plots
    plots = await make_service_request(
        f"{FARM_SERVICE_URL}/api/v1/plots",
        headers=get_auth_headers(credentials)
    )

    # Get active seasons
    seasons = await make_service_request(
        f"{FARM_SERVICE_URL}/api/v1/seasons?status=active",
        headers=get_auth_headers(credentials)
    )

    # Calculate total area
    total_area = sum([f.get("total_area", 0) for f in farms]) if isinstance(farms, list) else 0

    return {
        "farms": farms,
        "plots": plots,
        "seasons": seasons,
        "summary": {
            "total_farms": len(farms) if isinstance(farms, list) else 0,
            "total_plots": len(plots) if isinstance(plots, list) else 0,
            "total_area": total_area,
            "active_seasons": len(seasons) if isinstance(seasons, list) else 0
        }
    }


@app.post("/w/reports/generate")
async def generate_report(
    report_request: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Generate a report (PDF or Excel)
    Delegates to Reporting Service
    """
    report = await make_service_request(
        f"{REPORTING_SERVICE_URL}/api/v1/reports",
        method="POST",
        headers=get_auth_headers(credentials),
        json_data=report_request
    )

    return {"report": report, "message": "Report generation started"}


@app.get("/w/reports")
async def list_reports(
    report_type: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """List generated reports"""
    params = f"?report_type={report_type}" if report_type else ""

    reports = await make_service_request(
        f"{REPORTING_SERVICE_URL}/api/v1/reports{params}",
        headers=get_auth_headers(credentials)
    )

    return {"reports": reports}


@app.get("/w/users/management")
async def get_users_management(
    current_user: TokenData = Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    User management overview
    Returns: All users + roles + permissions
    """
    # Get all users
    users = await make_service_request(
        f"{IDENTITY_SERVICE_URL}/api/v1/users",
        headers=get_auth_headers(credentials)
    )

    # Get all roles
    roles = await make_service_request(
        f"{IDENTITY_SERVICE_URL}/api/v1/roles",
        headers=get_auth_headers(credentials)
    )

    return {
        "users": users,
        "roles": roles,
        "summary": {
            "total_users": len(users) if isinstance(users, list) else 0,
            "total_roles": len(roles) if isinstance(roles, list) else 0
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bff-web"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
