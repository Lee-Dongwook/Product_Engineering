
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProductNotFoundError
from app.models.product import Product
from app.models.sales_record import SalesRecord

class SalesRecordService:
    @staticmethod
    async def get_daily_sales_history(
        db: AsyncSession,
        product_id: int,
        tenant_id: int,
        days: int = 30,
        end_date: date | None = None,
    ) -> list[int]:
        if days < 1:
            raise ValueError("days는 1 이상이어야 합니다.")

        product_stmt = select(Product.id).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id,
        )
        product_result = await db.execute(product_stmt)
        
        if product_result.scalar_one_or_none() is None:
            raise ProductNotFoundError(product_id)
        
        last_day = end_date or date.today()
        first_day = last_day - timedelta(days=days -1)

        start_at = datetime.combine(first_day, time.min)
        end_at = datetime.combine(
            last_day + timedelta(days=1),
            time.min,
        )

        sales_stmt = select(
            SalesRecord.sold_at,
            SalesRecord.quantity,
        ).where(
            SalesRecord.product_id == product_id,
            SalesRecord.tenant_id == tenant_id,
            SalesRecord.sold_at >= start_at,
            SalesRecord.sold_at < end_at,
        )

        result = await db.execute(sales_stmt)

        totals_by_day: dict[date, int] = defaultdict(int)

        for sold_at, quantity in result.all():
            totals_by_day[sold_at.date()] += quantity
        
        return [
            totals_by_day[first_day + timedelta(days=offset)]
            for offset in range(days)
        ]
