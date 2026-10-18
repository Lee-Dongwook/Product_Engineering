import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.tenant import Tenant, User, UserRole


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        tenant = await session.scalar(select(Tenant).where(Tenant.name == "Company A"))
        if not tenant:
            tenant = Tenant(name="Company A")
            session.add(tenant)

        supplier = await session.scalar(select(Supplier).where(Supplier.name == "기본 공급사"))
        if not supplier:
            supplier = Supplier(name="기본 공급사", lead_time_days=7, moq=20)
            session.add(supplier)

        await session.flush()

        user = await session.scalar(select(User).where(User.email == "admin@companyA.com"))
        if not user:
            session.add(
                User(
                    email="admin@companyA.com",
                    hashed_password="development-only",
                    role=UserRole.ADMIN,
                    tenant_id=tenant.id,
                )
            )

        product = await session.scalar(select(Product).where(Product.sku == "SKU-001"))
        if not product:
            session.add(
                Product(
                    tenant_id=tenant.id,
                    supplier_id=supplier.id,
                    sku="SKU-001",
                    name="무선 키보드",
                    category="전자기기",
                    current_stock=5,
                    safety_stock=10,
                    unit_cost=35000,
                )
            )

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
