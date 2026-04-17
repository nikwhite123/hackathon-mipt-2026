from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.repositories.data_repository import get_data_repository
from starlette import status

from app.api.auth import router as auth_router
from app.auth.dependencies import get_current_user
from app.db.base import Base
from app.db.session import engine, get_db
from app.dependencies import (
    get_prediction_service,
    get_stats_service,
    get_threat_catalog_service,
    get_vulnerability_mapping_service,
)
from app.models import Organization, User
from app.schemas import (
    ErrorResponse,
    PredictMethodResponse,
    PredictRecommendationsResponse,
    PredictRequest,
    PredictResponse,
    PredictTargetResponse,
    PredictTimeResponse,
    Severity,
    ThreatFilter,
    ThreatListResponse,
    ThreatStats,
    VulnerabilityMapRequest,
    VulnerabilityMapResponse,
)
from app.services.prediction_service import PredictionService
from app.services.access_control_service import AccessControlService
from app.services.bootstrap_service import BootstrapService
from app.services.stats_service import StatsService
from app.services.threat_catalog_service import ThreatCatalogService
from app.services.vulnerability_mapping_service import VulnerabilityMappingService

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("AUTO_CREATE_DB", "true").lower() == "true":
        Base.metadata.create_all(bind=engine)
        with Session(engine) as db:
            BootstrapService(get_data_repository()).seed_organizations(db)
    yield


app = FastAPI(
    title='Rostelecom Threat Analytics Mock API',
    version='3.0.0',
    summary='Mock API for cyber threat prediction, threat registry and vulnerability mapping.',
    description=(
        'Mock API для MVP аналитического приложения: прогноз атаки, список угроз, '
        'рекомендации по защите, маппинг уязвимостей, регистрация пользователей и JWT-авторизация. '
        'Swagger доступен по /docs, OpenAPI JSON по /openapi.json.'
    ),
    contact={'name': 'Project Team', 'email': 'team@example.com'},
    license_info={'name': 'MIPT'},
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(detail="Validation error", errors=exc.errors()).model_dump(),
    )


@app.get("/health", tags=["system"])
def healthcheck():
    logger.info("Healthcheck requested")
    return {"status": "ok"}


@app.post(
    "/predict",
    tags=["prediction"],
    response_model=PredictResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Получить полный mock-прогноз атаки",
)
def predict(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization_code = _ensure_user_has_access(payload, current_user, db)
    logger.info("Prediction request received for organization_code=%s", organization_code)
    return service.predict(payload)


@app.post(
    "/predict/time",
    tags=["prediction"],
    response_model=PredictTimeResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Спрогнозировать временное окно атаки",
)
def predict_time(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization_code = _ensure_user_has_access(payload, current_user, db)
    logger.info("Time prediction requested for organization_code=%s", organization_code)
    return service.predict_time(payload)


@app.post(
    "/predict/target",
    tags=["prediction"],
    response_model=PredictTargetResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Спрогнозировать объект атаки",
)
def predict_target(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization_code = _ensure_user_has_access(payload, current_user, db)
    logger.info("Target prediction requested for organization_code=%s", organization_code)
    return service.predict_target(payload)


@app.post(
    "/predict/method",
    tags=["prediction"],
    response_model=PredictMethodResponse,
    responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}, 422: {'model': ErrorResponse}},
    summary='Спрогнозировать метод атаки',
)
def predict_method(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization_code = _ensure_user_has_access(payload, current_user, db)
    logger.info("Method prediction requested for organization_code=%s", organization_code)
    return service.predict_method(payload)


@app.post(
    "/predict/recommendations",
    tags=["prediction"],
    response_model=PredictRecommendationsResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Получить рекомендации по защите на основе спрогнозированной угрозы",
)
def predict_recommendations(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization_code = _ensure_user_has_access(payload, current_user, db)
    logger.info("Recommendations request received for organization_code=%s", organization_code)
    return service.get_recommendations(payload)


@app.get(
    "/threats",
    tags=["threats"],
    response_model=ThreatListResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Список угроз из mock-реестра ФСТЭК",
)
def get_threats(
    severity: Severity | None = Query(default=None, description="Фильтр по уровню severity"),
    category: str | None = Query(default=None, description="Фильтр по категории угрозы"),
    service: ThreatCatalogService = Depends(get_threat_catalog_service),
):
    logger.info("Threat list requested with severity=%s category=%s", severity, category)
    return service.list_threats(ThreatFilter(severity=severity, category=category))


@app.get(
    "/stats",
    tags=["analytics"],
    response_model=ThreatStats,
    responses={401: {"model": ErrorResponse}},
    summary="Сводная mock-статистика по инцидентам текущей организации",
)
def get_stats(
    service: StatsService = Depends(get_stats_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    logger.info('Stats requested for organization_id=%s', current_user.organization_id)
    return service.build_stats(organization_code=organization.code if organization else None)


@app.post(
    "/vulnerabilities/map",
    tags=["early-warning"],
    response_model=VulnerabilityMapResponse,
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Сопоставить уязвимости инфраструктуры с угрозами",
)
def map_vulnerabilities_to_threats(
    payload: VulnerabilityMapRequest,
    service: VulnerabilityMappingService = Depends(get_vulnerability_mapping_service),
    current_user: User = Depends(get_current_user),
):
    logger.info(
        "Vulnerability mapping requested for organization_id=%s, vulnerabilities=%s",
        current_user.organization_id,
        len(payload.vulnerabilities),
    )
    return service.map_vulnerabilities(payload)

access_control_service = AccessControlService()


def _ensure_user_has_access(payload: PredictRequest, current_user: User, db: Session) -> str:
    return access_control_service.ensure_prediction_access(payload, current_user, db)
