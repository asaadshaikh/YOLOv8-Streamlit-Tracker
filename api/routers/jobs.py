"""
Background job management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from services.job_service import JobService
from services.auth_service import get_current_user
from database import User

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/{task_id}")
async def get_job_status(
    task_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get status of a background job"""
    status = JobService.get_job_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

