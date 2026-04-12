from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Rostelecom Threat Analytics Mock API",
    version="2.1.0",
    summary="Mock API for cyber threat prediction, threat registry and vulnerability mapping.",
    description=(
        "Mock API для MVP аналитического приложения: прогноз атаки, список угроз, "
        "рекомендации по защите и маппинг уязвимостей с базой угроз. "
        "Swagger доступен по /docs, OpenAPI JSON по /openapi.json."
    ),
    contact={"name": "Project Team", "email": "team@example.com"},
    license_info={"name": "MIPT"},
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.dependencies import (
    get_prediction_service,
    get_stats_service,
    get_threat_catalog_service,
    get_vulnerability_mapping_service,
)
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
from app.services.stats_service import StatsService
from app.services.threat_catalog_service import ThreatCatalogService
from app.services.vulnerability_mapping_service import VulnerabilityMappingService

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
):
    logger.info("Prediction request received for organization_id=%s", payload.organization_id)
    return service.predict(payload)


@app.post(
    "/predict/time",
    tags=["prediction"],
    response_model=PredictTimeResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Спрогнозировать временное окно атаки",
)
def predict_time(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
):
    logger.info("Time prediction requested for organization_id=%s", payload.organization_id)
    return service.predict_time(payload)


@app.post(
    "/predict/target",
    tags=["prediction"],
    response_model=PredictTargetResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Спрогнозировать объект атаки",
)
def predict_target(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
):
    logger.info("Target prediction requested for organization_id=%s", payload.organization_id)
    return service.predict_target(payload)


@app.post(
    "/predict/method",
    tags=["prediction"],
    response_model=PredictMethodResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Спрогнозировать метод атаки",
)
def predict_method(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
):
    logger.info("Method prediction requested for organization_id=%s", payload.organization_id)
    return service.predict_method(payload)


@app.post(
    "/predict/recommendations",
    tags=["prediction"],
    response_model=PredictRecommendationsResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Получить рекомендации по защите на основе спрогнозированной угрозы",
)
def predict_recommendations(
    payload: PredictRequest,
    service: PredictionService = Depends(get_prediction_service),
):
    logger.info("Recommendations request received for organization_id=%s", payload.organization_id)
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
    summary="Сводная mock-статистика по инцидентам",
)
def get_stats(service: StatsService = Depends(get_stats_service)):
    logger.info("Stats requested")
    return service.build_stats()


@app.post(
    "/vulnerabilities/map",
    tags=["early-warning"],
    response_model=VulnerabilityMapResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Сопоставить уязвимости инфраструктуры с угрозами",
)
def map_vulnerabilities_to_threats(
    payload: VulnerabilityMapRequest,
    service: VulnerabilityMappingService = Depends(get_vulnerability_mapping_service),
):
    logger.info("Vulnerability mapping requested for %s vulnerabilities", len(payload.vulnerabilities))
    return service.map_vulnerabilities(payload)