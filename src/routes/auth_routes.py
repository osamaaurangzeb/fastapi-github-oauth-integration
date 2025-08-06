from fastapi import APIRouter, Query
from src.controllers.integration_controller import IntegrationController

router = APIRouter(prefix="/integration", tags=["Integration"])

@router.get("/status")
async def get_status(user_id: int = Query(...)):
    """Check integration status"""
    return await IntegrationController.get_status(user_id)

@router.post("/remove")
async def remove_integration(user_id: int = Query(...)):
    """Delete integration data from MongoDB"""
    return await IntegrationController.remove_integration(user_id)

@router.post("/resync")
async def resync_data(user_id: int = Query(...)):
    """Re-fetch all GitHub data and re-store"""
    return await IntegrationController.resync_data(user_id)