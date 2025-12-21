"""
Metrics and monitoring endpoints
"""
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from utils.metrics import metrics

router = APIRouter(prefix="/api/v1", tags=["metrics"])


@router.get("/metrics")
async def get_metrics():
    """Get Prometheus-compatible metrics"""
    return PlainTextResponse(metrics.get_prometheus_format())


@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get metrics summary as JSON"""
    return metrics.get_summary()

