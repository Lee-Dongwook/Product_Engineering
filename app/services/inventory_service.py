from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.product import Product
from app.models.inventory import InventoryLog
from app.models.purchase_order import PurchaseOrder
from app.core.exceptions import ProductNotFoundError

class InventoryService:
    @staticmethod
    async def get_product_with_inventory(db: AsyncSession, product_id: int):
        result = await db.execute(select(Product).filter(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            raise ProductNotFoundError(product_id)
        return product
    
    @staticmethod
    async def create_purchase_order_draft(db: AsyncSession, product_id: int, suggested_qty: int, reasoning: str):
        order = PurchaseOrder(
            product_id=product_id,
            ordered_qty=suggested_qty,
            status="DRAFT",
            reasoning=reasoning
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order
