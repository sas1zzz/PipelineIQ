from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import PipelineRun
from .schemas import PipelineRunCreate, PipelineRunResponse


router = APIRouter(
    prefix="/api/pipeline-runs",
    tags=["Pipeline Runs"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "",
    response_model=PipelineRunResponse,
    status_code=201,
)
def create_pipeline_run(
    pipeline_run: PipelineRunCreate,
    db: Session = Depends(get_db),
):
    run = PipelineRun(
        pipeline_name=pipeline_run.pipeline_name,
        status=pipeline_run.status,
        started_at=pipeline_run.started_at,
        finished_at=pipeline_run.finished_at,
        records_processed=pipeline_run.records_processed,
        error_message=pipeline_run.error_message,
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


@router.get(
    "",
    response_model=list[PipelineRunResponse],
)
def get_pipeline_runs(
    db: Session = Depends(get_db),
):
    runs = (
        db.query(PipelineRun)
        .order_by(PipelineRun.started_at.desc())
        .all()
    )

    return runs


@router.get(
    "/{run_id}",
    response_model=PipelineRunResponse,
)
def get_pipeline_run(
    run_id: int,
    db: Session = Depends(get_db),
):
    run = (
        db.query(PipelineRun)
        .filter(PipelineRun.id == run_id)
        .first()
    )

    if not run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found",
        )

    return run