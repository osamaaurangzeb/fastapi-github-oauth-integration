from fastapi import HTTPException, status, Query
from typing import Optional, Dict, Any, List
import json
import re
from src.helpers.database import get_database
import logging

logger = logging.getLogger(__name__)

class DataController:
    @staticmethod
    async def get_collection_data(
        collection: str,
        page: int = 1,
        limit: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        filter_params: Optional[str] = None,
        search: Optional[str] = None
    ):
        """Get paginated data from any GitHub collection"""
        try:
            db = get_database()
            
            # Validate collection name
            valid_collections = [
                "github_organizations", "github_repos", "github_commits",
                "github_pulls", "github_issues", "github_changelogs", "github_users"
            ]
            
            if collection not in valid_collections:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid collection. Must be one of: {', '.join(valid_collections)}"
                )
            
            # Build query
            query = {}
            
            # Apply filters
            if filter_params:
                try:
                    filters = json.loads(filter_params)
                    query.update(filters)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid filter JSON format"
                    )
            
            # Apply search
            if search:
                search_fields = DataController._get_search_fields(collection)
                search_conditions = []
                for field in search_fields:
                    search_conditions.append({
                        field: {"$regex": search, "$options": "i"}
                    })
                if search_conditions:
                    query["$or"] = search_conditions
            
            # Get collection
            coll = db[collection]
            
            # Count total documents
            total = await coll.count_documents(query)
            
            # Build sort
            sort_criteria = []
            if sort_by:
                sort_direction = 1 if sort_order == "asc" else -1
                sort_criteria.append((sort_by, sort_direction))
            else:
                # Default sort by creation date or _id
                if collection in ["github_commits", "github_pulls", "github_issues"]:
                    sort_criteria.append(("created_at", -1))
                else:
                    sort_criteria.append(("_id", -1))
            
            # Calculate pagination
            skip = (page - 1) * limit
            
            # Execute query
            cursor = coll.find(query).sort(sort_criteria).skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            
            # Calculate pagination info
            total_pages = (total + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "data": documents,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total,
                    "items_per_page": limit,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting collection data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve data"
            )
    
    @staticmethod
    async def global_search(query: str, limit: int = 50):
        """Search across all GitHub collections"""
        try:
            db = get_database()
            results = {}
            
            collections = {
                "organizations": "github_organizations",
                "repositories": "github_repos", 
                "commits": "github_commits",
                "pull_requests": "github_pulls",
                "issues": "github_issues",
                "users": "github_users"
            }
            
            for result_key, collection_name in collections.items():
                search_fields = DataController._get_search_fields(collection_name)
                search_conditions = []
                
                for field in search_fields:
                    search_conditions.append({
                        field: {"$regex": query, "$options": "i"}
                    })
                
                if search_conditions:
                    coll = db[collection_name]
                    cursor = coll.find({"$or": search_conditions}).limit(limit)
                    documents = await cursor.to_list(length=limit)
                    
                    # Convert ObjectId to string
                    for doc in documents:
                        if "_id" in doc:
                            doc["_id"] = str(doc["_id"])
                    
                    results[result_key] = documents
                else:
                    results[result_key] = []
            
            return {
                "query": query,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in global search: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search failed"
            )
    
    @staticmethod
    def _get_search_fields(collection: str) -> List[str]:
        """Get searchable fields for each collection"""
        search_fields_map = {
            "github_organizations": ["login", "name", "description"],
            "github_repos": ["name", "full_name", "description", "language"],
            "github_commits": ["message", "author_name", "author_email"],
            "github_pulls": ["title", "body", "user_login"],
            "github_issues": ["title", "body", "user_login"],
            "github_changelogs": ["event", "actor_login"],
            "github_users": ["login", "name", "bio", "company", "location"]
        }
        return search_fields_map.get(collection, ["name", "title", "login"])