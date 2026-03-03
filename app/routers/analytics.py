"""Analytics endpoints for denial trends, payer comparison, and adjustment summary."""
from fastapi import APIRouter, Query
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/denial-trends")
async def denial_trends(
    group_by: str = Query("reason", regex="^(reason|payer|provider)$"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    """Get denial/adjustment trends over time."""
    return analytics_service.get_denial_trends(
        group_by=group_by,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/payer-comparison")
async def payer_comparison():
    """Compare payers by payment rate and denial reasons."""
    return analytics_service.get_payer_comparison()


@router.get("/adjustment-summary")
async def adjustment_summary():
    """Get combined adjustment summary."""
    return analytics_service.get_adjustment_summary()
