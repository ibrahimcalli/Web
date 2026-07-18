"""Multi-tenant middleware — domain bazlı tenant yönlendirme."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from backend.services.tenant_service import TenantService


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        host = request.headers.get("host", "").split(":")[0]
        request.state.tenant = None
        request.state.tenant_domain = host

        if host and host != "localhost" and host != "127.0.0.1":
            try:
                ts = TenantService()
                tenant = ts.domain_bul(host)
                request.state.tenant = tenant
            except Exception:
                pass

        response = await call_next(request)
        if request.state.tenant:
            response.headers["X-Tenant"] = request.state.tenant.get("firma_adi", "")
        return response
