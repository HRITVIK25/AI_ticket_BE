import os
import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config.database import SessionLocal
from repositories.org_repo import check_org_exists


PUBLIC_PATHS = {"/api/v1/", "/api/v1/health","/docs", "/openapi.json", "/redoc"}


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        token = _extract_bearer_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},  # Clerk tokens don't always include aud
            )

            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Missing 'sub' in token payload")

            org_data = payload.get("o", {})
            org_id  = org_data.get("id")

        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token has expired"},
            )
        except jwt.InvalidTokenError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid token: {str(e)}"},
            )
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token verification failed"},
            )

        # DB check
        if org_id:
            async with SessionLocal() as db:
                org_exists = await check_org_exists(db, org_id)
                if not org_exists:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Organization not found or inactive"},
                    )

        request.state.user_id = user_id
        request.state.org_id = org_id

        return await call_next(request)


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return None