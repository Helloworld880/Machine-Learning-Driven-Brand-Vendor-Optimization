import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import pandas as pd
from pydantic import BaseModel, Field
from sqlalchemy import text

from config.settings import get_settings
from database.db import engine, initialize_database
from database.queries import get_user_by_username
from services.vendor_service import VendorService
from utils.logging_setup import setup_logging
from utils.redis_client import redis_client
from utils.security import verify_password


settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)
api_v1 = APIRouter(prefix="/api/v1")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")
vendor_service = VendorService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VendorRiskPredictionRequest(BaseModel):
    delivery_rate: float = Field(ge=0, le=100)
    quality_score: float = Field(ge=0, le=100)
    cost_efficiency: float = Field(ge=0, le=100)
    on_time_rate: float = Field(ge=0, le=100)
    cost_variance: float
    reliability: float = Field(ge=0, le=100)
    performance_score: float = Field(ge=0, le=100)


@app.on_event("startup")
def startup_init() -> None:
    initialize_database()
    redis_client.get_client().ping()
    vendor_service.risk_model.load()
    logger.info("Startup checks complete")


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            json.dumps(
                {
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "endpoint": request.url.path,
                    "status_code": 500,
                }
            )
        )
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        json.dumps(
            {
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "endpoint": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, _: Exception):
    logger.exception("Unhandled exception for %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


def _redis_safe_client():
    try:
        return redis_client.get_client()
    except Exception as exc:
        logger.critical("Redis unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Service unavailable")


def _enforce_rate_limit(client_key: str) -> None:
    redis_conn = _redis_safe_client()
    script = """
    local current = redis.call('INCR', KEYS[1])
    if current == 1 then
      redis.call('EXPIRE', KEYS[1], ARGV[1])
    end
    return current
    """
    current = redis_conn.eval(script, 1, f"rate_limit:{client_key}", 60)
    if int(current) > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


def _create_token(subject: str, role: str, token_type: str, minutes: int) -> str:
    issued = datetime.now(timezone.utc)
    expire = issued + timedelta(minutes=minutes)
    jti = str(uuid.uuid4())
    payload = {"sub": subject, "role": role, "type": token_type, "jti": jti, "iat": issued, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def _create_access_token(subject: str, role: str) -> str:
    return _create_token(subject=subject, role=role, token_type="access", minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def _create_refresh_token(subject: str, role: str) -> str:
    return _create_token(subject=subject, role=role, token_type="refresh", minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)


def _decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def _is_token_blacklisted(jti: str) -> bool:
    redis_conn = _redis_safe_client()
    return bool(redis_conn.exists(f"blacklist:{jti}"))


def _blacklist_token(jti: str, expires_at_epoch: int) -> None:
    redis_conn = _redis_safe_client()
    ttl = max(int(expires_at_epoch - datetime.now(timezone.utc).timestamp()), 1)
    redis_conn.setex(f"blacklist:{jti}", ttl, "1")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    payload = _decode_token(token)
    jti = str(payload.get("jti"))
    if _is_token_blacklisted(jti):
        raise HTTPException(status_code=401, detail="Token revoked")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"username": username, "role": payload.get("role", "viewer"), "jti": jti}


def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


def _cache_key(prefix: str, payload: dict[str, Any]) -> str:
    hashed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}:{hashed}"


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Vendor Insight 360 API is running"}


@api_v1.post("/login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    _enforce_rate_limit(client_ip)
    user = get_user_by_username(form_data.username)
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not verify_password(form_data.password, str(user["password_hash"])):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    role = str(user.get("role", "viewer"))
    return {
        "access_token": _create_access_token(form_data.username, role),
        "refresh_token": _create_refresh_token(form_data.username, role),
        "token_type": "bearer",
    }


@api_v1.post("/refresh")
def refresh_token(payload: RefreshTokenRequest) -> dict[str, str]:
    decoded = _decode_token(payload.refresh_token)
    jti = str(decoded.get("jti"))
    if _is_token_blacklisted(jti):
        raise HTTPException(status_code=401, detail="Token revoked")
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    username = decoded.get("sub")
    role = decoded.get("role", "viewer")
    return {"access_token": _create_access_token(username, role), "token_type": "bearer"}


@api_v1.post("/logout")
def logout(user: dict[str, Any] = Depends(get_current_user), token: str = Depends(oauth2_scheme)) -> dict[str, str]:
    decoded = _decode_token(token)
    _blacklist_token(str(user["jti"]), int(decoded.get("exp")))
    return {"message": "Logged out"}


@api_v1.get("/vendors")
def list_vendors(
    page: int = 1,
    limit: int = 20,
    _: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if page < 1 or limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")
    data, pagination = vendor_service.get_vendor_kpis(page=page, limit=limit)
    return {"data": data.where(data.notna(), None).to_dict("records"), "pagination": pagination}


@api_v1.get("/vendors/performance")
def vendor_performance(
    page: int = 1,
    limit: int = 20,
    _: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if page < 1 or limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")
    cache_payload = {"page": page, "limit": limit}
    key = _cache_key("vendors:performance", cache_payload)
    try:
        redis_conn = _redis_safe_client()
        cached = redis_conn.get(key)
    except HTTPException:
        cached = None
    if cached:
        return json.loads(cached)

    data, pagination = vendor_service.get_vendor_performance(page=page, limit=limit)
    response = {"data": data.where(data.notna(), None).to_dict("records"), "pagination": pagination}
    try:
        redis_conn = _redis_safe_client()
        redis_conn.setex(key, settings.CACHE_TTL_SECONDS, json.dumps(response))
    except HTTPException:
        logger.error("Caching skipped due to Redis outage")
    return response


@api_v1.get("/vendors/performance/export", response_class=PlainTextResponse)
def export_vendor_performance(
    page: int = 1,
    limit: int = 1000,
    _: dict[str, Any] = Depends(require_admin),
) -> str:
    return vendor_service.export_vendor_performance_csv(page=page, limit=limit)


@api_v1.post("/predict/vendor-risk")
def predict_vendor_risk(
    payload: VendorRiskPredictionRequest,
    _: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    frame = vendor_service._calculate_metrics(pd.DataFrame([payload.model_dump()]))
    prediction = vendor_service.risk_model.predict_risk(frame).iloc[0]
    return {"risk_prediction": str(prediction)}


@app.get("/health")
def health(response: Response) -> dict[str, str]:
    db_state = "connected"
    redis_state = "connected"
    api_state = "ok"
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_state = "disconnected"
        api_state = "degraded"
    try:
        _redis_safe_client().ping()
    except Exception:
        redis_state = "disconnected"
        api_state = "degraded"
    if api_state != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": api_state, "database": db_state, "redis": redis_state}


app.include_router(api_v1)
