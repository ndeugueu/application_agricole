# Tests (Auth / Health)

These are optional integration tests that hit running services.

Requirements:
- Services running (docker-compose up)
- httpx installed in your Python environment

Environment variables:
- AGRO_IDENTITY_URL
- AGRO_FARM_URL
- AGRO_INVENTORY_URL
- AGRO_SALES_URL
- AGRO_ACCOUNTING_URL
- AGRO_REPORTING_URL
- AGRO_BFF_MOBILE_URL
- AGRO_BFF_WEB_URL
- AGRO_ADMIN_USER
- AGRO_ADMIN_PASS
- AGRO_LIMITED_USER (optional)
- AGRO_LIMITED_PASS (optional)
- AGRO_LIMITED_EXPECT_FORBIDDEN=1 (optional, enables limited-role checks)
- AGRO_HTTP_TIMEOUT (optional, seconds)

Example (PowerShell):
$env:AGRO_IDENTITY_URL = "http://localhost:8001"
$env:AGRO_FARM_URL = "http://localhost:8002"
$env:AGRO_INVENTORY_URL = "http://localhost:8003"
$env:AGRO_SALES_URL = "http://localhost:8004"
$env:AGRO_ACCOUNTING_URL = "http://localhost:8005"
$env:AGRO_REPORTING_URL = "http://localhost:8006"
$env:AGRO_BFF_MOBILE_URL = "http://localhost:8010"
$env:AGRO_BFF_WEB_URL = "http://localhost:8011"
$env:AGRO_ADMIN_USER = "admin"
$env:AGRO_ADMIN_PASS = $env:ADMIN_PASSWORD

pytest -q
