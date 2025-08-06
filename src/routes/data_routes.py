from fastapi import APIRouter, Query, Path
from typing import Optional
from src.controllers.data_controller import DataController

router = APIRouter(prefix="/data", tags=["Data"])

@router.get("/{collection}")
async def get_collection_data(
    collection: str = Path(...),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    filter: Optional[str] = Query(None, alias="filter"),
    search: Optional[str] = Query(None)
):
    """Get paginated data from any GitHub collection"""
    return await DataController.get_collection_data(
        collection=collection,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        filter_params=filter,
        search=search
    )

@router.get("/")
async def global_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100)
):
    """Search across all GitHub collections"""
    return await DataController.global_search(q, limit)