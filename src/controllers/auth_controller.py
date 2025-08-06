from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from datetime import datetime
from src.helpers.github_client import GitHubClient, exchange_code_for_token
from src.helpers.database import get_database
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class AuthController:
    @staticmethod
    def github_login():
        """Redirect to GitHub OAuth authorization page"""
        auth_url = (
            f"{settings.GITHUB_OAUTH_BASE}/authorize?"
            f"client_id={settings.GITHUB_CLIENT_ID}&"
            f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
            f"scope=repo,user,read:org"
        )
        return RedirectResponse(url=auth_url)
    
    @staticmethod
    async def github_callback(code: str):
        """Handle GitHub OAuth callback"""
        try:
            # Exchange code for access token
            access_token = await exchange_code_for_token(code)
            
            # Get user info from GitHub
            github_client = GitHubClient(access_token)
            user_data = await github_client.get_user()
            
            # Store integration data
            db = get_database()
            integration_data = {
                "github_user_id": user_data["id"],
                "username": user_data["login"],
                "email": user_data.get("email"),
                "access_token": access_token,
                "integration_status": "active",
                "connection_timestamp": datetime.utcnow(),
                "last_sync": None
            }
            
            # Update or insert integration
            await db.github_integration.update_one(
                {"github_user_id": user_data["id"]},
                {"$set": integration_data},
                upsert=True
            )
            
            return {
                "message": "GitHub integration successful",
                "user": {
                    "id": user_data["id"],
                    "username": user_data["login"],
                    "email": user_data.get("email")
                }
            }
            
        except Exception as e:
            logger.error(f"GitHub OAuth callback error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub OAuth authentication failed"
            )