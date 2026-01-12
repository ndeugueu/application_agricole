import os
import pytest

try:
    import httpx
except Exception:
    pytest.skip("httpx not installed", allow_module_level=True)


DEFAULT_TIMEOUT = float(os.getenv("AGRO_HTTP_TIMEOUT", "10"))


def _get_urls():
    return {
        "identity": os.getenv("AGRO_IDENTITY_URL"),
        "farm": os.getenv("AGRO_FARM_URL"),
        "inventory": os.getenv("AGRO_INVENTORY_URL"),
        "sales": os.getenv("AGRO_SALES_URL"),
        "accounting": os.getenv("AGRO_ACCOUNTING_URL"),
        "reporting": os.getenv("AGRO_REPORTING_URL"),
        "bff_mobile": os.getenv("AGRO_BFF_MOBILE_URL"),
        "bff_web": os.getenv("AGRO_BFF_WEB_URL"),
    }


def _request(method, url, token=None, params=None, json=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.request(
        method,
        url,
        headers=headers,
        params=params,
        json=json,
        timeout=DEFAULT_TIMEOUT,
    )


def _login(identity_url, username_env, password_env):
    username = os.getenv(username_env)
    password = os.getenv(password_env)
    if not username or not password:
        pytest.skip(f"{username_env}/{password_env} not set")
    login_url = f"{identity_url}/api/v1/auth/login"
    try:
        res = _request(
            "post",
            login_url,
            json={"username": username, "password": password},
        )
    except Exception as exc:
        pytest.skip(f"Login request failed: {exc}")
    if res.status_code != 200:
        pytest.skip(f"Login failed: {res.status_code} {res.text}")
    data = res.json()
    return data.get("access_token")


def _login_admin(identity_url):
    return _login(identity_url, "AGRO_ADMIN_USER", "AGRO_ADMIN_PASS")


def _login_limited(identity_url):
    return _login(identity_url, "AGRO_LIMITED_USER", "AGRO_LIMITED_PASS")


@pytest.mark.parametrize("service,endpoint", [
    ("identity", "/health"),
    ("farm", "/health"),
    ("inventory", "/health"),
    ("sales", "/health"),
    ("accounting", "/health"),
    ("reporting", "/health"),
    ("bff_mobile", "/health"),
    ("bff_web", "/health"),
])
def test_health_endpoints(service, endpoint):
    urls = _get_urls()
    base = urls.get(service)
    if not base:
        pytest.skip(f"{service} URL not set")
    try:
        res = _request("get", f"{base}{endpoint}")
    except Exception as exc:
        pytest.skip(f"Service not reachable: {exc}")
    assert res.status_code == 200
    if res.headers.get("content-type", "").startswith("application/json"):
        body = res.json()
        assert "status" in body


@pytest.mark.parametrize("service,endpoint", [
    ("identity", "/api/v1/users"),
    ("farm", "/api/v1/farms"),
    ("inventory", "/api/v1/products"),
    ("sales", "/api/v1/customers"),
    ("accounting", "/api/v1/accounts"),
    ("reporting", "/api/v1/reports"),
    ("bff_mobile", "/m/home"),
    ("bff_web", "/w/dashboard"),
])
def test_auth_required(service, endpoint):
    urls = _get_urls()
    base = urls.get(service)
    if not base:
        pytest.skip(f"{service} URL not set")
    try:
        res = _request("get", f"{base}{endpoint}")
    except Exception as exc:
        pytest.skip(f"Service not reachable: {exc}")
    assert res.status_code in (401, 403)


def test_admin_access_smoke():
    urls = _get_urls()
    identity_url = urls.get("identity")
    if not identity_url:
        pytest.skip("Identity URL not set")

    token = _login_admin(identity_url)
    if not token:
        pytest.skip("No token returned")

    checks = [
        ("farm", "/api/v1/farms"),
        ("inventory", "/api/v1/products"),
        ("sales", "/api/v1/customers"),
        ("accounting", "/api/v1/accounts"),
        ("reporting", "/api/v1/reports"),
    ]

    for service, endpoint in checks:
        base = urls.get(service)
        if not base:
            continue
        try:
            res = _request("get", f"{base}{endpoint}", token=token)
        except Exception as exc:
            pytest.skip(f"Service not reachable: {exc}")
        assert res.status_code == 200


def test_admin_access_response_types():
    urls = _get_urls()
    identity_url = urls.get("identity")
    if not identity_url:
        pytest.skip("Identity URL not set")

    token = _login_admin(identity_url)
    if not token:
        pytest.skip("No token returned")

    checks = [
        ("farm", "/api/v1/farms", list),
        ("inventory", "/api/v1/products", list),
        ("sales", "/api/v1/customers", list),
        ("accounting", "/api/v1/accounts", list),
        ("reporting", "/api/v1/reports", list),
        ("bff_mobile", "/m/home", dict),
        ("bff_web", "/w/dashboard", dict),
    ]

    for service, endpoint, expected_type in checks:
        base = urls.get(service)
        if not base:
            continue
        try:
            res = _request("get", f"{base}{endpoint}", token=token)
        except Exception as exc:
            pytest.skip(f"Service not reachable: {exc}")
        assert res.status_code == 200
        if res.headers.get("content-type", "").startswith("application/json"):
            body = res.json()
            assert isinstance(body, expected_type)


def test_limited_user_forbidden_on_admin_endpoints():
    if os.getenv("AGRO_LIMITED_EXPECT_FORBIDDEN") != "1":
        pytest.skip("AGRO_LIMITED_EXPECT_FORBIDDEN not set to 1")

    urls = _get_urls()
    identity_url = urls.get("identity")
    if not identity_url:
        pytest.skip("Identity URL not set")

    token = _login_limited(identity_url)
    if not token:
        pytest.skip("No token returned")

    restricted = [
        ("identity", "/api/v1/users"),
        ("farm", "/api/v1/farms"),
        ("inventory", "/api/v1/products"),
        ("sales", "/api/v1/customers"),
        ("accounting", "/api/v1/accounts"),
        ("reporting", "/api/v1/templates"),
    ]

    for service, endpoint in restricted:
        base = urls.get(service)
        if not base:
            continue
        try:
            res = _request("get", f"{base}{endpoint}", token=token)
        except Exception as exc:
            pytest.skip(f"Service not reachable: {exc}")
        assert res.status_code in (401, 403)
