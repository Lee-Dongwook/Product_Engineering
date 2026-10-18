from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.tenant import User, UserRole
from app.models.product import Product
from app.models.inventory import InventoryLog
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.core.exceptions import ProductNotFoundError

router = APIRouter()

@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Product).filter(Product.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    products = result.scalars().all()
    return products

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Product).filter(
        Product.id == product_id,
        Product.tenant_id == current_user.tenant_id
    )
    result = await db.execute(stmt)
    product = result.scalars().first()
    if not product:
        raise ProductNotFoundError(product_id)
    return product

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    product = Product(
        **product_in.model_dump(exclude={"tenant_id"}),
        tenant_id=current_user.tenant_id
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product
