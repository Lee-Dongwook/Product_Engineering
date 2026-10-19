
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ProductNotFoundError
from app.models.domain import OrderStatus
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.services.inventory_service import InventoryService


@pytest.fixture
def db():
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_get_product_with_inventory_returns_owned_product(db):
    product = Product(
        id=1,
        tenant_id=10,
        sku="SKU-001",
        name="Product A",
        current_stock=50,
        safety_stock=10,
        unit_cost=20.0,
    )

    result = MagicMock()
    result.scalar_one_or_none.return_value = product
    db.execute.return_value = result

    actual = await InventoryService.get_product_with_inventory(
        db=db,
        product_id=1,
        tenant_id=10,
    )

    assert actual is product

    stmt = db.execute.await_args.args[0]
    assert "products.tenant_id" in str(stmt)
    
@pytest.mark.asyncio
async def test_get_product_with_inventory_rejects_other_tenant(db):
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(ProductNotFoundError):
        await InventoryService.get_product_with_inventory(
            db=db,
            product_id=1,
            tenant_id=20,
        )


@pytest.mark.asyncio
async def test_create_purchase_order_rejects_product_from_other_tenant(db):
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(ProductNotFoundError):
        await InventoryService.create_purchase_order_draft(
            db=db,
            product_id=1,
            suggested_qty=25,
            reasoning="Test proposal",
            tenant_id=20,
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_purchase_order_uses_verified_tenant(db):
    result = MagicMock()
    result.scalar_one_or_none.return_value = 1
    db.execute.return_value = result

    await InventoryService.create_purchase_order_draft(
        db=db,
        product_id=1,
        suggested_qty=25,
        reasoning="Test proposal",
        tenant_id=10,
    )

    order = db.add.call_args.args[0]

    assert isinstance(order, PurchaseOrder)
    assert order.product_id == 1
    assert order.tenant_id == 10
    assert order.suggested_qty == 25
    assert order.status == OrderStatus.DRAFT

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(order)
