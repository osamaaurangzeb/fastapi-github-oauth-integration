from datetime import datetime
from src.helpers.github_client import GitHubClient
from src.helpers.database import get_database
import logging
import asyncio

logger = logging.getLogger(__name__)

class SyncController:
    async def sync_all_data(self, user_id: int, access_token: str):
        """Sync all GitHub data for a user"""
        github_client = GitHubClient(access_token)
        db = get_database()
        
        try:
            # Sync organizations
            await self._sync_organizations(github_client, db, user_id)
            
            # Sync user repositories
            await self._sync_user_repositories(github_client, db, user_id)
            
            # Sync organization repositories
            await self._sync_organization_repositories(github_client, db, user_id)
            
            logger.info(f"Data sync completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error syncing data for user {user_id}: {e}")
            raise
    
    async def _sync_organizations(self, github_client: GitHubClient, db, user_id: int):
        """Sync user organizations"""
        try:
            orgs = await github_client.get_organizations()
            
            for org_data in orgs:
                org_doc = {
                    "github_id": org_data["id"],
                    "login": org_data["login"],
                    "name": org_data.get("name"),
                    "description": org_data.get("description"),
                    "url": org_data["url"],
                    "avatar_url": org_data.get("avatar_url"),
                    "created_at": datetime.fromisoformat(org_data["created_at"].replace("Z", "+00:00")),
                    "updated_at": datetime.fromisoformat(org_data["updated_at"].replace("Z", "+00:00")),
                    "user_id": user_id
                }
                
                await db.github_organizations.update_one(
                    {"github_id": org_data["id"]},
                    {"$set": org_doc},
                    upsert=True
                )
                
                # Sync organization members
                await self._sync_organization_members(github_client, db, org_data["login"], user_id)
                
        except Exception as e:
            logger.error(f"Error syncing organizations: {e}")
            raise
    
    async def _sync_user_repositories(self, github_client: GitHubClient, db, user_id: int):
        """Sync user repositories"""
        try:
            page = 1
            while True:
                repos = await github_client.get_user_repos(page=page, per_page=100)
                if not repos:
                    break
                
                for repo_data in repos:
                    await self._process_repository(github_client, db, repo_data, user_id)
                
                if len(repos) < 100:
                    break
                page += 1
                
        except Exception as e:
            logger.error(f"Error syncing user repositories: {e}")
            raise
    
    async def _sync_organization_repositories(self, github_client: GitHubClient, db, user_id: int):
        """Sync repositories for all organizations"""
        try:
            orgs = await db.github_organizations.find({"user_id": user_id}).to_list(None)
            
            for org in orgs:
                page = 1
                while True:
                    repos = await github_client.get_organization_repos(org["login"], page=page, per_page=100)
                    if not repos:
                        break
                    
                    for repo_data in repos:
                        await self._process_repository(github_client, db, repo_data, user_id)
                    
                    if len(repos) < 100:
                        break
                    page += 1
                    
        except Exception as e:
            logger.error(f"Error syncing organization repositories: {e}")
            raise
    
    async def _process_repository(self, github_client: GitHubClient, db, repo_data: dict, user_id: int):
        """Process a single repository and sync its data"""
        try:
            # Store repository
            repo_doc = {
                "github_id": repo_data["id"],
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "description": repo_data.get("description"),
                "private": repo_data["private"],
                "owner_login": repo_data["owner"]["login"],
                "owner_id": repo_data["owner"]["id"],
                "html_url": repo_data["html_url"],
                "clone_url": repo_data["clone_url"],
                "language": repo_data.get("language"),
                "stargazers_count": repo_data["stargazers_count"],
                "watchers_count": repo_data["watchers_count"],
                "forks_count": repo_data["forks_count"],
                "open_issues_count": repo_data["open_issues_count"],
                "default_branch": repo_data["default_branch"],
                "created_at": datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00")),
                "updated_at": datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00")),
                "pushed_at": datetime.fromisoformat(repo_data["pushed_at"].replace("Z", "+00:00")) if repo_data.get("pushed_at") else None,
                "user_id": user_id
            }
            
            await db.github_repos.update_one(
                {"github_id": repo_data["id"]},
                {"$set": repo_doc},
                upsert=True
            )
            
            # Sync repository data concurrently
            await asyncio.gather(
                self._sync_repository_commits(github_client, db, repo_data["owner"]["login"], repo_data["name"], repo_data["id"], user_id),
                self._sync_repository_pulls(github_client, db, repo_data["owner"]["login"], repo_data["name"], repo_data["id"], user_id),
                self._sync_repository_issues(github_client, db, repo_data["owner"]["login"], repo_data["name"], repo_data["id"], user_id)
            )
            
        except Exception as e:
            logger.error(f"Error processing repository {repo_data['full_name']}: {e}")
    
    async def _sync_repository_commits(self, github_client: GitHubClient, db, owner: str, repo: str, repo_id: int, user_id: int):
        """Sync commits for a repository"""
        try:
            page = 1
            while True:
                commits = await github_client.get_repository_commits(owner, repo, page=page, per_page=100)
                if not commits:
                    break
                
                for commit_data in commits:
                    commit_doc = {
                        "sha": commit_data["sha"],
                        "message": commit_data["commit"]["message"],
                        "author_name": commit_data["commit"]["author"].get("name"),
                        "author_email": commit_data["commit"]["author"].get("email"),
                        "author_date": datetime.fromisoformat(commit_data["commit"]["author"]["date"].replace("Z", "+00:00")),
                        "committer_name": commit_data["commit"]["committer"].get("name"),
                        "committer_email": commit_data["commit"]["committer"].get("email"),
                        "committer_date": datetime.fromisoformat(commit_data["commit"]["committer"]["date"].replace("Z", "+00:00")),
                        "html_url": commit_data["html_url"],
                        "repository_id": repo_id,
                        "repository_name": f"{owner}/{repo}",
                        "additions": commit_data.get("stats", {}).get("additions"),
                        "deletions": commit_data.get("stats", {}).get("deletions"),
                        "total_changes": commit_data.get("stats", {}).get("total"),
                        "user_id": user_id
                    }
                    
                    await db.github_commits.update_one(
                        {"sha": commit_data["sha"], "repository_id": repo_id},
                        {"$set": commit_doc},
                        upsert=True
                    )
                
                if len(commits) < 100:
                    break
                page += 1
                
        except Exception as e:
            logger.error(f"Error syncing commits for {owner}/{repo}: {e}")
    
    async def _sync_repository_pulls(self, github_client: GitHubClient, db, owner: str, repo: str, repo_id: int, user_id: int):
        """Sync pull requests for a repository"""
        try:
            page = 1
            while True:
                pulls = await github_client.get_repository_pulls(owner, repo, page=page, per_page=100)
                if not pulls:
                    break
                
                for pull_data in pulls:
                    pull_doc = {
                        "github_id": pull_data["id"],
                        "number": pull_data["number"],
                        "title": pull_data["title"],
                        "body": pull_data.get("body"),
                        "state": pull_data["state"],
                        "user_login": pull_data["user"]["login"],
                        "user_id": pull_data["user"]["id"],
                        "assignee_login": pull_data["assignee"]["login"] if pull_data.get("assignee") else None,
                        "assignee_id": pull_data["assignee"]["id"] if pull_data.get("assignee") else None,
                        "html_url": pull_data["html_url"],
                        "created_at": datetime.fromisoformat(pull_data["created_at"].replace("Z", "+00:00")),
                        "updated_at": datetime.fromisoformat(pull_data["updated_at"].replace("Z", "+00:00")),
                        "closed_at": datetime.fromisoformat(pull_data["closed_at"].replace("Z", "+00:00")) if pull_data.get("closed_at") else None,
                        "merged_at": datetime.fromisoformat(pull_data["merged_at"].replace("Z", "+00:00")) if pull_data.get("merged_at") else None,
                        "head_ref": pull_data["head"]["ref"],
                        "base_ref": pull_data["base"]["ref"],
                        "repository_id": repo_id,
                        "repository_name": f"{owner}/{repo}",
                        "integration_user_id": user_id
                    }
                    
                    await db.github_pulls.update_one(
                        {"github_id": pull_data["id"]},
                        {"$set": pull_doc},
                        upsert=True
                    )
                
                if len(pulls) < 100:
                    break
                page += 1
                
        except Exception as e:
            logger.error(f"Error syncing pulls for {owner}/{repo}: {e}")
    
    async def _sync_repository_issues(self, github_client: GitHubClient, db, owner: str, repo: str, repo_id: int, user_id: int):
        """Sync issues for a repository"""
        try:
            page = 1
            while True:
                issues = await github_client.get_repository_issues(owner, repo, page=page, per_page=100)
                if not issues:
                    break
                
                for issue_data in issues:
                    # Skip pull requests (they appear in issues API)
                    if issue_data.get("pull_request"):
                        continue
                    
                    issue_doc = {
                        "github_id": issue_data["id"],
                        "number": issue_data["number"],
                        "title": issue_data["title"],
                        "body": issue_data.get("body"),
                        "state": issue_data["state"],
                        "user_login": issue_data["user"]["login"],
                        "user_id": issue_data["user"]["id"],
                        "assignee_login": issue_data["assignee"]["login"] if issue_data.get("assignee") else None,
                        "assignee_id": issue_data["assignee"]["id"] if issue_data.get("assignee") else None,
                        "labels": [label["name"] for label in issue_data.get("labels", [])],
                        "html_url": issue_data["html_url"],
                        "created_at": datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                        "updated_at": datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00")),
                        "closed_at": datetime.fromisoformat(issue_data["closed_at"].replace("Z", "+00:00")) if issue_data.get("closed_at") else None,
                        "repository_id": repo_id,
                        "repository_name": f"{owner}/{repo}",
                        "integration_user_id": user_id
                    }
                    
                    await db.github_issues.update_one(
                        {"github_id": issue_data["id"]},
                        {"$set": issue_doc},
                        upsert=True
                    )
                    
                    # Sync issue events (changelog)
                    await self._sync_issue_events(github_client, db, owner, repo, issue_data["number"], repo_id, user_id)
                
                if len(issues) < 100:
                    break
                page += 1
                
        except Exception as e:
            logger.error(f"Error syncing issues for {owner}/{repo}: {e}")
    
    async def _sync_issue_events(self, github_client: GitHubClient, db, owner: str, repo: str, issue_number: int, repo_id: int, user_id: int):
        """Sync events (changelog) for an issue"""
        try:
            events = await github_client.get_issue_events(owner, repo, issue_number)
            
            for event_data in events:
                event_doc = {
                    "github_id": event_data["id"],
                    "event": event_data["event"],
                    "actor_login": event_data["actor"]["login"],
                    "actor_id": event_data["actor"]["id"],
                    "created_at": datetime.fromisoformat(event_data["created_at"].replace("Z", "+00:00")),
                    "issue_id": event_data.get("issue", {}).get("id"),
                    "issue_number": issue_number,
                    "repository_id": repo_id,
                    "repository_name": f"{owner}/{repo}",
                    "integration_user_id": user_id
                }
                
                await db.github_changelogs.update_one(
                    {"github_id": event_data["id"]},
                    {"$set": event_doc},
                    upsert=True
                )
                
        except Exception as e:
            logger.error(f"Error syncing events for issue {issue_number} in {owner}/{repo}: {e}")
    
    async def _sync_organization_members(self, github_client: GitHubClient, db, org: str, user_id: int):
        """Sync members of an organization"""
        try:
            page = 1
            while True:
                members = await github_client.get_organization_members(org, page=page, per_page=100)
                if not members:
                    break
                
                for member_data in members:
                    member_doc = {
                        "github_id": member_data["id"],
                        "login": member_data["login"],
                        "name": None,  # Basic member info doesn't include name
                        "email": None,
                        "bio": None,
                        "avatar_url": member_data.get("avatar_url"),
                        "html_url": member_data["html_url"],
                        "company": None,
                        "location": None,
                        "created_at": None,
                        "updated_at": datetime.utcnow(),
                        "public_repos": 0,
                        "public_gists": 0,
                        "followers": 0,
                        "following": 0,
                        "integration_user_id": user_id
                    }
                    
                    await db.github_users.update_one(
                        {"github_id": member_data["id"]},
                        {"$set": member_doc},
                        upsert=True
                    )
                
                if len(members) < 100:
                    break
                page += 1
                    
        except Exception as e:
            logger.error(f"Error syncing organization members for {org}: {e}")