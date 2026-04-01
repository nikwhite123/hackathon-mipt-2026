from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.schemas import (
    ErrorResponse,
    PredictRequest,
    PredictResponse,
    ThreatListResponse,
    ThreatStats,
    VulnerabilityMapRequest,
    VulnerabilityMapResponse,
)
from app.services import build_stats, generate_prediction, list_threats, map_vulnerabilities

app = FastAPI(
    title="Rostelecom Threat Analytics Mock API",
    version="1.0.0",
    summary="Mock API for cyber threat prediction, threat registry and vulnerability mapping.",
    description=(
        "Mock API для MVP аналитического приложения: прогноз атаки, список угроз, "
        "рекомендации по защите и маппинг уязвимостей с базой угроз. "
        "Swagger доступен по /docs, OpenAPI JSON по /openapi.json."
    ),
    contact={"name": "Project Team", "email": "hereIsNothing@maybeUseless"},
    license_info={"name": "MIPT"},
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.get("/health", tags=["system"])
def healthcheck():
    return {"status": "ok"}


@app.post(
    "/predict",
    tags=["prediction"],
    response_model=PredictResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Получить mock-прогноз атаки",
)
def predict(payload: PredictRequest):
    return generate_prediction(payload)


@app.get(
    "/threats",
    tags=["threats"],
    response_model=ThreatListResponse,
    summary="Список угроз из mock-реестра ФСТЭК",
)
def get_threats(
    severity: str | None = Query(default=None, description="Фильтр по уровню severity"),
    category: str | None = Query(default=None, description="Фильтр по категории угрозы"),
):
    response = list_threats()
    items = response.items

    if severity:
        items = [item for item in items if item.severity.value == severity]
    if category:
        items = [item for item in items if item.category == category]

    return {"total": len(items), "items": items}


@app.get(
    "/stats",
    tags=["analytics"],
    response_model=ThreatStats,
    summary="Сводная mock-статистика по инцидентам",
)
def get_stats():
    return build_stats()


@app.post(
    "/vulnerabilities/map",
    tags=["early-warning"],
    response_model=VulnerabilityMapResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Сопоставить уязвимости инфраструктуры с угрозами",
)
def map_vulnerabilities_to_threats(payload: VulnerabilityMapRequest):
    return map_vulnerabilities(payload)
