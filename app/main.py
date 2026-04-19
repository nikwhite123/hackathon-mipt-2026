"""FastAPI application: prediction, threat catalog, stats, vulnerability mapping, auth, organization settings."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from sqlalchemy.orm import Session

from starlette import status

from app.api.auth import router as auth_router
from app.auth.dependencies import get_current_user
from app.core.logging_setup import setup_logging
from app.core.settings import settings
from app.middleware.request_id import RequestIdMiddleware
from app.db.session import get_db
from app.db.startup import run_database_startup
from app.dependencies import (
    get_organization_settings_service,
    get_prediction_service,
    get_stats_service,
    get_threat_catalog_service,
    get_vulnerability_mapping_service,
)
from app.models import Organization, User
from app.schemas import (
    ErrorResponse,
    OrganizationSettingsRequest,
    OrganizationSettingsResponse,
    PredictMethodResponse,
    PredictRecommendationsResponse,
    PredictRequest,
    PredictResponse,
    PredictTargetResponse,
    PredictTimeResponse,
    SeasonType,
    Severity,
    StatsFacetsResponse,
    ThreatFilter,
    ThreatListResponse,
    ThreatMethod,
    ThreatStats,
    TimeOfDay,
    VulnerabilityMapRequest,
    VulnerabilityMapResponse,
)
from app.services.prediction_service import PredictionService
from app.services.access_control_service import AccessControlService
from app.services.organization_settings_service import OrganizationSettingsService
from app.services.stats_service import StatsService
from app.services.threat_catalog_service import ThreatCatalogService
from app.services.vulnerability_mapping_service import VulnerabilityMappingService

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Run Alembic migrations and seeds per RUN_MIGRATIONS_ON_START / RUN_SEED_ON_START."""
    run_database_startup()
    yield


app = FastAPI(
    title="Rostelecom Threat Analytics API",
    version="3.0.0",
    summary="Cyber threat prediction, threat catalog, vulnerability mapping, and organization analytics.",
    description=(
        "REST API for the analytics app: attack prediction, threat catalog, protection recommendations, "
        "vulnerability mapping, user registration, and JWT auth. "
        "Swagger: /docs, OpenAPI JSON: /openapi.json."
    ),
    contact={'name': 'Project Team', 'email': 'team@example.com'},
    license_info={'name': 'MIPT'},
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost', 'http://127.0.0.1'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(RequestIdMiddleware)

app.include_router(auth_router)


def _request_id(request: Request) -> str | None:
    """Return the request correlation id set by RequestIdMiddleware, if any."""
    return getattr(request.state, "request_id", None)


def _error_payload(detail: str, *, request: Request, errors: list | None = None, code: str | None = None) -> dict:
    """Build a JSON-serializable error body aligned with ErrorResponse."""
    body = ErrorResponse(
        detail=detail,
        errors=errors,
        request_id=_request_id(request),
        code=code,
    )
    return body.model_dump(exclude_none=True) if hasattr(body, "model_dump") else body.dict(exclude_none=True)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    raw_errors = exc.errors()
    logger.warning("Validation error: %s", raw_errors)
    safe_errors = jsonable_encoder(raw_errors)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_payload(
            "Validation error",
            request=request,
            errors=safe_errors,
            code="validation_error",
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP errors in the same JSON shape as validation errors."""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    code = f"http_{exc.status_code}"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(detail, request=request, code=code),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload("Internal server error", request=request, code="internal_error"),
    )


@app.get("/health", tags=["system"])
def healthcheck():
    """Liveness probe: process is up (no DB check)."""
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
def readiness(db: Session = Depends(get_db)):
    """Readiness probe: database connectivity for orchestrators and alerts."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": {"database": {"ok": False}}},
        )
    return {"status": "ready", "checks": {"database": {"ok": True}}}


@app.post(
    "/predict",
    tags=["prediction"],
    response_model=PredictResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Full attack prediction",
)
def predict(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Full prediction: risk score, time window, method, target, recommendations, and rationale."""
    scoped, organization_code = _prepare_prediction_request(payload, current_user, db)
    logger.info("Prediction request received for organization_code=%s", organization_code)
    return service.predict(scoped, db=db)


@app.post(
    "/predict/time",
    tags=["prediction"],
    response_model=PredictTimeResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Predict attack time window",
)
def predict_time(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Predicted attack time window and confidence (subset of full prediction)."""
    scoped, organization_code = _prepare_prediction_request(payload, current_user, db)
    logger.info("Time prediction requested for organization_code=%s", organization_code)
    return service.predict_time(scoped, db=db)


@app.post(
    "/predict/target",
    tags=["prediction"],
    response_model=PredictTargetResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Predict attack target",
)
def predict_target(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Predicted target asset type and confidence."""
    scoped, organization_code = _prepare_prediction_request(payload, current_user, db)
    logger.info("Target prediction requested for organization_code=%s", organization_code)
    return service.predict_target(scoped, db=db)


@app.post(
    "/predict/method",
    tags=["prediction"],
    response_model=PredictMethodResponse,
    responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}, 422: {'model': ErrorResponse}},
    summary="Predict attack method",
)
def predict_method(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Predicted attack method and confidence."""
    scoped, organization_code = _prepare_prediction_request(payload, current_user, db)
    logger.info("Method prediction requested for organization_code=%s", organization_code)
    return service.predict_method(scoped, db=db)


@app.post(
    "/predict/recommendations",
    tags=["prediction"],
    response_model=PredictRecommendationsResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Protection recommendations for the predicted threat",
)
def predict_recommendations(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Protection recommendations for the predicted scenario (no full risk payload)."""
    scoped, organization_code = _prepare_prediction_request(payload, current_user, db)
    logger.info("Recommendations request received for organization_code=%s", organization_code)
    return service.get_recommendations(scoped, db=db)


@app.get(
    "/threats",
    tags=["threats"],
    response_model=ThreatListResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Threat list from the catalog (reference registry)",
)
def get_threats(
    severity: Severity | None = Query(default=None, description="Filter by severity"),
    category: str | None = Query(default=None, description="Filter by threat category"),
    service: ThreatCatalogService = Depends(get_threat_catalog_service),
):
    """Reference threat catalog with optional severity/category filters."""
    logger.info("Threat list requested with severity=%s category=%s", severity, category)
    return service.list_threats(ThreatFilter(severity=severity, category=category))


@app.get(
    "/stats",
    tags=["analytics"],
    response_model=ThreatStats,
    responses={401: {"model": ErrorResponse}},
    summary="Incident aggregates for the current user's organization",
)
def get_stats(
    service: StatsService = Depends(get_stats_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    season: SeasonType | None = Query(default=None, description="Filter by season (incidents.season)"),
    attack_method: ThreatMethod | None = Query(
        default=None,
        description="Filter by classified attack method (not a raw SQL column)",
    ),
    region: str | None = Query(default=None, max_length=255, description="Exact match incidents.region"),
    industry: str | None = Query(default=None, max_length=128, description="Exact match incidents.industry"),
    success: int | None = Query(default=None, ge=0, le=1, description="incidents.success"),
    time_of_day: TimeOfDay | None = Query(default=None, description="incidents.time_of_day"),
    date_from: date | None = Query(default=None, description="incidents.incident_date >= date_from"),
    date_to: date | None = Query(default=None, description="incidents.incident_date <= date_to (end of day)"),
    threat_code: int | None = Query(default=None, ge=1, description="incidents.threat_code"),
):
    """Aggregated incident statistics for the JWT user's organization."""
    organization = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if organization is None or not organization.code:
        logger.warning("Stats requested for unavailable organization_id=%s", current_user.organization_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization access is unavailable")
    logger.info(
        "Stats requested for organization_id=%s filters season=%s region=%s industry=%s",
        current_user.organization_id,
        season,
        region,
        industry,
    )
    return service.build_stats(
        organization_code=organization.code if organization else None,
        season=season,
        attack_method=attack_method,
        region=region,
        industry=industry,
        success=success,
        time_of_day=time_of_day,
        date_from=date_from,
        date_to=date_to,
        threat_code=threat_code,
        db=db,
    )


@app.get(
    "/stats/facets",
    tags=["analytics"],
    response_model=StatsFacetsResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Distinct region and industry for the organization (UI filters)",
)
def get_stats_facets(
    service: StatsService = Depends(get_stats_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Distinct region and industry values for dashboard filters."""
    organization = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if organization is None:
        return StatsFacetsResponse(regions=[], industries=[])
    regions, industries = service.incident_facets(organization.code, db)
    return StatsFacetsResponse(regions=regions, industries=industries)


@app.get(
    "/org/settings",
    tags=["organization"],
    response_model=OrganizationSettingsResponse | None,
    responses={401: {"model": ErrorResponse}},
    summary="Get current organization settings",
)
def get_organization_settings(
    service: OrganizationSettingsService = Depends(get_organization_settings_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Load persisted infrastructure settings for the current organization."""
    return service.get_for_user(current_user, db)


@app.post(
    "/org/settings",
    tags=["organization"],
    response_model=OrganizationSettingsResponse,
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Upsert current organization settings",
)
def save_organization_settings(
    payload: OrganizationSettingsRequest,
    service: OrganizationSettingsService = Depends(get_organization_settings_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update infrastructure settings for the current organization."""
    logger.info("Organization settings update requested for organization_id=%s", current_user.organization_id)
    return service.upsert_for_user(payload, current_user, db)


@app.post(
    "/vulnerabilities/map",
    tags=["early-warning"],
    response_model=VulnerabilityMapResponse,
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Map infrastructure vulnerabilities to threats",
)
def map_vulnerabilities_to_threats(
    payload: VulnerabilityMapRequest,
    service: VulnerabilityMappingService = Depends(get_vulnerability_mapping_service),
    current_user: User = Depends(get_current_user),
):
    """Map reported vulnerabilities to catalog threats and recommended actions."""
    logger.info(
        "Vulnerability mapping requested for organization_id=%s, vulnerabilities=%s",
        current_user.organization_id,
        len(payload.vulnerabilities),
    )
    return service.map_vulnerabilities(payload)


if settings.enable_metrics:
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator(should_group_status_codes=True).instrument(app).expose(app, include_in_schema=False)


access_control_service = AccessControlService()


def _ensure_user_has_access(payload: PredictRequest, current_user: User, db: Session) -> str:
    """Ensure body organization_id matches the user's organization; return canonical organization code."""
    return access_control_service.ensure_prediction_access(payload, current_user, db)


def _scoped_predict_request(payload: PredictRequest, organization_code: str) -> PredictRequest:
    """Return a copy of the request with server-scoped organization_id after access checks."""
    if hasattr(payload, 'model_copy'):
        return payload.model_copy(update={'organization_id': organization_code})
    return payload.copy(update={'organization_id': organization_code})


def _prepare_prediction_request(
    payload: PredictRequest,
    current_user: User,
    db: Session,
) -> tuple[PredictRequest, str]:
    """Validate access, scope organization_id, and return (scoped_payload, canonical_code) for logging."""
    organization_code = _ensure_user_has_access(payload, current_user, db)
    scoped = _scoped_predict_request(payload, organization_code)
    return scoped, organization_code
