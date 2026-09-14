from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.core.database import get_db
from app.services.stock_cleaner_service import StockCleanerService

router = APIRouter(prefix="/cron", tags=["Cron / Maintenance"])

CRON_SECRET = os.getenv("CRON_SECRET")


@router.get("/clean-expired-stock")
async def clean_expired_stock(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    # Protect endpoint so only Vercel Cron can call it
    if CRON_SECRET and authorization != f"Bearer {CRON_SECRET}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing cron authorization header",
        )

    service = StockCleanerService(db)
    result = await service.sweep_expired_reservations(batch_size=50)
    return {"status": "success", **result}