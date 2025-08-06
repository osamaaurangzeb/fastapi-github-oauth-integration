import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = settings.GITHUB_API_BASE
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Integration-App"
        }
    
    async def get_user(self) -> Dict[str, Any]:
        """Get authenticated user info"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Get user organizations"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/orgs",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_organization_repos(self, org: str, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get repositories for an organization"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/orgs/{org}/repos",
                headers=self.headers,
                params={"page": page, "per_page": per_page, "sort": "updated"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_repos(self, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get user repositories"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/repos",
                headers=self.headers,
                params={"page": page, "per_page": per_page, "sort": "updated"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_repository_commits(self, owner: str, repo: str, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get commits for a repository"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/commits",
                headers=self.headers,
                params={"page": page, "per_page": per_page}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_repository_pulls(self, owner: str, repo: str, state: str = "all", page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get pull requests for a repository"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls",
                headers=self.headers,
                params={"state": state, "page": page, "per_page": per_page}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_repository_issues(self, owner: str, repo: str, state: str = "all", page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get issues for a repository"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=self.headers,
                params={"state": state, "page": page, "per_page": per_page}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_issue_events(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        """Get events (changelog) for an issue"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/events",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_organization_members(self, org: str, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get organization members"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/orgs/{org}/members",
                headers=self.headers,
                params={"page": page, "per_page": per_page}
            )
            response.raise_for_status()
            return response.json()

async def exchange_code_for_token(code: str) -> str:
    """Exchange OAuth code for access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.GITHUB_OAUTH_BASE}/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]