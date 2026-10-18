from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.product import Product
from app.models.inventory import InventoryLog
from app.models.purchase_order import PurchaseOrder
from app.models.domain import OrderStatus
from app.core.exceptions import ProductNotFoundError

class InventoryService:
    @staticmethod
    async def get_product_with_inventory(db: AsyncSession, product_id: int, tenant_id: Optional[int] = None):
        stmt = select(Product).filter(Product.id == product_id)
        if tenant_id is not None:
            stmt = stmt.filter(Product.tenant_id == tenant_id)
        result = await db.execute(stmt)
        product = result.scalars().first()
        if not product:
            raise ProductNotFoundError(product_id)
        return product
    
    @staticmethod
    async def create_purchase_order_draft(
        db: AsyncSession,
        product_id: int,
        suggested_qty: int,
        reasoning: str,
        tenant_id: int = 1
    ):
        order = PurchaseOrder(
            tenant_id=tenant_id,
            product_id=product_id,
            suggested_qty=suggested_qty,
            status=OrderStatus.DRAFT,
            reasoning_summary=reasoning
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

