from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud.stats import get_overview_stats
from app.db.session import get_db
from app.deps import require_admin
from app.schemas.stats import StatsOverviewOut

router = APIRouter()


@router.get("/overview", response_model=StatsOverviewOut, dependencies=[Depends(require_admin)])
def stats_overview_api(
    store_id: int | None = None,
    query_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> StatsOverviewOut:
    target_date = query_date or datetime.now(timezone.utc).date()
    stats, _ = get_overview_stats(db, target_date=target_date, store_id=store_id)
    return stats
