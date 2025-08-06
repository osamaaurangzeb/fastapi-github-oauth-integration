from fastapi import HTTPException, status
from datetime import datetime
from src.helpers.database import get_database
from src.helpers.github_client import GitHubClient
from src.controllers.sync_controller import SyncController
import logging

logger = logging.getLogger(__name__)

class IntegrationController:
    @staticmethod
    async def get_status(user_id: int):
        """Check integration status"""
        try:
            db = get_database()
            integration = await db.github_integration.find_one({"github_user_id": user_id})
            
            if not integration:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Integration not found"
                )
            
            return {
                "status": integration["integration_status"],
                "username": integration["username"],
                "connected_at": integration["connection_timestamp"],
                "last_sync": integration.get("last_sync")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting integration status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get integration status"
            )
    
    @staticmethod
    async def remove_integration(user_id: int):
        """Remove integration and all associated data"""
        try:
            db = get_database()
            
            # Check if integration exists
            integration = await db.github_integration.find_one({"github_user_id": user_id})
            if not integration:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Integration not found"
                )
            
            # Delete all associated data
            collections = [
                "github_integration",
                "github_organizations",
                "github_repos",
                "github_commits",
                "github_pulls",
                "github_issues",
                "github_changelogs",
                "github_users"
            ]
            
            for collection_name in collections:
                collection = db[collection_name]
                if collection_name == "github_integration":
                    await collection.delete_one({"github_user_id": user_id})
                else:
                    await collection.delete_many({"integration_user_id": user_id})
            
            return {"message": "Integration removed successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing integration: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove integration"
            )
    
    @staticmethod
    async def resync_data(user_id: int):
        """Re-fetch and re-store all GitHub data"""
        try:
            db = get_database()
            
            # Get integration
            integration = await db.github_integration.find_one({"github_user_id": user_id})
            if not integration:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Integration not found"
                )
            
            # Clear existing data (except integration)
            collections = [
                "github_organizations",
                "github_repos", 
                "github_commits",
                "github_pulls",
                "github_issues",
                "github_changelogs",
                "github_users"
            ]
            
            for collection_name in collections:
                collection = db[collection_name]
                await collection.delete_many({"integration_user_id": user_id})
            
            # Re-sync all data
            sync_controller = SyncController()
            await sync_controller.sync_all_data(user_id, integration["access_token"])
            
            # Update last sync timestamp
            await db.github_integration.update_one(
                {"github_user_id": user_id},
                {"$set": {"last_sync": datetime.utcnow()}}
            )
            
            return {"message": "Data resync completed successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resyncing data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resync data"
            )