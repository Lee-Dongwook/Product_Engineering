from fastapi import APIRouter
from app.api.v1.endpoints import orders, streaming, tracking, inventory, auth

api_router = APIRouter()

api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(streaming.router, prefix="/stream", tags=["stream"])
api_router.include_router(tracking.router, prefix="/tracking", tags=["tracking"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
