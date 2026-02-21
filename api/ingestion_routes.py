"""API routes for controlling ingestion runs (Stage 7)."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ingestion.control import (
    get_run,
    get_run_errors,
    import_local_directory,
    list_runs,
    onboard_source,
    start_ingestion,
    start_ingestion_batch,
)
from ingestion.monitoring import ingestion_health, ingestion_metrics, source_freshness
from ingestion.sources import list_sources

ingestion_router = APIRouter(tags=["ingestion"])


class StartIngestionRequest(BaseModel):
    source_name: str = Field(default="hugo_love", min_length=1)
    index_after_crawl: bool = False


class StartIngestionBatchRequest(BaseModel):
    source_names: list[str] | None = None
    only_active: bool = True
    index_after_crawl: bool = False
    stop_on_error: bool = False


class OnboardSourceRequest(BaseModel):
    name: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    start_urls: list[str] = Field(min_length=1)
    allowed_paths: list[str] = Field(default_factory=list)
    blocked_paths: list[str] = Field(default_factory=list)
    max_depth: int = Field(default=2, ge=0, le=8)
    max_pages: int = Field(default=300, ge=1, le=50000)
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ManualImportDirectoryRequest(BaseModel):
    directory: str = Field(min_length=1)
    source_name: str = Field(default="startup_strategy_pack", min_length=1)
    topic: str = Field(default="startup_strategy", min_length=1)
    recursive: bool = True
    index_after_import: bool = True


@ingestion_router.post("/ingestion/start")
async def start_ingestion_run(req: StartIngestionRequest) -> dict[str, Any]:
    try:
        return start_ingestion(
            source_name=req.source_name,
            index_after_crawl=req.index_after_crawl,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@ingestion_router.post("/ingestion/start-batch")
async def start_ingestion_runs_batch(req: StartIngestionBatchRequest) -> dict[str, Any]:
    try:
        return start_ingestion_batch(
            source_names=req.source_names,
            only_active=req.only_active,
            index_after_crawl=req.index_after_crawl,
            stop_on_error=req.stop_on_error,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@ingestion_router.get("/ingestion/runs")
async def get_ingestion_runs(
    limit: int = Query(default=50, ge=1, le=500),
    source_name: str | None = Query(default=None),
) -> dict[str, Any]:
    try:
        runs = list_runs(limit=limit, source_name=source_name)
        return {"runs": runs, "count": len(runs)}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@ingestion_router.get("/ingestion/sources")
async def get_ingestion_sources(
    only_active: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        sources = list_sources(only_active=only_active)
        return {"sources": sources, "count": len(sources)}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@ingestion_router.post("/ingestion/sources")
async def onboard_ingestion_source(req: OnboardSourceRequest) -> dict[str, Any]:
    try:
        payload = req.model_dump()
        return onboard_source(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@ingestion_router.post("/ingestion/import/local")
async def import_ingestion_directory(req: ManualImportDirectoryRequest) -> dict[str, Any]:
    try:
        return import_local_directory(
            directory=req.directory,
            source_name=req.source_name,
            topic=req.topic,
            recursive=req.recursive,
            index_after_import=req.index_after_import,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@ingestion_router.get("/ingestion/runs/{run_id}")
async def get_ingestion_run(run_id: int) -> dict[str, Any]:
    try:
        run = get_run(run_id=run_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run not found: {run_id}")
    return run


@ingestion_router.get("/ingestion/errors/{run_id}")
async def get_ingestion_run_errors(
    run_id: int,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, Any]:
    try:
        errors = get_run_errors(run_id=run_id, limit=limit)
        return {"run_id": run_id, "errors": errors, "count": len(errors)}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@ingestion_router.get("/ingestion/metrics")
async def get_ingestion_metrics() -> dict[str, Any]:
    try:
        metrics = ingestion_metrics()
        return {"metrics": metrics}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@ingestion_router.get("/ingestion/health")
async def get_ingestion_health() -> dict[str, Any]:
    try:
        return ingestion_health()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@ingestion_router.get("/ingestion/freshness")
async def get_source_freshness(
    max_age_hours: int = Query(default=72, ge=1, le=24 * 60),
) -> dict[str, Any]:
    try:
        return source_freshness(max_age_hours=max_age_hours)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
