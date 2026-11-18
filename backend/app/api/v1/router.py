from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.email_ingestion import router as email_router
from app.api.v1.households import router as households_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.ocr import router as ocr_router
from app.api.v1.purchases import router as purchases_router
from app.api.v1.receipts import router as receipts_router
from app.api.v1.reports import router as reports_router
from app.api.v1.search import router as search_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.sync import router as sync_router
from app.api.v1.warranties import router as warranties_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(receipts_router)
api_v1_router.include_router(purchases_router)
api_v1_router.include_router(warranties_router)
api_v1_router.include_router(subscriptions_router)
api_v1_router.include_router(ocr_router)
api_v1_router.include_router(sync_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(households_router)
api_v1_router.include_router(email_router)
