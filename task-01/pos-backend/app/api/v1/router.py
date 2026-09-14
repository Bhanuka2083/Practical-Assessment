from fastapi import APIRouter
from app.api.v1.endpoints import auth, cart, orders, payments, products
from app.api.v1.endpoints import cron

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(cron.router)