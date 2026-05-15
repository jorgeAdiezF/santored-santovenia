import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from typing import Optional

from shared.config import get_settings
from shared.auth import decode_token

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address)
    SLOWAPI_AVAILABLE = True
except ImportError:
    limiter = None
    SLOWAPI_AVAILABLE = False

settings = get_settings()

app = FastAPI(title="API Gateway", version="1.0.0")

if SLOWAPI_AVAILABLE and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_ROUTES = {
    "/auth": settings.auth_service_url,
    "/users": settings.auth_service_url,
    "/documents": settings.document_service_url,
    "/segmentation": settings.segmentation_service_url,
    "/ocr": settings.ocr_service_url,
    "/materials": settings.materials_service_url,
    "/providers": settings.materials_service_url,
    "/homologation": settings.homologation_service_url,
    "/reviews": settings.review_service_url,
    "/destinations": settings.destinations_service_url,
    "/invoice-lines": settings.destinations_service_url,
    "/invoice-line-destinations": settings.destinations_service_url,
    "/analytics": settings.analytics_service_url,
}

PUBLIC_PATHS = {"/health", "/auth/login", "/docs", "/openapi.json", "/redoc"}


def get_service_url(path: str) -> Optional[str]:
    """Determine which service to route to based on path."""
    for prefix, url in SERVICE_ROUTES.items():
        if path.startswith(prefix):
            return url
    return None


def verify_token(request: Request) -> Optional[dict]:
    """Verify JWT token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = decode_token(token)
        return payload
    except Exception:
        return None


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "api_gateway",
        "services": {
            "auth": settings.auth_service_url,
            "documents": settings.document_service_url,
            "materials": settings.materials_service_url,
            "analytics": settings.analytics_service_url,
        },
    }


@app.api_route(
    "/api/v1/materials",
    methods=["GET"],
)
async def external_list_materials(request: Request):
    """External API: List/search materials."""
    payload = verify_token(request)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.materials_service_url}/materials/search"
        params = dict(request.query_params)
        response = await client.get(
            url,
            params=params,
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)


@app.api_route(
    "/api/v1/materials/{material_id}/last-price",
    methods=["GET"],
)
async def external_last_price(material_id: int, request: Request):
    """External API: Get last price for material."""
    payload = verify_token(request)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.analytics_service_url}/analytics/last-price/{material_id}"
        response = await client.get(
            url,
            params=dict(request.query_params),
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)


@app.api_route(
    "/api/v1/materials/{material_id}/history",
    methods=["GET"],
)
async def external_price_history(material_id: int, request: Request):
    """External API: Get price history for material."""
    payload = verify_token(request)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.analytics_service_url}/analytics/price-history/{material_id}"
        response = await client.get(
            url,
            params=dict(request.query_params),
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)


@app.api_route(
    "/api/v1/providers",
    methods=["GET"],
)
async def external_list_providers(request: Request):
    """External API: List providers."""
    payload = verify_token(request)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.materials_service_url}/providers"
        response = await client.get(
            url,
            params=dict(request.query_params),
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)


@app.api_route(
    "/api/v1/destinations",
    methods=["GET"],
)
async def external_list_destinations(request: Request):
    """External API: List destinations."""
    payload = verify_token(request)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.destinations_service_url}/destinations"
        response = await client.get(
            url,
            params=dict(request.query_params),
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)


@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy(full_path: str, request: Request):
    """Generic proxy for all other routes."""
    path = f"/{full_path}"

    service_url = get_service_url(path)
    if not service_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No service found for path: {path}",
        )

    target_url = f"{service_url}{path}"
    if request.query_params:
        target_url += f"?{request.query_params}"

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers.pop("transfer-encoding", None)
    headers.pop("connection", None)

    try:
        content_type = request.headers.get("content-type", "")
        async with httpx.AsyncClient(timeout=120.0) as client:
            if "multipart/form-data" in content_type:
                form = await request.form()
                fwd_headers = {k: v for k, v in headers.items() if "content-type" not in k.lower()}
                httpx_files = []
                httpx_data = {}
                for key, value in form.multi_items():
                    if hasattr(value, "read"):
                        data = await value.read()
                        httpx_files.append((key, (value.filename, data, value.content_type or "application/octet-stream")))
                    else:
                        httpx_data[key] = str(value)
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=fwd_headers,
                    files=httpx_files or None,
                    data=httpx_data or None,
                )
            else:
                body = await request.body()
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                )
            return JSONResponse(
                content=response.json() if response.content else None,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {service_url}",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Service timeout",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gateway error: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
